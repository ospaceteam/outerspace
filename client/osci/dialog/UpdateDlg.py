#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from ige import log
import ige.version
import os
from osci import client, gdata, res
import pygameui as ui
import sys
import urllib2
import webbrowser

class UpdateDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()
        self.checkedForUpdate = False

    def display(self, caller = None, options = None):
        self.caller = caller
        self.options = options
        if self.checkedForUpdate:
            log.debug("Update already checked this session, skipping it")
            self.onCancel(None, None, _(""))
            return
        update = self.isUpdateAvailable()
        # check for new version only once per session
        self.checkedForUpdate = True
        if update is False:
            self.onCancel(None, None, _("Client is up-to-date"))
            return
        self.win.show()
        self.win.vProgress.visible = 0
        if update is True:
            self.setUpdateAction()

    def hide(self):
        self.win.hide()

    def onConfirm(self, widget, action, data):
        self.win.vStatusBar.text = _("Updating client...")
        # self.win.hide()

    def onLaunchBrowser(self, widget, action, data):
        """Launch web browser with download page."""
        log.debug("Launching browser", self.url)
        webbrowser.open(self.url)
        self.app.exit()

    def onDownloadAndInstall(self, widget, action, data):
        """Download and run installer of the new version"""
        self.setProgress('Preparing download...', 0, 1)
        # setup proxies
        proxies = {}
        if gdata.config.proxy.http != None:
            proxies['http'] = gdata.config.proxy.http
        log.debug('Using proxies', proxies)
        # get file
        try:
            # open URL
            opener = urllib2.build_opener(urllib2.ProxyHandler(proxies))
            ifh = opener.open(self.url)
            log.debug("Retrieving URL", ifh.geturl())
            # download file
            total = int(ifh.info()["Content-Length"])
            basename = os.path.basename(ifh.geturl())
            if not basename:
                log.message("URL is not a file")
                self.reportFailure(_("Error: URL does not point to a file."))
                return
            filename = os.path.join(self.options.configDir, basename)
            log.debug("Downloading file %s of size %d" % (filename, total) )
            ofh = open(filename, "wb")
            # download and report progress
            downloaded = 0
            while True:
                data = ifh.read(100000)
                if not data:
                    break
                ofh.write(data)
                downloaded += len(data)
                log.debug("Download progress", downloaded, total)
                self.setProgress("Downloading update...", downloaded, total)
            ifh.close()
            ofh.close()
        except urllib2.URLError, e:
            log.warning("Cannot download file")
            self.reportFailure(_("Cannot finish download: %(s)") % str(e.reason))
            return
        self.setProgress('Finishing update...')
        # now somehow handle file we downloaded
        if hasattr(os, "startfile"):
            # win32 has startfile defined
            log.debug("Starting file", filename)
            os.startfile(os.path.normpath(filename))
            self.app.exit()
        else:
            # other systems
            log.debug("Don't know what to do with", filename)
            self.reportFailure(_("Cannot run %s." % filename))

    def reportFailure(self, reason):
        self.win.vProgress.visible = 0
        self.win.vText.text = [reason]
        self.win.vCancel.text = ""
        self.win.vConfirm.text = _("OK")
        self.win.vConfirm.action = "onCancel"

    def setProgress(self, text, current = None, max = None):
        self.win.vProgress.visible = 1
        if text:
            self.win.vText.text = [text]
        if max != None:
            self.win.vProgress.min = 0
            self.win.vProgress.max = max
        if current != None:
            self.win.vProgress.value = current
        self.app.update()

    def onCancel(self, widget, action, data):
        self.win.hide()
        if self.caller:
            self.caller.display(message = data or _("Update skipped."))

    def isUpdateAvailable(self):
        """Check if client version matches server version and update client
        if neccessary"""
        log.message("Checking for update...")
        if "oslauncher" in sys.modules:
            log.message("Application launched from Outer Space Launcher -- will not update")
            return False
        updateMode = gdata.config.client.updatemode or "normal"
        # quit if update is disabled
        if updateMode == 'never':
            return False
        # compare server and client versions
        log.message("Retrieving server version")
        try:
            self.serverVersion = client.cmdProxy.getVersion()
        except KeyError:
            # call is not supported on older server versions
            log.debug("getVersion call not supported")
            self.reportFailure(_("Server does not support update feature yet. Check for updates manually, please."))
            return None
        log.debug("Comparing server and client versions", self.serverVersion, ige.version.version)
        matches = True
        for i in ("major", "minor", "revision", "status"):
            if ige.version.version[i] != self.serverVersion[i]:
                matches = False
        if matches:
            log.message("Versions match, no need to update")
            return False
        log.message("Version do not match, update is needed")
        return True

    def setUpdateAction(self):
        # check if update URL exists
        action, self.url = self.serverVersion["clientURLs"].get(sys.platform, self.serverVersion["clientURLs"]["*"])
        version = "%(major)s.%(minor)s.%(revision)s%(status)s" % self.serverVersion
        text = [
            _("Server requires client version %s. It is recommended to update your client.") % version,
        ]
        if action == "browser":
            # open webbrowser with given url
            text.append(_("Do you want to display download page?"))
            self.win.vConfirm.action = "onLaunchBrowser"
        elif action == "execute":
            # download and run binary installer
            text.append(_("Do you want to download and install new version?"))
            self.win.vConfirm.action = "onDownloadAndInstall"
        else:
            log.message("Unsupported update action", action)
            self.onCancel(None, None, _("Unsupported update type."))
        self.win.vText.text = text

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            movable = 0,
            title = _('Outer Space Update Available'),
            rect = ui.Rect((w - 424) / 2, (h - 124) / 2, 424, 124),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        ui.Text(self.win, layout = (5, 0, 16, 3), id = 'vText', background = self.win.app.theme.themeBackground, editable = 0)
        ui.ProgressBar(self.win, layout = (5, 3, 16, 1), id = 'vProgress')
        ui.Label(self.win, layout = (0, 0, 5, 4), icons = ((res.loginLogoImg, ui.ALIGN_W),))
        ui.Title(self.win, layout = (0, 4, 13, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (13, 4, 4, 1), id = 'vCancel', text = _("No"), action = 'onCancel')
        ui.TitleButton(self.win, layout = (17, 4, 4, 1), id = 'vConfirm', text = _("Yes"), action = 'onConfirm')

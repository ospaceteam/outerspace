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
from ige.version import version as clientVersion
import os
from osci import client, gdata, res
import pygame
import pygameui as ui
import re
import shutil
import sys
import urllib2
import tarfile

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
            self.onCancel(None, None, '')
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

    def performDownload(self, updateDirectory):
        """Download zip with new version"""
        log.debug('Downloading new version')
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
            # it unfortunately is not completely reliable
            for i in xrange(1,5):
                try:
                    ifh = opener.open(self.url)
                    log.debug("Retrieving URL", ifh.geturl())
                    # download file
                    total = int(ifh.info()["content-length"])
                    basename = re.search('(?<=filename=).*', ifh.info()["content-disposition"]).group(0)
                    break
                except KeyError:
                    pygame.time.wait(1)
            if not basename:
                log.message("URL is not a file")
                self.reportFailure(_("Error: URL does not point to a file."))
                return
            filename = os.path.join(updateDirectory, basename)
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
            return filename
        except urllib2.URLError, e:
            log.warning("Cannot download file")
            self.reportFailure(_("Cannot finish download: %(s)") % str(e.reason))
            return None

    def performUpdate(self, updateDirectory, filename):
        log.debug('Updating game to the new version')
        """Extract new version, and replace current directory with it"""
        self.setProgress('Preparing update...', 0, 4)
        # we expect archive contains one common prefix
        version = "%(major)s.%(minor)s.%(revision)s%(status)s" % self.serverVersion
        expectedDir = 'outerspace-' + version
        # now extraction!
        archive = tarfile.open(filename, 'r:gz')
        for member in archive.getnames():
            if not re.match('^{0}'.format(expectedDir), member):
                log.error("That archive is suspicious, because of file {0}".format(member))
                log.debug("Expected prefix directory is {0}".format(expectedDir))
                sys.exit(1)
        log.debug('Archive has expected directory structure')
        self.setProgress('Extracting new version...', 1, 4)
        archive.extractall(updateDirectory)
        log.debug('Update extracted to temporary directory')

        self.setProgress('Backing up old version...', 2, 4)
        # move current directory to temporary location
        actualDir = os.path.dirname(os.path.abspath(sys.argv[0]))
        actualDirTrgt = os.path.join(updateDirectory, os.path.basename(actualDir))
        if os.path.exists(actualDirTrgt):
            shutil.rmtree(actualDirTrgt)
        # we have to clear out of CWD, as it might get deleted
        # and python does not like that situation
        savedCWD = os.getcwd()
        os.chdir(updateDirectory)  # this is ensured to exist
        shutil.copytree(actualDir, actualDirTrgt)
        # ignore_errors is set because of windows
        # they prohibit removing of directory, if user browse it.
        # result is empty actualDir
        shutil.rmtree(actualDir, ignore_errors=True)
        log.debug('Old version backuped to {0}'.format(actualDirTrgt))

        self.setProgress('Applying new version...', 3, 4)

        # move newly extracted directory to original location
        extractedDir = os.path.join(updateDirectory, expectedDir)
        if os.path.exists(actualDir):
            # most likely due to Windows issue described above
            # as normally this directory should have been removed
            log.debug('Moving new version item by item')
            for item in os.listdir(extractedDir):
                shutil.move(os.path.join(extractedDir, item), os.path.join(actualDir, item))
            os.rmdir(extractedDir)
        else:
            log.debug('Moving new version in bulk')
            # simple version, non-windows
            shutil.move(extractedDir, actualDir)
        os.chdir(savedCWD)
        self.setProgress('Update complete', 4, 4)
        log.debug('Game prepared for restart')


    def performRestart(self, widget, action, data):
        text = [
            _("Game will now restart itself.")
        ]
        self.win.vConfirm.action = "onRestart"
        self.win.vConfirm.text = _("Restart")
        self.win.vCancel.text = ""
        self.win.vCancel.enabled = False
        self.win.vText.text = text
        self.win.title = _("Outer Space Update Complete")

    def onRestart(self, widget, action, data):
        if os.name == 'nt':
            quoted = map(lambda x: '"' + str(x) + '"', sys.argv)
            os.execl(sys.executable, sys.executable, *quoted)
        else:
            os.execl(sys.executable, sys.executable, *sys.argv)


    def onDownloadAndInstall(self, widget, action, data):

        updateDirectory = os.path.join(self.options.configDir, 'Update')
        if not os.path.isdir(updateDirectory):
            log.debug("Creating update directory")
            os.mkdir(updateDirectory)
        filename = self.performDownload(updateDirectory)
        if filename is None:
            self.onQuit(widget, action, data)
        self.performUpdate(updateDirectory, filename)
        self.performRestart(widget, action, data)


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

    def onQuit(self, widget, action, data):
        self.win.hide()
        self.app.exit()

    def isUpdateAvailable(self):
        """Check if client version matches server version and update client
        if neccessary"""
        log.message("Checking for update...")
        updateMode = gdata.config.client.updatemode or "normal"
        # quit if update is disabled
        if updateMode == 'never':
            return False
        # compare server and client versions
        log.message("Retrieving server version")
        self.serverVersion = client.cmdProxy.getVersion()
        log.debug("Comparing server and client versions", self.serverVersion, clientVersion)
        matches = True
        for i in ("major", "minor", "revision", "status"):
            if clientVersion[i] != self.serverVersion[i]:
                matches = False
        if matches:
            log.message("Versions match, no need to update")
            return False
        log.message("Version do not match, update is needed")
        return True

    def setUpdateAction(self):
        response = self.serverVersion["clientURLs"].get(sys.platform, self.serverVersion["clientURLs"]["*"])
        self.url = response
        # if the game resides in git repository, leave it on user, otherwise volunteer to perform update
        gameDirectory = os.path.realpath(os.path.dirname(sys.argv[0]))
        gitDir = os.path.join(gameDirectory, '.git')
        if os.path.isdir(gitDir):
            version = "%(major)s.%(minor)s.%(revision)s%(status)s" % self.serverVersion
            text = [
                _("Server requires client version %s. It is recommended to update your client.") % version,
                "",
                _('Please update your git repo to tag "%s"') % version
            ]
            self.win.vConfirm.action = "onQuit"
            self.win.vConfirm.text = _("OK")
            self.win.vStatusBar.layout = (0, 5, 17,1)
            self.win.vCancel.visible = 0
        else:
            version = "%(major)s.%(minor)s.%(revision)s%(status)s" % self.serverVersion
            text = [
                _("Server requires client version %s. It is necessary to update your client.") % version,
                "",
                _("Do you want Outer Space to perform update?")
            ]
            self.win.vConfirm.action = "onDownloadAndInstall"
            self.win.vCancel.action = "onQuit"
            self.win.vCancel.text = _("Quit")
        self.win.vText.text = text

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            movable = 0,
            title = _('Outer Space Update Available'),
            rect = ui.Rect((w - 424) / 2, (h - 144) / 2, 424, 144),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        ui.Text(self.win, layout = (5, 0, 16, 4), id = 'vText', background = self.win.app.theme.themeBackground, editable = 0)
        ui.ProgressBar(self.win, layout = (0, 4, 21, 1), id = 'vProgress')
        ui.Label(self.win, layout = (0, 0, 5, 4), icons = ((res.loginLogoImg, ui.ALIGN_W),))
        ui.Title(self.win, layout = (0, 5, 13, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (13, 5, 4, 1), id = 'vCancel', text = _("No"), action = 'onCancel')
        ui.TitleButton(self.win, layout = (17, 5, 4, 1), id = 'vConfirm', text = _("Yes"), action = 'onConfirm')

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

import os
import os.path
import gettext
import re

import pygame
import pygameui as ui
from osci import client, gdata, res
import ige.ospace.Const as Const
from ige import log
import resources

from ChangePasswordDlg import ChangePasswordDlg

class OptionsDlg:
    """Displays options dialog.

    Dialog can change display flags, display resolution, client language
    and proxy settings.
    Proxy can have one of following formats:
    http://username:password@host:port
    http://username@host:port
    http://host:port
    http://host
    where port must be integer value.
    Options are saved to file imediately, after users press OK button.
    """


    def __init__(self, app):
        self.app = app
        self.changePasswordDlg = ChangePasswordDlg(app)
        self.languages = {}
        self.languages['en']=_('English')
        self.languages['cs']=_('Czech')
        self.languages['fr']=_('French')
        self.languages['de']=_('German')
        self.resolutions = ["FULLSCREEN", "800x600", "1024x768", "1280x800", "1280x1024", "1366x768", "1440x900","1400x1050","1600x900","1680x1050","1600x1200","1920x1080","1920x1200"]
        self.curLang = gdata.config.client.language
        self.createUI()

    def display(self, caller = None, message = None):
        self.caller = caller
        if message is not None:
            self.win.setStatus(message)
        self.show()
        # show window
        if not self.win.visible:
            self.win.show()

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()

    def update(self):
        if self.win.visible:
            self.show()

    def show(self):
        # reading resolution info
        if gdata.config.display.resolution != None:
            resolution = gdata.config.display.resolution
            self.win.vResolution2.text = resolution

        self.win.vResolution.text = _("Select Mode")
        self.win.vResolution.action = "onSelectResolution"

        # reading client language
        if gdata.config.client.language != None:
            lang = gdata.config.client.language
            try:
                self.win.vLangSel.text = self.languages[lang]
            except:
                self.win.vLangSel.text = lang

        # reading proxy settings
        if gdata.config.proxy.http != None:
            proxy = gdata.config.proxy.http
            m = re.match('^http://(.*?):(.*?)@(.*?):(\d+)', proxy)
            host = ''
            port = ''
            username = ''
            password = ''
            if m == None:
                m = re.match('^http://(.*?)@(.*?):(\d+)', proxy)
                if m == None:
                    m = re.match('^http://(.*?):(\d+)', proxy)
                    if m == None:
                        m = re.match('^http://(.*?)', proxy)
                        if m != None:
                            host = m.group(1)
                    else:
                        host = m.group(1)
                        port = m.group(2)
                else:
                    username = m.group(1)
                    host = m.group(2)
                    port = m.group(3)
            else:
                username = m.group(1)
                password = m.group(2)
                host = m.group(3)
                port = m.group(4)

            self.win.vProxyHost.text = host
            self.win.vProxyPort.text = port
            self.win.vProxyUsername.text = username
            self.win.vProxyPassword.text = password

        self.win.vTheme.text = _("Select Theme")
        self.win.vTheme2.text = gdata.config.client.theme
        self.win.vTheme.action = "onSelectTheme"

        # reading defaults
        if gdata.config.defaults.reportfinalization != None:
            val = gdata.config.defaults.reportfinalization
            self.win.vReportFin.checked = val == 'yes'

        if gdata.config.defaults.showredirects != None:
            val = gdata.config.defaults.showredirects
            self.win.vRedirects.checked = val == 'yes'

        if gdata.config.defaults.showcoords != None:
            val = gdata.config.defaults.showcoords
            self.win.vCoords.checked = val == 'yes'

        if gdata.config.defaults.highlights != None:
            val = gdata.config.defaults.highlights
            self.win.vHighlights.checked = val == 'yes'

        if gdata.config.defaults.displayhelp != None:
            val = gdata.config.defaults.displayhelp
            self.win.vDisplayHelp.checked = val == 'yes'

        if gdata.config.defaults.showminimap != None:
            val = gdata.config.defaults.showminimap
            self.win.vShowMinimap.checked = val == 'yes'

        if gdata.config.defaults.showgatesystems != None:
            val = gdata.config.defaults.showgatesystems
            self.win.vShowGateSystems.checked = val == 'yes'

        if gdata.config.defaults.showmapgrid != None:
            val = gdata.config.defaults.showmapgrid
            self.win.vShowMapGrid.checked = val == 'yes'

        if gdata.config.defaults.showmapscanners != None:
            val = gdata.config.defaults.showmapscanners
            self.win.vShowMapScanners.checked = val == 'yes'

        if gdata.config.defaults.showfleetlines != None:
            val = gdata.config.defaults.showfleetlines
            self.win.vShowMapFleetLines.checked = val == 'yes'

        if gdata.config.defaults.alternateviewmode != None:
            val = gdata.config.defaults.alternateviewmode
            self.win.vShowAlternateView.checked = val == 'yes'

        if gdata.config.defaults.showPlayerZones != None:
            val = gdata.config.defaults.showplayerzones
            self.win.vShowPlayerZones.checked = val == 'yes'

        # login defaults
        self.win.vAutoLogin.enabled = False
        if gdata.savePassword:
            self.win.vSavePassword.enabled = True
            self.win.vSavePassword.checked = True
            self.win.vAutoLogin.enabled = True
        elif (gdata.config.game.lastpasswordcrypted != None) and (gdata.config.game.lastpasswordcrypted != ''):
            self.win.vSavePassword.enabled = True
            self.win.vSavePassword.checked = False
        else:
            self.win.vSavePassword.enabled = False
            self.win.vSavePassword.checked = False

        if gdata.config.game.autologin != None:
            val = gdata.config.game.autologin
            if self.win.vAutoLogin.enabled:
                self.win.vAutoLogin.checked = val == 'yes'

        # sounds/music
        if gdata.config.defaults.sound != None:
            val = gdata.config.defaults.sound
        else:
            val = "no"
        self.win.vSoundEnabled.checked = val == "yes"
        self.win.vSoundVolume.slider.min = 0
        self.win.vSoundVolume.slider.max = 110
        if gdata.config.defaults.soundvolume != None:
            val = float(gdata.config.defaults.soundvolume)
        else:
            val = 100
        self.win.vSoundVolume.slider.position = val
        # disabled because of a bug in pygame
        self.win.vSoundEnabled.enabled = False
        self.win.vSoundVolume.enabled = False

        if gdata.config.defaults.music != None:
            val = gdata.config.defaults.music
        else:
            val = "no"
        self.win.vMusicEnabled.checked = val == "yes"
        self.win.vMusicVolume.slider.min = 0
        self.win.vMusicVolume.slider.max = 110
        if gdata.config.defaults.musicvolume != None:
            val = float(gdata.config.defaults.musicvolume)
        else:
            val = 100
        self.win.vMusicVolume.slider.position = val
        # disabled because of a bug in pygame
        self.win.vMusicEnabled.enabled = False
        self.win.vMusicVolume.enabled = False

        self.win.vChangePassword.enabled = client.db is not None

    def onCancel(self, widget, action, data):
        self.hide()
        if self.caller:
            self.caller.display()

    def onOK(self, widget, action, data):
        # set client language
        gdata.config.client.language = self.curLang

        # set proxy
        host = self.win.vProxyHost.text
        port = self.win.vProxyPort.text
        username = self.win.vProxyUsername.text
        password = self.win.vProxyPassword.text

        proxy = ''
        # host must be always present
        if len(host) > 0:
            proxy += host
            if len(port) > 0:
                proxy += ':'
                proxy += port
            if len(password) > 0 and len(username):
                proxy = username + ':' + password + '@' + proxy
            elif len(username) > 0:
                proxy = username + '@' + proxy

            if len(proxy) > 0:
                proxy = 'http://' + proxy

        if len(proxy) > 0:
            gdata.config.proxy.http = proxy
        else:
            # if host not present, delete proxy section
            gdata.config.proxy = None

        # defaults
        gdata.config.defaults.reportfinalization = 'yes' if self.win.vReportFin.checked else 'no'
        gdata.config.defaults.showredirects = 'yes' if self.win.vRedirects.checked else 'no'
        gdata.config.defaults.showcoords = 'yes' if self.win.vCoords.checked else 'no'
        gdata.config.defaults.highlights = 'yes' if self.win.vHighlights.checked else 'no'
        gdata.config.defaults.displayhelp = 'yes' if self.win.vDisplayHelp.checked else 'no'
        gdata.config.defaults.showminimap = 'yes' if self.win.vShowMinimap.checked else 'no'
        gdata.config.defaults.showgatesystems = 'yes' if self.win.vShowGateSystems.checked else 'no'
        gdata.config.defaults.showmapgrid = 'yes' if self.win.vShowMapGrid.checked else 'no'
        gdata.config.defaults.showmapscanners = 'yes' if self.win.vShowMapScanners.checked else 'no'
        gdata.config.defaults.showfleetlines = 'yes' if self.win.vShowMapFleetLines.checked else 'no'
        gdata.config.defaults.alternateviewmode = 'yes' if self.win.vShowAlternateView.checked else 'no'
        gdata.config.defaults.showplayerzones = 'yes' if self.win.vShowPlayerZones.checked else 'no'

        gdata.config.defaults.sound = 'yes' if self.win.vSoundEnabled.checked else 'no'
        gdata.config.defaults.soundvolume = self.win.vSoundVolume.slider.position
        gdata.config.defaults.music = 'yes' if self.win.vMusicEnabled.checked else 'no'
        gdata.config.defaults.musicvolume = self.win.vMusicVolume.slider.position

        gdata.config.game.autologin = 'yes' if self.win.vAutoLogin.checked else 'no'

        if self.win.vSavePassword.checked:
            gdata.savePassword = True
        else:
            gdata.savePassword = False
            gdata.config.game.lastpasswordcrypted = None

        ui.SkinableTheme.enableMusic(self.win.vMusicEnabled.checked)
        ui.SkinableTheme.enableSound(self.win.vSoundEnabled.checked)

        self.hide()
        if self.caller:
            self.caller.display()    # Redisplay login dlg
        elif gdata.mainGameDlg:
            gdata.mainGameDlg.update(configUpdated=True) # redraw screen (highlights etc)

    def onSelectTheme(self, widget, action, data):
        items = []
        themeDir = resources.get("themes")
        for term in os.listdir(themeDir):
            if os.path.isfile(os.path.join(themeDir, term, "config.ini")) and not term.startswith("."):
                item = ui.Item(term, tTheme = term)
                items.append(item)
        self.twin.vThemes.items = items
        self.twin.vThemes.itemsChanged()
        self.twin.show()

    def onThemeCancel(self, widget, action, data):
        self.twin.hide()

    def onThemeSelected(self, widget, action, data):
        self.recipientObjID = []
        text = ""
        if not self.twin.vThemes.selection:
            return
        curTheme = self.twin.vThemes.selection[0].tTheme
        # set theme for ui
        ui.SkinableTheme.setSkin(os.path.join(resources.get("themes"), curTheme))
        res.prepareUIIcons(ui.SkinableTheme.themeIcons)
        ui.SkinableTheme.loadMusic(gdata.config.defaults.mymusic)
        ui.SkinableTheme.playMusic()
        # update foreground colors
        gdata.sevColors[gdata.CRI] = (ui.SkinableTheme.themeCritical)
        gdata.sevColors[gdata.MAJ] = (ui.SkinableTheme.themeMajor)
        gdata.sevColors[gdata.MIN] = (ui.SkinableTheme.themeMinor)
        gdata.sevColors[gdata.NONE] = (ui.SkinableTheme.themeNone)
        gdata.sevColors[gdata.DISABLED] = (ui.SkinableTheme.themeDisabled)
        # all OK? (no exception) -> store settings
        gdata.config.client.theme = curTheme
        self.win.vTheme2.text = curTheme
        self.twin.hide()

    def onSelectLanguage(self, widget, action, data):
        items = []
        items.append(ui.Item(self.languages['en'],tLanguage = 'en'))
        langDir = resources.get('translations')
        for term in os.listdir(langDir):
            if os.path.isfile(os.path.join(langDir, term,"LC_MESSAGES", "OSPACE.mo")) and not term.startswith("."):
                if self.languages.has_key(term):
                    item = ui.Item(self.languages[term], tLanguage = term)
                else:
                    item = ui.Item(term, tLanguage = term)
                items.append(item)
        self.lwin.vLanguages.items = items
        self.lwin.vLanguages.itemsChanged()
        self.lwin.show()

    def onLanguageCancel(self, widget, action, data):
        self.lwin.hide()

    def onLanguageSelected(self, widget, action, data):
        self.recipientObjID = []
        text = ""
        if not self.lwin.vLanguages.selection:
            return
        self.curLang = self.lwin.vLanguages.selection[0].tLanguage
        self.lwin.hide()
        if self.curLang == 'en':
            tran = gettext.NullTranslations()
        else:
            tran = gettext.translation('OSPACE', resources.get('translations'), languages = [self.curLang])
        tran.install(unicode = 1)
        try:
            self.win.vLangSel.text = self.languages[self.curLang]
        except:
            self.win.vLangSel.text = self.curLang
        self.win.setStatus(_("You should restart client to change the language."))


    def onSelectResolution(self, widget, action, data):
        items = []
        for mode in self.resolutions:
            items.append(ui.Item(mode,tRes = mode))
        self.reswin.vResolutions.items = items
        self.reswin.vResolutions.itemsChanged()
        self.reswin.show()

    def onResolutionCancel(self, widget, action, data):
        self.reswin.hide()

    def onResolutionSelected(self, widget, action, data):
        if not self.reswin.vResolutions.selection:
            return
        curMode = self.reswin.vResolutions.selection[0].tRes
        if curMode != "FULLSCREEN":
            try:
                width,height = curMode.split('x')
            except:
                self.win.setStatus(_("The mode you selected is not properly formatted."))
        gdata.config.display.resolution = curMode
        self.win.vResolution2.text = curMode
        self.reswin.hide()
        self.win.setStatus(_("You have to restart client to change the resolution."))

    def onChangeMusicVolume(self, widget, action, data):
        ui.SkinableTheme.setMusicVolume(float(self.win.vMusicVolume.slider.position) / 100.0)

    def onChangeSoundVolume(self, widget, action, data):
        ui.SkinableTheme.enableSound(self.win.vSoundEnabled.checked)
        ui.SkinableTheme.setVolume(self.win.vSoundVolume.slider.position / 100.0)

    def onChangeSavePassword(self, widget, action, data):
        if self.win.vSavePassword.checked:
            self.win.vAutoLogin.enabled = True
        else:
            self.win.vAutoLogin.enabled = False
            self.win.vAutoLogin.checked = False

    def onChangePassword(self, widget, action, data):
        self.changePasswordDlg.display(self)

    def createUI(self):
        screenWidth, screenHeight = gdata.scrnSize
        # size of dialog in layout metrics (for SimpleGridLM)
        cols = 33
        rows = 18
        # dialog width and height in pixels
        width = cols * 20 + 5
        height = rows * 20 + 4
        #creating dialog window
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _("Options"),
            rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True
        )
        self.win.subscribeAction('*', self)
        # first row is window title
        rows -= 1

        # Resolution
        ui.Title(self.win, layout = (1, 1, 5, 1), text = _('Resolution'),
            align = ui.ALIGN_NONE, font = 'normal-bold')

        ui.Button(self.win, layout = (1, 2, 5, 1), id = "vResolution", align = ui.ALIGN_W)
        ui.ActiveLabel(self.win, layout = (1, 3, 5, 1), id = "vResolution2")
        width = 304  # 15 * 20 + 4
        height = 264 # 13 * 20 + 4
        self.reswin = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            titleOnly = 0,
            movable = 0,
            title = _("Select resolution"),
            rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
        )
        self.reswin.subscribeAction('*', self)
        # rename
        ui.Listbox(self.reswin, layout = (0, 0, 15, 11), id = 'vResolutions', columnLabels = 0,
            columns = ((None, 'text', 0, ui.ALIGN_W),), multiselection = 0)
        # status bar + submit/cancel
        ui.TitleButton(self.reswin, layout = (10, 11, 5, 1), text = _("Select"), action = 'onResolutionSelected')
        ui.TitleButton(self.reswin, layout = (5, 11, 5, 1), text = _("Cancel"), action = 'onResolutionCancel')
        ui.Title(self.reswin, id = 'vStatusBar', layout = (0, 11, 5, 1), align = ui.ALIGN_W)

        # Languages
        ui.Title(self.win, layout = (1, 5, 5, 1), text = _('Language'),
            align = ui.ALIGN_NONE, font = 'normal-bold')
        try:
            longLang = self.languages[self.curLang]
        except:
            longLang = self.curLang
        ui.Button(self.win, layout = (1, 6, 5, 1), text = longLang, id = 'vLangSel', action = 'onSelectLanguage')
        lcols = 12
        lrows = 6
        width = lcols * 20 + 4
        height = lrows * 20 + 4
        self.lwin = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            titleOnly = 0,
            movable = 0,
            title = _("Select language"),
            rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
        )
        self.lwin.subscribeAction('*', self)
        # rename
        ui.Listbox(self.lwin, layout = (0, 0, lcols, lrows-2), id = 'vLanguages', columnLabels = 0,
            columns = ((None, 'text', 0, ui.ALIGN_W),), multiselection = 0, sortedBy=('text', 1))
        # status bar + submit/cancel
        ui.TitleButton(self.lwin, layout = (lcols-5, lrows-2, 5, 1), text = _("Select"), action = 'onLanguageSelected')
        ui.TitleButton(self.lwin, layout = (lcols-10, lrows-2, 5, 1), text = _("Cancel"), action = 'onLanguageCancel')
        ui.Title(self.lwin, id = 'vStatusBar', layout = (0, lrows-2, lcols-10, 1), align = ui.ALIGN_W)

        # Theme
        ui.Title(self.win, layout = (1, 9, 5, 1), text = _('Themes'),
            align = ui.ALIGN_NONE, font = 'normal-bold')
        ui.Button(self.win, layout = (1, 10, 5, 1), id = "vTheme", align = ui.ALIGN_W)
        ui.ActiveLabel(self.win, layout = (1, 11, 5, 1), id = "vTheme2")
        width = 304  # 15 * 20 + 4
        height = 264 # 13 * 20 + 4
        self.twin = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            titleOnly = 0,
            movable = 0,
            title = _("Select theme"),
            rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
        )
        self.twin.subscribeAction('*', self)

        # rename
        ui.Listbox(self.twin, layout = (0, 0, 15, 11), id = 'vThemes', columnLabels = 0,
            columns = ((None, 'text', 0, ui.ALIGN_W),), multiselection = 0, sortedBy=('text', 1))
        # status bar + submit/cancel
        ui.TitleButton(self.twin, layout = (10, 11, 5, 1), text = _("Select"), action = 'onThemeSelected')
        ui.TitleButton(self.twin, layout = (5, 11, 5, 1), text = _("Cancel"), action = 'onThemeCancel')
        ui.Title(self.twin, id = 'vStatusBar', layout = (0, 11, 5, 1), align = ui.ALIGN_W)

        # Defaults
        ui.Title(self.win, layout = (7, 7, 25, 1), text = _('Default settings'),
            align = ui.ALIGN_NONE, font = 'normal-bold')
        ui.Check(self.win, layout = (7, 8, 8, 1), text = _('Report finalization'), id = 'vReportFin',
            checked = 0)
        ui.Check(self.win, layout = (15, 8, 8, 1), text = _('Display help/tooltip'), id = 'vDisplayHelp',
            checked = 1)
        ui.Check(self.win, layout = (23, 8, 9, 1), text = _('Show coordinates'), id = 'vCoords',
            checked = 1)
        ui.Check(self.win, layout = (7 ,9 ,8 ,1), text = _('Players highlight'), id = 'vHighlights',
            checked = 1)
        ui.Check(self.win, layout = (15, 9, 8, 1), text = _('Show minimap'), id = 'vShowMinimap',
            checked = 1)
        ui.Check(self.win, layout = (23, 9, 8, 1), text = _('Show gate systems'), id = 'vShowGateSystems',
            checked = 1)
        ui.Check(self.win, layout = (7, 10, 8, 1), text = _('Show redirects'), id = 'vRedirects',
            checked = 1, tooltipTitle = _('Starmap hotkey:'), tooltip = _('CTRL-R'))
        ui.Check(self.win, layout = (15, 10, 8, 1), text = _('Show map grid'), id = 'vShowMapGrid',
            checked = 1, tooltipTitle = _('Starmap hotkey'), tooltip = _('CTRL-G'))
        ui.Check(self.win, layout = (23, 10, 8, 1), text = _('Alternate system info'), id = 'vShowAlternateView',
            checked = 0, tooltipTitle = _('Starmap hotkey'), tooltip = _('CTRL-A'))
        ui.Check(self.win, layout = (7, 11, 8, 1), text = _('Show map scanners'), id = 'vShowMapScanners',
            checked = 1, tooltipTitle = _('Starmap hotkey'), tooltip = _('CTRL-S'))
        ui.Check(self.win, layout = (15, 11, 8, 1), text = _('Show fleet lines'), id = 'vShowMapFleetLines',
            checked = 1, tooltipTitle = _('Starmap hotkey'), tooltip = _('CTRL-L'))
        ui.Check(self.win, layout = (23, 11, 8, 1), text = _('Show player zones'), id = 'vShowPlayerZones',
            checked = 0, tooltipTitle = _('Starmap hotkey'), tooltip = _('CTRL-P'))

        # Login settings
        ui.Title(self.win, layout = (7,13, 15, 1), text = _('Login settings'),
            align = ui.ALIGN_NONE, font = 'normal-bold')
        ui.Check(self.win, layout = (15,14,8,1), text = _('Auto-login'), id = 'vAutoLogin',
            checked = 0)
        ui.Check(self.win, layout = (7,14,8,1), text = _('Remember password'), id = 'vSavePassword',
            checked = 0, action = "onChangeSavePassword")
        ui.Button(self.win, layout = (23.5, 13, 9, 1), id = "vChangePassword", text = _("Change password"), action = 'onChangePassword', align = ui.ALIGN_NONE)

        # proxy settings
        ui.Title(self.win, layout = (13, 1, 9, 1), text = _('Proxy'), font = 'normal-bold')
        ui.Label(self.win, layout = (13, 2, 4, 1), text = _('Host:'), align = ui.ALIGN_E)
        ui.Entry(self.win, layout = (17, 2, 5, 1), id = 'vProxyHost', align = ui.ALIGN_W, orderNo = 1)
        ui.Label(self.win, layout = (13, 3, 4, 1), text = _('Port:'), align = ui.ALIGN_E)
        ui.Entry(self.win, layout = (17, 3, 5, 1), id = 'vProxyPort', align = ui.ALIGN_W, orderNo = 2)
        ui.Label(self.win, layout = (13, 4, 4, 1), text = _('Username:'), align = ui.ALIGN_E)
        ui.Entry(self.win, layout = (17, 4, 5, 1), id = 'vProxyUsername', align = ui.ALIGN_W, orderNo = 3)
        ui.Label(self.win, layout = (13, 5, 4, 1), text = _('Password:'), align = ui.ALIGN_E)
        ui.Entry(self.win, layout = (17, 5, 5, 1), id = 'vProxyPassword', align = ui.ALIGN_W, orderNo = 4)

        # sound options
        ui.Title(self.win, layout = (23, 1, 9, 1), text = _('Sound / Music'), font = 'normal-bold')
        ui.Check(self.win, layout = (23, 2, 9, 1), text = _('Sounds'), id = 'vSoundEnabled',
            checked = 1)
        ui.Scrollbar(self.win, layout = (23, 3, 9, 1), id = 'vSoundVolume',
            action = "onChangeSoundVolume")
        ui.Check(self.win, layout = (23, 4, 9, 1), text = _('Music'), id = 'vMusicEnabled',
            checked = 1)
        ui.Scrollbar(self.win, layout = (23, 5, 9, 1), id = 'vMusicVolume',
            action = "onChangeMusicVolume")

        # dialog bottom line
        ui.Title(self.win, layout = (0, rows - 1, cols - 10, 1))
        ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Cancel"), action = 'onCancel')
        ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("OK"), action = 'onOK')

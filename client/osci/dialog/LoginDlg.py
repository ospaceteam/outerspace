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

import pygameui as ui
from osci import client, gdata, res
from NewAccountDlg import NewAccountDlg
from PlayerSelectDlg import PlayerSelectDlg
from ConfirmDlg import ConfirmDlg
from OptionsDlg import OptionsDlg
import binascii
from ige import log
from igeclient.IClient import IClientException

class LoginDlg:

    def __init__(self, app):
        self.app = app
        self.newAccDlg = NewAccountDlg(app)
        self.playerSelectDlg = PlayerSelectDlg(app)
        self.confirmDlg = ConfirmDlg(app)
        self.firstlogin = True
        self.versionChecked = False
        self.createUI()

    def display(self, caller = None, message = None):
        self.caller = caller
        # get game names from the server
        try:
            self.gameIDs = client.cmdProxy.getRegisteredGames()
        except IClientException:
            # server is probably down, what to do?
            self.gameIDs = {"UNDEFINED": "Not available"}
        except KeyError:
            # server does not support this call
            self.gameIDs = {"Alpha": "Alpha"}
        # show / hide new account button
        self.win.vCreate.visible = gdata.config.game.accountcreated == None
        # fill in default values
        if gdata.config.game.lastlogin != None:
            self.win.vLogin.text = gdata.config.game.lastlogin
        if gdata.config.game.lastpassword:
            self.win.vPassword.text = gdata.config.game.lastpassword
            self.win.vSavePassword.checked = True
        if gdata.config.game.lastpasswordcrypted:
            self.win.vPassword.text = binascii.a2b_base64(gdata.config.game.lastpasswordcrypted)
            self.win.vSavePassword.checked = True
        if gdata.config.game.autologin == 'yes':
            self.win.vAutoLogin.checked = True
        if not gdata.config.game.lastgameid:
            gdata.config.game.lastgameid = 'Alpha'
        if gdata.config.game.lastgameid not in self.gameIDs:
            # use first gameid returned by server
            gdata.config.game.lastgameid = sorted(self.gameIDs.keys())[0]
        self.win.vUniverse.text = self.gameIDs[gdata.config.game.lastgameid]
        self.win.vUniverse.data = gdata.config.game.lastgameid
        # disable Universe selection if there's just one universe on the server
        self.win.vUniverse.enabled = len(self.gameIDs) > 1
        self.win.vMessage.text = message
        #if gdata.config.game.autologin != 'yes':    # enable this to disable auto-login after change in options
        #    self.firstlogin = false
        self._updatePasswordGData()
        self.win.show()
        if gdata.config.game.autologin == 'yes':
            self.autoLogin()

    def hide(self):
        self.win.hide()

    def autoLogin(self):
        if self.firstlogin:
            self.firstlogin = False
            self.win.vMessage.text = _('Auto-login in progress ...')
            login = self.win.vLogin.text
            password = self.win.vPassword.text
            gameID = self.win.vUniverse.data
            self.doLogin(gameID,login,password)

    def onLogin(self, widget, action, data):
        self.firstlogin = False
        login = self.win.vLogin.text
        password = self.win.vPassword.text
        gameID = self.win.vUniverse.data
        self.win.vMessage.text = _('Login in progress ...')
        # self.win.hide()
        self.doLogin(gameID,login,password)

    def doLogin(self,gameID,login,password):
        result = client.login(gameID, login, password)
        self.win.hide()
        if result == 1:
            gdata.config.game.lastlogin = login
            # TODO: remove in 0.6
            gdata.config.game.lastpassword = None
            #
            if gdata.savePassword:
                gdata.config.game.lastpasswordcrypted = binascii.b2a_base64(password).strip()
            else:
                gdata.config.game.lastpasswordcrypted = None
            gdata.config.game.lastgameid = gameID
            gdata.config.game.accountcreated = 1
            # write configuration
            gdata.config.save()
            gdata.config.game.lastpasswordcrypted = binascii.b2a_base64(password).strip()
            self.playerSelectDlg.display(self)
        elif result == 2:
            pass
        else:
            # login failed
            self.win.vPassword.text = ''
            self.win.vMessage.text = _('Wrong login and/or password')
            self.win.show()

    def onCancel(self, widget, action, data):
        self.win.hide()
        if self.caller:
            self.caller.display()
        else:
            self.app.exit()

    def onCreateAccount(self, widget, action, data):
        self.win.hide()
        self.newAccDlg.display(self)

    def onOptions(self, widget, action, data):
        self.win.hide()
        gdata.config.game.lastpasswordcrypted = binascii.b2a_base64(self.win.vPassword.text).strip()
        OptionsDlg(gdata.app).display(self)

    def onUniverse(self, widget, action, data):
        # create menu
        items = list()
        index = 0
        for gameID in sorted(self.gameIDs.keys()):
            item = ui.Item(self.gameIDs[gameID], data = gameID, action = "onUniverseSelected")
            items.append(item)
            index += 1
        self.universeMenu.items = items
        # show
        self.universeMenu.show((self.win.rect.x + 11 * 20 + 2, self.win.rect.y + 20 + 2))

    def _updatePasswordGData(self):
        if self.win.vSavePassword.checked:
            self.win.vAutoLogin.enabled = True
            gdata.savePassword = True
        else:
            gdata.savePassword = False
            gdata.config.game.lastpasswordcrypted = None
            self.win.vAutoLogin.enabled = False
            self.win.vAutoLogin.checked = False

        if self.win.vAutoLogin.checked:
            gdata.config.game.autologin = 'yes'
        else:
            gdata.config.game.autologin = 'no'


    def onSavePassword(self, widget, action, data):
        self._updatePasswordGData()

    def onAutoLogin(self, widget, action, data):
        self._updatePasswordGData()

    def onUniverseSelected(self, widget, action, data):
        self.win.vUniverse.text = self.gameIDs[data]
        self.win.vUniverse.data = data

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            movable = 0,
            title = _('Outer Space Login'),
            rect = ui.Rect((w - 424) / 2, (h - 164) / 2, 424, 164),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True,
        )
        self.win.subscribeAction('*', self)
        ui.Label(self.win,
            text = _('Universe'),
            align = ui.ALIGN_E,
            layout = (5, 0, 6, 1)
        )
        ui.Button(self.win, id = 'vUniverse',
            align = ui.ALIGN_W,
            layout = (11, 0, 10, 1),
            action = "onUniverse",
        )
        ui.Label(self.win,
            text = _('Login'),
            align = ui.ALIGN_E,
            layout = (5, 1, 6, 1)
        )
        ui.Entry(self.win, id = 'vLogin',
            align = ui.ALIGN_W,
            layout = (11, 1, 10, 1),
            orderNo = 1
        )
        ui.Label(self.win,
            text = _('Password'),
            align = ui.ALIGN_E,
            layout = (5, 2, 6, 1),
        )
        ui.Entry(self.win, id = 'vPassword',
            align = ui.ALIGN_W,
            showChar = '*',
            layout = (11, 2, 10, 1),
            orderNo = 2
        )
        ui.Check(self.win, layout = (16.5,3,5,1), text = _('Auto-login'), id = 'vAutoLogin',
            checked = 0, action = "onAutoLogin")
        ui.Check(self.win, layout = (11.25,3,5,1), text = _('Remember'), id = 'vSavePassword',
            checked = 0, action = "onSavePassword")
        ui.Button(self.win, layout = (11, 4, 10, 1), text = _("Options"), action = "onOptions", id = "vOptions")
        ui.Button(self.win, layout = (11, 5, 10, 1), text = _("New account"),
            action = "onCreateAccount", id = "vCreate")
        ui.Title(self.win, layout = (0, 6, 11, 1), id = 'vMessage', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (11, 6, 5, 1), text = _('Exit'), action = 'onCancel')
        loginBtn = ui.TitleButton(self.win, layout = (16, 6, 5, 1), text = _('Login'), action = 'onLogin')
        ui.Label(self.win, layout = (0, 0, 5, 4), icons = ((res.loginLogoImg, ui.ALIGN_W),))
        self.win.acceptButton = loginBtn
        # Universe selection
        self.universeMenu = ui.Menu(self.app, title = _("Universes"),
            width = 10,
        )
        self.universeMenu.subscribeAction("*", self)

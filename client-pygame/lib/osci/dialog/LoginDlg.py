#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygameui as ui
from osci import client, gdata, res, version, revision
from MainGameDlg import MainGameDlg
from NewAccDlg import NewAccDlg
from ConfirmDlg import ConfirmDlg
from OptionsDlg import OptionsDlg
import binascii
from ige import log

class LoginDlg:

	def __init__(self, app):
		self.app = app
		self.newAccDlg = NewAccDlg(app)
		self.confirmDlg = ConfirmDlg(app)
		self.firstlogin = True
		self.createUI()

	def display(self, caller = None, message = None):
		self.caller = caller
		self.win.vCreate.visible = gdata.config.game.accountcreated == None
		#self.win.vSavePassword.visible = gdata.config.game.accountcreated != None
		#self.win.vSavePassword.checked = False
		#self.win.vAutoLogin.checked = False
		if gdata.config.game.lastlogin != None:
			self.win.vLogin.text = gdata.config.game.lastlogin
		if gdata.config.game.lastpassword:
			self.win.vPassword.text = gdata.config.game.lastpassword
		if gdata.config.game.lastpasswordcrypted:
			self.win.vPassword.text = binascii.a2b_base64(gdata.config.game.lastpasswordcrypted)
		if not gdata.config.game.lastgameid:
			gdata.config.game.lastgameid = 'Alpha'
		self.win.vMessage.text = message
		#if gdata.config.game.autologin != 'yes':	# enable this to disable auto-login after change in options
		#	self.firstlogin = false
		self.win.show()

	def hide(self):
		self.win.hide()

	def autoLogin(self):
		if self.firstlogin:
			self.firstlogin = False
			self.win.vMessage.text = _('Auto-login in progress ...')
			login = self.win.vLogin.text
			password = self.win.vPassword.text
			gameID = gdata.config.game.lastgameid
			self.doLogin(gameID,login,password)

	def onLogin(self, widget, action, data):
		self.firstlogin = False
		login = self.win.vLogin.text
		password = self.win.vPassword.text
		gameID = gdata.config.game.lastgameid
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
			# Auto-login
			#if self.win.vAutoLogin.checked:
			#	gdata.config.game.autologin = 'yes'
			#else:
			#	gdata.config.game.autologin = 'no'
			# write configuration
			gdata.config.save('var/osci.ini')
			# check version
			if client.lastClientVersion != version or client.lastClientRevision != revision:
				# wow, a different version!
				self.confirmDlg.display(
					_("Your client version does not match server version %d.%d.%d%s [Revision %d]. Do you want to continue?") % (
						client.lastClientVersion[0],
						client.lastClientVersion[1],
						client.lastClientVersion[2],
						client.lastClientVersion[3],
						client.lastClientRevision,
					),
					_('Yes'), _('No'), self.onContinueWithOld, self.app.exit)
				return
			# show main dialog
			if not gdata.mainGameDlg:
				gdata.mainGameDlg = MainGameDlg(self.app)
				gdata.mainGameDlg.display()
			client.updateDatabase()
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

	def onContinueWithOld(self):
			# show main dialog
			self.win.hide()
			if not gdata.mainGameDlg:
				gdata.mainGameDlg = MainGameDlg(self.app)
				gdata.mainGameDlg.display()
			client.updateDatabase()

	def onCreateAccount(self, widget, action, data):
		self.win.hide()
		self.newAccDlg.display(self)

	def onOptions(self, widget, action, data):
		self.win.hide()
		gdata.config.game.lastpasswordcrypted = binascii.b2a_base64(self.win.vPassword.text).strip()
		OptionsDlg(gdata.app).display(self)

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			movable = 0,
			title = _('Outer Space Login'),
			rect = ui.Rect((w - 424) / 2, (h - 124) / 2, 424, 124),
			layoutManager = ui.SimpleGridLM(),
			tabChange = True,
		)
		self.win.subscribeAction('*', self)
		ui.Label(self.win,
			text = _('Login'),
			align = ui.ALIGN_E,
			layout = (5, 0, 6, 1)
		)
		ui.Entry(self.win, id = 'vLogin',
			align = ui.ALIGN_W,
			layout = (11, 0, 10, 1),
			orderNo = 1
		)
		ui.Label(self.win,
			text = _('Password'),
			align = ui.ALIGN_E,
			layout = (5, 1, 6, 1),
		)
		ui.Entry(self.win, id = 'vPassword',
			align = ui.ALIGN_W,
			showChar = '*',
			layout = (11, 1, 10, 1),
			orderNo = 2
		)
		#ui.Label(self.win,
		#	align = ui.ALIGN_E,
		#	text = _('Game ID'),
		#	layout = (5, 2, 6, 1),
		#)
		#ui.Entry(self.win, id = 'vGameID',
		#	align = ui.ALIGN_W,
		#	layout = (11, 2, 10, 1),
		#	enabled = 0,
		#)
		#ui.Check(self.win, id = 'vSavePassword',
		#	text = _("Remember password"),
		#	align = ui.ALIGN_W,
		#	layout = (11, 3, 10, 1),
		#)
		#ui.Check(self.win, id = 'vAutoLogin',
		#	text = _("Auto-login"),
		#	align = ui.ALIGN_W,
		#	layout = (5,3,6,1),
		#)
		ui.Button(self.win, layout = (11, 2, 10, 1), text = _("Options"), action = "onOptions", id = "vOptions")
		ui.Button(self.win, layout = (11, 3, 10, 1), text = _("New account"),
			action = "onCreateAccount", id = "vCreate")
		ui.Title(self.win, layout = (0, 4, 11, 1), id = 'vMessage', align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (11, 4, 5, 1), text = _('Exit'), action = 'onCancel')
		loginBtn = ui.TitleButton(self.win, layout = (16, 4, 5, 1), text = _('Login'), action = 'onLogin')
		ui.Label(self.win, layout = (0, 0, 5, 4), icons = ((res.loginLogoImg, ui.ALIGN_W),))
		self.win.acceptButton = loginBtn

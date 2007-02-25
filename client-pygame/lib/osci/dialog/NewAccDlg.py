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
from osci import client, gdata, res
from MainGameDlg import MainGameDlg
from ige import SecurityException

class NewAccDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, caller = None, message = None):
		self.caller = caller
		self.win.vNick.text = ""
		self.win.vLogin.text = ""
		self.win.vPassword.text = ""
		self.win.vConfirm.text = ""
		self.win.vEmail.text = ""
		self.win.vMessage.text = message
		self.win.show()

	def hide(self):
		self.win.hide()

	def onCreate(self, widget, action, data):
		nick = self.win.vNick.text
		login = self.win.vLogin.text
		password = self.win.vPassword.text
		confirm = self.win.vConfirm.text
		email = self.win.vEmail.text
		if password != confirm:
			self.win.vMessage.text = _("Passwords do not match.")
			self.win.vPassword.text = ""
			self.win.vConfirm.text = ""
			return
		self.win.hide()
		try:
			result = client.createAccount(login, password, nick, email)
		except SecurityException, e:
			# failed
			self.win.vMessage.text = _(e.args[0])
			self.win.show()
			return
		# account created, record login
		gdata.config.game.lastlogin = login
		gdata.config.game.lastpassword = ""
		gdata.config.game.accountcreated = 1
		if self.caller:
			self.caller.display(message = "The account has been created.")

	def onCancel(self, widget, action, data):
		self.win.hide()
		if self.caller:
			self.caller.display()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			movable = 0,
			title = _('Create account'),
			rect = ui.Rect((w - 424) / 2, (h - 144) / 2, 424, 144),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		ui.Label(self.win,
			text = _('Nick'),
			align = ui.ALIGN_E,
			layout = (5, 0, 6, 1)
		)
		ui.Entry(self.win, id = 'vNick',
			align = ui.ALIGN_W,
			layout = (11, 0, 10, 1),
		)
		ui.Label(self.win,
			text = _('Login'),
			align = ui.ALIGN_E,
			layout = (5, 1, 6, 1)
		)
		ui.Entry(self.win, id = 'vLogin',
			align = ui.ALIGN_W,
			layout = (11, 1, 10, 1),
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
		)
		ui.Label(self.win,
			align = ui.ALIGN_E,
			text = _('Confirm'),
			layout = (5, 3, 6, 1),
		)
		ui.Entry(self.win, id = 'vConfirm',
			align = ui.ALIGN_W,
			layout = (11, 3, 10, 1),
			showChar = "*",
		)
		ui.Label(self.win,
			align = ui.ALIGN_E,
			text = _('E-mail'),
			layout = (5, 4, 6, 1),
		)
		ui.Entry(self.win, id = 'vEmail',
			align = ui.ALIGN_W,
			layout = (11, 4, 10, 1),
		)
		ui.Title(self.win, layout = (0, 5, 13, 1), id = 'vMessage', align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (13, 5, 4, 1), text = _('Cancel'), action = 'onCancel')
		ui.TitleButton(self.win, layout = (17, 5, 4, 1), text = _('Create'), action = 'onCreate')
		ui.Label(self.win, layout = (0, 0, 5, 4), icons = ((res.loginLogoImg, ui.ALIGN_W),))

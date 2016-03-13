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
from LoginDlg import LoginDlg
from CreateAccountDlg import CreateAccountDlg
from OptionsDlg import OptionsDlg

class MainMenuDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self):
		self.win.show()

	def hide(self):
		self.win.hide()

	def onLogin(self, widget, action, data):
		self.hide()
		dlg = LoginDlg(self.app).display(self)

	def onCreateAccount(self, widget, action, data):
		self.hide()
		dlg = CreateAccountDlg(self.app).display(self)

	def onOptions(self, widget, action, data):
		self.hide()
		dlg = OptionsDlg(self.app).display(self)

	def onQuit(self, widget, action, data):
		self.hide()
		self.app.exit()

	def createUI(self):
		self.win = ui.Window(self.app,
			modal = 1,
			movable = 0,
			rect = ui.Rect(300, 200, 206, 230),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		ui.Label(self.win,
			font = 'large-bold',
			layout = (1, 1, 8, 1),
			text = 'Main Menu',
		)
		ui.Button(self.win,
			layout = (1, 3, 8, 1),
			text = 'Login',
			action = 'onLogin',
		)
		ui.Button(self.win,
			layout = (1, 5, 8, 1),
			text = 'Create Account',
			action = 'onCreateAccount'
		)
		ui.Button(self.win,
			layout = (1, 7, 8, 1),
			text = 'Options',
			action = 'onOptions',
		)
		ui.Button(self.win,
			layout = (1, 9, 8, 1),
			text = 'Quit',
			action = 'onQuit',
		)

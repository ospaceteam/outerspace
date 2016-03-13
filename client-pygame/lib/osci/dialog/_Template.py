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
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
from ige.ospace.Const import *

class MessagesDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self):
		self.show()
		self.win.show()
		# register for updates
		if self not in gdata.updateDlgs:
			gdata.updateDlgs.append(self)

	def hide(self):
		self.win.hide()
		# unregister updates
		if self in gdata.updateDlgs:
			gdata.updateDlgs.remove(self)

	def update(self):
		self.show()

	def show(self):
		pass

	def onEvent(self, widget, action, data):
		pass

	def onCancel(self, widget, action, data):
		self.hide()

	def onClose(self, widget, action, data):
		self.hide()

	def createUI(self):
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = 1,
			movable = 0,
			title = _('Split Fleet'),
			rect = ui.Rect(0, 0, 800, 580),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# original fleet
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.TitleButton(self.win, layout = (30, 27, 5, 1), text = _('Cancel'), action = 'onCancel')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 30, 1), align = ui.ALIGN_W)
		self.win.statusBar = self.win.vStatusBar
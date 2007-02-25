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

import pygameui as ui, string
from osci import client, gdata, res
from ige.ospace.Const import *

class BuoyDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, buoyText, buoyType, confirmAction = None):
		self.confirmAction = confirmAction
		self.win.vText.text = buoyText.split("\n")
		self.win.vAllied.checked = buoyType == BUOY_TO_ALLY
		self.win.show()
		self.app.setFocus(self.win.vText)
		# register for updates
		if self not in gdata.updateDlgs:
			gdata.updateDlgs.append(self)

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()
		# unregister updates
		if self in gdata.updateDlgs:
			gdata.updateDlgs.remove(self)

	def update(self):
		self.win.show()

 	def onOK(self, widget, action, data):
 		self.buoyText = string.join(self.win.vText.text, "\n")
 		if self.win.vAllied.checked:
 			self.buoyType = BUOY_TO_ALLY
 		else:
 			self.buoyType = BUOY_PRIVATE
		self.hide()
		if self.confirmAction:
			self.confirmAction()

	def onCancel(self, widget, action, data):
		self.quantity = None
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		cols = 20
		rows = 13
		width = cols * 20 + 4
		height = rows * 20 + 24
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Edit buoy"),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		# creating dialog window
		self.win.subscribeAction('*', self)

		ui.Label(self.win,
			text = _("Buoy text:"),
			align = ui.ALIGN_W,
			layout = (0, 0, 3, 1)
		)
		ui.Check(self.win,
			text = _("Visible to allies"),
			align = ui.ALIGN_W,
			layout = (14, 0, 6, 1),
			id = 'vAllied',
		)
		s = ui.Scrollbar(self.win, layout = (cols - 1, 1, 1, rows - 3))
		t = ui.Text(self.win, id = 'vText',
			align = ui.ALIGN_W,
			layout = (0, 1, cols - 1, rows - 2),
		)
		t.attachVScrollbar(s)

		ui.Title(self.win, layout = (0, rows - 1, cols - 10, 1))
		ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Cancel"), action = "onCancel")
		okBtn = ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("OK"), action = 'onOK')
		self.win.acceptButton = okBtn
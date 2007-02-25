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

class ChangeQtyDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, quantity, confirmAction = None):
		self.confirmAction = confirmAction
		self.win.vQuantity.text = str(quantity)
		self.win.show()
		self.app.setFocus(self.win.vQuantity)
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
		self.show()

 	def onOK(self, widget, action, data):
		try:
			self.quantity = int(self.win.vQuantity.text)
		except ValueError:
			self.win.setStatus(_("Specify quantity (1, 2, 3, ...)."))
			return
		self.hide()
		if self.confirmAction:
			self.confirmAction()

	def onCancel(self, widget, action, data):
		self.quantity = None
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Change quantity'),
			rect = ui.Rect((w - 264) / 2, (h - 104) / 2, 264, 104),
			layoutManager = ui.SimpleGridLM(),
		)
		# creating dialog window
		self.win.subscribeAction('*', self)

		ui.Label(self.win,
			text = _("New quantity:"),
			align = ui.ALIGN_E,
			layout = (0, 1, 6, 1)
		)
		ui.Entry(self.win, id = 'vQuantity',
			align = ui.ALIGN_W,
			layout = (6, 1, 3, 1),
			#text = self.quantity,
		)
		ui.Title(self.win, layout = (0, 3, 3, 1))
		ui.TitleButton(self.win, layout = (3, 3, 5, 1), text = _("Cancel"), action = "onCancel")
		okBtn = ui.TitleButton(self.win, layout = (8, 3, 5, 1), text = _("OK"), action = 'onOK')
		self.win.acceptButton = okBtn
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
from ige import log
from ige.ospace.Const import *

class KeyModHelp:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self):
		if not self.win.visible:
			self.win.show()

	def hide(self):
		self.win.hide()

	def update(self):
		self.win.show()

	def show(self):
		#self.win.vText.text = _("You have ");
		text = []
		text.append(_("You have pressed 'Ctrl+Number.' This allows you to set a control key. Click on a system, planet, or fleet on the starmap after closing this dialog to set the number key that you pressed to access that object. You can always cancel this action with the ESCAPE key while on the Star Map."))
		text.append("")
		text.append(_("Once you have selected an object:"))
		text.append(_("- Pressing 'Number' will open that object's dialog."))
		text.append(_("- Pressing 'Shift+Number' will center the starmap on that object."))
		self.win.vText.text = text
		self.win.show()

 	def onOK(self, widget, action, data):
 		gdata.config.defaults.displayhelp = 'no'
 		log.debug('Set display help to:',gdata.config.defaults.displayhelp);
 		self.hide()

	def onCancel(self, widget, action, data):
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		cols = 22
		rows = 13
		width = cols * 20 + 4
		height = rows * 20 + 24
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Key Command Help"),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		# creating dialog window
		self.win.subscribeAction('*', self)
		
		t = ui.Text(self.win, id = 'vText',
			align = ui.ALIGN_W,
			layout = (0, 0, cols - 1, rows - 2),
			editable = 0
		)
		s = ui.Scrollbar(self.win, layout = (cols - 1, 0, 1, rows - 2))
		t.attachVScrollbar(s)

		ui.Title(self.win, layout = (0, rows - 1, cols - 16, 1))
		ui.TitleButton(self.win, layout = (cols - 4, rows - 1, 4, 1), text = _("OK"), action = "onCancel")
		ui.TitleButton(self.win, layout = (cols - 16, rows - 1, 12, 1), text = _("Do not show help/tooltip again"), action = "onOK")

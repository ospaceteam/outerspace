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
from osci import client, gdata
from ige.ospace.Const import *

class ShowBuoyDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, objID):
		player = client.getPlayer()
		text = []
		if hasattr(player, "buoys") and objID in player.buoys:
			label = _("Private buoy text")
			if player.buoys[objID][1] == BUOY_TO_ALLY:
				label = u"%s%s:" % (label, _(" (visible to allies)"))
			else:
				label = u"%s:" % label
			text.append(label)
			text.extend(player.buoys[objID][0].split("\n"))
			text.append("")

		if hasattr(player, "alliedBuoys") and objID in player.alliedBuoys:
			text.append(_("Buoy texts from allies:"))
			for buoy in player.alliedBuoys[objID]:
				text.extend(buoy[0].split("\n"))
				text.append("")

		self.win.vText.text = text
		self.win.show()
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
			title = _("Show buoy text"),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		# creating dialog window
		self.win.subscribeAction('*', self)

		s = ui.Scrollbar(self.win, layout = (cols - 1, 0, 1, rows - 1))
		t = ui.Text(self.win, id = 'vText',
			align = ui.ALIGN_W,
			layout = (0, 0, cols - 1, rows - 1),
			editable = 0
		)
		t.attachVScrollbar(s)

		ui.Title(self.win, layout = (0, rows - 1, cols - 5, 1))
		okBtn = ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("OK"), action = 'onOK')

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
from osci import gdata, res, client, sequip
from ige.ospace.Const import *
from ige.ospace import ShipUtils, Rules
from ige import GameException, log
import math

class MinefieldDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.systemID = OID_NONE
		self._mines = {}

	def display(self, systemID):
		self.systemID = systemID
		self.show()
		# show window
		if not self.win.visible:
			self.win.show()
		# register for updates
		if self not in gdata.updateDlgs:
			gdata.updateDlgs.append(self)

	def precompute(self):
		system = client.get(self.systemID, noUpdate = 1)
		self._mines = {}
		if hasattr(system, "minefield"):
			for mine in system.minefield:
				if mine in self._mines:
					self._mines[mine] += 1
				else:
					self._mines[mine] = 1

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()
		# unregister updates
		if self in gdata.updateDlgs:
			gdata.updateDlgs.remove(self)

	def update(self):
		self.setDefaults()
		if self.fleetID != OID_NONE: #MaxHPs or Shield Piercing flag might have changed, so recalc fleet
			self.calcFleet(self.fleet)
		elif self.designID != OID_NONE:
			self.calcDesign(self.designID)
		self.show()

	def show(self):
		self.precompute()
		keys = self._mines.keys()
		keys.sort()
		items = []
		for minetech in keys:
			num = self._mines[minetech]
			tech = client.getFullTechInfo(minetech)
			if tech.weaponIgnoreShield:
				igsh = _('Yes')
			else:
				igsh = _('No')
			items.append(ui.Item(tech.name,
				tNum = num,
				tMinDmg = tech.weaponDmgMin,
				tMaxDmg = tech.weaponDmgMax,
				tAtt = tech.weaponAtt,
				tIS = igsh
			))
		self.win.vMines.items = items
		self.win.vMines.itemsChanged()

	def onToggleCondition(self, widget, action, data):
		setattr(self, widget.data, not getattr(self, widget.data))
		self.update()

	def onClose(self, widget, action, data):
		self.hide()

	def createUI(self):
		screenWidth, screenHeight = gdata.scrnSize
		# size of dialog in layout metrics (for SimpleGridLM)
		cols = 23
		rows = 12
		# dialog width and height in pixels
		width = cols * 20 + 5
		height = rows * 20 + 4
		#creating dialog window
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Mine Field Details"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# playets listbox
		ui.Listbox(self.win, layout = (0, 0, cols, rows-2), id = 'vMines',
			columns = [(_('Type'), 'text', 7, ui.ALIGN_W),
			(_('Number'), 'tNum', 3, ui.ALIGN_E),
			(_('Min Dmg'), 'tMinDmg', 3, ui.ALIGN_E),
			(_('Max Dmg'), 'tMaxDmg', 3, ui.ALIGN_E),
			(_('Attack'), 'tAtt', 3, ui.ALIGN_E),
			(_('Ign. Shld'), 'tIS', 3, ui.ALIGN_E)],
			columnLabels = 1, sortable = 0)
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (cols-5, rows-2, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, rows-2, cols-5, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

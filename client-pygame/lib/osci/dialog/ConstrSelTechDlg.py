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

ENGINE = 1
SMALL = 2
MEDIUM = 4
LARGE = 8
PLANET = 16
OTHER = 32

typeText = {
	ENGINE: _('Engine'),
	SMALL:  _('Anti-small'),
	MEDIUM: _('Anti-medium'),
	LARGE:  _('Anti-large'),
	PLANET: _('Anti-planet'),
	OTHER:  _('Other'),
}

class ConstrSelTechDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, techType, techSubtype, selectCallback, selected = 0, hullID = 0):
		self.techID = OID_NONE
		self.selectCallback = selectCallback
		self.techType = techType
		self.techSubtype = techSubtype
		self.selected = selected
		if hullID:
			self.hullType = client.getFullTechInfo(hullID).combatClass
		else:
			self.hullType = 0
		self.typeFilter = ENGINE | SMALL | MEDIUM | LARGE | PLANET | OTHER
		self.win.vEngine.checked = self.typeFilter & ENGINE
		self.win.vSmall.checked = self.typeFilter & SMALL
		self.win.vMedium.checked = self.typeFilter & MEDIUM
		self.win.vLarge.checked = self.typeFilter & LARGE
		self.win.vPlanet.checked = self.typeFilter & PLANET
		self.win.vOther.checked = self.typeFilter & OTHER
		self.show()
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
		self.show()

	def getTechType(self, tech):
		if getattr(tech, "engPwr") > 0:
			return ENGINE
		if getattr(tech, "weaponClass") == 0 and getattr(tech, "weaponDmgMin") > 0:
			return SMALL
		if getattr(tech, "weaponClass") == 1:
			return MEDIUM
		if getattr(tech, "weaponClass") == 2:
			return LARGE
		if getattr(tech, "weaponClass") == 3:
			return PLANET
		return OTHER

	def show(self):
		self.showItems()

	def showItems(self):
		items = []
		selected = None
		player = client.getPlayer()
		for techID in player.techs:
			tech = client.getTechInfo(techID)
			if getattr(tech, self.techType) == 0:
				continue
			if self.techSubtype and tech.subtype not in self.techSubtype:
				continue
			# skip equipment not suitable for this hull
			if tech.minHull > self.hullType:
				continue
			if tech.maxHull < self.hullType:
				continue

			techType = self.getTechType(tech)
			if self.typeFilter & techType == 0:
				continue

			item = ui.Item(tech.name, tData = sequip.getLongDescr(techID), techID = techID,
							tType = typeText[techType])

			if techID == self.selected:
				selected = item

			items.append(item)
		self.win.vList.items = items
		self.win.vList.itemsChanged()
		self.win.vList.selectItem(selected)

	def onCancel(self, widget, action, data):
		self.hide()

	def onFilter(self, widget, action, data):
		if widget.checked:
			self.typeFilter |= widget.data
		else:
			self.typeFilter &= ~widget.data
		self.showItems()

	def onSelect(self, widget, action, data):
		self.hide()
		if self.win.vList.selection:
			self.selectCallback(self.win.vList.selection[0].techID)

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Select component'),
			rect = ui.Rect((w - 764) / 2, (h - 463) / 2, 764, 463),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# component list
		ui.Listbox(self.win, layout = (0, 0, 38, 20), id = "vList",
			columns = (
				(_('Name'), 'text', 9, ui.ALIGN_W),
				(_('Type'), 'tType', 4, ui.ALIGN_W),
				(_('Data'), 'tData', 0, ui.ALIGN_W),
			),
			columnLabels = 1
		)

		ui.Check(self.win, layout = (0, 20, 5, 1), text = typeText[ENGINE], id = 'vEngine',
			checked = 1, action = 'onFilter', data = ENGINE)
		ui.Check(self.win, layout = (5, 20, 5, 1), text = typeText[SMALL], id = 'vSmall',
			checked = 1, action = 'onFilter', data = SMALL)
		ui.Check(self.win, layout = (10, 20, 5, 1), text = typeText[MEDIUM], id = 'vMedium',
			checked = 1, action = 'onFilter', data = MEDIUM)
		ui.Check(self.win, layout = (15, 20, 5, 1), text = typeText[LARGE], id = 'vLarge',
			checked = 1, action = 'onFilter', data = LARGE)
		ui.Check(self.win, layout = (20, 20, 5, 1), text = typeText[PLANET], id = 'vPlanet',
			checked = 1, action = 'onFilter', data = PLANET)
		ui.Check(self.win, layout = (25, 20, 5, 1), text = typeText[OTHER], id = 'vOther',
			checked = 1, action = 'onFilter', data = OTHER)

		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (33, 21, 5, 1), text = _('Select'), action = 'onSelect')
		ui.TitleButton(self.win, layout = (28, 21, 5, 1), text = _('Cancel'), action = 'onCancel')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 21, 28, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

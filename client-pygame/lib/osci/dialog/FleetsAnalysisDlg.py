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
from osci import gdata, client
from ige.ospace.Const import *
from ige.ospace import ShipUtils, Rules

class FleetsAnalysisDlg:
	"""Displays analysis on existing fleets.

	Dialog displays list of current ship designs
	and list of fleets containing particular ship
	design.
	"""
	def __init__(self, app):
		self._textRows = 0
		self.app = app
		self.createUI()

	def display(self):
		self.show()
		# show window
		if not self.win.visible:
			self.win.show()

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()

	def update(self):
		if self.win.visible:
			self.show()

	def show(self):
		player = client.getPlayer()

		self.fleetsByDesign = {}
		self.fleetCountsByDesign = {}
		items = []
		for designID in player.shipDesigns:
			spec = player.shipDesigns[designID]
			fleets = {}
			fleetCounts = {}
			for fleetID in player.fleets:
				fleet = client.get(fleetID)
				count = 0
				for tmpDesignID, hp, shieldHP, exp in fleet.ships:
					if tmpDesignID == designID:
						count += 1
						fleets[fleet] = 1
				fleetCounts[fleetID] = count
			self.fleetsByDesign[designID] = fleets.keys()
			self.fleetCountsByDesign[designID] = fleetCounts
			item = ui.Item(spec.name, tDesignID = designID, tShipsCount = len(fleets.keys()))
			items.append(item)
		self.win.vDesigns.items = items
		self.win.vDesigns.itemsChanged()

	def onClose(self, widget, action, data):
		self.hide()

	def onSelectDesign(self, widget, action, data):
		player = client.getPlayer()
		fleets = self.fleetsByDesign[data.tDesignID]
		fleetCounts = self.fleetCountsByDesign[data.tDesignID]
		spec = player.shipDesigns[data.tDesignID]
		self.win.vFleetsTitle.text = _("Fleets contains design %s") % spec.name
		items = []
		if fleets:
			for fleet in fleets:
				items.append(ui.Item(fleet.name, tShipsCount = len(fleet.ships), fleet = fleet, tClassCount = fleetCounts[fleet.oid], tFleetID = fleet.oid))
		self.win.vFleets.items = items
		self.win.vFleets.itemsChanged()

	def onSelectFleet(self, widget, action, data):
		item = self.win.vFleets.selection[0]
		fleet = item.fleet #client.get(item.tFleetID, noUpdate = 1)
#		if hasattr(fleet, "owner") and fleet.owner == client.getPlayerID():
			# show dialog
		gdata.mainGameDlg.onSelectMapObj(None, None, item.tFleetID)

	def onShowLocation(self, widget, action, data):
		# center on map
		if hasattr(data.fleet, "x"):
			gdata.mainGameDlg.win.vStarMap.highlightPos = (data.fleet.x, data.fleet.y)
			gdata.mainGameDlg.win.vStarMap.setPos(data.fleet.x, data.fleet.y)
			self.hide()
			return
		self.win.setStatus(_("Cannot show location"))

	def createUI(self):
		screenWidth, screenHeight = gdata.scrnSize
		# size of dialog in layout metrics (for SimpleGridLM)
		cols = 36
		rows = 27
		# dialog width and height in pixels
		width = cols * 20 + 5
		height = rows * 20 + 4
		#creating dialog window
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Fleets analysis"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# first row is window title
		rows -= 1

		halfCols = cols / 2
		ui.Title(self.win, layout = (0, 0, halfCols, 1), text = _("Ship designs"),
			align = ui.ALIGN_W, id = "vDesignsTitle", font = "normal-bold")
		ui.Listbox(self.win, layout = (0, 1, halfCols, rows - 2), id = "vDesigns",
			columns = (
				(_("Design name"), "text", halfCols - 5, ui.ALIGN_W),
				(_("# fleets"), "tShipsCount", 4, ui.ALIGN_E)
			),
			columnLabels = 1, action = "onSelectDesign", sortable = True)

		ui.Title(self.win, layout = (halfCols, 0, halfCols, 1), text = "",
			align = ui.ALIGN_W, id = "vFleetsTitle", font = "normal-bold")
		ui.Listbox(self.win, layout = (halfCols, 1, halfCols, rows - 2), id = "vFleets",
			columns = (
				(_("Fleet name"), "text", halfCols - 9, ui.ALIGN_W),
				(_("Ships"), "tClassCount",4, ui.ALIGN_E),
				(_("Fleet size"), "tShipsCount", 4, ui.ALIGN_E)
			),
			columnLabels = 1, action = "onSelectFleet", rmbAction = "onShowLocation", sortable = True)

		# dialog bottom line
		ui.Title(self.win, layout = (0, rows - 1, cols - 5, 1))
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Close"), action = "onClose")

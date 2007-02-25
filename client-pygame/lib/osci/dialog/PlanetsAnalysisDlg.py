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

class PlanetsAnalysisDlg:
	"""Displays analysis on planets structures.

	Dialog displays list of current created structures
	and list of planets where particular type of structure
	is created.
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

		self.buildingsCount = {}
		self.buildingsPos = {}
		for planetID in player.planets:
			planet = client.get(planetID)
			if hasattr(planet, "slots"):
				for struct in planet.slots:
					techID = struct[STRUCT_IDX_TECHID]
					if not techID in self.buildingsCount:
						self.buildingsCount[techID] = 1
					else:
						self.buildingsCount[techID] = self.buildingsCount[techID] + 1
					if not techID in self.buildingsPos:
						self.buildingsPos[techID] = {planetID: 1}
					else:
						planetList = self.buildingsPos[techID]
						if not planetID in planetList:
							planetList[planetID] = 1
						else:
							planetList[planetID] = planetList[planetID] + 1

		items = []
		for techID in self.buildingsCount:
			tech = client.getTechInfo(techID)
			items.append(ui.Item(tech.name, tStructCount = self.buildingsCount[techID], techID = techID))

		self.win.vStructures.items = items
		self.win.vStructures.itemsChanged()

	def onClose(self, widget, action, data):
		self.hide()

	def onSelectStruct(self, widget, action, data):
		planetList = self.buildingsPos[data.techID]
		tech = client.getTechInfo(data.techID)
		self.win.vPlanetsTitle.text = _("Planets with structure %s") % tech.name
		if planetList:
			items = []
			for planetID in planetList:
				planet = client.get(planetID)
				items.append(ui.Item(planet.name, tStructCount = planetList[planetID], planetID = planetID))
			self.win.vPlanets.items = items
			self.win.vPlanets.itemsChanged()

	def onSelectPlanet(self, widget, action, data):
		gdata.mainGameDlg.onSelectMapObj(None, None, data.planetID)
		pass

	def onShowLocation(self, widget, action, data):
		planet = client.get(data.planetID, noUpdate = 1)
		# center on map
		if hasattr(planet, "x"):
			gdata.mainGameDlg.win.vStarMap.highlightPos = (planet.x, planet.y)
			gdata.mainGameDlg.win.vStarMap.setPos(planet.x, planet.y)
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
			title = _("Planets analysis"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# first row is window title
		rows -= 1

		halfCols = cols / 2
		ui.Title(self.win, layout = (0, 0, halfCols, 1), text = _("Structures"),
			align = ui.ALIGN_W, id = "vStructuresTitle", font = "normal-bold")
		ui.Listbox(self.win, layout = (0, 1, halfCols, rows - 2), id = "vStructures",
			columns = (
				(_("Structure name"), "text", halfCols - 5, ui.ALIGN_W),
				(_("Total #"), "tStructCount", 4, ui.ALIGN_E)
			),
			columnLabels = 1, action = "onSelectStruct", sortable = True)

		ui.Title(self.win, layout = (halfCols, 0, halfCols, 1), text = "",
			align = ui.ALIGN_W, id = "vPlanetsTitle", font = "normal-bold")
		ui.Listbox(self.win, layout = (halfCols, 1, halfCols, rows - 2), id = "vPlanets",
			columns = (
				(_("Planet name"), "text", halfCols - 5, ui.ALIGN_W),
				(_("# of structs"), "tStructCount", 4, ui.ALIGN_E)
			),
			columnLabels = 1, action = "onSelectPlanet", rmbAction = "onShowLocation", sortable = True)

		# dialog bottom line
		ui.Title(self.win, layout = (0, rows - 1, cols - 5, 1))
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Close"), action = "onClose")

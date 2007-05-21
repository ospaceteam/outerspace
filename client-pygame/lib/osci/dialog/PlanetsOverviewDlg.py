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
from ige import GameException
import math

class PlanetsOverviewDlg:

	def __init__(self, app):
		self.app = app
		self.showMine = 1
		self.showColonizable = 0
		self.showOtherPlayers = 0
		self.showUncolonizable = 0
		self.createUI()

	def display(self):
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

	def show(self):
		player = client.getPlayer()
		#
		items = []
		for planetID in client.db.keys():
			planet = client.get(planetID, noUpdate = 1)
			# skip non-planets
			if not hasattr(planet, "type") or planet.type != T_PLANET:
				continue
			# shall be shown?
			ok = 0
			if hasattr(planet, 'owner'):
				if self.showMine and planet.owner == player.oid:
					ok = 1
				if self.showOtherPlayers and planet.owner != OID_NONE and \
					planet.owner != player.oid:
					ok = 1
				if self.showColonizable and planet.owner == OID_NONE and \
					planet.plType not in ('G', 'A'):
					ok = 1
				if self.showUncolonizable and planet.plType in ('G', 'A'):
					ok = 1
			elif hasattr(planet, 'plType'):
				if self.showColonizable and planet.plType not in ('G', 'A'):
					ok = 1
				if self.showUncolonizable and planet.plType in ('G', 'A'):
					ok = 1
			if not ok:
				continue
			# fill in data
			#rel = REL_UNDEF
			maxNA = 999999
			maxNone = 99999
			ownerID = OID_NONE
			if hasattr(planet, 'owner'):
				ownerID = planet.owner
				#if planet.owner != OID_NONE:
				#	rel = client.getRelationTo(planet.owner)
				if planet.owner == OID_NONE:
				#else:
					owner = _('[Nobody]')
			if hasattr(planet, 'owner') and planet.owner == player.oid:
				if planet.prodQueue and planet.effProdProd > 0:
					index = 0
					totalEtc = 0
					for task in planet.prodQueue:
						if task.isShip:
							tech = client.getPlayer().shipDesigns[task.techID]
						else:
							tech = client.getFullTechInfo(task.techID)
						if index == 0:
							constrInfo = tech.name
						# etc
						if task.targetID != planetID:
							if index == 0:
								etc = math.ceil(float(tech.buildProd * Rules.buildOnAnotherPlanetMod - task.currProd) / planet.effProdProd)
								totalEtc += etc
								totalEtc += math.ceil((task.quantity - 1) * float(tech.buildProd * Rules.buildOnAnotherPlanetMod) / planet.effProdProd)
							else:
								totalEtc += math.ceil(float(tech.buildProd * Rules.buildOnAnotherPlanetMod - task.currProd) / planet.effProdProd)
								totalEtc += math.ceil((task.quantity - 1) * float(tech.buildProd * Rules.buildOnAnotherPlanetMod) / planet.effProdProd)
						else:
							if index == 0:
								etc = math.ceil(float(tech.buildProd - task.currProd) / planet.effProdProd)
								totalEtc += etc
								totalEtc += math.ceil((task.quantity - 1)* float(tech.buildProd) / planet.effProdProd)
							else:
								totalEtc += math.ceil(task.quantity * float(tech.buildProd - task.currProd) / planet.effProdProd)
								totalEtc += math.ceil((task.quantity - 1) * float(tech.buildProd) / planet.effProdProd)
						index += 1
					etc_raw = etc
					etc = res.formatTime(etc)
					totalEtc_raw = totalEtc
					totalEtc = res.formatTime(totalEtc)
				elif planet.prodQueue:
					task = planet.prodQueue[0]
					if task.isShip:
						tech = client.getPlayer().shipDesigns[task.techID]
					else:
						tech = client.getTechInfo(task.techID)
					constrInfo = tech.name
					etc = _('N/A')
					etc_raw = maxNA
					totalEtc = _("N/A")
					totalEtc_raw = maxNA
				elif planet.effProdProd > 0:
					constrInfo = _("-")
					etc = "-"
					etc_raw = 0
					totalEtc = _("-")
					totalEtc_raw = 0
				else:
					constrInfo = _("-")
					etc = "-"
					etc_raw = maxNone
					totalEtc = _("-")
					totalEtc_raw = maxNone
			else:
				constrInfo = '?'
				etc = '?'
				etc_raw = maxNA
				totalEtc = '?'
				totalEtc_raw = maxNA
			# used slots
			if hasattr(planet, 'slots'):
				freeSlots = planet.plSlots - len(planet.slots)
			else:
				freeSlots = '?'
			# morale
			if hasattr(planet, "morale"):
				morale = int(planet.morale)
			else:
				morale = "?"
			#
			plType = gdata.planetTypes[getattr(planet, 'plType', None)]
			# list item
			item = ui.Item(
				getattr(planet, 'name', res.getUnknownName()),
				tPlType = _(plType),
				tPlBio = getattr(planet, 'plBio', '?'),
				tPlMin = getattr(planet, 'plMin', '?'),
				tPlEn = getattr(planet, 'plEn', '?'),
				tChangeBio = getattr(planet, 'changeBio', '?'),
				tChangeEn = getattr(planet, 'changeEn', '?'),
				tETC = etc,
				tETC_raw = etc_raw,
				tTotalETC = totalEtc,
				tTotalETC_raw = totalEtc_raw,
				tConstrInfo = constrInfo,
				tFree = freeSlots,
				tMorale = morale,
				tSpace = getattr(planet, 'plSlots', '?'),
				tDiam = getattr(planet, 'plDiameter',0)/1000,
				tProd = getattr(planet, 'effProdProd', '?'),
				tSci = getattr(planet, 'effProdSci', '?'),
				tPlanetID = planetID,
				#foreground = res.getFFColorCode(rel),
				foreground = res.getPlayerColor(ownerID),
			)
			items.append(item)
		self.win.vPlanets.items = items
		self.win.vPlanets.itemsChanged()
		# buttons
		self.win.vMine.pressed = self.showMine
		self.win.vOtherPlayers = self.showOtherPlayers
		self.win.vColonizable = self.showColonizable
		self.win.vUncolonizable = self.showUncolonizable

	def onSelectPlanet(self, widget, action, data):
		item = self.win.vPlanets.selection[0]
		planet = client.get(item.tPlanetID, noUpdate = 1)
		if hasattr(planet, "owner") and planet.owner == client.getPlayerID():
			# show dialog
			gdata.mainGameDlg.onSelectMapObj(None, None, item.tPlanetID)
		else:
			# center on map
			if hasattr(planet, "x"):
				gdata.mainGameDlg.win.vStarMap.highlightPos = (planet.x, planet.y)
				gdata.mainGameDlg.win.vStarMap.setPos(planet.x, planet.y)
				self.hide()
				return
			self.win.setStatus(_("Cannot show location"))

	def onShowLocation(self, widget, action, data):
		item = self.win.vPlanets.selection[0]
		planet = client.get(item.tPlanetID, noUpdate = 1)
		# center on map
		if hasattr(planet, "x"):
			gdata.mainGameDlg.win.vStarMap.highlightPos = (planet.x, planet.y)
			gdata.mainGameDlg.win.vStarMap.setPos(planet.x, planet.y)
			self.hide()
			return
		self.win.setStatus(_("Cannot show location"))

	def onToggleCondition(self, widget, action, data):
		setattr(self, widget.data, not getattr(self, widget.data))
		self.update()

	def onClose(self, widget, action, data):
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Planets Overview'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# playets listbox
		ui.Listbox(self.win, layout = (0, 0, 40, 26), id = 'vPlanets',
			columns = [(_('Planet'), 'text', 6, ui.ALIGN_W),
			(_('Type'), 'tPlType', 3.5, ui.ALIGN_W),
			(_('Bio'), 'tPlBio', 1.5, ui.ALIGN_E),
			(_('Min'), 'tPlMin', 1.5, ui.ALIGN_E),
			(_('En'), 'tPlEn', 1.5, ui.ALIGN_E),
			(_('Bio+-'), 'tChangeBio', 2.0, ui.ALIGN_E),
			(_('En+-'), 'tChangeEn', 2.0, ui.ALIGN_E),
			(_('Free'), 'tFree', 2.0, ui.ALIGN_E),
			(_('Sl.'), 'tSpace', 1.5, ui.ALIGN_E),
			(_('D.'),'tDiam',1.5, ui.ALIGN_E),
			(_('Mrl'), 'tMorale', 2, ui.ALIGN_E),
			(_('CP'), 'tProd', 2, ui.ALIGN_E),
			(_('RP'), 'tSci', 2, ui.ALIGN_E),
			(_('ETC'), 'tETC', 2.5, ui.ALIGN_E),
			(_('Tot.ETC'), 'tTotalETC', 2.5, ui.ALIGN_E),
			(_('Constructing'), 'tConstrInfo', 7.0, ui.ALIGN_W)],
			columnLabels = 1, action = 'onSelectPlanet', rmbAction = "onShowLocation")
		ui.Button(self.win, layout = (0, 26, 5, 1), text = _('My planets'), id = "vMine",
			toggle = 1,	action = "onToggleCondition", data = "showMine")
		ui.Button(self.win, layout = (5, 26, 5, 1), text = _('Other cmdrs'), id = "vOtherPlayers",
			toggle = 1,	action = "onToggleCondition", data = "showOtherPlayers")
		ui.Button(self.win, layout = (10, 26, 5, 1), text = _('Colonizable'), id = "vColonizable",
			toggle = 1,	action = "onToggleCondition", data = "showColonizable")
		ui.Button(self.win, layout = (15, 26, 5, 1), text = _('Uncolonizable'), id = "vUncolonizable",
			toggle = 1,	action = "onToggleCondition", data = "showUncolonizable")
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

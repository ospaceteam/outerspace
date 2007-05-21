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

class SystemOverviewDlg:

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
		items = []
		player = client.getPlayer()
		#
		for systemID in client.db.keys():
			if systemID == player.oid:
				continue
			system = client.get(systemID, noUpdate = 1)
			if hasattr(system, 'planets'):
				owned = False
				planetsYours = 0
				planetsOwned = 0
				planetsUnowned = 0
				en = 0
				bio = 0
				stratRes = SR_NONE
				refuelMax = 0
				refuelInc = 0
				upgradeShip = 0
				repairShip = 0
				speedBoost = 0
				for planetID in system.planets:
					planet = client.get(planetID, noUpdate = 1)
					owner = getattr(planet, 'owner', OID_NONE)
					if owner == player.oid:
						owned = True
						planetsYours += 1
						if hasattr(planet, 'changeEn'):
							en += planet.changeEn
						if hasattr(planet, "changeBio"):
							bio += planet.changeBio
						if hasattr(planet, "plStratRes") and planet.plStratRes != SR_NONE:
							stratRes = gdata.stratRes[planet.plStratRes]
						if hasattr(planet, "refuelMax"):
							refuelMax = max(refuelMax, planet.refuelMax)
							refuelInc = max(refuelInc, planet.refuelInc)
						if hasattr(planet, "repairShip"):
							upgradeShip += planet.upgradeShip
							repairShip = max(repairShip, planet.repairShip)
						if hasattr(planet, "fleetSpeedBoost"):
							speedBoost = max(speedBoost, planet.fleetSpeedBoost)
					else:
						if owner == OID_NONE:
							if not(hasattr(planet, "plType") and planet.plType in ("A", "G")) or self.showUncolonizable: #ignore planets that need conversion, normally
								planetsUnowned += 1
						else:
							planetsOwned += 1
				if owned:
					if stratRes == SR_NONE:
						stratRes = ''
					problem = (bio < 0 or en < 0)
					if planetsYours > 0: #make sure you own it
						owner = player.oid
					if speedBoost > 1:
						speedBoost = (int) ((speedBoost-1)*100)
					else:
						speedBoost = ''
					item = ui.Item(
						getattr(system, 'name', res.getUnknownName()),
						tSyPnum = planetsYours+planetsOwned+planetsUnowned,
						tSyPYnum = planetsYours,
						tSyPOnum = planetsOwned,
						tSyPUnum = planetsUnowned,
						tSyBio = bio,
						tSyEn = en,
						tSyRefuel = refuelInc,
						tSyRefuelMax = refuelMax,
						tSyRepair = (repairShip*100),
						tSyUpgrade = upgradeShip,
						tSyGate = speedBoost,
                                                tStRes = _(stratRes),
                                                tSysID = systemID,
						foreground = res.getSystemOverviewProblemColor(owner, problem),
					)
					items.append(item)
		self.win.vPlanets.items = items
		self.win.vPlanets.itemsChanged()
		# buttons
		#self.win.vMine.pressed = self.showMine
		#self.win.vOtherPlayers = self.showOtherPlayers
		#self.win.vColonizable = self.showColonizable
		self.win.vUncolonizable = self.showUncolonizable

	def onSelectPlanet(self, widget, action, data):
		item = self.win.vPlanets.selection[0]
		player = client.getPlayer()
		system = client.get(item.tSysID, noUpdate = 1)
		if item.tSyPYnum > 0: #you own
			# show dialog
			gdata.mainGameDlg.onSelectMapObj(None, None, item.tSysID)
		else:
			# center on map
			if hasattr(system, "x"):
				gdata.mainGameDlg.win.vStarMap.highlightPos = (system.x, system.y)
				gdata.mainGameDlg.win.vStarMap.setPos(system.x, system.y)
				self.hide()
				return
			self.win.setStatus(_("Cannot show location"))

	def onShowLocation(self, widget, action, data):
		item = self.win.vPlanets.selection[0]
		system = client.get(item.tSysID, noUpdate = 1)
		if hasattr(system, "x"):
			gdata.mainGameDlg.win.vStarMap.highlightPos = (system.x, system.y)
			gdata.mainGameDlg.win.vStarMap.setPos(system.x, system.y)
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
			title = _('Systems Overview'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# playets listbox
		ui.Listbox(self.win, layout = (0, 0, 40, 26), id = 'vPlanets',
			columns = [(_('System'), 'text', 7.5, ui.ALIGN_W),
			(_('#Pl'), 'tSyPnum', 2, ui.ALIGN_W),
			(_('Yours'), 'tSyPYnum', 2, ui.ALIGN_W),
			(_('Other'), 'tSyPOnum', 2, ui.ALIGN_W),
			(_('Colonize'), 'tSyPUnum', 2.5, ui.ALIGN_W),
			(_('Sys Bio'), 'tSyBio', 2.5, ui.ALIGN_E),
			(_('Sys En'), 'tSyEn', 2.5, ui.ALIGN_E),
			(_('Refuel %'), 'tSyRefuel', 3, ui.ALIGN_E),
			(_('Max %'), 'tSyRefuelMax', 2.5, ui.ALIGN_E),
			(_('Repair %'), 'tSyRepair', 3, ui.ALIGN_E),
			(_('Upgrade'), 'tSyUpgrade', 3, ui.ALIGN_E),
			(_('Gate +%'), 'tSyGate', 3, ui.ALIGN_E),
			(_('Strat Res'), 'tStRes', 4.5, ui.ALIGN_E)],
			columnLabels = 1, action = 'onSelectPlanet', rmbAction = "onShowLocation")
		#ui.Button(self.win, layout = (0, 26, 5, 1), text = _('My planets'), id = "vMine",
		#	toggle = 1,	action = "onToggleCondition", data = "showMine")
		#ui.Button(self.win, layout = (5, 26, 5, 1), text = _('Other cmdrs'), id = "vOtherPlayers",
		#	toggle = 1,	action = "onToggleCondition", data = "showOtherPlayers")
		#ui.Button(self.win, layout = (10, 26, 5, 1), text = _('Colonizable'), id = "vColonizable",
		#	toggle = 1,	action = "onToggleCondition", data = "showColonizable")
		ui.Button(self.win, layout = (0, 26, 15, 1), text = _('Include Gas Giants and Asteroids'), id = "vUncolonizable",
			toggle = 1,	action = "onToggleCondition", data = "showUncolonizable")
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

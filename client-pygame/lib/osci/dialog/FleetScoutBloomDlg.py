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
from ige.ospace import Rules
from osci import gdata, res, client, sequip
from ige.ospace.Const import *
from ige import log
import ige
import math
import string

class FleetScoutBloomDlg:

	NEW_COMMAND = 10000

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.targetID = OID_NONE
		self.targetPlayerID = OID_NONE
		self.fleet = None
		self.sendShips = []

	def display(self, fleetDlg):
		self.fleetDlg = fleetDlg
		self.fleet = fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
		self.win.vStarMap.currX = fleet.x
		self.win.vStarMap.currY = fleet.y
		self.win.vStarMap.alwaysShowRangeFor = fleet.oid
		self.win.vStarMap.setPosition = 0
		self.win.vStarMap.lockObj = fleet.orbiting
		self.win.vStarMap.precompute()
		self.sendShipIndex = 0
		self.targets = []
		if self.targetID:
			target = client.get(self.targetID, noUpdate = 1)
			self.win.vStarMap.highlightPos = (target.x, target.y)
		# ships
		self.sendShips = []
		# collect buildings
		for designID, a, b, c in self.fleet.ships: #fixed bug in reference of designID...added a, b, c to do it; breaks list lookup otherwise (not sure why) with hash error --RC
			if designID not in self.sendShips:
				self.sendShips.append(designID)
		self.showCommands()
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
		self.win.vStarMap.precompute()
		self.showCommands()

	def showCommands(self):
		if self.targetID == OID_NONE:
			info = _('No target selected')
		else:
			target = client.get(self.targetID, noUpdate = 1)
			info = getattr(target, 'name', res.getUnknownName())
		# correct buildingIndex
		if self.sendShipIndex >= len(self.sendShips):
			self.sendShipIndex = 0
		# get target data
		self.win.vTarget.text = info
		fleet = self.fleet
		if self.targetID != OID_NONE:
			curTarget = client.get(self.targetID, noUpdate = 1)
			target = OID_NONE
			if len(fleet.actions) > 1:
				if self.cmdIndex != 0 and self.cmdIndex < len(fleet.actions):
					idx = self.cmdIndex
				else:
					idx = len(fleet.actions)
				while True:
					idx -= 1
					if idx < 0:
						break
					#print "idx", idx, fleet.actions[idx]
					action, target, actionData = fleet.actions[idx]
					if target != OID_NONE:
						break
			if fleet.orbiting != OID_NONE and target == OID_NONE:
				target = fleet.orbiting
			elif target == OID_NONE:
				target = fleet.oid

			if target != OID_NONE:
				lastTarget = client.get(target, noUpdate = 1)
				curX = curTarget.x
				curY = curTarget.y
				lstX = lastTarget.x
				lstY = lastTarget.y
				dx = curX - lstX
				dy = curY - lstY
				lnght = math.sqrt(dx*dx + dy*dy)
				speedBoost = getattr(fleet, "speedBoost", 1)
				fleetSpeed = getattr(fleet, "speed", 0)
				maxDelta = fleetSpeed / Rules.turnsPerDay * speedBoost
				if maxDelta != 0:
					eta = lnght / maxDelta
					self.win.vEta.text = res.formatTime(eta)
				else:
					self.win.vEta.text = _("N/A")
			else:
				self.win.vEta.text = _("N/A")

		if self.sendShips:
			self.win.vSendShip.enabled = 1
			techID = self.sendShips[self.sendShipIndex]
			self.win.vSendShip.text = client.getPlayer().shipDesigns[techID].name
			self.win.vSendShip.data = techID
		else:
			self.win.setStatus(_("No ships found."))

	def onSelectMapObj(self, widget, action, data):
		target = client.get(data, noUpdate = 1)
		if not self.sendShips:
			self.win.setStatus(_("No ships found."))
			return
		if target.type == T_PLANET:
			self.targetID = target.oid
			self.win.vStarMap.highlightPos = (target.x, target.y)
		elif target.type in (T_SYSTEM, T_WORMHOLE):
			self.targetID = target.oid
			self.win.vStarMap.highlightPos = (target.x, target.y)
		else:
			self.win.vStarMap.hightlightPos = None
			return
		self.targetID = target.oid
		#prevent spam abuse
		if self.targetID not in self.targets:
			#split single ship off fleet
			newfleet = self.splitShip()
			if newfleet:
				#move the ship
				self.moveShip(newfleet)
				#add fleet to starmap without recomputing the whole starmap
				client.db[newfleet.oid] = client.get(newfleet.oid, forceUpdate = 1)
				self.win.vStarMap.precomputeFleet(newfleet)
				self.win.vStarMap.requestRepaint()
		else:
			self.win.setStatus(_("You cannot order a ship to the same system twice in one Scout Wave command"))
		self.showCommands()

	def splitShip(self):
		designID = self.sendShips[self.sendShipIndex]
		ships = []
		for ship in self.fleet.ships:
			if ship[0] == designID:
				ships = [ship]
				break
		if len(ships) == 0:
			self.win.setStatus(_("No ships left of the class %s" % client.getPlayer().shipDesigns[designID].name))
			return False
		#there is only one ship left in the original fleet
		if len(self.fleet.ships) == 1:
			return self.fleet
		#split the ship off the fleet; note: storeEn = self.fleet.storEn will result in max energy for the new fleet
		newfleet, self.fleet, fleets = client.cmdProxy.splitFleet(self.fleet.oid,ships,self.fleet.storEn)
		client.getPlayer().fleets = fleets
		client.db[newfleet.oid] = newfleet
		client.db[self.fleet.oid] = self.fleet
		return newfleet

	def moveShip(self,fleet):
		self.targets.append(self.targetID)
		client.cmdProxy.addAction(fleet.oid, 0, FLACTION_MOVE, self.targetID, 0)


	def onDone(self, widget, action, data):
		gdata.mainGameDlg.update()
		self.fleetDlg.update()
		self.hide()

	def onSendShipChange(self, widget, action, data):
		self.sendShipIndex += 1
		self.showCommands()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Send Single Ships'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
			tabChange = True
		)
		self.win.subscribeAction('*', self)
		StarMapWidget(self.win, layout = (0, 0, 40, 24),
			id = 'vStarMap', action = 'onSelectMapObj')
		# order buttons
		ui.Title(self.win, layout = (0, 24, 40, 1), text = _('Choose a ship class to send:'),
			font = 'normal-bold', align = ui.ALIGN_W)

		# Ship to send
		ui.Label(self.win, layout = (0, 25, 5, 1), text = _('Ship'),
			align = ui.ALIGN_E)
		ui.Button(self.win, layout = (5, 25, 10, 1), id = 'vSendShip',
			align = ui.ALIGN_NONE, action = 'onSendShipChange')
		ui.Label(self.win, layout = (0, 26, 5, 1), text = _("For last move:"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (5, 26, 2, 1), text = _("ETA:"), align = ui.ALIGN_W)
 		ui.Label(self.win, layout = (7, 26, 2, 1), id = 'vEta', align = ui.ALIGN_E)
		ui.Label(self.win, layout = (10, 26, 3, 1), text = _("Target:"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (13, 26, 7, 1), id = 'vTarget', align = ui.ALIGN_W)
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Done'), action = 'onDone')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

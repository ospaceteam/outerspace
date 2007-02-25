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

class FleetCommandDlg:

	NEW_COMMAND = 10000

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.targetID = OID_NONE
		self.targetPlayerID = OID_NONE

	def display(self, fleetDlg, cmdIndex):
		self.fleetDlg = fleetDlg
		self.cmdIndex = cmdIndex
		fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
		self.win.vStarMap.currX = fleet.x
		self.win.vStarMap.currY = fleet.y
		self.win.vStarMap.alwaysShowRangeFor = fleet.oid
		self.win.vStarMap.setPosition = 0
		self.win.vStarMap.precompute()
		self.command = FLACTION_MOVE
		self.deplShipIndex = 0
		if self.targetID:
			target = client.get(self.targetID, noUpdate = 1)
			self.win.vStarMap.highlightPos = (target.x, target.y)
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
		self.win.vMoveBtn.pressed =  self.command == FLACTION_MOVE
		self.win.vAttackBtn.pressed =  self.command == FLACTION_DECLAREWAR
		self.win.vDeplShipBtn.pressed =  self.command == FLACTION_DEPLOY
		self.win.vWaitBtn.pressed =  self.command == FLACTION_WAIT
		self.win.vRefuelBtn.pressed =  self.command == FLACTION_REFUEL
		self.win.vRepeatBtn.pressed =  self.command == FLACTION_REPEATFROM
		self.win.vWormholeBtn.pressed =  self.command == FLACTION_ENTERWORMHOLE
		# hide/show widgets
		for widget in self.win.widgets:
			if widget.tags and self.command in widget.tags:
				widget.visible = 1
			elif widget.tags:
				widget.visible = 0
		# target
		if self.targetID == OID_NONE:
			info = _('No target selected')
		elif self.command in (FLACTION_MOVE, FLACTION_REFUEL, FLACTION_ENTERWORMHOLE):
			target = client.get(self.targetID, noUpdate = 1)
			info = getattr(target, 'name', res.getUnknownName())
		elif self.command == FLACTION_DEPLOY:
			target = client.get(self.targetID, noUpdate = 1)
			if target.type == T_PLANET:
				info = getattr(target, 'name', res.getUnknownName())
			else:
				info = _('No planet selected')
		elif self.command == FLACTION_DECLAREWAR:
			if self.targetPlayerID not in (OID_NONE, client.getPlayerID()):
				target = client.get(self.targetPlayerID, noUpdate = 1)
				info = getattr(target, 'name', res.getUnknownName())
			else:
				info = _("No commander specified.")
		else:
			info = _('?')
		self.win.vTarget.text = info
		if self.targetID != OID_NONE:
			curTarget = client.get(self.targetID, noUpdate = 1)
			fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
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

		# ships
		fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
		self.deplShips = []
		# collect buildings
                for designID, a, b, c in fleet.ships: #fixed bug in reference of designID...added a, b, c to do it; breaks list lookup otherwise (not sure why) with hash error --RC
			tech = client.getPlayer().shipDesigns[designID]
			if tech.deployStructs:
				self.deplShips.append(designID)
				log.debug('Adding design with structure',designID)
			elif tech.deployHandlers:
				hasHandler = False
				for handler in tech.deployHandlers:
					if handler != '': #why are blank handlers getting added in ship construction? catch here for now
						hasHandler = True
						break
				if hasHandler:
					self.deplShips.append(designID)
					log.debug('Adding design with project',designID)
		# correct buildingIndex
		if self.deplShipIndex >= len(self.deplShips):
			self.deplShipIndex = 0
		if self.deplShips:
			self.win.vDeplShipBtn.enabled = 1
			techID = self.deplShips[self.deplShipIndex]
			self.win.vDeplShip.text = client.getPlayer().shipDesigns[techID].name
			self.win.vDeplShip.data = techID
		else:
			self.win.vDeplShipBtn.enabled = 0
			if self.command == FLACTION_DEPLOY:
				self.command == FLACTION_MOVE
				self.showCommands()

	def onSelectCommand(self, widget, action, data):
		self.command = widget.data
		self.showCommands()

	def onSelectMapObj(self, widget, action, data):
		target = client.get(data, noUpdate = 1)
		if target.type == T_PLANET:
			self.targetID = target.oid
			self.win.vStarMap.highlightPos = (target.x, target.y)
		elif target.type in (T_SYSTEM, T_WORMHOLE):
			self.targetID = target.oid
			self.win.vStarMap.highlightPos = (target.x, target.y)
		else:
			self.win.vStarMap.hightlightPos = None
		self.targetPlayerID = getattr(target, "owner", OID_NONE)
		self.showCommands()

	def onCancel(self, widget, action, data):
		self.hide()

	def onDeplShipChange(self, widget, action, data):
		self.deplShipIndex += 1
		self.showCommands()

	def onOrder(self, widget, action, data):
		targetID = self.targetID
		if self.command in (FLACTION_MOVE, FLACTION_REFUEL):
			if self.targetID == OID_NONE:
				self.win.setStatus(_('Select target, please.'))
				return
			commandData = None
		elif self.command == FLACTION_ENTERWORMHOLE:
                        if self.targetID == OID_NONE:
				self.win.setStatus(_('Select target, please.'))
				return
			target = client.get(self.targetID, noUpdate = 1)
			if target.type != T_WORMHOLE:
				self.win.setStatus(_('Can only traverse wormholes.'))
				return
			commandData = None
		elif self.command == FLACTION_DECLAREWAR:
			if self.targetPlayerID == OID_NONE:
				self.win.setStatus(_('Select object with valid owner, please.'))
				return
			commandData = self.targetPlayerID
			targetID = OID_NONE
		elif self.command == FLACTION_DEPLOY:
			if self.targetID == OID_NONE:
				self.win.setStatus(_('Select target planet, please.'))
				return
			target = client.get(self.targetID, noUpdate = 1)
			if target.type != T_PLANET:
				self.win.setStatus(_('You can build on planets only.'))
				return
			commandData = self.win.vDeplShip.data
		elif self.command == FLACTION_WAIT:
			try:
				commandData = int(self.win.vTurns.text)
			except ValueError:
				self.win.setStatus(_('Enter number into "Turns" field.'))
				return
			if commandData < 1:
				self.win.setStatus(_('"Turns" must be 1 or greater.'))
				return
			targetID = OID_NONE
		elif self.command == FLACTION_REPEATFROM:
			try:
				commandData = int(self.win.vStartFrom.text)
			except ValueError:
				self.win.setStatus(_('Enter number into "Start from command #" field.'))
				return
			if commandData < 1:
				self.win.setStatus(_('"Start from command #" must be 1 or greater'))
				return
			commandData -= 1
			targetID = OID_NONE
		else:
			self.win.setStatus(_('Command not supported yet.'))
			return
		try:
			self.win.setStatus(_('Executing ISSUE COMMAND command...'))
			fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
			fleet.actions, fleet.actionIndex = client.cmdProxy.addAction(self.fleetDlg.fleetID,
				self.cmdIndex, self.command, targetID, commandData)
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			self.fleetDlg.update()
			gdata.mainGameDlg.update()
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('New Command'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		StarMapWidget(self.win, layout = (0, 0, 40, 24),
			id = 'vStarMap', action = 'onSelectMapObj')
		# order buttons
		ui.Title(self.win, layout = (0, 24, 40, 1), text = _('Select command'),
			font = 'normal-bold', align = ui.ALIGN_W)
		ui.Button(self.win, layout = (0, 25, 5, 1), text = _('Move'), toggle = 1,
			id = 'vMoveBtn', action = 'onSelectCommand', data = FLACTION_MOVE)
		ui.Button(self.win, layout = (5, 25, 5, 1), text = _('Refuel at'), toggle = 1,
			id = 'vRefuelBtn', action = 'onSelectCommand', data = FLACTION_REFUEL)
		ui.Button(self.win, layout = (10, 25, 5, 1), text = _('Deploy'), toggle = 1,
			id = 'vDeplShipBtn', action = 'onSelectCommand', data = FLACTION_DEPLOY)
		ui.Button(self.win, layout = (15, 25, 5, 1), text = _('Wait'), toggle = 1,
			id = 'vWaitBtn', action = 'onSelectCommand', data = FLACTION_WAIT)
		ui.Button(self.win, layout = (20, 25, 5, 1), text = _('Declare War'), toggle = 1,
			id = 'vAttackBtn', action = 'onSelectCommand', data = FLACTION_DECLAREWAR)
		ui.Button(self.win, layout = (25, 25, 5, 1), text = _('Repeat'), toggle = 1,
			id = 'vRepeatBtn', action = 'onSelectCommand', data = FLACTION_REPEATFROM)
		ui.Button(self.win, layout = (30, 25, 5, 1), text = _('Use Wormhole'), toggle = 1,
			id = 'vWormholeBtn', action = 'onSelectCommand', data = FLACTION_ENTERWORMHOLE)
		# Target indicator
		ui.Label(self.win, layout = (0, 26, 5, 1), text = _('Target'),
			align = ui.ALIGN_W, tags = [FLACTION_MOVE, FLACTION_DEPLOY, FLACTION_REFUEL, FLACTION_ENTERWORMHOLE])
		ui.Label(self.win, layout = (0, 26, 5, 1), text = _('At commander'),
			align = ui.ALIGN_W, tags = [FLACTION_DECLAREWAR])
		ui.Label(self.win, layout = (5, 26, 10, 1), id = 'vTarget',
			align = ui.ALIGN_E, tags = [FLACTION_MOVE, FLACTION_DEPLOY,
			FLACTION_DECLAREWAR, FLACTION_REFUEL, FLACTION_ENTERWORMHOLE])
		# Delay indicator
		ui.Label(self.win, layout = (0, 26, 5, 1), text = _('Turns'),
			align = ui.ALIGN_W, tags = [FLACTION_WAIT])
		ui.Entry(self.win, layout = (5, 26, 5, 1), id = 'vTurns', text = '1',
			align = ui.ALIGN_E, tags = [FLACTION_WAIT])
		# Ship to deploy
		ui.Label(self.win, layout = (15, 26, 5, 1), text = _('Ship'),
			align = ui.ALIGN_E, tags = [FLACTION_DEPLOY])
		ui.Button(self.win, layout = (20, 26, 10, 1), id = 'vDeplShip',
			align = ui.ALIGN_NONE, tags = [FLACTION_DEPLOY], action = 'onDeplShipChange')
		# Repeat
		ui.Label(self.win, layout = (0, 26, 10, 1), text = _('Start from command #'),
			align = ui.ALIGN_W, tags = [FLACTION_REPEATFROM])
		ui.Entry(self.win, layout = (10, 26, 5, 1), id = 'vStartFrom', text = _('1'),
			align = ui.ALIGN_E, tags = [FLACTION_REPEATFROM])
		ui.Label(self.win, layout = (36, 26, 2, 1), text = _("ETA:"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (38, 26, 2, 1), id = 'vEta', align = ui.ALIGN_E)
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Order'), action = 'onOrder')
		ui.TitleButton(self.win, layout = (30, 27, 5, 1), text = _('Cancel'), action = 'onCancel')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 30, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

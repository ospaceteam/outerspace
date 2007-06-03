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
from osci import client, res, gdata, sequip
from osci.SystemMapWidget import SystemMapWidget
from FleetCommandDlg import FleetCommandDlg
from FleetSpecsDlg import FleetSpecsDlg
from FleetSplitDlg import FleetSplitDlg
from ConfirmDlg import ConfirmDlg
from ige.ospace.Const import *
from ige.ospace import Rules
import ige
import string

class FleetDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.fleetCommandDlg = FleetCommandDlg(self.app)
		self.fleetSpecsDlg = FleetSpecsDlg(self.app)
		self.fleetSplitDlg = FleetSplitDlg(self.app)
		self.confirmDlg = ConfirmDlg(app)

	def display(self, objID):
		fleet = client.get(objID)
		if not hasattr(fleet, "ships"):
			return
		self.fleetID = objID
		self.showFleet()
		# show window
		if not self.win.visible:
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
		if self.win.visible:
			self.showFleet()

	def showFleet(self):
		fleet = client.get(self.fleetID, noUpdate = 1)
		self.win.title = _('Fleet: %s') % getattr(fleet, 'name', res.getUnknownName())
		# fill listbox
		items = []
		# serial ships
		if hasattr(fleet, 'ships'):
			for designID, hp, shield, exp in fleet.ships:
				tech = client.getPlayer().shipDesigns[designID]
				if shield > 0:
					hpInfo = _("%d + %d") % (hp, shield)
					hpSort = hp + 1000 * shield
				else:
					hpInfo = _("%d") % hp
					hpSort = hp
				item = ui.Item(tech.name,
					tHP = hpInfo,
					tHP_raw = hpSort,
					tExp = exp,
					tClass = _(gdata.shipClasses[tech.combatClass]),
					designID = designID,
					tLevel = Rules.shipExpToLevel.get(int(exp / tech.baseExp), Rules.shipDefLevel),
					tSpec = [designID, hp, shield, exp],
					tSpeed = _("%.2f") % tech.speed
				)
				items.append(item)
		self.win.vShips.items = items
		self.win.vShips.itemsChanged()
		self.win.vShips.selectItem(self.win.vShips.items[0])
		self.showShip(self.win.vShips.items[0].designID, self.win.vShips.items[0].tExp)
		# fleet info
		self.win.vFCoordinates.text = '[%.1f, %.1f]' % (fleet.x, fleet.y)
		if fleet.orbiting != OID_NONE:
			self.win.vFOrbiting.text = getattr(client.get(fleet.orbiting, noUpdate = 1), 'name', res.getUnknownName())
		else:
			self.win.vFOrbiting.text = _('N/A')
		if hasattr(fleet, "speedBoost") and hasattr(fleet, "maxSpeed"):
			text = _("%.2f") % (fleet.maxSpeed * fleet.speedBoost)
			info = _("Base speed %.2f, speed boost %.2f") % (
				fleet.maxSpeed, fleet.speedBoost
			)
		else:
			text = _("?")
			info = None
		self.win.vFMaxSpeed.text = text
		self.win.vFMaxSpeed.tooltip = info
		self.win.vFMaxSpeed.statustip = info
		self.win.vFSignature.text =  getattr(fleet, 'signature', '?')
		# commands
		items = []
		index = 0
		if hasattr(fleet, 'actions'):
			for action, target, data in fleet.actions:
				info = "-"
				if target != OID_NONE:
					targetName = getattr(client.get(target, noUpdate = 1), 'name', res.getUnknownName())
				else:
					targetName = '-'
				if index == fleet.actionIndex: current = '>'
				else: current = ''
				# additional info
				if action == FLACTION_DECLAREWAR:
					info = getattr(client.get(data, noUpdate = 1), 'name', res.getUnknownName())
				elif action == FLACTION_DEPLOY:
					info = client.getPlayer().shipDesigns[data].name
				elif action == FLACTION_REPEATFROM:
					info = _("Command #%d") % (data + 1)
				elif action == FLACTION_WAIT:
					info = _("%d / %d") % (fleet.actionWaitCounter, data)
				# create item
				item = ui.Item(gdata.fleetActions[action], targetName = targetName, data = info, tIndex = index + 1, current = current)
				items.append(item)
				index += 1
		self.win.vCommands.items = items
		self.win.vCommands.selection = []
		self.win.vCommands.itemsChanged()
		self.win.vCommandUp.enabled = 0
		self.win.vCommandDown.enabled = 0
		self.win.vCommandDel.enabled = 0
		self.win.vCommandSetActive.enabled = 0

	def showShip(self, techID, exp):
		tech = client.getPlayer().shipDesigns[techID]
		level = Rules.shipExpToLevel.get(int(exp / tech.baseExp), Rules.shipDefLevel)
		self.win.vShipModel.text = tech.name
		self.win.vShipClass.text = _(gdata.shipClasses[tech.combatClass])
		self.win.vShipAtt.text = int(tech.combatAtt * Rules.shipLevelEff[level])
		self.win.vShipDef.text = _("%d / %d") % (
			int(tech.combatDef * Rules.shipLevelEff[level]),
			int(tech.missileDef * Rules.shipLevelEff[level]),
		)
		self.win.vShipMaxSpeed.text = _("%.2f") % tech.speed
		self.win.vShipScannerPwr.text = tech.scannerPwr
		self.win.vShipSupport.text = _("%d + %d") % (tech.operEn, int(tech.buildProd * Rules.operProdRatio))
		info = _("Support: %d energy and %d contruction points per turn.") % (tech.operEn, int(tech.buildProd * Rules.operProdRatio))
		self.win.vShipSupport.statustip = info
		self.win.vShipSupport.tooltip = info
		self.win.vShipStorages.text = _("%d") % tech.storEn
		self.win.vShipSignature.text = tech.signature
		if tech.shieldHP > 0:
			self.win.vShipMaxHP.text = _("%d + %d") % (
				tech.maxHP,
				tech.shieldHP,
			)
		else:
			self.win.vShipMaxHP.text = _("%d") % (
				tech.maxHP,
			)
		# show equipment
		items = []
		for techID in tech.eqIDs:
			eq = client.getTechInfo(techID)
			short = sequip.getShortDescr(techID)
			long = sequip.getLongDescr(techID)
			item = ui.Item(_("%d x %s") % (tech.eqIDs[techID], eq.name),
				tData = short, tooltip = long, statustip = long)
			items.append(item)
		self.win.vShipEquipment.items = items
		self.win.vShipEquipment.itemsChanged()

	def onFleetSpecs(self, widget, action, data):
		self.fleetSpecsDlg.displayFleet(self.fleetID)

	def onShipSelected(self, widget, action, data):
		self.showShip(data.designID, data.tExp)

	def onSelectCommand(self, widget, action, data):
		index = self.win.vCommands.items.index(self.win.vCommands.selection[0])
		self.win.vCommandUp.enabled = index > 0
		self.win.vCommandDown.enabled = index < len(self.win.vCommands.items) - 1
		self.win.vCommandDel.enabled = 1
		self.win.vCommandSetActive.enabled = 1

	def onNewCommand(self, widget, action, data):
		sel = self.win.vCommands.selection
		if not sel:
			self.fleetCommandDlg.display(self, FleetCommandDlg.NEW_COMMAND)
		else:
			self.fleetCommandDlg.display(self, self.win.vCommands.items.index(sel[0]) + 1)

	def onDeleteCommand(self, widget, action, data, all=0):
		sel = self.win.vCommands.selection
		if not sel:
			self.win.setStatus(_('Select command to delete.'))
			return
		item = sel[0]
		try:
			self.win.setStatus(_('Executing DELETE COMMAND command...'))
			fleet = client.get(self.fleetID, noUpdate = 1)
			fleet.actions, fleet.actionIndex = client.cmdProxy.deleteAction(self.fleetID,
				item.tIndex - 1)
			self.win.vCommands.selection = []
			if not all: # 0 from UI; 1 from "DeleteAll" function
				self.win.setStatus(_('Command has been executed.'))
				if item.text == gdata.fleetActions[FLACTION_WAIT]:
					fleet = client.get(self.fleetID,forceUpdate=1)
				self.update()
				gdata.mainGameDlg.update()
			return 0
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))
			return 1

	def onDeleteAllCommands(self, widget, action, data):
		index = 0
		while len(self.win.vCommands.items) > index:
			self.win.vCommands.selection = [self.win.vCommands.items[index]]
			index += self.onDeleteCommand(widget, action, data, all=1)
		self.win.setStatus(_('Command has been executed.'))
		fleet = client.get(self.fleetID,forceUpdate=1)
		self.update()
		gdata.mainGameDlg.update()

	def onSetActiveCommand(self, widget, action, data):
		sel = self.win.vCommands.selection
		if not sel:
			self.win.setStatus(_('Select command to activate.'))
			return
		item = sel[0]
		try:
			self.win.setStatus(_('Executing ACTIVATE COMMAND command...'))
			fleet = client.get(self.fleetID, noUpdate = 1)
			fleet.actionIndex = client.cmdProxy.setActionIndex(self.fleetID,
				item.tIndex - 1)
			self.win.setStatus(_('Command has been executed.'))
			self.win.vCommands.selection = []
			self.update()
			gdata.mainGameDlg.update()
			return 0
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))
			return 1

	def onCommandMove(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing MOVE ACTION command...'))
			fleet = client.get(self.fleetID, noUpdate = 1)
			index = self.win.vCommands.items.index(self.win.vCommands.selection[0])
			# execute command
			fleet.actions = client.cmdProxy.moveAction(fleet.oid, index, widget.data)
			self.update()
			index += widget.data
			self.win.vCommands.selectItem(self.win.vCommands.items[index])
			self.win.setStatus(_('Command has been executed.'))
			self.onSelectCommand(widget, action, None)
			gdata.mainGameDlg.update()
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))
			return 1

	def onAutoDelete(self, widget, action, data):
		self.win.setStatus(_('Executing CLEAR PROCESSED ACTIONS command...'))
		fleet = client.get(self.fleetID, noUpdate = 1)
		fleet.actions, fleet.actionIndex = client.cmdProxy.clearProcessedActions(fleet.oid)
		self.win.setStatus(_('Command has been executed.'))
		self.win.vCommands.selection = []
		self.update()
		gdata.mainGameDlg.update()

	def onCloseDlg(self, widget, action, data):
		self.hide()

	def onSplitFleet(self, widget, action, data):
		self.fleetSplitDlg.display(self)

	def onDeleteSelectedShip(self, widget, action, data):
		self.confirmDlg.display(_("Really scrap this ship?"),
			_("Yes"), _("No"), self.onDeleteSelectedShipConfirmed)

	def onDeleteSelectedShipConfirmed(self):
		if self.win.vShips.selection:
			item = self.win.vShips.selection[0]
		try:
			self.win.setStatus(_('Executing SCRAP SHIP command...'))
			client.db[self.fleetID] = client.cmdProxy.removeShips(self.fleetID,
				[item.tSpec])
			self.win.setStatus(_('Command has been executed.'))
			if not client.get(self.fleetID, noUpdate = 1).ships:
				# remove fleet
				client.getPlayer().fleets.remove(self.fleetID)
				del client.db[self.fleetID]
				self.hide()
			else:
				self.update()
			gdata.mainGameDlg.update()
			return 0
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))
			return 1

	def onRenameFleet(self, widget, action, data):
		pass

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		ui.Title(self.win, layout = (0, 27, 35, 1), id = 'vStatusBar',
			align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'),
			action = 'onCloseDlg')
		# fleet selection
		ui.Listbox(self.win, id = 'vShips', layout = (0, 0, 20, 12),
			columns = (
			(_('Name'), 'text', 6.5, ui.ALIGN_W),
			(_('Lvl'), 'tLevel', 1.5, ui.ALIGN_NONE),
			(_('Class'), 'tClass', 3, ui.ALIGN_E),
			(_('HP'), 'tHP', 4, ui.ALIGN_E),
			(_('Exp'), 'tExp', 2, ui.ALIGN_E),
			(_('Spd'), 'tSpeed', 2, ui.ALIGN_E),
			),
			columnLabels = 1, action = 'onShipSelected')
		# fleet data
		ui.Label(self.win, text = _('Coordinates'), layout = (20, 0, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vFCoordinates', layout = (25, 0, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Orbiting'), layout = (30, 0, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vFOrbiting', layout = (35, 0, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Max speed'), layout = (20, 1, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vFMaxSpeed', layout = (25, 1, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Signature'), layout = (30, 1, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vFSignature', layout = (35, 1, 5, 1), align = ui.ALIGN_E)
		# commands
		ui.Title(self.win, text = _('Commands'), align = ui.ALIGN_W, font = 'normal-bold',
			layout = (20, 12, 20, 1))
		ui.Listbox(self.win, layout = (20, 13, 20, 10), id = 'vCommands',
			columns = (('', 'current', 1, 0), (_('#'), 'tIndex', 1, 0), (_('Command'), 'text', 5, ui.ALIGN_W),
				(_('Target'), 'targetName', 7, ui.ALIGN_W),	(_('Info'), 'data', 7, ui.ALIGN_W)),
			columnLabels = 1, action = 'onSelectCommand', sortable = False)
		ui.Button(self.win, text = _('New cmd'), layout = (20, 23, 4, 1),
			action = 'onNewCommand')
		ui.Button(self.win, text = _('Set active'), layout = (24, 23, 4, 1),
			id = 'vCommandSetActive', action = 'onSetActiveCommand')
		ui.Button(self.win, text = _('Delete cmd'), layout = (28, 23, 4, 1),
			id = 'vCommandDel', action = 'onDeleteCommand')
		ui.Button(self.win, text = _('Delete All'), layout = (32, 23, 4, 1),
			action = 'onDeleteAllCommands')
		ui.ArrowButton(self.win, layout = (36, 23, 1, 1), direction = ui.ALIGN_N,
			id = 'vCommandUp', action = 'onCommandMove', data = -1)
		ui.ArrowButton(self.win, layout = (37, 23, 1, 1), direction = ui.ALIGN_S,
			id = 'vCommandDown', action = 'onCommandMove', data = 1)
		ui.Title(self.win, text = _('Other commands'), align = ui.ALIGN_W, font = 'normal-bold',
			layout = (20, 24, 20, 1))
		ui.Button(self.win, text = _('Split fleet'), id = 'vSplitButton',
			layout = (20, 25, 5, 1), action = 'onSplitFleet')
		ui.Button(self.win, text = _('Rename fleet'), id = 'vRenameButton',
			layout = (25, 25, 5, 1), action = 'onRenameFleet', enabled = 0)
		ui.Button(self.win, text = _('Auto delete'), id = 'vAutoDeleteButton',
			layout = (30, 25, 5, 1), action = 'onAutoDelete')
		ui.Button(self.win, text = _('Fleet Specs'), id = 'vFleetSpecs',
			layout = (35, 25, 5, 1), action = 'onFleetSpecs')
		# ship data
		ui.Title(self.win, text = _('Ship Data'), layout = (0, 12, 15, 1),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Button(self.win, text = _("Scrap"), layout = (15, 12, 5, 1),
			action = "onDeleteSelectedShip")
		ui.Label(self.win, text = _('Name'), layout = (0, 13, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipModel', layout = (5, 13, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Class'), layout = (10, 13, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipClass', layout = (15, 13, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Attack eff'), layout = (0, 14, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipAtt', layout = (5, 14, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Defence eff'), layout = (10, 14, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipDef', layout = (15, 14, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Max speed'), layout = (0, 15, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipMaxSpeed', layout = (5, 15, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Scanner Pwr'), layout = (10, 15, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipScannerPwr', layout = (15, 15, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Tanks'), layout = (0, 16, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipStorages', layout = (5, 16, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Signature'), layout = (10, 16, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipSignature', layout = (15, 16, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Support'), layout = (0, 17, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipSupport', layout = (5, 17, 5, 1), align = ui.ALIGN_E)
		ui.Label(self.win, text = _('Max HP'), layout = (10, 17, 5, 1), align = ui.ALIGN_W)
		ui.Label(self.win, id = 'vShipMaxHP', layout = (15, 17, 5, 1), align = ui.ALIGN_E)
		ui.Title(self.win, text = _("Equipment"), layout = (0, 18, 20, 1),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Listbox(self.win, id = 'vShipEquipment', layout = (0, 19, 20, 8),
			columns = ((_('Name'), 'text', 8, ui.ALIGN_W),
			(_('Data'), 'tData', 0, ui.ALIGN_W)),
			columnLabels = 1)

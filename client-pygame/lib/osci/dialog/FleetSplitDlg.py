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

import types
import pygameui as ui
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
from ige.ospace.Const import *
from ige.ospace import Rules
import ige

# grouping options
CLASS = 1
DAMAGE = 2
EXPERIENCE = 4
DESIGN = 8
LEVEL = 16
SPEED = 32

speedDesc = {
	0: _("0"),
	1: _("0 - 4"),
	2: _("4 - 5"),
	3: _("5 - 6"),
	4: _("6 - 7"),
	5: _("7 - 8"),
	6: _("> 8"),
}

dmgDesc = {
	0: _("0% - 33%"),
	1: _("34% - 66%"),
	2: _("67% - 99%"),
	3: _("100%"),
}

def getCountShipsByDesign(ships, maxCount, shipDesignID):
	count = 0
	retShips = []
	for ship in ships:
		if ship[0] == shipDesignID and (count < maxCount or maxCount == -1):
			retShips.append(ship)
			count += 1
	return retShips

def getCountShips(ships, maxCount):
	count = 0
	retShips = []
	for ship in ships:
		if count < maxCount or maxCount == -1:
			retShips.append(ship)
			count += 1
	return retShips

def appendToDict(dict, key, object):
	if not dict.has_key(key):
		dict[key] = [object]
	else:
		dict[key].append(object)

def groupShipsByClass(ships):
	retShips = {}
	for ship in ships:
		appendToDict(retShips, getTech(ship).combatClass, ship)

	return retShips

def groupShipsByExpr(ships):
	retShips = {}
	for ship in ships:
		appendToDict(retShips, ship[3], ship)

	return retShips

def groupShipsByDmg(ships):
	retShips = {}
	for ship in ships:
		appendToDict(retShips, getDamageLevel(ship), ship)

	return retShips

def groupShipsByDesign(ships):
	player = client.getPlayer()
	retShips = {}
	for ship in ships:
		appendToDict(retShips, ship[0], ship)

	return retShips

def groupShipsByLevel(ships):
	retShips = {}
	for ship in ships:
		appendToDict(retShips, getExperienceLevel(ship), ship)

	return retShips

def groupShipsBySpeed(ships):
	retShips = {}
	for ship in ships:
		appendToDict(retShips, getSpeedLevel(ship), ship)

	return retShips

def getTech(ship):
	player = client.getPlayer()
	return player.shipDesigns[ship[0]]

def getExperienceLevel(ship):
	tech = getTech(ship)
	return Rules.shipExpToLevel.get(int(ship[3] / tech.baseExp), Rules.shipDefLevel)

def getDamageLevel(ship):
	tech = getTech(ship)
	dmg = (float(ship[1]) / tech.maxHP) * 100
	if dmg <= 33:
		return 0
	elif dmg > 33 and dmg <= 66:
		return 1
	elif dmg > 66 and dmg <= 99:
		return 2
	else: # 100%
		return 3

def getSpeedLevel(ship):
	speed = getTech(ship).speed
	if speed <= 0:
		return 0
	elif speed > 0 and speed < 4:
		return 1
	elif speed >= 4 and speed < 5:
		return 2
	elif speed >= 5 and speed < 6:
		return 3
	elif speed >= 6 and speed < 7:
		return 4
	elif speed >= 7 and speed < 8:
		return 5
	else: # >= 8
		return 6

class FleetSplitDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, fleetDlg):
		self.fleetDlg = fleetDlg
		fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
		self.origShips = fleet.ships[:]
		self.storEn = self.origEn = fleet.storEn
		self.origEnMax = fleet.maxEn
		self.newShips = []
		self.newBio = 0
		self.newMin = 0
		self.newEn = 0
		self.newEnMax = 0
		self.checks = 0
		self.Nchecks = 0

		self.win.vDesign.checked = 0
		self.win.vClass.checked = 0
		self.win.vDmg.checked = 0
		self.win.vExpr.checked = 0
		self.win.vLevel.checked = 0
		self.win.vSpeed.checked = 0
		self.win.vNDesign.checked = 0
		self.win.vNClass.checked = 0
		self.win.vNDmg.checked = 0
		self.win.vNExpr.checked = 0
		self.win.vNLevel.checked = 0
		self.win.vNSpeed.checked = 0

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
		self.hide()

	def groupShips(self, grouped, by):
		for key, item in grouped.items():
			if type(item) == types.ListType:
				if by & DESIGN:
					grouped[key] = groupShipsByDesign(item)
					self.groupShips(grouped[key], by - DESIGN)
				elif by & CLASS:
					grouped[key] = groupShipsByClass(item)
					self.groupShips(grouped[key], by - CLASS)
				elif by & DAMAGE:
					grouped[key] = groupShipsByDmg(item)
					self.groupShips(grouped[key], by - DAMAGE)
				elif by & LEVEL:
					grouped[key] = groupShipsByLevel(item)
					self.groupShips(grouped[key], by - LEVEL)
				elif by & EXPERIENCE:
					grouped[key] = groupShipsByExpr(item)
					self.groupShips(grouped[key], by - EXPERIENCE)
				elif by & SPEED:
					grouped[key] = groupShipsBySpeed(item)
					self.groupShips(grouped[key], by - SPEED)

	def appendShips(self, grouped, items, player, checks):
		for key, item in grouped.items():
			if checks == 0:
				for ship in item:
					self.appendItem(ship, items, player, 0)

				return

			if type(item) == types.ListType:
				self.appendItem(item, items, player, checks)
			else:
				self.appendShips(item, items, player, checks)

	def show(self):
		# orig fleet
		items = []
		player = client.getPlayer()

		grouped = {None: self.origShips}
		self.groupShips(grouped, self.checks)
		self.appendShips(grouped, items, player, self.checks)

		self.win.vOShips.items = items
		self.win.vOShips.itemsChanged()
		self.win.vOShips.selectItem(None)
		self.win.vOEn.text = str(self.origEn)
		self.win.vOEnMax.text = _('/ %d') % self.origEnMax

		# new fleet
		items = []

		grouped = {None: self.newShips}
		self.groupShips(grouped, self.Nchecks)
		self.appendShips(grouped, items, player, self.Nchecks)

		self.win.vNShips.items = items
		self.win.vNShips.itemsChanged()
		self.win.vNShips.selectItem(None)
		self.win.vNEn.text = str(self.newEn)
		self.win.vNEnMax.text = _('/ %d') % self.newEnMax

	def appendItem(self, ships, items, player, checks):
		if type(ships[0]) == types.ListType:
			count = len(ships)
			designName = ""
			listData = ships
			exp = ""
			hpText = ""
			designID = None
			className = ""
			level = ""
			speed = ""
		else:
			count = ""
			designID, hp, shield, exp = ships
			tech = getTech(ships)
			designName = tech.name
			className = _(gdata.shipClasses[tech.combatClass])
			hpText = _("%d / %d") % (hp, shield)
			level = getExperienceLevel(ships)
			listData = [ships]
			speed = _("%.2f") % tech.speed

		if checks & DAMAGE:
			hpText = dmgDesc[getDamageLevel(listData[0])]

		if checks & CLASS:
			tech = getTech(listData[0])
			className = _(gdata.shipClasses[tech.combatClass])
			
		if checks & EXPERIENCE:
			exp = listData[0][3]

		if checks & LEVEL:
			level = getExperienceLevel(listData[0])

		if checks & SPEED:
			speed = speedDesc[getSpeedLevel(listData[0])]

		if checks & DESIGN:
			designName = getTech(listData[0]).name
			if not (checks & CLASS):
				tech = getTech(listData[0])
				className = _(gdata.shipClasses[tech.combatClass])
			if not (checks & SPEED):
				speed = _("%.2f") % getTech(listData[0]).speed


		item = ui.Item(designName,
			tHP = hpText,
			tExp = exp,
			tClass = className,
			designID = designID,
			tLevel = level,
			tShip = listData,
			tCount = count,
			tSpeed = speed,
		)
		items.append(item)

	def onSplit(self, widget, action, data):
		# TODO
		self.win.setStatus(_('Executing SPLIT FLEET command...'))
		try:
			fleet = client.get(self.fleetDlg.fleetID, noUpdate = 1)
			newFleet, origFleet, fleets = client.cmdProxy.splitFleet(self.fleetDlg.fleetID,
				self.newShips, self.newEn)
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return
		# update related objects
		client.getPlayer().fleets = fleets
		client.db[newFleet.oid] = newFleet
		client.db[origFleet.oid] = origFleet
		# update client
		self.win.setStatus(_('Command has been executed.'))
		self.hide()
		self.fleetDlg.display(newFleet.oid)
		gdata.mainGameDlg.update()

	def updateRes(self):
		# orig max
		player = client.getPlayer()
		self.origEnMax = 0
		for designID, hp, shield, exp in self.origShips:
			tech = player.shipDesigns[designID]
			self.origEnMax += tech.storEn
		# new max
		self.newEnMax = 0
		for designID, hp, shield, exp in self.newShips:
			tech = player.shipDesigns[designID]
			self.newEnMax += tech.storEn
		# orig
		if self.origEn > self.origEnMax:
			self.newEn += self.origEn - self.origEnMax
			self.origEn = self.origEnMax
		# new
		if self.newEn > self.newEnMax:
			self.origEn += self.newEn - self.newEnMax
			self.newEn = self.newEnMax

	def onOShipSelected(self, widget, action, data):
		item = self.win.vOShips.selection[0]
		self.moveShipsToRight(item.tShip)
		#
		self.updateRes()
		self.show()

	def onNShipSelected(self, widget, action, data):
		item = self.win.vNShips.selection[0]
		self.moveShipsToLeft(item.tShip)
		#
		self.updateRes()
		self.show()

	def onStorChng(self, widget, action, data):
		try:
			self.origEn = int(self.win.vOEn.text)
			self.newEn = int(self.win.vNEn.text)
		except ValueError:
			self.win.setStatus(_('Enter a number.'))
			self.show()
			return
		# update changed
		newVal = getattr(self, widget.data)
		if widget.data[:4] == 'orig':
			mirror = 'new%s' % widget.data[4:]
			total = getattr(self, 'stor%s' % widget.data[4:])
		if widget.data[:3] == 'new':
			mirror = 'orig%s' % widget.data[3:]
			total = getattr(self, 'stor%s' % widget.data[3:])
		mirrVal = total - newVal
		if mirrVal < 0:
			newVal = total
			mirrVal = 0
		setattr(self, widget.data, newVal)
		setattr(self, mirror, mirrVal)
		self.updateRes()
		self.show()

	def onMoveMenu(self, widget, action, data):
		selItem = self.win.vOShips.selection[0]
		if hasattr(selItem, "designID"):
			self.moveRightPopup.show()

	def onNMoveMenu(self, widget, action, data):
		selItem = self.win.vNShips.selection[0]
		if hasattr(selItem, "designID"):
			self.moveLeftPopup.show()

	def onMoveAction(self, widget, action, data):
		selItem = self.win.vOShips.selection[0]
		if selItem.designID == None:
			self.moveShipsToRight(getCountShips(selItem.tShip, data))
		else:
			self.moveShipsToRight(getCountShipsByDesign(self.origShips, data, selItem.designID))

		self.updateRes()
		self.show()

	def onNMoveAction(self, widget, action, data):
		selItem = self.win.vNShips.selection[0]
		if selItem.designID == None:
			self.moveShipsToLeft(getCountShips(selItem.tShip, data))
		else:
			self.moveShipsToLeft(getCountShipsByDesign(self.newShips, data, selItem.designID))

		self.updateRes()
		self.show()

	def onClear(self, widget, action, data):
		self.moveShipsToLeft(self.newShips[:])
		self.updateRes()
		self.show()

	def moveShipsToRight(self, ships):
		for ship in ships:
			self.origShips.remove(ship)
			self.newShips.append(ship)
			# move fuel to the new fleet
			tech = client.getPlayer().shipDesigns[ship[0]]
			avail = min(self.origEn, tech.storEn)
			self.newEn += avail
			self.origEn -= avail

	def moveShipsToLeft(self, ships):
		for ship in ships:
			self.newShips.remove(ship)
			self.origShips.append(ship)
			# move fuel to the new fleet
			tech = client.getPlayer().shipDesigns[ship[0]]
			avail = min(self.origEn, tech.storEn)
			self.newEn -= avail
			self.origEn += avail

  	def onGroup(self, widget, action, data):
  		if widget.checked:
  			self.checks += widget.data
  		else:
  			self.checks -= widget.data

		self.updateRes()
		self.show()

  	def onNGroup(self, widget, action, data):
  		if widget.checked:
  			self.Nchecks += widget.data
  		else:
  			self.Nchecks -= widget.data

		self.updateRes()
		self.show()

  	def onCancel(self, widget, action, data):
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Split Fleet'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
			tabChange = True,
		)
		self.win.subscribeAction('*', self)
		# original fleet
		ui.Title(self.win, layout = (0, 0, 20, 1), text = _('Original fleet'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Listbox(self.win, id = 'vOShips', layout = (0, 1, 20, 21),
			columns = (
			(_('#'), 'tCount', 1.5, ui.ALIGN_NONE),
			(_('Name'), 'text', 5, ui.ALIGN_W),
			(_('Lvl'), 'tLevel', 1.5, ui.ALIGN_NONE),
			(_('Class'), 'tClass', 3, ui.ALIGN_E),
			(_('HP'), 'tHP', 4, ui.ALIGN_E),
			(_('Exp'), 'tExp', 2, ui.ALIGN_E),
			(_('Spd'), 'tSpeed', 2, ui.ALIGN_E),
			),
			columnLabels = 1, action = 'onOShipSelected', rmbAction = 'onMoveMenu'
		)
		# grouping options
		ui.Title(self.win, layout = (0, 22, 20, 1), text = _('Group by'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Check(self.win, layout = (0, 23, 5, 1), id = "vDesign", text = _("design"),
			action = "onGroup", data = DESIGN)
		ui.Check(self.win, layout = (5, 23, 5, 1), id = "vClass", text = _("class"),
			action = "onGroup", data = CLASS)
		ui.Check(self.win, layout = (10, 23, 5, 1), id = "vDmg", text = _("damage"),
			action = "onGroup", data = DAMAGE)
		ui.Check(self.win, layout = (15, 23, 5, 1), id = "vExpr", text = _("experience"),
			action = "onGroup", data = EXPERIENCE)
		ui.Check(self.win, layout = (0, 24, 5, 1), id = "vLevel", text = _("level"),
			action = "onGroup", data = LEVEL)
		ui.Check(self.win, layout = (5, 24, 5, 1), id = "vSpeed", text = _("speed"),
			action = "onGroup", data = SPEED)
		# tanks
		ui.Title(self.win, layout = (0, 25, 20, 1), text = _('Tanks'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Label(self.win, layout = (0, 26, 5, 1), text = _('Fuel'), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (5, 26, 5, 1), id = 'vOEn', action = 'onStorChng',
			align = ui.ALIGN_E, data ='origEn', orderNo = 15)
		ui.Label(self.win, layout = (10, 26, 5, 1), id = 'vOEnMax', align = ui.ALIGN_W)

		# new fleet
		ui.Title(self.win, layout = (20, 0, 20, 1), text = _('New fleet'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Listbox(self.win, id = 'vNShips', layout = (20, 1, 20, 21),
			columns = (
			(_('#'), 'tCount', 1.5, ui.ALIGN_NONE),
			(_('Name'), 'text', 5, ui.ALIGN_W),
			(_('Lvl'), 'tLevel', 1.5, ui.ALIGN_NONE),
			(_('Class'), 'tClass', 3, ui.ALIGN_E),
			(_('HP'), 'tHP', 4, ui.ALIGN_E),
			(_('Exp'), 'tExp', 2, ui.ALIGN_E),
			(_('Spd'), 'tSpeed', 2, ui.ALIGN_E),
			),
			columnLabels = 1, action = 'onNShipSelected', rmbAction = 'onNMoveMenu')
		# grouping
		ui.Title(self.win, layout = (20, 22, 16, 1), text = _('Group by'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Button(self.win, layout = (36, 22, 4, 1), text = _("Clear"), action = 'onClear')
		ui.Check(self.win, layout = (20, 23, 5, 1), id = "vNDesign", text = _("design"),
			action = "onNGroup", data = DESIGN)
		ui.Check(self.win, layout = (25, 23, 5, 1), id = "vNClass", text = _("class"),
			action = "onNGroup", data = CLASS)
		ui.Check(self.win, layout = (30, 23, 5, 1), id = "vNDmg", text = _("damage"),
			action = "onNGroup", data = DAMAGE)
		ui.Check(self.win, layout = (35, 23, 5, 1), id = "vNExpr", text = _("experience"),
			action = "onNGroup", data = EXPERIENCE)
		ui.Check(self.win, layout = (20, 24, 5, 1), id = "vNLevel", text = _("level"),
			action = "onNGroup", data = LEVEL)
		ui.Check(self.win, layout = (25, 24, 5, 1), id = "vNSpeed", text = _("speed"),
			action = "onNGroup", data = SPEED)
		# tanks
		ui.Title(self.win, layout = (20, 25, 20, 1), text = _('Tanks'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Label(self.win, layout = (20, 26, 5, 1), text = _('Fuel'), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (25, 26, 5, 1), id = 'vNEn', action = 'onStorChng',
			align = ui.ALIGN_E, data ='newEn', orderNo = 16)
		ui.Label(self.win, layout = (30, 26, 5, 1), id = 'vNEnMax', align = ui.ALIGN_W)

		# status bar + submit/cancel
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 30, 1), align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Split'), action = 'onSplit')
		ui.TitleButton(self.win, layout = (30, 27, 5, 1), text = _('Cancel'), action = 'onCancel')
		self.moveRightPopup = ui.Menu(self.app, title = _("Move right"),
			width = 5,
			items = [
				ui.Item(_("1 ship"), action = "onMoveAction", data = 1),
				ui.Item(_("5 ships"), action = "onMoveAction", data = 5),
				ui.Item(_("10 ships"), action = "onMoveAction", data = 10),
				ui.Item(_("50 ships"), action = "onMoveAction", data = 50),
				ui.Item(_("100 ships"), action = "onMoveAction", data = 100),
				ui.Item(_("All ships"), action = "onMoveAction", data = -1),
			]
		)
		self.moveRightPopup.subscribeAction("*", self)

		self.moveLeftPopup = ui.Menu(self.app, title = _("Move left"),
			width = 5,
			items = [
				ui.Item(_("1 ship"), action = "onNMoveAction", data = 1),
				ui.Item(_("5 ships"), action = "onNMoveAction", data = 5),
				ui.Item(_("10 ships"), action = "onNMoveAction", data = 10),
				ui.Item(_("50 ships"), action = "onNMoveAction", data = 50),
				ui.Item(_("100 ships"), action = "onNMoveAction", data = 100),
				ui.Item(_("All ships"), action = "onNMoveAction", data = -1),
			]
		)
		self.moveLeftPopup.subscribeAction("*", self)

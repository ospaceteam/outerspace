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
from TechInfoDlg import TechInfoDlg
from ige.ospace.Const import *
from ige.ospace import Rules
from osci import gdata, client, res
from ige import GameException
import math

class StructTaskDlg:

	def __init__(self, app):
		self.app = app
		self.showStructures = 1
		self.showShips = 0
		self.showOther = 0
		self.techID = 0
		self.showLevels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
		self.techInfoDlg = TechInfoDlg(app)
		self.createUI()

	def display(self, caller, planetID, extraSlot = False, structToDemolish = OID_NONE):
		if gdata.config.defaults.reportfinalization != None:
			val = gdata.config.defaults.reportfinalization
			self.win.vReportFin.checked = val == 'yes'

		self.caller = caller
		self.systemID = caller.systemID
		self.planetID = caller.planetID
		self.playerID = client.getPlayerID()
		self.sourceID = caller.planetID
		self.extraSlot = extraSlot
		self.maxTechLevel = 0
		self.quantity = 1
		self.structToDemolish = structToDemolish
		self.win.vPlanets.selectItem(None)
		self.showPlanets()
		self.showTechs()
		self.win.show()
		gdata.updateDlgs.append(self)

	def hide(self):
		self.win.setStatus(_("Ready."))
		if self in gdata.updateDlgs:
			gdata.updateDlgs.remove(self)
		self.win.hide()

	def update(self):
		if self.win.visible:
			self.showPlanets()
			self.showTechs()

	def showPlanets(self):
		info = []
		system = client.get(self.systemID, noUpdate = 1)
		select = None
		playerID = client.getPlayerID()
		firstEnabled = None
		if hasattr(system, 'planets'):
			for planetID in system.planets:
				# get planet
				planet = client.get(planetID, noUpdate = 1)
				# only player owned planets can be source planets
				enabled = getattr(planet, "owner") == playerID
				buttonText = "%s / %s" % (getattr(planet, 'name', res.getUnknownName()), getattr(planet, "effProdProd", "?"))
				item = ui.Item(
					buttonText,
					planetID = planetID,
					enabled = enabled,
					align = ui.ALIGN_NONE,
				)
				info.append(item)
				# remember first players planet
				if enabled and firstEnabled == None:
					firstEnabled = item

				# select actual planet as source only if player owns it
				if planetID == self.sourceID and enabled:
					select = item

		# set as selected source first players planet
		if select == None:
			select = firstEnabled
			self.sourceID = firstEnabled.planetID

		self.win.vPlanets.items = info
		self.win.vPlanets.itemsChanged()
		self.win.vPlanets.selectItem(select)

	def showTechs(self):
		# techs
		items = []
		select = None
		showMilitary = self.win.vMilitary.checked
		showBio = self.win.vBioProduction.checked
		showEn = self.win.vEnProduction.checked
		showCP = self.win.vCPProduction.checked
		showRP = self.win.vRPProduction.checked
		showMorale = self.win.vMorale.checked

		for techID in client.getPlayer().techs.keys():
			tech = client.getTechInfo(techID)

			if not ((tech.isMilitary and showMilitary) or \
			   ((getattr(tech, "prodBio", 0) > 0 or getattr(tech, "prodEnv", 0) > 0) and showBio) or \
			   (getattr(tech, "prodEn", 0) > 0 and showEn) or \
			   (getattr(tech, "prodProd", 0) > 0 and showCP) or \
			   (getattr(tech, "prodSci", 0) > 0 and showRP) or \
			   (getattr(tech, "moraleTrgt", 0) > 0 and showMorale)):
				continue

			sourcePlanet = client.get(self.sourceID, noUpdate = 1)
			prodProd = getattr(sourcePlanet, "effProdProd", 0)

			if prodProd > 0:
				etc = math.ceil(float(tech.buildProd) / prodProd)
				if self.sourceID != self.planetID:
					etc *= Rules.buildOnAnotherPlanetMod
				etc = res.formatTime(etc)
			else:
				etc = _("N/A")

			item = ui.Item(etc,
				techID = techID,
				tIsShip = 0,
				name = tech.name,
				icons = ((res.getTechImg(techID), ui.ALIGN_N),),
				font = "small-bold",
				align = ui.ALIGN_S,
				tooltip = "%s, %d CP, TL %d" % (tech.name, tech.buildProd, tech.level),
				statustip = "%s, %d CP, TL %d" % (tech.name, tech.buildProd, tech.level),
			)
			if tech.level > self.maxTechLevel:
				self.maxTechLevel = tech.level
			# TODO FIX ME
			if tech.level in self.showLevels and \
				((self.showStructures and tech.isStructure) or \
				(self.showOther and (tech.isProject))) or tech.level == 99:
				items.append(item)
				if techID == self.techID:
					select = item

		# sort it by level and then by name
		items.sort(lambda a, b: cmp(a.name, b.name))
		self.win.vTechs.items = items
		self.win.vTechs.itemsChanged()
		if select:
			self.win.vTechs.selectItem(select)

		# filter
		for i in xrange(1, 10):
			widget = getattr(self.win, 'vLevel%d' % i)
			if i in self.showLevels and i <= self.maxTechLevel:
				widget.visible = 1
				widget.pressed = 1
			elif i not in self.showLevels and i <= self.maxTechLevel:
				widget.visible = 1
				widget.pressed = 0
			else:
				widget.visible = 0

		# quantity
		self.win.vQuantity.text = str(self.quantity)

	def onSelectPlanet(self, widget, action, data):
		if data == None:
			for item in self.win.vPlanets.items:
				if self.sourceID == item.planetID:
					self.win.vPlanets.selectItem(item)
					break
			return
		self.sourceID = data.planetID
		self.showTechs()

	def onToggleLevel(self, widget, action, data):
		i = widget.data
		if i in self.showLevels:
			self.showLevels.remove(i)
		else:
			self.showLevels.append(i)
		self.update()

	def onCancel(self, widget, action, data):
		self.hide()

	def onConstruct(self, widget, action, data):
		if not data:
			self.win.setStatus(_('Select technology to construct.'))
			return

		if not self.sourceID:
			self.sourceID = self.planetID

		try:
			self.quantity = int(self.win.vQuantity.text)
		except ValueError:
			self.win.setStatus(_('Specify quantity (1, 2, 3, ...).'))
			return

		try:
			self.win.setStatus(_('Executing START CONSTRUCTION command...'))
			planet = client.get(self.sourceID, noUpdate = 1)
			if self.extraSlot:
				for i in range(1, self.quantity + 1):
					client.cmdProxy.startConstruction(self.sourceID,
						Rules.Tech.ADDSLOT3, 1, self.planetID, False,
						self.win.vReportFin.checked, OID_NONE)
					player = client.getPlayer()
					planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(self.sourceID,
						data.techID, 1, self.planetID, data.techID < 1000,
						self.win.vReportFin.checked, self.structToDemolish)
			else:
				player = client.getPlayer()
				planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(self.sourceID,
					data.techID, self.quantity, self.planetID, data.techID < 1000,
					self.win.vReportFin.checked, self.structToDemolish)
			self.win.setStatus(_('Command has been executed.'))
		except GameException, e:
			self.win.setStatus(e.args[0])
			return

		self.hide()
		self.caller.update()

	def onInfo(self, widget, action, data):
		if data:
			self.techInfoDlg.display(data.techID)

	def onFilter(self, widget, action, data):
		self.update()

	def createUI(self):
		w, h = gdata.scrnSize
		cols = 32
		rows = 20
		dlgWidth = cols * 20 + 4
		dlgHeight = rows * 20 + 4
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Select structure to construct'),
			rect = ui.Rect((w - dlgWidth) / 2, (h - dlgHeight) / 2, dlgWidth, dlgHeight),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		rows -= 1 # title

		ui.Title(self.win, layout = (0, 0, cols, 1), text = _('Production planet'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.ButtonArray(self.win, layout = (0, 1, cols, 3), id = 'vPlanets',
			buttonSize = (8, 1), showSlider = 0, action = 'onSelectPlanet')

		ui.Title(self.win, layout = (0, 4, cols - 10, 1), text = _('Structures to construct'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Title(self.win, layout = (cols - 10, 4, 10, 1), text = _('(right click for technology info)'),
			align = ui.ALIGN_E, font = 'normal')
		ui.ButtonArray(self.win, layout = (0, 5, cols, 6), id = 'vTechs',
			buttonSize = (2, 3), showSlider = 0, action = 'onConstruct', rmbAction = 'onInfo')

		ui.Title(self.win, layout = (0, 14, 18, 1), text = _('Filters'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Label(self.win, layout = (0, 15, 6, 1), text = _('Technology levels:'), align = ui.ALIGN_W)
		ui.Button(self.win, layout = (6, 15, 1, 1), text = _('1'), id = 'vLevel1',
			toggle = 1, action = 'onToggleLevel', data = 1)
		ui.Button(self.win, layout = (7, 15, 1, 1), text = _('2'), id = 'vLevel2',
			toggle = 1, action = 'onToggleLevel', data = 2)
		ui.Button(self.win, layout = (8, 15, 1, 1), text = _('3'), id = 'vLevel3',
			toggle = 1, action = 'onToggleLevel', data = 3)
		ui.Button(self.win, layout = (9, 15, 1, 1), text = _('4'), id = 'vLevel4',
			toggle = 1, action = 'onToggleLevel', data = 4)
		ui.Button(self.win, layout = (10, 15, 1, 1), text = _('5'), id = 'vLevel5',
			toggle = 1, action = 'onToggleLevel', data = 5)
		ui.Button(self.win, layout = (11, 15, 1, 1), text = _('6'), id = 'vLevel6',
			toggle = 1, action = 'onToggleLevel', data = 6)
		ui.Button(self.win, layout = (12, 15, 1, 1), text = _('7'), id = 'vLevel7',
			toggle = 1, action = 'onToggleLevel', data = 7)
		ui.Button(self.win, layout = (13, 15, 1, 1), text = _('8'), id = 'vLevel8',
			toggle = 1, action = 'onToggleLevel', data = 8)
		ui.Button(self.win, layout = (14, 15, 1, 1), text = _('9'), id = 'vLevel9',
			toggle = 1, action = 'onToggleLevel', data = 9)

		ui.Check(self.win, layout = (0, 16, 6, 1), text = _('Bio production'),
			id = 'vBioProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
		ui.Check(self.win, layout = (0, 17, 6, 1), text = _('En production'),
			id = 'vEnProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
		ui.Check(self.win, layout = (6, 16, 6, 1), text = _('CP production'),
			id = 'vCPProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
		ui.Check(self.win, layout = (6, 17, 6, 1), text = _('RP production'),
			id = 'vRPProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
		ui.Check(self.win, layout = (12, 16, 6, 1), text = _('Military'),
			id = 'vMilitary', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
		ui.Check(self.win, layout = (12, 17, 6, 1), text = _('Morale'),
			id = 'vMorale', checked = 1, align = ui.ALIGN_W, action = 'onFilter')

		ui.Title(self.win, layout = (18, 14, 8, 1), text = _('Options'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Label(self.win, layout = (18, 15, 3, 1), text = _('Quantity'), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (21, 15, 5, 1), id = 'vQuantity', align = ui.ALIGN_E)
		ui.Check(self.win, layout = (20, 16, 8, 1), id = 'vReportFin', text = _('Report finalization'),
			align = ui.ALIGN_W)

		ui.Title(self.win, layout = (0, rows - 1, cols - 5, 1), align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _('Cancel'), action = 'onCancel')

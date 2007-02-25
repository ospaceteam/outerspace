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
from osci import client, res, gdata
from osci.SystemMapWidget import SystemMapWidget
from NewTaskDlg import NewTaskDlg
from StructTaskDlg import StructTaskDlg
from RenameSysDlg import RenameSysDlg
from TechInfoDlg import TechInfoDlg
from ConfirmDlg import ConfirmDlg
from BuoyDlg import BuoyDlg
from ConstructionDlg import ConstructionDlg
from FleetRedirectionDlg import FleetRedirectionDlg
from ChangeQtyDlg import ChangeQtyDlg
import ige
from ige.ospace.Const import *
from ige.ospace import Rules
from ige import log
import math
import Utils

INFO_NONE = 0
INFO_TASK = 1
INFO_SLOT = 2

class StarSystemDlg:

	def __init__(self, app):
		self.wormhole = 0
		self.app = app
		self.createUI()
		self.newTaskDlg = NewTaskDlg(self.app)
		self.structTaskDlg = StructTaskDlg(self.app)
		self.renameSysDlg = RenameSysDlg(self.app)
		self.techInfoDlg = TechInfoDlg(app)
		self.confirmDlg = ConfirmDlg(app)
		self.changeQtyDlg = ChangeQtyDlg(app)
		self.constructionDlg = ConstructionDlg(app)
		self.buoyDlg = BuoyDlg(app)
		self.fleetRedirectionDlg = FleetRedirectionDlg(app)

	def display(self, objID):
		# set initial state
		obj = client.get(objID, noUpdate = 1)
		if obj.type == T_PLANET:
			self.systemID = obj.compOf
			self.planetID = objID
		elif obj.type in (T_SYSTEM, T_WORMHOLE):
			self.systemID = objID
			self.planetID = None
			if obj.type == T_WORMHOLE:
				self.wormhole = 1
				self.win.vSFWHExit.tags=['sys']
				self.win.vSRedirect.tags=['hidden']
		else:
			raise 'Unsupported type of object %d' % obj.type
		self.plInfoType = 0
		self.plInfoData = None
		#
		self.win.vSystemMap.systemID = self.systemID
		self.win.vSystemMap.selectedObjID = objID
		self.win.vSystemMap.precompute()

		# check, if player owns at least one planet in system
		self.playerOwnsSomePlanet = False
		playerID = client.getPlayerID()
		system = client.get(self.systemID, noUpdate = True)
		if hasattr(system, 'planets'):
			for planetID in system.planets:
				planet = client.get(planetID, noUpdate = True)
				if getattr(planet, "owner", None) == playerID:
					self.playerOwnsSomePlanet = True
					break

		# show window
		if not self.win.visible:
			self.win.show()
		# display planet or system info
		self.update()
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
			system = client.get(self.systemID,noUpdate =1)
			name = getattr(system,'name',res.getUnknownName());
			if gdata.config.defaults.showcoords == 'yes':
				self.win.title = _('System: %s [%.02f, %.02f]') % (name,system.x,system.y)
			else:
				self.win.title = _('System: %s') % name
			# clean up info area
			self.plInfoType = INFO_NONE
			self.plInfoData = None
			if self.planetID:
				self.showPlanet()
			else:
				self.showSystem()
			self.win.vSystemMap.precompute()

	def appendTechIcon(self, index, planet, task, items, extraSlot = False, setIndex = True):
		if index < planet.plSlots:
			shift = res.whiteShift
		else:
			shift = res.redShift

		if type(task) == int:
			imgID = task
		else:
			imgID = task.techID + shift

		if setIndex:
			indexToSet = index
		else:
			indexToSet = None

		icons = ((res.getTechImg(imgID), ui.ALIGN_NONE),)
		item = ui.Item(None, icons = icons, index = indexToSet, extraSlot = extraSlot)
		items.append(item)

	def showPlanet(self):
		self.win.setTagAttr('pl', 'visible', 1)
		self.win.setTagAttr('sys', 'visible', 0)
		self.win.setTagAttr('hidden', 'visible', 0)
		planet = client.get(self.planetID, noUpdate = 1)
		player = client.getPlayer()
		if hasattr(planet, 'revoltLen') and planet.revoltLen > 0:
			self.win.vPName.text = _('Planet %s: POPULATION IS REVOLTING') % \
				getattr(planet, 'name', res.getUnknownName())
		elif hasattr(planet, 'morale') and hasattr(planet, "morale"):
			prodState = gdata.moraleStates[Rules.moraleProdBonus[int(planet.morale / Rules.moraleProdStep)]]
			self.win.vPName.text = _('Planet %s: %s') % \
				(getattr(planet, 'name', res.getUnknownName()), _(prodState))
		else:
			self.win.vPName.text = _('Planet %s') % \
				getattr(planet, 'name', res.getUnknownName())
			self.win.vPName.foreground = None
		# structures
		items = []
		if hasattr(planet, 'slots'):
			index = 0
			for struct in planet.slots:
				tech = client.getTechInfo(struct[STRUCT_IDX_TECHID])
				icons = [(res.getTechImg(struct[STRUCT_IDX_TECHID]), ui.ALIGN_NONE)]
				if not struct[STRUCT_IDX_STATUS] & STRUCT_STATUS_ON:
					icons.append((res.structOffImg, ui.ALIGN_NE))
				elif struct[STRUCT_IDX_STATUS] & ~STRUCT_STATUS_ON & ~STRUCT_STATUS_REPAIRING:
						icons.append((res.structProblemImg, ui.ALIGN_NE))
				item = ui.Item(None, icons = icons, tooltip = tech.name, statustip = tech.name, index = index,
					align = ui.ALIGN_W, techID = struct[STRUCT_IDX_TECHID])
				items.append(item)
				index += 1

			# add production queue items to planet slots
			if hasattr(planet, 'prodQueue'):
				for task in planet.prodQueue:
					if not task.isShip and self.planetID == task.targetID and task.demolishStruct == 0:
						tech = client.getFullTechInfo(task.techID)
           					if tech.isStructure:
							for i in range(0, task.quantity):
								self.appendTechIcon(index, planet, task, items, False, False)
								index += 1

			# add production queue items from other planets to this planet slots
			system = client.get(self.systemID, noUpdate = 1)
			if hasattr(system, "planets"):
				for aPlanetID in system.planets:
					if aPlanetID == self.planetID:
						continue
					aPlanet = client.get(aPlanetID, noUpdate = 1)
					if hasattr(aPlanet, "prodQueue"):
						for aTask in aPlanet.prodQueue:
							if not aTask.isShip and self.planetID == aTask.targetID and aTask.demolishStruct == 0:
								aTech = client.getFullTechInfo(aTask.techID)
								if aTech.isStructure:
                                                                        taskQuantity = min(aTask.quantity,30) #30 is max displayable slots, including the line that "shouldn't be used" - fixes breakage of accidental million-slot build command!
									for i in range(0, taskQuantity):
										self.appendTechIcon(index, planet, aTask, items, False, False)
										index += 1

			while index < planet.plSlots:
				self.appendTechIcon(None, planet, 1, items)
				index += 1

			if planet.owner == player.oid and Rules.Tech.ADDSLOT3 in player.techs:
				while index < planet.plMaxSlots:
					self.appendTechIcon(None, planet, 2, items, True)
					index += 1

		self.win.vPSlots.items = items
		self.win.vPSlots.itemsChanged()
		# enable/disable button for moving and destroying structures
		if hasattr(planet, "owner") and planet.owner == client.getPlayerID():
			enabled = 1
		else:
			enabled = 0
		self.win.vISOnOff.enabled = enabled
		self.win.vISDemolish.enabled = enabled
		# construction queue
		items = []
		if hasattr(planet, 'prodQueue'):
			index = 0
			for task in planet.prodQueue:
				if task.isShip:
					tech = player.shipDesigns[task.techID]
					icons = ((res.getShipImg(tech.combatClass, tech.isMilitary), ui.ALIGN_NONE),)
				else:
					tech = client.getFullTechInfo(task.techID)
					icons = ((res.getTechImg(task.techID), ui.ALIGN_NONE),)

				if task.targetID != self.planetID:
					mod = Rules.buildOnAnotherPlanetMod
				else:
					mod = Rules.buildOnSamePlanetMod

				perc = 100.0 * task.currProd / (tech.buildProd * mod)
				if planet.effProdProd > 0:
					if task.targetID != self.planetID:
						etc = math.ceil(float(tech.buildProd * Rules.buildOnAnotherPlanetMod - task.currProd) / planet.effProdProd)
					else:
						etc = math.ceil(float(tech.buildProd - task.currProd) / planet.effProdProd)
					text = _("%s") % res.formatTime(etc)
				else:
					text = _('N/A')
				item = ui.Item(text, font = 'small', align = ui.ALIGN_NE, icons = icons, tooltip = tech.name, statustip = tech.name, index = index)
				if task.isShip:
					item.background = None
				else:
					item.background = (0x44, 0x44, 0x44)
				items.append(item)
				index += 1
			icons = ((res.getTechImg(1), ui.ALIGN_NONE),)
			item = ui.Item(_('New'), font = 'small-bold', align = ui.ALIGN_SW, icons = icons, index = None)
			items.append(item)
		self.win.vPQueue.items = items
		self.win.vPQueue.itemsChanged()
		# planet data
		self.win.vPPType.text = gdata.planetTypes[getattr(planet, 'plType', None)]
		self.win.vPDiameter.text = getattr(planet, 'plDiameter', '?')
		self.win.vPBioAbund.text = getattr(planet, 'plBio', '?')
		if hasattr(planet, 'plBio') and hasattr(planet, 'plEn'):
			spec = Rules.planetSpec[planet.plType]
			if spec.upgradeTo and planet.plEn >= spec.upgradeEnReqs[0] and \
				planet.plEn <= spec.upgradeEnReqs[1]:
				if planet.plBio >= spec.maxBio:
					info = _('Planet downgrade limit %d, upgrade limit %d, can be terraformed to a %s.') % (
						spec.minBio,
						spec.maxBio,
						gdata.planetTypes[spec.upgradeTo]
					)
				else:
					info = _('Planet downgrade limit %d, upgrade limit %d, can terraformed to a %s in the future.') % (
						spec.minBio,
						spec.maxBio,
						gdata.planetTypes[spec.upgradeTo]
					)
			else:
				info = _('Planet downgrade limit %d, upgrade limit %d.') % (spec.minBio, spec.maxBio)
		else:
			info = None
		self.win.vPBioAbund.tooltip = info
		self.win.vPBioAbund.statustip = info
		self.win.vPMinAbund.text = getattr(planet, 'plMin', '?')
		self.win.vPEnAbund.text = getattr(planet, 'plEn', '?')
		info = _("Energy abundance for average EMR level is %s.") % getattr(planet, 'plEn', '?')
		self.win.vPEnAbund.tooltip = info
		self.win.vPEnAbund.statustip = info
		# used slots
		if hasattr(planet, 'slots'):
			usedSlots = planet.plSlots - len(planet.slots)
		else:
			usedSlots = '?'
		self.win.vPSlotsAbund.text = _('%s / %s') % (
			usedSlots,
			getattr(planet, 'plSlots', '?'),
		)
		info = _('Planet has %s free, %s usable out of maximum %s slots .') % (
			usedSlots,
			getattr(planet, 'plSlots', '?'),
			getattr(planet, 'plMaxSlots', '?'),
		)
		self.win.vPSlotsAbund.tooltip = info
		self.win.vPSlotsAbund.statustip = info
		# colony data
		# population
		self.win.vPCPop.text = getattr(planet, 'storPop', '?')
		tip = _('Population: %s (max. %s, %+d last turn)') % (
			str(getattr(planet, 'storPop', '?')),
			str(getattr(planet, 'maxPop', '?')),
			getattr(planet, 'changePop', 0)
		)
		self.win.vPCPop.tooltip = tip
		self.win.vPCPop.statustip = tip
		self.win.vPCConsumes.text = _('%s / %s') % (
			str(getattr(planet, 'popEatBio', '?')),
			str(getattr(planet, 'popEatEn', '?')),
		)
		tip =_('1000 units of population consumes %s bio, and %s en.') % (
			str(getattr(planet, 'popEatBio', '?')),
			str(getattr(planet, 'popEatEn', '?')),
		)
		self.win.vPCConsumes.tooltip = tip
		self.win.vPCConsumes.statustip = tip
		# bio
		self.win.vPCStorBio.text = getattr(planet, 'storBio', '?')
		tip = _('Biomatter reserve: %s (max. %s, %+d last turn)') % (
			str(getattr(planet, 'storBio', '?')),
			str(getattr(planet, 'maxBio', '?')),
			getattr(planet, 'changeBio', 0),
		)
		self.win.vPCStorBio.tooltip = tip
		self.win.vPCStorBio.statustip = tip
		# en
		self.win.vPCStorEn.text = getattr(planet, 'storEn', '?')
		tip = _('Energy reserve: %s (max. %s, %+d last turn)') % (
			str(getattr(planet, 'storEn', '?')),
			str(getattr(planet, 'maxEn', '?')),
			getattr(planet, 'changeEn', 0),
		)
		self.win.vPCStorEn.tooltip = tip
		self.win.vPCStorEn.statustip = tip
		# prod & sci
		self.win.vPCUnempl.text = str(getattr(planet, 'unemployedPop', '?'))
		if hasattr(planet, "owner") and planet.owner == player.oid:
			moraleBonus = Rules.moraleProdBonus[int(planet.morale / Rules.moraleProdStep)]
			self.win.vPCProd.text = _("%d / %d") % (
				int(planet.effProdProd),
				planet.prodProd,
			)
			info = _("Effective / raw construction points. Empire efficiency %+d %%, %+d %% because of morale.") % (
				player.prodEff * 100 - 100,
				moraleBonus * 100,
			)
			self.win.vPCProd.statustip = info
			self.win.vPCProd.tooltip = info
		else:
			self.win.vPCProd.text = str(getattr(planet, 'prodProd', '?'))
		if hasattr(planet, "owner") and planet.owner == player.oid:
			moraleBonus = Rules.moraleProdBonus[int(planet.morale / Rules.moraleProdStep)]
			self.win.vPCSci.text = _("%d / %d") % (
				planet.effProdSci,
				planet.prodSci,
			)
			info = _("Effective / raw research points. Empire efficiency %+d %%, %+d %% because of morale.") % (
				player.sciEff * 100 - 100,
				moraleBonus * 100,
			)
			self.win.vPCSci.statustip = info
			self.win.vPCSci.tooltip = info
		else:
			self.win.vPCSci.text = str(getattr(planet, 'effProdSci', '?'))
		if hasattr(planet, 'plEnv'):
			maxVal = Rules.envInterval
			if planet.changeEnv > 0:
				time = int((maxVal - planet.plEnv) / planet.changeEnv)
				tip = _('Enviroment (%d / %d) is improving (%d per turn), %s turns to improve.') \
					% (planet.plEnv, maxVal, planet.changeEnv, res.formatTime(time))
				self.win.vPCEnvStatus.foreground = None
			elif planet.changeEnv < 0:
				time = - int(planet.plEnv / planet.changeEnv)
				tip = _('Enviroment (%d / %d) is deteriorating (%d per turn), %s turns to deteriorate.') % \
					(planet.plEnv, maxVal, -planet.changeEnv, res.formatTime(time))
				self.win.vPCEnvStatus.foreground = gdata.sevColors[gdata.CRI]
			else:
				tip = _('Enviroment (%d / %d) is stable.') % (planet.plEnv, maxVal)
				self.win.vPCEnvStatus.foreground = None
			if maxVal > 0:
				self.win.vPCEnvStatus.text = _('%d %%') % (planet.plEnv * 100 / maxVal)
			else:
				self.win.vPCEnvStatus.text = _('0 %')
			self.win.vPCEnvStatus.tooltip = tip
			self.win.vPCEnvStatus.statustip = tip
		else:
			self.win.vPCEnvStatus.foreground = None
			self.win.vPCEnvStatus.text = '?'
			self.win.vPCEnvStatus.tooltip = None
			self.win.vPCEnvStatus.statustip = None
		# morale
		if hasattr(planet, 'morale'):
			self.win.vPCMorale.text = _('%d / %d') % (
				planet.morale, planet.moraleTrgt)
		elif hasattr(planet, 'morale'):
			self.win.vPCMorale.text = _('%d') % planet.morale
		else:
			self.win.vPCMorale.text = _('?')
		if hasattr(planet, 'shield'):
			self.win.vPCShield.text = _('%d') % planet.shield
			shieldTip = True
			if hasattr(planet,'prevShield'):
			    if planet.prevShield < 0: #server reset your data becuase you went to war
				shieldTip = False
			if hasattr(planet,'prevShield') and hasattr(planet,'maxShield') and shieldTip:
				delta = planet.shield - planet.prevShield
				if (planet.shield > planet.prevShield):
				    info = _('Sheild (%d/%d) charged by %+d last turn.') % (
					planet.shield,
					planet.maxShield,
					delta
				    )
				elif (planet.shield < planet.prevShield):
				    info = _('Sheild (%d/%d) was damaged by %+d last turn.') % (
					planet.shield,
					planet.maxShield,
					delta
				    )
				elif (planet.shield < planet.maxShield):
				    info = _('Sheild (%d/%d) is unable to charge.') % (
					planet.shield,
					planet.maxShield,
				    )
				else:
				    info = _('Sheild (%d/%d) is fully charged.') % (
					planet.shield,
					planet.maxShield,
				    )
			else:
                        	info = _('Sheild (%d/unknown)') % (
				    planet.shield,
				)
			self.win.vPCShield.tooltip = info
			self.win.vPCShield.statustip = info
		if hasattr(planet, 'revoltLen') and planet.revoltLen > 0:
			self.win.vPCMorale.foreground = gdata.sevColors[gdata.CRI]
		else:
			self.win.vPCMorale.foreground = None
		if hasattr(planet, 'changeMorale'):
			if planet.changeMorale > 0:
				info = _('Morale is increasing (%+d last turn) to %d, revolt threshold is %d.') % (
					planet.changeMorale,
					planet.moraleTrgt,
					Rules.revoltThr,
				)
			elif planet.changeMorale < 0:
				info = _('Morale is decreasing (%+d last turn), revolt threshold is %d.') % (
					planet.changeMorale,
					Rules.revoltThr,
				)
			else:
				info = _('Morale is stable (%d / %d), revolt threshold is %d.') % (
					planet.morale,
					planet.moraleTrgt,
					Rules.revoltThr,
				)
			self.win.vPCMorale.tooltip = info
			self.win.vPCMorale.statustip = info
		# strategic resource
		if hasattr(planet, "plStratRes"):
			self.win.vPCSRes.text = _(gdata.stratRes[planet.plStratRes])
		else:
			self.win.vPCSRes.text = _("?")
		# min storage
		# auto storage regulation?
		if hasattr(planet, 'minBio'):
			self.win.setTagAttr('minStor', 'visible', 1)
			text = _("Minimal storage %d.") % planet.minBio
			self.win.vPCMinBio.text = str(planet.minBio)
			self.win.vPCMinBio.tooltip = text
			self.win.vPCMinBio.statustip = text
			text = _("Minimal storage %d") % planet.minEn
			self.win.vPCMinEn.text = str(planet.minEn)
			self.win.vPCMinEn.tooltip = text
			self.win.vPCMinEn.statustip = text
			self.win.vPCAutoMinStor.enabled = 1
			self.win.vPCAutoMinStor.pressed = planet.autoMinStor
		else:
			self.win.setTagAttr('minStor', 'visible', 0)
			self.win.vPCAutoMinStor.enabled = 0
			self.win.vPCAutoMinStor.pressed = 0
		# show info
		self.showPlInfo()

	def showSystem(self):
		self.win.setTagAttr('pl', 'visible', 0)
		self.win.setTagAttr('sys', 'visible', 1)
		self.win.setTagAttr('hidden', 'visible', 0)
		system = client.get(self.systemID, noUpdate = 1)
		self.win.vSystemMap.selectedObjID = self.systemID
		# star info
		if hasattr(system, 'starClass'):
			title = _('System overview for star %s [%s]') % (
				system.starClass[1:],
				gdata.starTypes[system.starClass[0]],
			)
		else:
			title = _('System overview')
		self.win.vSTitle.text = title
		player = client.getPlayer()
		# planets
		info = []
		tStorBio = 0
		tChangeBio = 0
		tStorEn = 0
		tChangeEn = 0
		tProdProd = 0
		tProdSci = 0
		hasPlanet = 0
		if hasattr(system, 'planets'):
			for planetID in system.planets:
				planet = client.get(planetID, noUpdate = 1)
				owner = res.getUnknownName()
				#rel = REL_UNDEF
				ownerID = OID_NONE
				if hasattr(planet, 'owner'):
					ownerID = planet.owner
					#if planet.owner != OID_NONE:
					if planet.owner == OID_NONE:
						#rel = client.getRelationTo(planet.owner)
					#else:
						owner = _('[Nobody]')
				if hasattr(planet, 'prodQueue'):
					if planet.prodQueue:
						item = planet.prodQueue[0]
						if item.isShip:
							tech = client.getPlayer().shipDesigns[item.techID]
						else:
							tech = client.getTechInfo(item.techID)
						constrInfo = _('%d x %s') % (item.quantity, tech.name)
					else:
						constrInfo = _('-')
				else:
					constrInfo = '?'
				# used slots
				if hasattr(planet, 'slots'):
					usedSlots = planet.plSlots - len(planet.slots)
				else:
					usedSlots = '?'
				item = ui.Item(
					getattr(planet, 'name', res.getUnknownName()).split(' ')[-1],
					plType = gdata.planetTypes[getattr(planet, 'plType', None)],
					plBio = getattr(planet, 'plBio', '?'),
					plMin = getattr(planet, 'plMin', '?'),
					plEn = getattr(planet, 'plEn', '?'),
					storBio = getattr(planet, 'storBio', '?'),
					changeBio = getattr(planet, 'changeBio', '?'),
					storEn = getattr(planet, 'storEn', '?'),
					changeEn = getattr(planet, 'changeEn', '?'),
					constrInfo = constrInfo,
					space = _('%s / %s') % (
						usedSlots,
						getattr(planet, 'plSlots', '?'),
					),
					consci = _('%s / %s') % (
						getattr(planet, 'effProdProd', '?'),
						getattr(planet, 'effProdSci', '?'),
					),
					planetID = planetID,
					plOwner = owner,
					#foreground = res.getFFColorCode(rel),
					foreground = res.getPlayerColor(ownerID)
				)
				# show effective con/sci pts
				if hasattr(planet, "owner") and planet.owner == player.oid:
					con = int(planet.effProdProd)
					sci = int(planet.effProdSci)
					item.consci = _("%d / %d") % (con, sci)
					hasPlanet = 1
				if getattr(planet, 'plType', None) in ("G", "A"):
					item.foreground = gdata.sevColors[gdata.DISABLED]
				info.append(item)
				# compute sums
				if hasattr(planet, 'owner') and planet.owner == client.getPlayerID():
					tStorBio += getattr(planet, 'storBio', 0)
					tChangeBio += getattr(planet, 'changeBio', 0)
					tStorEn += getattr(planet, 'storEn', 0)
					tChangeEn += getattr(planet, 'changeEn', 0)
					tProdProd += getattr(planet, 'effProdProd', 0)
					tProdSci += getattr(planet, 'effProdSci', 0)

		self.win.vSSOver.items = info
		self.win.vSSOver.itemsChanged()
		# show totals
		self.win.vSTStorBio.text = tStorBio
		if tChangeBio >= 0: foreground = None
		else: foreground = gdata.sevColors[gdata.CRI]
		self.win.vSTChangeBio.text = tChangeBio
		self.win.vSTChangeBio.foreground = foreground
		self.win.vSTStorEn.text = tStorEn
		if tChangeEn >= 0: foreground = None
		else: foreground = gdata.sevColors[gdata.CRI]
		self.win.vSTChangeEn.foreground = foreground
		self.win.vSTChangeEn.text = tChangeEn
		self.win.vSTConSci.text = _('%d / %d') % (tProdProd, tProdSci)
		# redirection
		if hasPlanet:
			if self.systemID in player.shipRedirections:
				targetName = getattr(client.get(player.shipRedirections[self.systemID]), "name", _("[Unknown]"))
				self.win.vSRedirect.text = _("Redirect to %s") % targetName
				self.win.vSRedirect.enabled = 1
			else:
				self.win.vSRedirect.text = _("Redirection OFF")
				self.win.vSRedirect.enabled = 1
		else:
			self.win.vSRedirect.text = _("Redirection OFF")
			self.win.vSRedirect.enabled = 0

		if hasattr(player, "buoys"):
			if self.systemID in player.buoys.keys():
				self.win.vSBuoy.text = _("Edit buoy")
				self.win.vSDeleteBuoy.enabled = 1
			else:
				self.win.vSBuoy.text = _("Add buoy")
				self.win.vSDeleteBuoy.enabled = 0

	def showPlInfo(self):
		if self.plInfoType == INFO_NONE:
			self.win.setTagAttr('task', 'visible', 0)
			self.win.setTagAttr('slot', 'visible', 0)
			self.win.vITitle.text = _('N/A')
		elif self.plInfoType == INFO_TASK:
			self.win.setTagAttr('task', 'visible', 1)
			self.win.setTagAttr('slot', 'visible', 0)
			planet = client.get(self.planetID, noUpdate = 1)
			task = planet.prodQueue[self.plInfoData]
			if task.isShip:
				tech = client.getPlayer().shipDesigns[task.techID]
				self.win.vITInfo.enabled = Utils.enableConstruction(client)
			else:
				self.win.vITInfo.enabled = True
				tech = client.getFullTechInfo(task.techID)
			self.win.vITitle.text = _('Task info: %s') % tech.name

			if task.targetID != self.planetID: mod = Rules.buildOnAnotherPlanetMod
			else: mod = Rules.buildOnSamePlanetMod
			perc = 100.0 * task.currProd / (tech.buildProd * mod)
			self.win.vITCompl.text = _('%d %% [%+d %%]') % (int(perc), task.changePerc / 100)
			if planet.effProdProd > 0:
				if task.targetID != self.planetID:
					etc = math.ceil(float(tech.buildProd * Rules.buildOnAnotherPlanetMod - task.currProd) / planet.effProdProd)
				else:
					etc = math.ceil(float(tech.buildProd - task.currProd) / planet.effProdProd)
				self.win.vITEtc.text = res.formatTime(etc)
			else:
				self.win.vITEtc.text = _('N/A')
			self.win.vITProd.text = _('%d / %d') % (task.currProd, tech.buildProd * mod)
			self.win.vITQuantity.text = _('%d') % task.quantity
			self.win.vITTarget.text = getattr(client.get(task.targetID, noUpdate = 1), 'name', res.getUnknownName())
			if hasattr(task, "demolishStruct") and task.demolishStruct != 0:
				structTech = client.getFullTechInfo(task.demolishStruct)
				self.win.vITTargetSlot.text = structTech.name
			else:
				self.win.vITTargetSlot.text = _("None")

			self.win.vITFirst.enabled = self.win.vITPrev.enabled = self.plInfoData > 0
			self.win.vITNext.enabled = self.win.vITLast.enabled = self.plInfoData < len(planet.prodQueue) - 1
			# self.win.vITInfo.enabled = not task.isShip
		elif self.plInfoType == INFO_SLOT:
			self.win.setTagAttr('task', 'visible', 0)
			self.win.setTagAttr('slot', 'visible', 1)
			planet = client.get(self.planetID, noUpdate = 1)
			struct = planet.slots[self.plInfoData]
			tech = client.getFullTechInfo(struct[STRUCT_IDX_TECHID])
			self.win.vITitle.text = _('Slot info: %s') % tech.name
			if not struct[STRUCT_IDX_STATUS] & ~STRUCT_STATUS_ON:
				info = _('None')
				text = _('No problems.')
				self.win.vISStatus.foreground = None
			elif not struct[STRUCT_IDX_STATUS] & STRUCT_STATUS_ON:
				info = _('Switched OFF')
				text = _('Structure is switched OFF.')
				self.win.vISStatus.foreground = gdata.sevColors[gdata.CRI]
			else:
				self.win.vISStatus.foreground = gdata.sevColors[gdata.CRI]
				# extended status
				status = struct[STRUCT_IDX_STATUS]
				info = ''
				text = ''
				if status & STRUCT_STATUS_NOBIO:
					text += _('Insufficient biomatter, ')
					info += _('Bio/')
				if status & STRUCT_STATUS_NOEN:
					text += _('Insufficient energy, ')
					info += _('En/')
				if status & STRUCT_STATUS_NOPOP:
					text += _('Insufficient workers, ')
					info += _('Wrk/')
				if status & STRUCT_STATUS_DETER:
					text += _('Deteriorating, ')
					info += _('Deter/')
				if status & STRUCT_STATUS_REPAIRING:
					text += _('Repairing, ')
					info += _('Rep/')
				if status & STRUCT_STATUS_NEW:
					text += _('New structure, ')
					info += _('New/')
				text = text[:-2]
				info = info[:-1]
			self.win.vISStatus.text = info
			self.win.vISStatus.statustip = text
			self.win.vISStatus.tooltip = text
			# this is taken from server's code (IPlanet)
			if planet.owner != OID_NONE:
				player = client.get(planet.owner, noUpdate = 1)
				if hasattr(player, 'techs'):
					techEff = Rules.techImprEff[player.techs.get(struct[STRUCT_IDX_TECHID], Rules.techBaseImprovement)]
				else:
					techEff = Rules.techImprEff[Rules.techBaseImprovement]
			else:
				techEff = Rules.techImprEff[Rules.techBaseImprovement]
			opStatus = struct[STRUCT_IDX_OPSTATUS] / 100.0
			if hasattr(tech, 'maxHP') and planet.owner == client.getPlayerID():
				self.win.vISHp.text = _('%d / %d') % (struct[STRUCT_IDX_HP], int(tech.maxHP * techEff))
			else:
				self.win.vISHp.text = _('%d / ?') % struct[STRUCT_IDX_HP]
			if hasattr(tech, 'prodBioMod'):
				# bio
				b, m, e, d = tech.prodBioMod
				prodMod = (b * planet.plBio + m * planet.plMin + e * planet.plEn + d * 100) / 100
				bioPC = int(tech.prodBio * prodMod * techEff * opStatus) - int(tech.operBio * opStatus)
				# en
				b, m, e, d = tech.prodEnMod
				prodMod = (b * planet.plBio + m * planet.plMin + e * planet.plEn + d * 100) / 100
				enPC = int(tech.prodEn * prodMod * techEff * opStatus) - int(tech.operEn * opStatus)
				if bioPC < 0: self.win.vISBioPC.foreground = gdata.sevColors[gdata.CRI]
				else: self.win.vISBioPC.foreground = None
				self.win.vISBioPC.text = _('%d') % bioPC
				if enPC < 0: self.win.vISEnPC.foreground = gdata.sevColors[gdata.CRI]
				else: self.win.vISEnPC.foreground = None
				self.win.vISEnPC.text = _('%d') % enPC
				self.win.vISWorkers.text = _('%d') % int(tech.operWorkers * opStatus)
				# prod
				b, m, e, d = tech.prodProdMod
				prodMod = (b * planet.plBio + m * planet.plMin + e * planet.plEn + d * 100) / 100
				self.win.vISConstr.text = _('%d') % int(tech.prodProd * prodMod * techEff * opStatus)
				# sci
				self.win.vISSci.text = _('%d') % int(tech.prodSci * techEff * opStatus)
				# op. status
				self.win.vISOpStatus.text = _("%d %%") % (opStatus * 100)
				info = _("Operational status of the structure.")
				self.win.vISOpStatus.tooltip = info
				self.win.vISOpStatus.statustip = info
			else:
				self.win.vISBioPC.text = '?'
				self.win.vISEnPC.text = '?'
				self.win.vISWorkers.text = '?'
				self.win.vISConstr.text = '? / ?'
				self.win.vISSci.text = "?"
			# buttons
			if hasattr(planet, "owner") and planet.owner == client.getPlayerID():
				self.win.vISPrev.enabled = self.win.vISFirst.enabled = self.plInfoData > 0
				self.win.vISNext.enabled = self.win.vISLast.enabled = self.plInfoData < len(planet.slots) - 1
			else:
				self.win.vISPrev.enabled = self.win.vISFirst.enabled = 0
				self.win.vISNext.enabled = self.win.vISLast.enabled = 0
		tChangeBio = 0
		tChangeEn = 0
		tProdProd = 0
		tProdSci = 0
		system = client.get(self.systemID, noUpdate = 1)
		# System Data Display
		if hasattr(system, 'planets'):
			for planetID in system.planets:
				planet = client.get(planetID, noUpdate = 1)
				# compute sums
				if hasattr(planet, 'owner') and planet.owner == client.getPlayerID():
					tChangeBio += getattr(planet, 'changeBio', 0)
					tChangeEn += getattr(planet, 'changeEn', 0)
					tProdProd += getattr(planet, 'effProdProd', 0)
					tProdSci += getattr(planet, 'effProdSci', 0)
		self.win.vSTPBio.text = tChangeBio
		self.win.vSTPEn.text = tChangeEn
		self.win.vSTPProd.text = tProdProd
		self.win.vSTPSci.text = tProdSci

	def onSelectMapObj(self, widget, action, data):
		self.display(data)

	def onSelectPlanet(self, widget, action, data):
		if data.planetID != OID_NONE:
			self.display(data.planetID)

	def onSlotSelected(self, widget, action, data):
		self.win.vPQueue.selectItem(None)
		if not data:
			self.plInfoType = INFO_NONE
			self.plInfoData = None
		elif data.index != None:
			self.plInfoType = INFO_SLOT
			self.plInfoData = data.index
		else:
			self.plInfoType = INFO_NONE
			self.plInfoData = None
			if self.playerOwnsSomePlanet:
				# display task dialog (select stuctures only)
				self.structTaskDlg.display(self, self.planetID, data.extraSlot)
				self.win.vPSlots.selectItem(None)

		self.showPlInfo()

	def onSlotRSelected(self, widget, action, data):
		# unselect struct
		self.win.vPQueue.selectItem(None)

		if data and data.index != None:
			#do not permit upgrade non-owned structures
			if client.getPlayerID() == getattr(client.get(self.planetID, noUpdate = True), "owner", 0):
				self.structTaskDlg.display(self, self.planetID, False, data.techID)
				self.win.vPSlots.selectItem(None)

		self.plInfoType = INFO_NONE
		self.plIndoData = None
		self.showPlInfo()

	def onQueueItemSelected(self, widget, action, data):
		# unselect structure
		self.win.vPSlots.selectItem(None)
		if not data:
			# unselected
			self.plInfoType = INFO_NONE
			self.plInfoData = None
		elif data.index == None:
			# new task
			self.plInfoType = INFO_NONE
			self.plInfoData = None
			self.win.vPQueue.selectItem(None)
			planet = client.get(self.planetID, noUpdate = 1)
			self.newTaskDlg.display(self, planet.effProdProd)
		else:
			# info about task
			self.plInfoType = INFO_TASK
			self.plInfoData = data.index
		self.showPlInfo()

	def onMoveStruct(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing MOVE STRUCTURE command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			planet.slots = client.cmdProxy.moveStruct(self.planetID, self.plInfoData, widget.data)
			self.plInfoData += widget.data
			self.showPlanet()
			self.win.vPSlots.selectItem(self.win.vPSlots.items[self.plInfoData])
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onMoveStructFirstLast(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing MOVE STRUCTURE command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			if widget.data == -1:
				rel = -1 * self.plInfoData
				pos = 0
			else:
				rel = len(planet.slots) - self.plInfoData - 1
				pos = len(planet.slots) - 1

			planet.slots = client.cmdProxy.moveStruct(self.planetID, self.plInfoData, rel)
			self.plInfoData = pos
			self.showPlanet()
			self.win.vPSlots.selectItem(self.win.vPSlots.items[self.plInfoData])
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onSwitchStructOnOff(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing SWITCH STRUCTURE ON/OFF command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			struct = planet.slots[self.plInfoData]
			planet.slots[self.plInfoData] = client.cmdProxy.setStructOn(self.planetID, self.plInfoData,
				not struct[STRUCT_IDX_STATUS] & STRUCT_STATUS_ON)
			self.showPlanet()
			self.win.vPSlots.selectItem(self.win.vPSlots.items[self.plInfoData])
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onDemolishStruct(self, widget, action, data):
		self.confirmDlg.display(_("Demolish this structure?"),
			_("Yes"), _("No"), self.onDemolishStructConfirmed)

	def onDemolishStructConfirmed(self):
		try:
			self.win.setStatus(_('Executing DEMOLISH STRUCTURE command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			planet.slots = client.cmdProxy.demolishStruct(self.planetID, self.plInfoData)
			self.plInfoType = INFO_NONE
			self.plInfoDat = None
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return
		self.showPlanet()

	def onStructInfo(self, widget, action, data):
		planet = client.get(self.planetID, noUpdate = 1)
		self.techInfoDlg.display(planet.slots[self.plInfoData][STRUCT_IDX_TECHID])

	def onMoveTaskFirstLast(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing MOVE TASK command...'))
			planet = client.get(self.planetID, noUpdate = 1)

			if widget.data == -1:
				rel = -1 * self.plInfoData
				pos = 0
			else:
				rel = len(planet.prodQueue) - self.plInfoData - 1
				pos = len(planet.prodQueue) - 1

			planet.prodQueue = client.cmdProxy.moveConstrItem(self.planetID, self.plInfoData, rel)
			self.plInfoData = pos
			self.showPlanet()
			self.win.vPQueue.selectItem(self.win.vPQueue.items[self.plInfoData])
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onMoveTask(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing MOVE TASK command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			planet.prodQueue = client.cmdProxy.moveConstrItem(self.planetID, self.plInfoData, widget.data)
			self.plInfoData += widget.data
			self.showPlanet()
			self.win.vPQueue.selectItem(self.win.vPQueue.items[self.plInfoData])
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onAbortTask(self, widget, action, data):
		self.confirmDlg.display(_("Abort this construction task?"),
			_("Yes"), _("No"), self.onAbortTaskConfirmed)

	def onQtyTask(self, widget, action, data):
		planet = client.get(self.planetID, noUpdate = 1)
		task = planet.prodQueue[self.plInfoData]
		self.changeQtyDlg.display(task.quantity, self.onChangeQtyConfirmed)

	def onChangeQtyConfirmed(self):
		if self.changeQtyDlg.quantity != None:
			try:
				self.win.setStatus(_('Executing CHANGE TASK command...'))
				planet = client.get(self.planetID, noUpdate = 1)
				player = client.getPlayer()
				planet.prodQueue, player.stratRes = client.cmdProxy.changeConstruction(self.planetID, self.plInfoData, self.changeQtyDlg.quantity)
				self.plInfoType = INFO_NONE
				self.plInfoDat = None
				self.showPlanet()
				self.win.setStatus(_('Command has been executed.'))
			except ige.GameException, e:
				self.win.setStatus(e.args[0])
				return

	def onAbortTaskConfirmed(self):
		try:
			self.win.setStatus(_('Executing ABORT TASK command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			player = client.getPlayer()
			planet.prodQueue, player.stratRes = client.cmdProxy.abortConstruction(self.planetID, self.plInfoData)
			self.plInfoType = INFO_NONE
			self.plInfoDat = None
			self.showPlanet()
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onTaskInfo(self, widget, action, data):
		planet = client.get(self.planetID, noUpdate = 1)
		task = planet.prodQueue[self.plInfoData]
		if not task.isShip:
			self.techInfoDlg.display(task.techID)
		else:
			log.debug("Show ship info")
			self.constructionDlg.selectedDesignID = task.techID;
			self.constructionDlg.display()

	def onRenameSystem(self, widget, action, data):
		self.renameSysDlg.display(self.systemID)

	def onRedirectFleets(self, widget, action, data):
		self.fleetRedirectionDlg.display(self.systemID, self)

	def onFindWormholeExit(self, widget, action, data):
		source = client.get(self.systemID, noUpdate = 1)
		try:
			dest = client.get(source.destinationOid)
			try:
				gdata.mainGameDlg.win.vStarMap.highlightPos = (dest.x, dest.y)
				gdata.mainGameDlg.win.vStarMap.setPos(dest.x, dest.y)
				self.hide()
				return
			except:
				log.debug("Invalid object information during wormhole find. Obj. Type: ", dest.typeID)
				self.win.setStatus(_("Destination not explored")) #don't show the end user this error
		except:
			self.win.setStatus(_("Destination not explored"))

	def onBuoy(self, widget, action, data):
		buoyText = ""
		buoyType = BUOY_PRIVATE
		player = client.getPlayer()
		if hasattr(player, "buoys"):
			if self.systemID in player.buoys.keys():
				buoyText = player.buoys[self.systemID][0]
				buoyType = player.buoys[self.systemID][1]
		self.buoyDlg.display(buoyText, buoyType, self.onBuoyConfirmed)

	def onBuoyConfirmed(self):
		try:
			self.win.setStatus(_('Executing ADD BUOY command...'))
			player = client.getPlayer()
			player.buoys = client.cmdProxy.addBuoy(player.oid, self.systemID, self.buoyDlg.buoyText, self.buoyDlg.buoyType)
			gdata.mainGameDlg.update()
			self.showSystem()
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onDeleteBuoy(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing DELETE BUOY command...'))
			player = client.getPlayer()
			player.buoys = client.cmdProxy.addBuoy(player.oid, self.systemID, "", 0)
			gdata.mainGameDlg.update()
			self.showSystem()
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onChangeMinStorage(self, widget, action, data):
		try:
			bio = int(self.win.vPCMinBio.text)
		except ValueError:
			self.win.setStatus(_('Enter number into biomatter min. reserve field.'))
			return
		try:
			en = int(self.win.vPCMinEn.text)
		except ValueError:
			self.win.setStatus(_('Enter number into energy min. reserve field.'))
			return
		try:
			self.win.setStatus(_('Executing CHANGE RESERVES LIMITS command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			client.cmdProxy.setMinStorage(self.planetID, bio, en)
			planet.minBio = bio
			planet.minMin = min
			planet.minEn = en
			self.showPlanet()
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onAutoMinStorage(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing SWITCH AUTOMATIC REGULATION command...'))
			planet = client.get(self.planetID, noUpdate = 1)
			planet.autoMinStor = client.cmdProxy.setAutoMinStorage(self.planetID, not planet.autoMinStor)
			self.showPlanet()
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return

	def onCloseDlg(self, widget, action, data):
		self.hide()

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
		# system
		self.win.subscribeAction('*', self)
		SystemMapWidget(self.win,
			id = 'vSystemMap',
			action = 'onSelectMapObj',
			layout = (0, 0, 40, 10)
		)
		ui.Title(self.win, layout = (0, 27, 35, 1), id = 'vStatusBar',
			align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'),
			action = 'onCloseDlg')
		## system
		ui.Title(self.win, layout = (0, 10, 40, 1), id = 'vSTitle',
			align = ui.ALIGN_W, font = 'normal-bold', tags = ['sys'])
		ui.Listbox(self.win, layout = (0, 11, 40, 14), id = 'vSSOver',
			columns = [(_('Planet'), 'text', 5, ui.ALIGN_W), (_('Type'), 'plType', 3.5, ui.ALIGN_W),
			(_('Bio'), 'plBio', 1.5, ui.ALIGN_E), (_('Min'), 'plMin', 1.5, ui.ALIGN_E), (_('En'), 'plEn', 1.5, ui.ALIGN_E),
			(_('Biomatter'), 'storBio', 3, ui.ALIGN_E), (_('+/-'), 'changeBio', 2, ui.ALIGN_E),
			(_('Energy'), 'storEn', 3, ui.ALIGN_E), (_('+/-'), 'changeEn', 2, ui.ALIGN_E),
			(_('Space'), 'space', 3, ui.ALIGN_E), (_('Con / Res'), 'consci', 4, ui.ALIGN_E),
			(_('Constructing'), 'constrInfo', 9, ui.ALIGN_W)],
			columnLabels = 1, tags = ['sys'], action = 'onSelectPlanet')
		ui.Title(self.win, layout = (0, 25, 13, 1), text = _('Total'), align = ui.ALIGN_W,
			font = 'normal-bold', tags = ['sys'])
		ui.Title(self.win, layout = (13, 25, 3, 1), id = 'vSTStorBio', align = ui.ALIGN_E, font = 'normal', tags = ['sys'])
		ui.Title(self.win, layout = (16, 25, 2, 1), id = 'vSTChangeBio', align = ui.ALIGN_E, font = 'normal-bold', tags = ['sys'])
		ui.Title(self.win, layout = (18, 25, 3, 1), id = 'vSTStorEn', align = ui.ALIGN_E, font = 'normal', tags = ['sys'])
		ui.Title(self.win, layout = (21, 25, 2, 1), id = 'vSTChangeEn', align = ui.ALIGN_E, font = 'normal-bold', tags = ['sys'])
		ui.Title(self.win, layout = (23, 25, 7, 1), id = 'vSTConSci', align = ui.ALIGN_E, font = 'normal', tags = ['sys'])
		ui.Title(self.win, layout = (30, 25, 10, 1), tags = ['sys'])
		ui.Button(self.win, layout = (0, 26, 5, 1), text = _('Rename'),
			id = 'vSRename', tags = ['sys'], action = 'onRenameSystem')
		ui.Button(self.win, layout = (5, 26, 10, 1), text = _('Find Wormhole Exit'),
			id = 'vSFWHExit', tags = ['hidden'], action = 'onFindWormholeExit')
		ui.Button(self.win, layout = (5, 26, 10, 1), text = _('Redirection OFF'),
			id = 'vSRedirect', tags = ['sys'], action = 'onRedirectFleets')
		ui.Button(self.win, layout = (15, 26, 5, 1), text = _('Add buoy'),
			id = 'vSBuoy', tags = ['sys'], action = 'onBuoy')
		ui.Button(self.win, layout = (20, 26, 5, 1), text = _('Delete buoy'),
			id = 'vSDeleteBuoy', tags = ['sys'], action = 'onDeleteBuoy')
		## planet
		ui.Title(self.win, layout = (0, 10, 20, 1), id = 'vPName',
			align = ui.ALIGN_W,	font = 'normal-bold', tags = ['pl'])
		ui.Title(self.win, layout = (20, 10, 20, 1), text = _('Structures'),
			align = ui.ALIGN_W, font = 'normal-bold', tags = ['pl'])
		ui.ButtonArray(self.win, layout = (20, 11, 20, 6), id = 'vPSlots',
			buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onSlotSelected', rmbAction = 'onSlotRSelected')
		ui.Title(self.win, layout = (20, 17, 20, 1), text = _('Task queue'),
			align = ui.ALIGN_W, font = 'normal-bold', tags = ['pl'])
		ui.ButtonArray(self.win, layout = (20, 18, 20, 2), id = 'vPQueue',
			buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onQueueItemSelected')
		ui.Label(self.win, layout = (0, 11, 5, 1), text = _('Planet type'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 11, 5, 1), id = 'vPPType',
			align = ui.ALIGN_E,	tags = ['pl'])
		ui.Label(self.win, layout = (10, 11, 5, 1), text = _('Diameter'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 11, 5, 1), id = 'vPDiameter',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 12, 5, 1), text = _('Environment'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 12, 5, 1), id = 'vPBioAbund',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 12, 5, 1), text = _('Min. abundance'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 12, 5, 1), id = 'vPMinAbund',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 13, 6, 1), text = _('En. abundance'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 13, 5, 1), id = 'vPEnAbund',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 13, 5, 1), text = _('Available space'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 13, 5, 1), id = 'vPSlotsAbund',
			align = ui.ALIGN_E, tags = ['pl'])
		## colony data
		ui.Title(self.win, layout = (0, 14, 20, 1), text = _('Colony data'),
			align = ui.ALIGN_W, font = 'normal-bold', tags = ['pl'])
		ui.Label(self.win, layout = (0, 15, 5, 1), text = _('Population'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 15, 5, 1), id = 'vPCPop',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 15, 6, 1), text = _('Pop. support'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 15, 5, 1), id = 'vPCConsumes',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 16, 5, 1), text = _('Biomatter'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 16, 5, 1), id = 'vPCStorBio',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 16, 5, 1), text = _('Min. reserve'),
			align = ui.ALIGN_W, tags = ['pl', 'minStor'])
		ui.Entry(self.win, layout = (15, 16, 5, 1), id = 'vPCMinBio',
			align = ui.ALIGN_E, tags = ['pl', 'minStor'])
		ui.Label(self.win, layout = (0, 17, 5, 1), text = _('Energy'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 17, 5, 1), id = 'vPCStorEn',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 17, 5, 1), text = _('Min. reserve'),
			align = ui.ALIGN_W, tags = ['pl', 'minStor'])
		ui.Entry(self.win, layout = (15, 17, 5, 1), id = 'vPCMinEn',
			align = ui.ALIGN_E, tags = ['pl', 'minStor'])
		ui.Button(self.win, layout = (15, 18, 4, 1), text = _('Change'),
			tags = ['pl', 'minStor'], action = 'onChangeMinStorage')
		ui.Button(self.win, layout = (19, 18, 1, 1), text = _('A'),
			tags = ['pl', 'minStor'], action = 'onAutoMinStorage', toggle = 1,
			tooltip = _('Automatic regulation on/off.'), id = 'vPCAutoMinStor',
			statustip = _('Automatic regulation on/off.'))
		ui.Label(self.win, layout = (0, 19, 5, 1), text = _('Free workers'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 19, 5, 1), id = 'vPCUnempl',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 20, 5, 1), text = _('Construction pts'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 20, 5, 1), id = 'vPCProd',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 21, 5, 1), text = _('Research pts'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 21, 5, 1), id = 'vPCSci',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 22, 5, 1), text = _('Env. status'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 22, 5, 1), id = 'vPCEnvStatus',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 20, 5, 1), text = _('Strat. resource'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 20, 5, 1), id = 'vPCSRes',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 19, 5, 1), text = _('Morale'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 19, 5, 1), id = 'vPCMorale',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 21, 5, 1), text = _('Planetary shield'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 21, 5, 1), id = 'vPCShield',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Title(self.win, layout = (0, 24, 20, 1), text = _('System data'),
			align = ui.ALIGN_W, font = 'normal-bold', tags = ['pl'])
		ui.Label(self.win, layout = (0, 25, 5, 1), text = _('Net Bio +/-'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 25, 5, 1), id = 'vSTPBio',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 25, 5, 1), text = _('Net Energy +/-'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 25, 5, 1), id = 'vSTPEn',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (0, 26, 5, 1), text = _('Net Construction'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (5, 26, 5, 1), id = 'vSTPProd',
			align = ui.ALIGN_E, tags = ['pl'])
		ui.Label(self.win, layout = (10, 26, 5, 1), text = _('Net Research'),
			align = ui.ALIGN_W, tags = ['pl'])
		ui.Label(self.win, layout = (15, 26, 5, 1), id = 'vSTPSci',
			align = ui.ALIGN_E, tags = ['pl'])
		## info
		ui.Title(self.win, layout = (20, 20, 20, 1), id = 'vITitle',
			align = ui.ALIGN_W, font = 'normal-bold', tags = ['pl'])
		# slot
		ui.Label(self.win, layout = (20, 21, 5, 1), text = _('Hit points'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (25, 21, 5, 1), id = 'vISHp', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (20, 22, 5, 1), text = _('Status'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (25, 22, 5, 1), id = 'vISOpStatus', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Title(self.win, layout = (20, 23, 10, 1), text = _('Problems'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (20, 24, 10, 1), id = 'vISStatus', align = ui.ALIGN_W,
			tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (30, 21, 5, 1), text = _('Biomatter p/c'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (35, 21, 5, 1), id = 'vISBioPC', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (30, 22, 5, 1), text = _('Energy p/c'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (35, 22, 5, 1), id = 'vISEnPC', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (30, 23, 5, 1), text = _('Constr pts'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (35, 23, 5, 1), id = 'vISConstr', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (30, 24, 5, 1), text = _('Research pts'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (35, 24, 5, 1), id = 'vISSci', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (30, 25, 5, 1), text = _('Workers'),
			align = ui.ALIGN_W, tags = ['slot', 'pl'])
		ui.Label(self.win, layout = (35, 25, 5, 1), id = 'vISWorkers', align = ui.ALIGN_E,
			tags = ['slot', 'pl'])
		ui.Button(self.win, layout = (20, 26, 2, 1), id = 'vISFirst', text = _('<<'),
			tags = ['slot', 'pl'], action = 'onMoveStructFirstLast', data = -1,
			tooltip = _('Move structure to first slot'))
		ui.Button(self.win, layout = (22, 26, 2, 1), id = 'vISPrev', text = _('<'),
			tags = ['slot', 'pl'], action = 'onMoveStruct', data = -1,
			tooltip = _('Move structure to previous slot'))
		ui.Button(self.win, layout = (24, 26, 2, 1), id = 'vISNext', text = _('>'),
			tags = ['slot', 'pl'], action = 'onMoveStruct', data = 1,
			tooltip = _('Move structure to next slot'))
		ui.Button(self.win, layout = (26, 26, 2, 1), id = 'vISLast', text = _('>>'),
			tags = ['slot', 'pl'], action = 'onMoveStructFirstLast', data = 1,
			tooltip = _('Move structure to last slot'))
		ui.Button(self.win, layout = (28, 26, 4, 1), text = _('ON/OFF'), id = 'vISOnOff',
			tags = ['slot', 'pl'], action = 'onSwitchStructOnOff',
			tooltip = _('Switch structure ON or OFF'))
		ui.Button(self.win, layout = (32, 26, 4, 1), text = _('Info'), id = 'vISTechInfo',
			tags = ['slot', 'pl'], action = 'onStructInfo',
			tooltip = _('Show structure information'))
		ui.Button(self.win, layout = (36, 26, 4, 1), text = _('Demolish'), id = 'vISDemolish',
			tags = ['slot', 'pl'], action = 'onDemolishStruct',
			tooltip = _('Demolish structure'))
		# task
		ui.Label(self.win, layout = (20, 21, 5, 1), text = _('Complete'),
			align = ui.ALIGN_W, tags = ['task', 'pl'])
		ui.Label(self.win, layout = (26, 21, 5, 1), id = 'vITCompl', align = ui.ALIGN_E,
			tags = ['task', 'pl'])
		ui.Label(self.win, layout = (31, 21, 3, 1), text = _('ETC'),
			align = ui.ALIGN_W, tags = ['task', 'pl'])
		ui.Label(self.win, layout = (35, 21, 5, 1), id = 'vITEtc', align = ui.ALIGN_E,
			tags = ['task', 'pl'])
		ui.Label(self.win, layout = (20, 22, 6, 1), text = _('Construction pts'),
			align = ui.ALIGN_W, tags = ['task', 'pl'])
		ui.Label(self.win, layout = (26, 22, 5, 1), id = 'vITProd', align = ui.ALIGN_E,
			tags = ['task', 'pl'])
		ui.Label(self.win, layout = (20, 24, 5, 1), text = _('Quantity'),
			align = ui.ALIGN_W, tags = ['task', 'pl'])
		ui.Label(self.win, layout = (26, 24, 5, 1), id = 'vITQuantity', align = ui.ALIGN_E,
			tags = ['task', 'pl'])
		ui.Label(self.win, layout = (20, 25, 5, 1), text = _('Target planet'),
			align = ui.ALIGN_W, tags = ['task', 'pl'])
		ui.Label(self.win, layout = (25, 25, 5, 1), id = 'vITTarget', align = ui.ALIGN_E,
			tags = ['task', 'pl'])
		ui.Label(self.win, layout = (30, 25, 4, 1), text = _('Target slot'),
			align = ui.ALIGN_W, tags = ['task', 'pl'])
		ui.Label(self.win, layout = (34, 25, 6, 1), id = 'vITTargetSlot', align = ui.ALIGN_W,
			tags = ['task', 'pl'])
		ui.Button(self.win, layout = (20, 26, 2, 1), id = 'vITFirst', text = _('<<'),
			tags = ['task', 'pl'], action = 'onMoveTaskFirstLast',
			tooltip = _('Move task to first position in queue'), data = -1)
		ui.Button(self.win, layout = (22, 26, 2, 1), id = 'vITPrev', text = _('<'),
			tags = ['task', 'pl'], action = 'onMoveTask', data = -1,
			tooltip = _('Move task to previous position in queue'))
		ui.Button(self.win, layout = (24, 26, 2, 1), id = 'vITNext', text = _('>'),
			tags = ['task', 'pl'], action = 'onMoveTask', data = 1,
			tooltip = _('Move task to next position in queue'))
		ui.Button(self.win, layout = (26, 26, 2, 1), id = 'vITLast', text = _('>>'),
			tags = ['task', 'pl'], action = 'onMoveTaskFirstLast',
			tooltip = _('Move task to last position in queue'), data = 1)
		ui.Button(self.win, layout = (28, 26, 4, 1), text = _('Quantity'),
			tags = ['task', 'pl'], action = 'onQtyTask',
			tooltip = _('Change task quantity'))
		ui.Button(self.win, layout = (32, 26, 4, 1), text = _('Info'), id = "vITInfo",
			tags = ['task', 'pl'], action = 'onTaskInfo',
			tooltip = _('Show task informations'))
		ui.Button(self.win, layout = (36, 26, 4, 1), text = _('Abort'),
			tags = ['task', 'pl'], action = 'onAbortTask',
			tooltip = _('Abort task construction'))

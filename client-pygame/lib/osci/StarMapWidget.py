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

from pygameui.Widget import Widget, registerWidget
import pygameui as ui
from pygameui.Fonts import *
from ige.ospace.Const import *
from ige.ospace import Rules, Utils
import pygame, pygame.draw, pygame.key
from pygame.locals import *
from dialog.ShowBuoyDlg import ShowBuoyDlg
from dialog.MapOverlayDlg import MapOverlayDlg
from dialog.KeyModHelp import KeyModHelp
import gdata, client, res, math, string
from ige import log
from osci.dialog.SearchDlg import SearchDlg
from osci.MiniMap import MiniMap

buoyColors = [(0xff, 0xff, 0x00), (0x00, 0xff, 0xff), (0xff, 0x00, 0xff), (0xb0, 0xb0, 0xff)]
MAX_BOUY_DISPLAY_LEN = 30

class StarMapWidget(Widget):

	MAP_SCANNER1 = 1
	MAP_SCANNER2 = 2
	MAP_SYSTEMS = 3
	MAP_PLANETS = 4
	MAP_FLEETS = 5
	MAP_FORDERS = 6
	MAP_OTHERS = 7
	MAP_FREDIRECTS = 8

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		self.searchDlg = SearchDlg(self.app)
		self.searchDlg.mapWidget = self
		self.showOverlayDlg = MapOverlayDlg(self.app)
		self.showOverlayDlg.mapWidget = self
		# data
		self.action = None
		# map
		self._mapSurf = None
		self._map = {
			self.MAP_SCANNER1: [],
			self.MAP_SCANNER2: [],
			self.MAP_SYSTEMS: [],
			self.MAP_PLANETS: [],
			self.MAP_FLEETS: [],
			self.MAP_FORDERS: [],
			self.MAP_OTHERS: [],
			self.MAP_FREDIRECTS: [],
		}
		self._popupInfo = {}
		self._fleetRanges = {}
		self._fleetTarget = {}
		self._actAreas = {}
		self._actBuoyAreas = {}
		self.currX = 0.0
		self.currY = 0.0
		self.scale = 35.0
		self.activeObjID = OID_NONE
		self.activeObjIDs = []
		self.pressedObjIDs = []
		self._newCurrXY = 0
		self.activePos = (0, 0)
		self.repaintMap = 1
		self.setPosition = 1
		self.showScanners = 1
		self.showSystems = 1
		self.showPlanets = 1
		self.showFleets = 1
		self.showGrid = 1
		self.showOverlaySelector = 1
		self.showRedirects = 1
		self.showPirateAreas = True
		self.highlightPos = None
		self.alwaysShowRangeFor = None
		self.showBuoyDlg = ShowBuoyDlg(self.app)
		self.KeyModHelp = KeyModHelp(self.app)
		self._miniMapRect = Rect(0, 20, 175, 175)
		self._overlayRect = Rect(0, 0, 175, 24)
		self._detectOverlayZone = Rect(0,0,0,0)
		self.miniMap = MiniMap(self._miniMapRect.width, self._miniMapRect.height)
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)
		# popup menu
		self.popup = ui.Menu(self.app, title = _("Select object"))
		self.popup.subscribeAction("*", self)
		# overlay system
		self.overlayMode = gdata.OVERLAY_OWNER
		self._overlayZone = False
		# key setting system
		self.selectobject = False
		self.setKey = False

	def precompute(self):
		# clear active areas for buoy texts
		self._actBuoyAreas = {}
		player_highlight = -1
		if gdata.config.game.highlight != None:
			player_highlight = gdata.config.game.highlight
		self._map = {
			self.MAP_SCANNER1: [],
			self.MAP_SCANNER2: [],
			self.MAP_SYSTEMS: [],
			self.MAP_PLANETS: [],
			self.MAP_FLEETS: [],
			self.MAP_FORDERS: [],
			self.MAP_OTHERS: [],
			self.MAP_FREDIRECTS: [],
		}
		self._popupInfo = {}
		self._fleetRanges = {}
		# find all pirate planets
		pirates = {}
		log.debug("Checking pirate planets and wormholes")
		for objID in client.db.keys():
			if objID < OID_FREESTART:
				continue
			obj = client.get(objID, noUpdate = 1)
			if not hasattr(obj, "type"):
				continue
			if obj.type == T_WORMHOLE and not hasattr(obj, 'destinationOid'):
				obj = client.get(objID, forceUpdate = 1, publicOnly = 1)
			if obj.type == T_PLANET and hasattr(obj, "x"):
				ownerID = getattr(obj, 'owner', OID_NONE)
				if ownerID == OID_NONE:
					continue
				owner = client.get(ownerID, noUpdate = 1)
				if hasattr(owner, "type") and owner.type == T_PIRPLAYER:
					pirates[obj.x, obj.y] = None
		# process objects
		fleetOrbit = {}
		anyX = 0.0
		anyY = 0.0
		player = client.getPlayer()
		for objID in client.db.keys():
			if objID < OID_FREESTART:
				continue
			obj = client.get(objID, noUpdate = 1)
			if not hasattr(obj, "type"):
				continue
			try:
				if obj.type == T_PLAYER:
					continue
				if hasattr(obj, "x"):
					anyX = obj.x
				if hasattr(obj, "y"):
					anyY = obj.y
			except AttributeError, e:
				log.warning('StarMapWidget', 'Cannot render objID = %d' % objID)
				continue
			if obj.type == T_SYSTEM:
				img = res.getSmallStarImg(obj.starClass[1]) # TODO correct me
				icons = []
				name = getattr(obj, 'name', None)
				# TODO compute real relationship
				#rel = REL_UNDEF
				refuelMax = 0
				refuelInc = 0
				upgradeShip = 0
				repairShip = 0
				speedBoost = 0
				moraleCount = 0
				morale = 200
				minerals = -1
				bio = -1
				slots = 0
				numPlanets = 0
				stratRes = SR_NONE
				#owner2 = 0
				ownerID = OID_NONE
				explored = False
				if hasattr(obj, 'planets'):
					hasPirate = False
					for planetID in obj.planets:
						planet = client.get(planetID, noUpdate = 1)
						owner = getattr(planet, 'owner', OID_NONE)
						if hasattr(planet, "plType") and planet.plType not in ("A", "G"):
							numPlanets += 1
						if owner:
								ownerID = owner
						if hasattr(planet, "morale"):
							morale = min(morale,planet.morale)
							#morale += planet.morale
							#moraleCount += 1
						if hasattr(planet, "plMin"):
							minerals = max(minerals,planet.plMin)
						if hasattr(planet, "plBio"):
							bio = max(bio,planet.plBio)
						if hasattr(planet, "plSlots"):
							slots += planet.plSlots
						if hasattr(planet, "plStratRes") and planet.plStratRes != SR_NONE:
							stratRes = planet.plStratRes
							stratRes = planet.plStratRes
							icons.append(res.icons["sr_%d" % planet.plStratRes])
						if hasattr(planet, "refuelMax"):
							refuelMax = max(refuelMax, planet.refuelMax)
							refuelInc = max(refuelInc, planet.refuelInc)
						if hasattr(planet, "repairShip"):
							upgradeShip += planet.upgradeShip
							repairShip = max(repairShip, planet.repairShip)
						if hasattr(planet, "fleetSpeedBoost"):
							speedBoost = max(speedBoost, planet.fleetSpeedBoost)
						# uncharted system
						if hasattr(planet, 'plBio') and hasattr(planet, 'plEn'):
							explored = True
				if not explored and name != None:
					name = "[%s]" % (name)
				#if moraleCount > 0:
				#	morale = morale/moraleCount
				if morale==200:
					morale = -1
				pirProb = self.precomputePirates(obj, pirates, icons)
				# refuelling
				if refuelMax >= 87:
					icons.append(res.icons["fuel_99"])
				elif refuelMax >= 62:
					icons.append(res.icons["fuel_75"])
				elif refuelMax >= 37:
					icons.append(res.icons["fuel_50"])
				elif refuelMax >= 12:
					icons.append(res.icons["fuel_25"])
				# repair and upgrade
				if upgradeShip > 10 and repairShip > 0.02:
					icons.append(res.icons["rep_10"])
				elif upgradeShip > 0 and repairShip > 0:
					icons.append(res.icons["rep_1"])

				self.precomputeCombat(obj, icons)
				self.precomputeBuoys(obj, player, icons)
				# star gates
				if speedBoost > 1.0:
					icons.append(res.icons["sg_%02d" % round(speedBoost)])
				#if owner2 != 0:
				#   color = gdata.playerHighlightColor
				#else:
				#   color = res.getFFColorCode(rel)
				colors = res.getStarmapWidgetSystemColor(ownerID,bio,minerals,slots,numPlanets,speedBoost, refuelInc, upgradeShip, pirProb*100, stratRes, morale)
				namecolor = res.getPlayerColor(ownerID)
				self._map[self.MAP_SYSTEMS].append((obj.oid, obj.x, obj.y, name, img, colors, namecolor, False, icons))
				# pop up info
				info = []
				info.append(_('System: %s [ID: %d]') % (name or res.getUnknownName(), obj.oid))
				info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
				info.append(_('Scan pwr: %d') % obj.scanPwr)
				info.append(_('Star Class: %s') % obj.starClass[1:])
				info.append(_('Star Type: %s') % _(gdata.starTypes[obj.starClass[0]]))
				if refuelMax > 0:
					info.append(_("Refuel: %d %%/turn [%d %% max]") % (refuelInc, refuelMax))
				if repairShip > 0:
					info.append(_("Repair ratio: %d %%/turn") % (repairShip * 100))
				if upgradeShip > 0:
					info.append(_("Upgrade points: %d/turn") % upgradeShip)
				if speedBoost > 0:
					info.append(_("Fleet speed: +%d %%") % (speedBoost * 100))
				if pirProb > 0.0:
					info.append(_("Pirate get fame chance: %d %%") % (pirProb * 100))
				self._popupInfo[obj.oid] = info
			elif obj.type == T_WORMHOLE:
				log.debug("Displaying wormhole",obj.oid)
				img = res.getSmallStarImg(obj.starClass[1])
				icons = []
				name = getattr(obj, 'name', None)
				pirProb = self.precomputePirates(obj, pirates, icons)
				self.precomputeCombat(obj, icons)
				self.precomputeBuoys(obj, player, icons)
				color = res.getPlayerColor(OID_NONE)
				self._map[self.MAP_SYSTEMS].append((obj.oid, obj.x, obj.y, name, img, color, namecolor, True, icons))
				# pop up info
				info = []
				info.append(_('Worm hole: %s [ID: %d]') % (name or res.getUnknownName(), obj.oid))
				info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
				try:
                                    log.debug("Attempting to get wormhole destination (",obj.destinationOid,") from client.")
				    whDestObj = client.get(obj.destinationOid, noUpdate = 1) #except if the client doesn't have this in their DB
				    whDestName = getattr(whDestObj, 'name', None)
				    info.append(_('Destination: %s [ID: %d]') % (whDestName or res.getUnknownName(), obj.oid))
				    info.append(_('Dest. Coords: [%.2f, %.2f]') % (whDestObj.x, whDestObj.y))
				except:
                                    log.debug("Failed getting wormhole destination from client.")
				    info.append(_('Destination: ? [ID: ?]'))
				    info.append(_('Dest. Coords: [?, ?]'))
				if pirProb > 0.0:
					info.append(_("Pirate get fame chance: %d %%") % (pirProb * 100))
				self._popupInfo[obj.oid] = info
			elif obj.type == T_PLANET:
				owner = getattr(obj, 'owner', OID_NONE)
				# set up color reference data
				biodata = -1
				mindata = -1
				slotdata = 0
				stargatedata = 0
				dockrefueldata = 0
				dockupgradedata = 0
				stratresdata = SR_NONE
				moraledata = -1
				pirProb = self.precomputePirates(obj, pirates, False)
				famedata = pirProb*100
				if hasattr(obj, 'plBio'):
					biodata = getattr(obj, 'plBio', OID_NONE)
				if hasattr(obj, 'plMin'):
					mindata = getattr(obj, 'plMin', OID_NONE)
				if hasattr(obj, 'plSlots'):
					slotdata = getattr(obj, 'plSlots', OID_NONE)
				if hasattr(obj, 'refuelInc'):
					dockrefueldata = getattr(obj, 'refuelInc', OID_NONE)
				if hasattr(obj, 'upgradeShip'):
					dockupgradedata = getattr(obj, 'upgradeShip', OID_NONE)
				if hasattr(obj, 'fleetSpeedBoost'):
					stargatedata = getattr(obj, 'fleetSpeedBoost', OID_NONE)
				if hasattr(obj, 'plStratRes'):
					stratresdata = getattr(obj, 'plStratRes', OID_NONE)
				if hasattr(obj, 'morale'):
					moraledata = getattr(obj, 'morale', OID_NONE)
				# build system
				name = getattr(obj, 'name', None) or res.getUnknownName()
				singlet = True
				if hasattr(obj, "plType") and obj.plType in ("A", "G"):
					colors = gdata.sevColors[gdata.DISABLED]
				else:
					singlet = False
					colors = res.getStarmapWidgetPlanetColor(owner,biodata,mindata,slotdata,stargatedata, dockrefueldata, dockupgradedata, famedata, stratresdata, moraledata)
				self._map[self.MAP_PLANETS].append((obj.oid, obj.x, obj.y, obj.orbit, colors, singlet))
				scannerPwr = getattr(obj, 'scannerPwr', 0)
				if scannerPwr:
					self._map[self.MAP_SCANNER1].append((obj.x, obj.y, scannerPwr / 10.0))
					self._map[self.MAP_SCANNER2].append((obj.x, obj.y, scannerPwr / 16.0))
				# pop up info
				info = []
				info.append(_('Planet: %s [ID: %d]') % (name, obj.oid))
				if hasattr(obj, 'scanPwr'): info.append(_('Scan pwr: %d') % obj.scanPwr)
				elif hasattr(obj, 'scannerPwr'): info.append(_('Scanner pwr: %d') % obj.scannerPwr)
				plType = gdata.planetTypes[getattr(obj, 'plType', None)]
				info.append(_('Type: %s') % _(plType))
				if hasattr(obj, 'plBio'): info.append(_('Environment: %d') % obj.plBio)
				if hasattr(obj, 'plMin'): info.append(_('Minerals: %d') % obj.plMin)
				if hasattr(obj, 'plEn'): info.append(_('Energy: %d') % obj.plEn)
				if hasattr(obj, "plStratRes") and obj.plStratRes != SR_NONE:
					info.append(_("Strat. resource: %s") % _(gdata.stratRes[obj.plStratRes]))
				if owner:
					onwerobj = client.get(owner)
					info.append(_('Owner: %s [ID: %s]') % (
						getattr(onwerobj, 'name', res.getUnknownName()),
						getattr(onwerobj, 'oid', '?')
					))
				self._popupInfo[obj.oid] = info
			elif obj.type == T_FLEET:
				owner = getattr(obj, 'owner', OID_NONE)
				name = getattr(obj, 'name', None) or res.getUnknownName()
				color = res.getPlayerColor(owner)
				scannerPwr = getattr(obj, 'scannerPwr', 0)
				if hasattr(obj, "scannerOn") and not obj.scannerOn:
					scannerPwr = 0
				if scannerPwr:
					self._map[self.MAP_SCANNER1].append((obj.x, obj.y, scannerPwr / 10.0))
					self._map[self.MAP_SCANNER2].append((obj.x, obj.y, scannerPwr / 16.0))
				orbit = -1
				if obj.orbiting != OID_NONE:
					orbit = fleetOrbit.get(obj.orbiting, 0)
					fleetOrbit[obj.orbiting] = orbit + 1
				eta = getattr(obj, 'eta', 0)
				self._map[self.MAP_FLEETS].append((obj.oid, obj.x, obj.y, obj.oldX, obj.oldY, orbit, res.formatTime(eta), color,
					obj.signature / 25, getattr(obj, "isMilitary", 0)))
				# pop up info
				info = []
				info.append(_('Fleet: %s [ID: %d]') % (name, obj.oid))
				if hasattr(obj, 'scanPwr'):	info.append(_('Scan pwr: %d') % obj.scanPwr)
				if hasattr(obj, 'scannerPwr'): info.append(_('Scanner pwr: %d') % obj.scannerPwr)
				info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
				info.append(_('Signature: %d') % obj.signature)
				if eta:
					info.append(_('ETA: %s') % res.formatTime(eta))
				if owner:
					onwerobj = client.get(owner)
					info.append(_('Owner: %s [ID: %s]') % (
						getattr(onwerobj, 'name', res.getUnknownName()),
						getattr(onwerobj, 'oid', '?')
					))
				if hasattr(obj, 'storEn'):
					if obj.maxEn > 0: full = 100 * obj.storEn / obj.maxEn
					else: full = 0
					info.append(_('Tanks: %d / %d [%d %%]') % (obj.storEn, obj.maxEn, full))
					info.append(_('Support (fuel): %d/turn') % (obj.operEn))
					info.append(_('Support (const. pts): %d/turn') % (obj.operProd))
				if hasattr(obj, 'combatPwr'):
					info.append(_('Military power: %d') % obj.combatPwr)
				# ranges
				if hasattr(obj, 'storEn') and hasattr(obj, 'operEn'):
					turns = 100000
					if obj.operEn > 0: turns = obj.storEn / obj.operEn
					range = turns * obj.speed / Rules.turnsPerDay
					self._fleetRanges[obj.oid] = (obj.x, obj.y, range, (range  * 0.75) / 2, (range  * 0.5) / 2, obj.speed * 6 / Rules.turnsPerDay, turns)
					info.append("Operational time: %s" % res.formatTime(turns))
				if hasattr(obj, 'target') and obj.target != OID_NONE:
					target = client.get(obj.target, noUpdate=1)
					if hasattr(target, "x"):
						self._fleetTarget[obj.oid] = (obj.x, obj.y, target.x, target.y)
					info.append(_('Target: %s') % getattr(target, "name", res.getUnknownName()))
				if hasattr(obj, 'ships'):
					info.append(_('Ships:'))
					number = {}
					for designID, hp, shield, exp in obj.ships:
						tech = client.getPlayer().shipDesigns[designID]
						level = Rules.shipExpToLevel.get(int(exp / tech.baseExp), Rules.shipDefLevel)
						if designID not in number:
							number[designID] = [0, 0, 0, 0, 0]
						number[designID][level - 1] += 1
					order = number.keys()
					order.sort()
					for designID in order:
						tech = client.getPlayer().shipDesigns[designID]
						levels = number[designID]
						info.append(_('  %d x %s   [%d, %d, %d, %d, %d]') % (
								levels[0] + levels[1] + levels[2] + levels[3] + levels[4],
								tech.name,
								levels[0], levels[1], levels[2], levels[3], levels[4],
							)
						)
				elif hasattr(obj, 'shipScan'):
					info.append(_('Ships:'))
					for name, shipClass, isMilitary in obj.shipScan:
						if isMilitary:
							sType = _("military")
						else:
							sType = _("civilian")
						info.append(_("  %d x %s [%s %s ship]") % (
							obj.shipScan[name, shipClass, isMilitary],
							name,
							_(gdata.shipClasses[shipClass]),
							sType
						))
				if hasattr(obj, 'actionIndex') and not Utils.isIdleFleet(obj):
					action, target, data = obj.actions[obj.actionIndex]
					if target != OID_NONE:
						targetName = getattr(client.get(target, noUpdate = 1), 'name', res.getUnknownName())
					else:
						targetName = ""
					info.append(_("Command: %s %s") % (
						gdata.fleetActions[action],
						targetName,
					))
				self._popupInfo[obj.oid] = info
				# orders
				if hasattr(obj, 'actions'):
					oldX = obj.x
					oldY = obj.y
					for action, target, aData in obj.actions[obj.actionIndex:]:
						if target:
							# TODO add action colors
							if action == FLACTION_REFUEL: color = (0x00, 0x90, 0x00)
							elif action == FLACTION_DEPLOY: color = (0x90, 0x90, 0x00)
							elif action == FLACTION_REDIRECT: color = (0x20, 0x20, 0x80)
							else: color = (0x90, 0x90, 0x90)
							trgt = client.get(target, noUpdate = 1)
							if hasattr(trgt, 'x'):
								self._map[self.MAP_FORDERS].append((oldX, oldY, trgt.x, trgt.y, color))
								oldX, oldY = trgt.x, trgt.y
			elif obj.type == T_ASTEROID:
				owner = getattr(obj, 'owner', OID_NONE)
				name = getattr(obj, 'name', None) or res.getUnknownName()
				color = (0xff, 0xff, 0xff)
				scannerPwr = getattr(obj, 'scannerPwr', 0)
				orbit = -1
				if obj.orbiting != OID_NONE:
					orbit = fleetOrbit.get(obj.orbiting, 0)
					fleetOrbit[obj.orbiting] = orbit + 1
				eta = getattr(obj, 'eta', 0)
				self._map[self.MAP_FLEETS].append((obj.oid, obj.x, obj.y, obj.oldX, obj.oldY, orbit, res.formatTime(eta), color,
					obj.signature / 25, 0))
				# pop up info
				info = []
				info.append(_('Asteroid: %s [ID: %d]') % (name, obj.oid))
				if hasattr(obj, 'scanPwr'): info.append(_('Scan pwr: %d') % obj.scanPwr)
				info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
				info.append(_('Signature: %d') % obj.signature)
				if hasattr(obj, 'asDiameter'): info.append(_('Diameter: %d') % obj.asDiameter)
				if hasattr(obj, 'asHP'): info.append(_('HP: %d') % obj.asHP)
				if hasattr(obj, 'speed'): info.append(_('Speed: %.2f') % obj.speed)
				if eta:
					info.append(_('ETA: %s') % res.formatTime(eta))
				if owner:
					onwerobj = client.get(owner)
					info.append(_('Owner: %s [ID: %s]') % (
						getattr(onwerobj, 'name', res.getUnknownName()),
						getattr(onwerobj, 'oid', '?')
					))
				self._popupInfo[obj.oid] = info
			elif obj.type in (T_GALAXY, T_AIRENPLAYER, T_AIMUTPLAYER, T_AIPIRPLAYER, T_AIEDENPLAYER, T_PIRPLAYER):
				pass
			elif obj.type == T_UNKNOWN:
				# pop up info
				info = []
				info.append(_('Unknown object [ID: %d]') % obj.oid)
				if hasattr(obj, 'scanPwr'):
					info.append(_('Scan pwr: %d') % obj.scanPwr)
				self._popupInfo[obj.oid] = info
			else:
				log.warning('StarMapWidget', 'Unknown object type %d' % obj.type)
		# redirections
		player = client.getPlayer()
		for sourceID in player.shipRedirections:
			targetID = player.shipRedirections[sourceID]
			source = client.get(sourceID, noUpdate = 1)
			target = client.get(targetID, noUpdate = 1)
			if hasattr(source, "x") and hasattr(target, "y"):
				self._map[self.MAP_FREDIRECTS].append((source.x, source.y, target.x, target.y))
		# set position (typically on first show)
		if self.setPosition:
			self.setPosition = 0
			self.currX = anyX
			self.currY = anyY
		
		self.miniMap.precompute()
		# self dirty flag
		self.repaintMap = 1

	def precomputePirates(self, system, pirates, icons = False):
		dist = 10000
		for pirX, pirY in pirates:
			dist = min(dist, math.hypot(system.x - pirX, system.y - pirY))
		pirProb = Rules.pirateGainFamePropability(dist)
		if icons != False:
		    if pirProb >= 1.0:
			    icons.append(res.icons["pir_99"])
		    elif pirProb > 0.0:
			    icons.append(res.icons["pir_00"])
		return pirProb

	def precomputeCombat(self, system, icons):
		if hasattr(system, "combatCounter") and system.combatCounter > 0:
			icons.append(res.icons["combat"])

	def precomputeBuoys(self, system, player, icons):
		if hasattr(player, "buoys") and system.oid in player.buoys:
			icons.append(res.icons["buoy_%d" % player.buoys[system.oid][1]])
		if hasattr(player, "alliedBuoys") and system.oid in player.alliedBuoys and len(player.alliedBuoys[system.oid]) > 0:
			buoyName = "buoy_%d" % player.alliedBuoys[system.oid][0][1]
			if len(player.alliedBuoys[system.oid]) > 1:
				buoyName = "%s_plus" % buoyName
			icons.append(res.icons[buoyName])

	def drawScanners(self):
		# coordinates
		centerX, centerY = self._mapSurf.get_rect().center
		maxY = self._mapSurf.get_rect().height
		currX = self.currX
		currY = self.currY
		scale = self.scale
		# draw
		for x, y, range in self._map[self.MAP_SCANNER1]:
			sx = int((x - currX) * scale) + centerX
			sy = maxY - (int((y - currY) * scale) + centerY)
			pygame.draw.circle(self._mapSurf, (0x00, 0x00, 0x60), (sx, sy), int(range * scale + 2), 0)
		for x, y, range in self._map[self.MAP_SCANNER1]:
			sx = int((x - currX) * scale) + centerX
			sy = maxY - (int((y - currY) * scale) + centerY)
			pygame.draw.circle(self._mapSurf, (0x00, 0x00, 0x30), (sx, sy), int(range * scale), 0)
		for x, y, range in self._map[self.MAP_SCANNER2]:
			sx = int((x - currX) * scale) + centerX
			sy = maxY - (int((y - currY) * scale) + centerY)
			pygame.draw.circle(self._mapSurf, (0x00, 0x00, 0x40), (sx, sy), int(range * scale), 0)

	def drawRedirects(self):
		# coordinates
		centerX, centerY = self._mapSurf.get_rect().center
		maxY = self._mapSurf.get_rect().height
		currX = self.currX
		currY = self.currY
		scale = self.scale
		for sx, sy, tx, ty in self._map[self.MAP_FREDIRECTS]:
			sx = int((sx - currX) * scale) + centerX
			sy = maxY - (int((sy - currY) * scale) + centerY)
			tx = int((tx - currX) * scale) + centerX
			ty = maxY - (int((ty - currY) * scale) + centerY)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx + 2, sy), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx - 2, sy), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy + 2), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy - 2), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy + 1), (tx, ty), 1)
			pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy - 1), (tx, ty), 1)
			# pygame.draw.line(self._mapSurf, (0x00, 0x00, 0x80), (sx, sy), ((sx + tx) / 2, (sy + ty) / 2), 3)

	def drawSystems(self):
		# coordinates
		centerX, centerY = self._mapSurf.get_rect().center
		maxY = self._mapSurf.get_rect().height
		currX = self.currX
		currY = self.currY
		scale = self.scale
		if scale >= 30:
			for objID, x, y, name, img, color, namecolor, singlet, icons in self._map[self.MAP_SYSTEMS]:
				sx = int((x - currX) * scale) + centerX
				sy = maxY - (int((y - currY) * scale) + centerY)
				w, h = img.get_size()
				x = sx - w / 2
				y = sy - h / 2
				self._mapSurf.blit(img, (x, y))
				# images are now smaller - TODO fix images of stars
				w = 22
				h = 22
				if name:
					if self.overlayMode != gdata.OVERLAY_OWNER:
						namecolor = res.fadeColor(namecolor)
					img = renderText('small', name, 1, namecolor)
					self._mapSurf.blit(img, (sx - img.get_width() / 2, sy + h / 2))
					buoy = self.getBuoy(objID)
					if buoy != None:
						lines = buoy[0].split("\n")
						nSy = sy + h / 2 + img.get_height()
						maxW = 0
						hh = 0
						for line in lines:
							if len(line) == 0:
								break
							if len(line) > MAX_BOUY_DISPLAY_LEN:
								line = u"%s..." % line[:MAX_BOUY_DISPLAY_LEN]
							if self.overlayMode == gdata.OVERLAY_OWNER:
								bouycolor = buoyColors[buoy[1] - 1]
							else:
								bouycolor = res.fadeColor(buoyColors[buoy[1] - 1])
							img = renderText('small', line, 1, bouycolor)
							maxW = max(img.get_width(), maxW)
							self._mapSurf.blit(img, (sx - img.get_width() / 2, nSy + hh))
							hh += img.get_height()
						if maxW > 0:
							actRect = Rect(sx - maxW / 2, nSy, maxW, hh)
							actRect.move_ip(self.rect.left, self.rect.top)
							self._actBuoyAreas[objID] = actRect
				for icon in icons:
					self._mapSurf.blit(icon, (x, y))
					x += icon.get_width() + 1
				# active rectangle
				actRect = Rect(sx - w / 2, sy - h / 2, w, h)
				actRect.move_ip(self.rect.left, self.rect.top)
				self._actAreas[objID] = actRect
		else:
			for objID, x, y, name, img, color, namecolor, singlet, icons in self._map[self.MAP_SYSTEMS]:
				if not singlet:
					color = color[self.overlayMode]
				sx = int((x - currX) * scale) + centerX
				sy = maxY - (int((y - currY) * scale) + centerY)
				pygame.draw.circle(self._mapSurf, color, (sx, sy), 5, 1)
				pygame.draw.circle(self._mapSurf, color, (sx, sy), 4, 0)
				if name and scale > 15:
					if self.overlayMode != gdata.OVERLAY_OWNER:
						namecolor = res.fadeColor(namecolor)
					img = renderText('small', name, 1, namecolor)
					self._mapSurf.blit(img, (sx - img.get_width() / 2, sy + 6 / 2))
					buoy = self.getBuoy(objID)
					if buoy != None:
						lines = buoy[0].split("\n")
						nSy = sy + 6 / 2 + img.get_height()
						maxW = 0
						hh = 0
						for line in lines:
							if len(line) == 0:
								break
							img = renderText('small', line, 1, buoyColors[buoy[1] - 1])
							maxW = max(img.get_width(), maxW)
							self._mapSurf.blit(img, (sx - img.get_width() / 2, nSy + hh))
							hh += img.get_height()
						if maxW > 0:
							actRect = Rect(sx - maxW / 2, nSy, maxW, hh)
							actRect.move_ip(self.rect.left, self.rect.top)
							self._actBuoyAreas[objID] = actRect
				# active rectangle
				actRect = Rect(sx - 6 / 2, sy - 6 / 2, 6, 6)
				actRect.move_ip(self.rect.left, self.rect.top)
				self._actAreas[objID] = actRect

	def drawPlanets(self):
		# coordinates
		centerX, centerY = self._mapSurf.get_rect().center
		maxY = self._mapSurf.get_rect().height
		currX = self.currX
		currY = self.currY
		scale = self.scale
		if scale >= 30:
			for objID, x, y, orbit, color, singlet in self._map[self.MAP_PLANETS]:
				if not singlet:
					color = color[self.overlayMode]
				sx = int((x - currX) * scale) + centerX
				sy = maxY - (int((y - currY) * scale) + centerY)
				orbit -= 1
				actRect = Rect(sx + (orbit % 8) * 6 + 13, sy + 6 * (orbit / 8) - 6, 5, 5)
				self._mapSurf.fill(color, actRect)
				actRect.move_ip(self.rect.left, self.rect.top)
				self._actAreas[objID] = actRect
		elif scale > 20:
			for objID, x, y, orbit, color, singlet in self._map[self.MAP_PLANETS]:
				if not singlet:
					color = color[self.overlayMode]
				sx = int((x - currX) * scale) + centerX
				sy = maxY - (int((y - currY) * scale) + centerY)
				orbit -= 1
				actRect = Rect(sx + (orbit % 8) * 3 + 7, sy - 3 * (orbit / 8) - 1, 2, 2)
				self._mapSurf.fill(color, actRect)
				actRect.move_ip(self.rect.left, self.rect.top)
				self._actAreas[objID] = actRect

	def drawFleets(self):
		# coordinates
		centerX, centerY = self._mapSurf.get_rect().center
		maxY = self._mapSurf.get_rect().height
		currX = self.currX
		currY = self.currY
		scale = self.scale
		# draw orders lines
		for x1, y1, x2, y2, color in self._map[self.MAP_FORDERS]:
			sx1 = int((x1 - currX) * scale) + centerX
			sy1 = maxY - (int((y1 - currY) * scale) + centerY)
			sx2 = int((x2 - currX) * scale) + centerX
			sy2 = maxY - (int((y2 - currY) * scale) + centerY)
			pygame.draw.line(self._mapSurf, color, (sx1, sy1), (sx2, sy2), 1)
		# draw fleet symbol
		for objID, x, y, oldX, oldY, orbit, eta, color, size, military in self._map[self.MAP_FLEETS]:
			if self.overlayMode != gdata.OVERLAY_OWNER:
				color = res.fadeColor(color)
			sx = int((x - currX) * scale) + centerX
			sy = maxY - (int((y - currY) * scale) + centerY)
			if orbit >= 0 and scale >= 30:
				actRect = Rect(sx + (orbit % 8) * 6 + 13, sy + 6 * (orbit / 8) + 6, 4, 4)
				# TODO this is a workaround - fix it when pygame gets fixed
				pygame.draw.polygon(self._mapSurf, color,
					(actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 1)
				pygame.draw.polygon(self._mapSurf, color,
					(actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 0)
				actRect.move_ip(self.rect.left, self.rect.top)
				self._actAreas[objID] = actRect
			elif orbit < 0:
				sox = int((oldX - currX) * scale) + centerX
				soy = maxY - (int((oldY - currY) * scale) + centerY)
				actRect = Rect(sx - 3, sy - 3, 6, 6)
				if military:
					mColor = color
				else:
					mColor = (0xff, 0xff, 0xff)
				pygame.draw.line(self._mapSurf, mColor, (sx, sy), (sox, soy), size + 1)
				# TODO rotate triangle
				pygame.draw.polygon(self._mapSurf, color,
					(actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 1)
				pygame.draw.polygon(self._mapSurf, color,
					(actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 0)
				if eta and scale > 15:
					img = renderText('small', eta, 1, color)
					self._mapSurf.blit(img, actRect.topright)
				actRect.move_ip(self.rect.left, self.rect.top)
				self._actAreas[objID] = actRect

	def draw(self, surface):
		if not self._mapSurf:
			self._mapSurf = pygame.Surface(self.rect.size, SWSURFACE | SRCALPHA, surface)
			# workaround for FILLED CIRCLE CLIP BUG - TODO remove
			clip = self._mapSurf.get_clip()
			clip.left += 1
			clip.top += 1
			clip.width -= 2
			clip.height -= 2
			self._mapSurf.set_clip(clip)
			#
			self._miniMapRect.left = self.rect.width - self._miniMapRect.width
			self._miniMapRect.top = self.rect.top
			#self._overlayRect.left = self.rect.width - self._overlayRect.width
			self._overlayRect.top = 0 #self.rect.top
			#log.debug("Overlay Rect aligned to top:",self.rect.top)
			self.repaintMap = 1
		if self.repaintMap:
			self._actAreas = {}
			mapSurface = self._mapSurf
			# redraw map
			mapSurface.fill((0x00, 0x00, 0x00))
			# coordinates
			centerX, centerY = mapSurface.get_rect().center
			maxY = mapSurface.get_rect().height
			currX = self.currX
			currY = self.currY
			scale = self.scale
			# clipping (TODO better one)
			clip = mapSurface.get_clip()
			# scanners
			# scanner ranges
			if self.showScanners:
				self.drawScanners()
			# pirate area
			if self.showPirateAreas:
				pass # TODO
			# grid
			if self.showGrid:
				self.drawGrid()
			# redirections
			if self.showRedirects:
				self.drawRedirects()
			# stars
			if self.showSystems:
				self.drawSystems()
			# planets
			if self.showPlanets:
				self.drawPlanets()
			# fleets
			if self.showFleets:
				self.drawFleets()
			# overlay selector
			if self.showOverlaySelector:
				self.drawOverlaySelector(surface)
			# clean up flag
			self.repaintMap = 0
		# blit cached map
		surface.blit(self._mapSurf, self.rect)
		# additional informations
		oldClip = surface.get_clip()
		surface.set_clip(self.rect)
		centerX, centerY = self._mapSurf.get_rect().center
		maxY = self._mapSurf.get_rect().height
		if self.highlightPos:
			sx = int((self.highlightPos[0] - self.currX) * self.scale) + centerX + self.rect.left
			sy = maxY - (int((self.highlightPos[1] - self.currY) * self.scale) + centerY) + self.rect.top
			pygame.draw.circle(surface, (0xff, 0xff, 0xff), (sx, sy), 13, 2)
		if self.alwaysShowRangeFor and self._fleetRanges.has_key(self.alwaysShowRangeFor):
			x, y, maxRange, operRange, halfRange, speed, turns = self._fleetRanges[self.alwaysShowRangeFor]
			sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
			sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
			rng = max(maxRange * self.scale, 0.2 * self.scale)
			if rng > 1:
				pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), int(rng), 1)
			rng = operRange * self.scale
			if rng > 1:
				pygame.draw.circle(surface, (0x20, 0x80, 0x20), (sx, sy), int(rng), 1)
			rng = halfRange * self.scale
			if rng > 1:
				pygame.draw.circle(surface, (0x20, 0x20, 0x80), (sx, sy), int(rng), 1)
		# draw ranges
		for activeObjID in self.activeObjIDs:
			if activeObjID and activeObjID in self._fleetTarget:
				x, y, x1, y1 = self._fleetTarget[activeObjID]
				sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
				sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
				dx = int((x1 - self.currX) * self.scale) + centerX + self.rect.left
				dy = maxY - (int((y1 - self.currY) * self.scale) + centerY) + self.rect.top
				pygame.draw.line(surface, (0xff, 0xff, 0x00), (sx, sy), (dx, dy), 2)
			if activeObjID and activeObjID in self._fleetRanges:
				x, y, maxRange, operRange, halfRange, speed, turns = self._fleetRanges[activeObjID]
				sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
				sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
				if pygame.key.get_mods() & KMOD_SHIFT:
					for i in xrange(1, turns / 6):
						rng = int(i * speed * self.scale)
						if rng > 1:
							pygame.draw.circle(surface, (0x70, 0x70, 0x80), (sx, sy), rng, 1)
							textSrfc = renderText('small', res.formatTime(i * 6), 1, (0x70, 0x70, 0x80), (0x00, 0x00, 0x00))
							surface.blit(textSrfc, (sx - rng, sy - textSrfc.get_height() / 2))
							surface.blit(textSrfc, (sx + rng, sy - textSrfc.get_height() / 2))
							surface.blit(textSrfc, (sx - textSrfc.get_width() / 2, sy - rng))
							surface.blit(textSrfc, (sx - textSrfc.get_width() / 2, sy + rng - textSrfc.get_height()))
					rng = int(max(maxRange * self.scale, 0.2 * self.scale))
					if rng > 1:
						pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), rng, 1)
				else:
					rng = int(max(maxRange * self.scale, 0.2 * self.scale))
					if rng > 1:
						pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), rng, 1)
					rng = int(operRange * self.scale)
					if rng > 1:
						pygame.draw.circle(surface, (0x20, 0x80, 0x20), (sx, sy), rng, 1)
					rng = int(halfRange * self.scale)
					if rng > 1:
						pygame.draw.circle(surface, (0x20, 0x20, 0x80), (sx, sy), rng, 1)

		self.miniMap.draw(surface, self._miniMapRect.left, self._miniMapRect.top)
		# draw popups
		moreIDs = len(self.activeObjIDs) > 1
		if not moreIDs:
			x, y = self.activePos
			x += 20
		else:
			x = self.rect.left + 2
			y = self.rect.top
		if not pygame.key.get_mods() & KMOD_SHIFT:
			for activeObjID in self.activeObjIDs:
				index = 0
				if self._popupInfo.has_key(activeObjID):
					# put pop up info on the screen
					info = self._popupInfo[activeObjID]
					# x1, y1 = self._actAreas[self.activeObjID].center
					fg = self.theme.themeForeground #(0x30, 0xe0, 0x30, 0xff)
					bg = self.theme.themeBackground #(0x20, 0x40, 0x20, 0x99)
					width = 0
					height = 0
					# pygame.draw.line(surface, fg, (x1, y1), (x, y), 1)
					for item in info:
						w, h = getTextSize('small', item)
						width = max(width, w)
						height += h
					if not moreIDs:
						if x + width >= self.rect.width:
							x -= width + 40
						if y + 1 + height >= self.rect.height:
							y -= height
					surface.fill(bg, (x, y, width + 2, height + 2))
					x += 1
					tmpY = y + 1
					for item in info:
						textSrfc = renderText('small', item, 1, fg)
						surface.blit(textSrfc, (x, tmpY))
						tmpY += textSrfc.get_height()
					x += width + 2
		# restore clipping
		surface.set_clip(oldClip)
		#
		return self.rect

	def getBuoy(self, objID):
		player = client.getPlayer()
		if hasattr(player, "buoys") and objID in player.buoys:
			lines = player.buoys[objID][0].split("\n")
			if len(lines) > 2:
				return (u"%s\n%s" % (lines[0], lines[1]), player.buoys[objID][1])
			else:
				return player.buoys[objID]
		else:
			if hasattr(player, "alliedBuoys") and objID in player.alliedBuoys:
				if len(player.alliedBuoys[objID]) > 0:
					lines = player.alliedBuoys[objID][0][0].split("\n")
					if len(lines) > 2:
						return (u"%s\n%s" % (lines[0], lines[1]), player.alliedBuoys[objID][0][1])
					else:
						return player.alliedBuoys[objID][0]
				else:
					return None
			else:
				return None

	def drawOverlaySelector(self,surface):

		#guess we have to make this a popup! :(
		#log.debug('Overlay Size:',self._overlayRect.width,self._overlayRect.height)
		if not self._overlayZone:
			self._overlayZone = pygame.Surface((self._overlayRect.width,self._overlayRect.height),SWSURFACE | SRCALPHA, surface)
		
		self._detectOverlayZone.top = self._overlayRect.top + self.rect.top
		self._detectOverlayZone.left = self._overlayRect.left
		self._detectOverlayZone.width = self._overlayRect.width
		self._detectOverlayZone.height = self._overlayRect.height

		self._overlayZone.fill((0x00,0x00,0x00))

		pygame.draw.rect(self._overlayZone,(0x00, 0x00, 0x90),Rect(0,0,self._overlayRect.width,self._overlayRect.height),1)
	        


		
		#pygame.draw.rect(self.overlayZone,(0x00, 0x00, 0x00),self._overlayRect,0) #this picks up mouse button position
		#pygame.draw.rect(self._mapSurf,(0x00, 0x00, 0x00),self._overlayRect,0)
		#pygame.draw.rect(self.overlayZone,(0x00, 0x00, 0x90),self._overlayRect,1)

		
		mode = _("Overlay Mode: ")
		if self.overlayMode == gdata.OVERLAY_OWNER:
			mode = mode + _("Normal")
		if self.overlayMode == gdata.OVERLAY_DIPLO:
			mode = mode + _("Diplomatic")
		if self.overlayMode == gdata.OVERLAY_BIO:
			mode = mode + _("Environment")
		if self.overlayMode == gdata.OVERLAY_FAME:
			mode = mode + _("Pirate Fame")
		if self.overlayMode == gdata.OVERLAY_MIN:
			mode = mode + _("Minerals")
		if self.overlayMode == gdata.OVERLAY_SLOT:
			mode = mode + _("Slots")
		if self.overlayMode == gdata.OVERLAY_STARGATE:
			mode = mode + _("Fleet Acceleration")
		if self.overlayMode == gdata.OVERLAY_DOCK:
			mode = mode + _("Refuel and Repair")
		if self.overlayMode == gdata.OVERLAY_MORALE:
			mode = mode + _("Morale")
		
		textSrfc = renderText('small', mode, 1, (0x70, 0x70, 0x80))
		self._overlayZone.blit(textSrfc, (
			6,
			4 )
		)
		
		self._mapSurf.blit(self._overlayZone, self._overlayRect)
#	        surface.blit(self._overlayZone, self._overlayRect)
		
		


	def drawGrid(self):
		rect = self._mapSurf.get_rect()
		centerX, centerY = rect.center
		maxY = rect.height
		currX = self.currX
		currY = self.currY
		scale = self.scale
		left = int((int(currX) - currX) * scale) + centerX - int(rect.width / scale / 2) * scale
		x = left
		while x < left + rect.width + scale:
			value =  math.floor((x - centerX) / scale + currX)
			if value % 5 == 0:
				pygame.draw.line(self._mapSurf, (0x00, 0x00, 0x90),
					(x, rect.top), (x, rect.bottom), 1)
				textSrfc = renderText('small', int(value), 1, (0x70, 0x70, 0x80))
				self._mapSurf.blit(textSrfc, (x + 2, rect.height - textSrfc.get_height()))
			else:
				pygame.draw.line(self._mapSurf, (0x33, 0x33, 0x66),
					(x, rect.top), (x, rect.bottom), 1)
			x += scale
		top = int((int(currY) - currY) * scale) + centerY - int(rect.height / scale / 2) * scale
		y = top
		while y < top + rect.height + scale:
			yScrn = maxY - y
			value =  math.floor(((maxY - yScrn) - centerY) / scale + currY)
			if value % 5 == 0:
				pygame.draw.line(self._mapSurf, (0x00, 0x00, 0x90),
					(rect.left, yScrn), (rect.right, yScrn), 1)
				textSrfc = renderText('small', int(value), 1, (0x70, 0x70, 0x80))
				self._mapSurf.blit(textSrfc, (0, yScrn))
			else:
				pygame.draw.line(self._mapSurf, (0x33, 0x33, 0x66),
					(rect.left, yScrn), (rect.right, yScrn), 1)
			y += scale

	def processMB1Down(self, evt):
		# handle SHIFT click as MB3
		mods = pygame.key.get_mods()
		if mods & KMOD_SHIFT:
			return self.processMB3Down(evt)
		pos = evt.pos
		if self._miniMapRect.collidepoint(pos):
			return ui.NoEvent
		if self._detectOverlayZone.collidepoint(pos):
			return ui.NoEvent
		self.pressedObjIDs = []
		for objID in self._actAreas.keys():
			rect = self._actAreas[objID]
			if rect.collidepoint(pos):
				self.pressedObjIDs.append(objID)

		self.pressedBuoyObjIDs = []
		for objID in self._actBuoyAreas.keys():
			rect = self._actBuoyAreas[objID]
			if rect.collidepoint(pos):
				self.pressedBuoyObjIDs.append(objID)

		if self.pressedObjIDs or self.pressedBuoyObjIDs:
			return ui.NoEvent
		else:
			self.activeObjID = OID_NONE
			return ui.NoEvent

	def processMB1Up(self, evt):
		# handle SHIFT click as MB3
		mods = pygame.key.get_mods()
		if mods & KMOD_SHIFT:
			return self.processMB3Up(evt)
		pos = evt.pos
		if self._miniMapRect.collidepoint(pos):
			self.currX, self.currY = self.miniMap.processMB1Up((pos[0] - self._miniMapRect.left, self._miniMapRect.height - pos[1] + self._miniMapRect.top))
			self.processMiniMapRect()
			self.repaintMap = 1
			return ui.NoEvent
		if self._detectOverlayZone.collidepoint(pos):
			self.showOverlayDlg.display()
			return ui.NoEvent
		objIDs = []
		for objID in self._actAreas.keys():
			rect = self._actAreas[objID]
			if rect.collidepoint(pos):
				objIDs.append(objID)

		bObjIDs = []
		for objID in self._actBuoyAreas.keys():
			rect = self._actBuoyAreas[objID]
			if rect.collidepoint(pos):
				bObjIDs.append(objID)

		if (objIDs or bObjIDs) and (self.pressedObjIDs == objIDs or self.pressedBuoyObjIDs == bObjIDs) and self.action:
			if self.selectobject:
				self.setKeyObject(objIDs,bObjIDs)
				return ui.NoEvent
			self.gotoObject(objIDs,bObjIDs)
			return ui.NoEvent
		else:
			self.activeObjID = OID_NONE
			return ui.NoEvent

	def gotoObject(self,objIDs,bObjIDs):
		if len(objIDs) + len(bObjIDs) == 1:
			if len(objIDs) == 1:
				if self.selectobject:
					return objIDs[0]
				self.processAction(self.action, objIDs[0])
				self.pressedObjIDs = []
			else:
				if self.selectobject:
					return OID_NONE
				self.showBuoyDlg.display(bObjIDs[0])
				self.pressedBuoyObjIDs = []
		else:
			# multiple objects -> post pop-up menu
			items = []
			for objID in objIDs:
				obj = client.get(objID)
				if obj.type == T_SYSTEM:
					name = getattr(obj, "name", None)
					name = _("System: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				elif obj.type == T_WORMHOLE:
					name = getattr(obj, "name", None)
					name = _("Worm hole: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				elif obj.type == T_PLANET:
					name = getattr(obj, "name", None)
					name = _("Planet: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				elif obj.type == T_FLEET:
					name = getattr(obj, "name", None)
					name = _("Fleet: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				elif obj.type == T_ASTEROID:
					name = getattr(obj, "name", None)
					name = _("Asteroid: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				else:
					name = _("Unknown object [ID: %d]") % obj.oid
				item = ui.Item(name, action = "onObjectSelected", data = objID)
				items.append(item)
			for objID in bObjIDs:
				obj = client.get(objID)
				if obj.type == T_SYSTEM:
					name = getattr(obj, "name", None)
					name = _("Buoy on system: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				elif obj.type == T_WORMHOLE:
					name = getattr(obj, "name", None)
					name = _("Buoy on worm hole: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
				else:
					name = _("Buoy on unknown object [ID: %d]") % obj.oid
				item = ui.Item(name, action = "onBuoySelected", data = objID)
				items.append(item)
			self.popup.items = items
			self.popup.show()
		if self.selectobject:
			return OID_NONE

	def onObjectSelected(self, widget, action, data):
		self.processAction(self.action, data)

	def onBuoySelected(self, widget, action, data):
		self.showBuoyDlg.display(data)

	def processMB3Down(self, evt):
		if self._miniMapRect.collidepoint(evt.pos):
			return ui.NoEvent
		self._newCurrXY = 1
		return ui.NoEvent

	def processMB3Up(self, evt):
		if self._newCurrXY:
			x, y = evt.pos
			centerX, centerY = self._mapSurf.get_rect().center
			self.currX -= float(centerX - x) / self.scale
			self.currY += float(centerY - y) / self.scale
			self.processMiniMapRect()
			self.repaintMap = 1
			self._newCurrXY = 0
		return ui.NoEvent

	def processMiniMapRect(self):
		rect = self._mapSurf.get_rect()
		self.miniMap.moveRect(self.currX, self.currY, rect.width / self.scale, rect.height / self.scale)

	def processMWUp(self, evt):
		self.scale += 5
		self.repaintMap = 1
		self.processMiniMapRect()
		return ui.NoEvent

	def processMWDown(self, evt):
		if self.scale > 10:
			self.scale -= 5
			self.repaintMap = 1
			self.processMiniMapRect()
		return ui.NoEvent

	def processMMotion(self, evt):
		pos = evt.pos
		if self._miniMapRect.collidepoint(pos):
			#log.debug('Minimap Rect Position');
			return ui.NoEvent
		if self._detectOverlayZone.collidepoint(pos):
			#log.debug('Overlay Rect Position');
			return ui.NoEvent
		self.activeObjID = OID_NONE
		self.activeObjIDs = []
		for objID in self._actAreas.keys():
			rect = self._actAreas[objID]
			if rect.collidepoint(pos):
				self.activeObjID = objID
				self.activeObjIDs.append(objID)
				self.activePos = pos
		return ui.NoEvent

	def processKeyDown(self, evt):
		#I have not found unicode escape characters for Ctrl-0 through Ctrl-9, so using direct key reference (less preferred due to international keyboards)
		if evt.key in [49,50,51,52,53,54,55,56,57,48]:
			if pygame.key.get_mods() & KMOD_CTRL:
				log.debug('Set Key:',evt.key)
				if gdata.config.defaults.showkeymodehelp != 'off':
					self.KeyModHelp.show()
				self.selectobject = True
				self.setKey = evt.key
			elif pygame.key.get_mods() & KMOD_SHIFT:
				log.debug('Focus Key:',evt.key)
				self.focusOnKeyObject(evt.key)
			else:
				log.debug('Goto Key:',evt.key)
				self.gotoKeyObject(evt.key)
			return ui.NoEvent
		elif evt.key == K_ESCAPE and self.selectobject:
			log.debug('Canceled Key')
			self.selectobject = False
			return ui.NoEvent
		if not evt.unicode:
			# force update
			self.scale += 1
			self.scale -= 1
			return ui.NoEvent
		if evt.unicode in u'+=':
			self.scale += 5
			self.repaintMap = 1
		elif evt.unicode == u'-':
			if self.scale > 10:
				self.scale -= 5
				self.repaintMap = 1
		# Ctrl+F
		elif evt.unicode == u'\x06' and pygame.key.get_mods() & KMOD_CTRL:
			self.searchDlg.display()
		# Ctrl+M
		elif evt.unicode == u'\x0D' and pygame.key.get_mods() & KMOD_CTRL:
			self.showOverlayDlg.display()
		elif evt.unicode == u' ':
			x, y = pygame.mouse.get_pos()
			centerX, centerY = self._mapSurf.get_rect().center
			self.currX -= float(centerX - x) / self.scale
			self.currY += float(centerY - y) / self.scale
			self.repaintMap = 1
			self._newCurrXY = 0
		else:
			# force update
			self.scale += 1
			self.scale -= 1
		return ui.NoEvent

	def setKeyObject(self,objIDs,bObjIDs):
		objID = self.gotoObject(objIDs,bObjIDs)
		log.debug('Setting Key Object To:',objID)
		self.selectobject = False
		if (objID == OID_NONE):
			return
		obj = client.get(objID)
		if obj.type in (T_SYSTEM, T_PLANET, T_FLEET):
			gdata.objectFocus[self.setKey]=objID

	def gotoKeyObject(self,evtkey):
		if evtkey in gdata.objectFocus:
			objID = gdata.objectFocus[evtkey]
			self.processAction(self.action, objID)
			self.pressedObjIDs = []

	def focusOnKeyObject(self,evtkey):
		if evtkey in gdata.objectFocus:
			objID = gdata.objectFocus[evtkey]
			obj = client.get(objID, noUpdate = 1)
			if hasattr(obj, "x"):
				gdata.mainGameDlg.win.vStarMap.highlightPos = (obj.x, obj.y)
				gdata.mainGameDlg.win.vStarMap.setPos(obj.x, obj.y)

	def setPos(self, x, y):
		self.currX = x
		self.currY = y
		self.repaintMap = 1
		# disable auto position setting
		self.setPosition = 0

registerWidget(StarMapWidget, 'starmapwidget')

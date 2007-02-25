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

from ige.IObject import IObject
from ige import *
from Const import *
from xml.dom.minidom import Node, parse
from ige.IObject import IObject
from ISystem import ISystem
from ige.IDataHolder import IDataHolder
import os.path, time, Utils, Rules
from ige import log

import Scanner

class IGalaxy(IObject):

	typeID = T_GALAXY
	forums = {"PUBLIC": 112, "NEWS": 112}

	def init(self, obj):
		IObject.init(self, obj)
		#
		obj.x = 0.0
		obj.y = 0.0
		obj.radius = 0.0
		obj.centerWeight = 250.0
		obj.systems = []
		obj.startingPos = []
		obj.numOfStartPos = 0
		obj.timeEnabled = 0 # TODO change to 0
		obj.timeStopped = 0
		obj.creationTime = 0.0
		obj.imperator = OID_NONE
		obj.description = ""
		# electromagnetic radiation
		obj.emrLevel = 1.0
		obj.emrTrend = 1.0
		obj.emrTime = 0

	def update(self, tran, obj):
		# check existence of all systems
		if 0:
			for systemID in obj.systems:
				if not tran.db.has_key(systemID):
					log.debug("CONSISTENCY - system %d from galaxy %d does not exists" % (systemID, obj.oid))
				elif tran.db[systemID].type not in (T_SYSTEM, T_WORMHOLE):
					log.debug("CONSISTENCY - system %d from galaxy %d is not a T_SYSTEM or T_WORMHOLE" % (systemID, obj.oid))
		# validate starting positions
		for planetID in obj.startingPos[:]:
			if not tran.db.has_key(planetID):
				log.debug("REMOVING nonexistent obj from start pos", planetID)
				obj.startingPos.remove(planetID)
			planet = tran.db[planetID]
			if planet.type != T_PLANET:
				log.debug("REMOVING ??? from start pos", planetID)
				obj.startingPos.remove(planetID)
			#if planet.plType != "E":
			#   log.debug("REMOVING non earth planet from start pos", planetID)
			#   obj.startingPos.remove(planetID)
		# check compOf
		if not tran.db.has_key(obj.compOf) or tran.db[obj.compOf].type != T_UNIVERSE:
			log.debug("CONSISTENCY invalid compOf for galaxy", obj.oid, obj.compOf)

	update.public = 0

	def getReferences(self, tran, obj):
		return obj.systems

	getReferences.public = 0

	def processINITPhase(self, tran, obj, data):
		# compute emr level
		turn = tran.db[OID_UNIVERSE].turn
		obj.emrTime -= 1
		if obj.emrTime <= 0:
			modulo = turn % Rules.emrPeriod
			for season in Rules.emrSeasons:
				if modulo >= season.startTime and modulo <= season.endTime:
					log.debug("EMR - season", season.name)
					obj.emrTrend = Utils.rand(int(season.emrLevelMin * 100), int(season.emrLevelMax * 100) + 1) / 100.0
					obj.emrTime = Utils.rand(Rules.emrMinDuration, Rules.emrMaxDuration)
					log.debug("EMR - trend, time", obj.emrTrend, obj.emrTime)
					message = {
						"sender": "GNC",
						"senderID": obj.oid,
						"forum": "NEWS",
						"data": (obj.oid, MSG_GNC_EMR_FORECAST, obj.oid, turn, (obj.emrTrend, obj.emrTime)),
						"topic": "EVENT",
					}
					self.cmd(obj).sendMsg(tran, obj, message)
					break
		elif obj.emrLevel >= obj.emrTrend:
			obj.emrLevel -= Utils.rand(1, 6) / 100.0
		elif obj.emrLevel <= obj.emrTrend:
			obj.emrLevel += Utils.rand(1, 6) / 100.0
		#
		if not obj.timeStopped:
			if not obj.timeEnabled:
				self.cmd(obj).enableTime(tran, obj)
		else:
			self.cmd(obj).enableTime(tran, obj, force = 1, enable = 0)
		# remove old messages
		self.cmd(obj).deleteOldMsgs(tran, obj)
		return obj.systems

	processINITPhase.public = 1
	processINITPhase.accLevel = AL_ADMIN

	def processPRODPhase(self, tran, obj, data):
		if obj.timeEnabled and not obj.timeStopped:
			return obj.systems

	processPRODPhase.public = 1
	processPRODPhase.accLevel = AL_ADMIN

	def processACTIONPhase(self, tran, obj, data):
		if obj.timeEnabled and not obj.timeStopped:
			return obj.systems

	processACTIONPhase.public = 1
	processACTIONPhase.accLevel = AL_ADMIN

	def processSCAN2Phase(self, tran, obj, data):
		# compute scanner for all objects on the map
		playerMap = Scanner.computeMap(self, tran, obj)
		# distribute map
		for playerID, map in playerMap.iteritems():
			player = tran.db[playerID]
			self.cmd(player).mergeScannerMap(tran, player, map)
		return

	processSCAN2Phase.public = 1
	processSCAN2Phase.accLevel = AL_ADMIN

	def processBATTLEPhase(self, tran, obj, data):
		if obj.timeEnabled and not obj.timeStopped:
			return obj.systems

	processBATTLEPhase.public = 1
	processBATTLEPhase.accLevel = AL_ADMIN

	def processFINALPhase(self, tran, obj, data):
		# validate starting positions
		remove = []
		for planetID in obj.startingPos:
			planet = tran.db[planetID]
			if planet.owner != OID_NONE:
				remove.append(planetID)
		for planetID in remove:
			obj.startingPos.remove(planetID)
		#
		#if obj.timeEnabled and not obj.timeStopped:
		return obj.systems

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	def processFINAL2Phase(self, tran, obj, data):
		# save history file
		turn = tran.db[OID_UNIVERSE].turn
		# TODO: reneable history when it's optimized
		if turn % 6 == 0 and False:
			log.debug("Saving history for galaxy", obj.oid, obj.name)
			fh = open("var/history/galaxy%d-%06d.xml" % (obj.oid, turn), "w+")
			print >>fh, '<?xml version="1.0" encoding="UTF-8"?>'
			print >>fh, '<history turn="%d" galaxy="%d" name="%s">' % (turn, obj.oid, obj.name)
			# save systems and owners
			players = {}
			print >>fh, '  <systems>'
			for systemID in obj.systems:
				system = tran.db[systemID]
				owners = {}
				for planetID in system.planets:
					ownerID = tran.db[planetID].owner
					if ownerID != OID_NONE:
						owners[ownerID] = tran.db[ownerID].name
						players[ownerID] = None
				print >>fh, '    <sys x="%.2f" y="%.2f" name="%s" owners="%s"/>' % (
					system.x,
					system.y,
					system.name,
					",".join(owners.values())
				)
			print >>fh, '  </systems>'
			# stats
			print >>fh, '  <stats>'
			for playerID in players:
				player = tran.db[playerID]
				print >>fh, '    <pl name="%s" pop="%d" planets="%d" stucts="%d" cp="%d" mp="%d" rp="%d"/>'% (
					player.name,
					player.stats.storPop,
					player.stats.planets,
					player.stats.structs,
					player.stats.prodProd,
					player.stats.fleetPwr,
					player.stats.prodSci,
				)
			print >>fh, '  </stats>'
			print >>fh, '</history>'

	processFINAL2Phase.public = 1
	processFINAL2Phase.accLevel = AL_ADMIN


	def loadFromXML(self, tran, obj, file, galID, x, y, name):
		log.message('IGalaxy', 'Parsing XML file...')
		dom = parse(os.path.join('data', file))
		log.message('IGalaxy', 'XML file parsed.')
		assert dom.documentElement.tagName == 'universe'
		for node in dom.documentElement.childNodes:
			if node.nodeType == Node.ELEMENT_NODE and node.tagName == 'galaxy':
				if node.getAttribute('id') == galID:
					self.loadDOMNode(tran, obj, node, x, y, name)
					self.connectWormHoles(tran, obj)
					return SUCC
		raise GameException('No such id %s in resource' % galID)

	loadFromXML.public = 1
	loadFromXML.accLevel = AL_ADMIN

	def loadDOMNode(self, tran, obj, node, x, y, name):
		obj.name = name
		obj.x = float(x)
		obj.y = float(y)
		xoff = x - float(node.getAttribute('x'))
		yoff = y - float(node.getAttribute('y'))
		obj.creationTime = time.time()
		for elem in node.childNodes:
			if elem.nodeType == Node.ELEMENT_NODE:
				name = elem.tagName
				if name == 'properties':
					self.loadDOMAttrs(obj, elem)
				elif name == 'system':
					system = tran.db[self.createSystem(tran, obj)]
					self.cmd(system).loadDOMNode(tran, system, xoff, yoff, elem)
				elif name == 'hole':
					wormHole = tran.db[self.createWormHole(tran, obj)]
					self.cmd(wormHole).loadDOMNode(tran, wormHole, xoff, yoff, elem)
				else:
					raise GameException('Unknown element %s' % name)
		return SUCC

	def connectWormHoles(self, tran, obj):
		wormHoles = {}
		for holeID in obj.systems:
			wormHole = tran.db[holeID]
			if wormHole.type == T_WORMHOLE:
				wormHoles[wormHole.name] = holeID
		
		for holeID in obj.systems:
			wormHole = tran.db[holeID]
			if wormHole.type != T_WORMHOLE:
				continue
			if len(wormHole.destination) == 0:
				raise GameException('Wrong WormHole(%d) definition' % holeID)
			if wormHole.destination == wormHole.name:
				raise GameException('Same destination as position for WormHole(%d)' % holeID)
			destinationOid = wormHoles[wormHole.destination]
			if destinationOid == OID_NONE:
				raise GameException('WormHole(%d) has wrong destination ''%s''' % (holeID, wormHole.destination))
			wormHole.destinationOid = destinationOid

	def createSystem(self, tran, obj):
		system = self.new(T_SYSTEM)
		system.compOf = obj.oid
		oid = tran.db.create(system)
		obj.systems.append(oid)
		return oid

	def createWormHole(self, tran, galaxy):
		hole = self.new(T_WORMHOLE)
		hole.compOf = galaxy.oid
		oid = tran.db.create(hole)
		galaxy.systems.append(oid)
		return oid

	def enableTime(self, tran, obj, force = 0, deleteSP = 0, enable = 1):
		log.debug('IGalaxy', 'Checking for time...')
		if not force:
			if obj.timeEnabled:
				return
			canRun = 0
			# there must be at least 1/2 positions already assigned
			#if len(obj.startingPos) <= obj.numOfStartPos / 2 and obj.creationTime < time.time() - 2 * 24 * 3600:
			#   log.debug("Half galaxy populated", len(obj.startingPos), obj.numOfStartPos)
			#   canRun = 1
			# at least two days must pass from creation
			if not obj.startingPos:
				log.debug("All positions taken, starting galaxy")
				canRun = 1
			if obj.creationTime < time.time() - 2 * 24 * 3600:
				log.debug("Two days passed", obj.creationTime, time.time() - 2 * 24 * 3600)
				canRun = 1
			if not canRun:
				return 0
		# ok, enable time
		log.message('IGalaxy', 'Enabling time for', obj.oid)
		obj.timeEnabled = enable
		# close galaxy
		if deleteSP:
			obj.startingPos = []
		# load new galaxy
		# TODO
		# enable time for players
		for systemID in obj.systems:
			system = tran.db[systemID]
			for planetID in system.planets:
				planet = tran.db[planetID]
				if planet.owner != OID_NONE:
					player = tran.db[planet.owner]
					if player.timeEnabled != enable:
						player.timeEnabled = enable
						player.lastLogin = time.time()
						if enable:
							Utils.sendMessage(tran, player, MSG_ENABLED_TIME, player.oid, None)

	enableTime.public = 1
	enableTime.accLevel = AL_ADMIN

	def delete(self, tran, obj):
		log.debug(obj.oid, "GALAXY - delete")
		universe = tran.db[OID_UNIVERSE]
		# delete systems and planets
		for systemID in obj.systems:
			log.debug("Deleting system", systemID)
			system = tran.db[systemID]
			log.debug("-- planets", system.planets)
			log.debug("-- fleets", system.fleets, system.closeFleets)
			for planetID in system.planets[:]:
				planet = tran.db[planetID]
				self.cmd(planet).changeOwner(tran, planet, OID_NONE, force = 1)
				del tran.db[planetID]
			for fleetID in system.closeFleets[:]:
				fleet = tran.db[fleetID]
				# this will modify system fleet and closeFleets attrs
				self.cmd(fleet).disbandFleet(tran, fleet)
			del tran.db[systemID]
		# delete all remaining fleets
		for playerID in universe.players[:]:
			player = tran.db[playerID]
			if obj.oid not in player.galaxies:
				continue
			if player.fleets:
				log.debug("Player %d has still fleets" % playerID, player.name, player.fleets)
				for fleetID in player.fleets:
					fleet = tran.db[fleetID]
					log.debug("Fleet NOT DELETED:", fleet)
			if player.planets:
				log.debug("Player %d has still planets" % playerID, player.name, player.planets)
			self.cmd(player).delete(tran, player)
		# remove this galaxy from the list of the galaxies
		tran.db[OID_UNIVERSE].galaxies.remove(obj.oid)
		del tran.db[obj.oid]
		return 1

	delete.public = 1
	delete.accLevel = AL_ADMIN

	def getPublicInfo(self, tran, obj):
		result = IDataHolder()
		result.oid = obj.oid
		result.type = obj.type
		result.name = obj.name
		result.emrLevel = obj.emrLevel
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE

	def getDescription(self,obj):
            return obj.description
        
	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE
	
	def setupEnvironment(self, tran, obj):
		# check required players
		universe = tran.db[OID_UNIVERSE]
		players = {}
		for playerType in (T_AIRENPLAYER, T_AIMUTPLAYER, T_AIPIRPLAYER, T_AIEDENPLAYER):
			found = 0
			for playerID in universe.players:
				player = tran.db[playerID]
				if obj.oid in player.galaxies and player.type == playerType:
					players[playerType] = player
					found = 1
					break
			if found:
				continue
			# create new player
			log.debug("Creating new player", playerType)
			player = self.new(playerType)
			self.cmd(player).register(tran, player)
			player.galaxies.append(obj.oid)
			players[playerType] = player
		# great we have all players - scan planets
		for systemID in obj.systems:
			system = tran.db[systemID]
			for planetID in system.planets:
				planet = tran.db[planetID]
				# renegades
				if planet.plStratRes in (SR_TL1A, SR_TL1B) and planet.owner == OID_NONE:
					# populate planet
					log.debug("Adding renegades", planetID)
					self.cmd(planet).changeOwner(tran, planet, players[T_AIRENPLAYER].oid, 1)
					planet.slots.append(Utils.newStructure(tran, Rules.Tech.RENEGADEBASE, planet.owner))
					planet.storPop = 3000
				# pirates
				if planet.plStratRes in (SR_TL3A, SR_TL3B, SR_TL3C) and planet.owner == OID_NONE:
					# populate planet
					log.debug("Adding pirates", planetID)
					self.cmd(planet).changeOwner(tran, planet, players[T_AIPIRPLAYER].oid, 1)
					planet.slots.append(Utils.newStructure(tran, Rules.Tech.PIRATEBASE, planet.owner))
					planet.storPop = 5000
					if planet.plSlots > 1:
						planet.slots.append(Utils.newStructure(tran, Rules.Tech.PIRATEDEN, planet.owner))
						planet.storPop += 1000
				# EDEN
				if planet.plStratRes in (SR_TL5A, SR_TL5B, SR_TL5C) and planet.owner == OID_NONE:
					# populate planet
					log.debug("Adding EDEN", planetID)
					self.cmd(planet).changeOwner(tran, planet, players[T_AIEDENPLAYER].oid, 1)
					if planet.plSlots < 2:
						planet.plSlots = 2
						if planet.plMaxSlots < 2:
							planet.plMaxSlots = 2
						if planet.plDiameter < 2000:
							planet.plDiameter = 2000
					planet.slots.append(Utils.newStructure(tran, Rules.Tech.EDENBASE, planet.owner))
					planet.slots.append(Utils.newStructure(tran, Rules.Tech.EDENSTATION, planet.owner))
					planet.storPop = 3000
				# mutants
				if planet.plDisease != 0 and planet.owner == OID_NONE:
					# populate planet
					log.debug("Adding mutants", planetID)
					self.cmd(planet).changeOwner(tran, planet, players[T_AIMUTPLAYER].oid, 1)
					planet.slots.append(Utils.newStructure(tran, Rules.Tech.MUTANTBASE, planet.owner))
					planet.storPop = 3000

	setupEnvironment.public = 1
	setupEnvironment.accLevel = AL_ADMIN

	## messaging
	def canGetMsgs(self, tran, obj, oid):
		return 1

	canGetMsgs.public = 0

	def canSendMsg(self, tran, obj, oid, forum):
		if forum == "PUBLIC":
			return 1
		elif forum == "NEWS":
			return 1
		return 0

	canSendMsg.public = 0

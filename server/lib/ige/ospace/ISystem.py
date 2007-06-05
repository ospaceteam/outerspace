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

from ige import *
from xml.dom.minidom import Node
from ige.IObject import IObject
from ige.IDataHolder import IDataHolder
from Const import *
import Rules, Utils, math, random, copy
from ige import log

class ISystem(IObject):

	typeID = T_SYSTEM

	def init(self, obj):
		IObject.init(self, obj)
		#
		obj.x = 0.0
		obj.y = 0.0
		obj.planets = []
		obj.fleets = []
		obj.closeFleets = []
		obj.starClass = u'---' # Star clasification
		obj.signature = 100
		# rotation
		#~ obj.dist = 0.0
		#~ obj.dAngle = 0.0
		#~ obj.sAngle = 0.0
		# renaming
		obj.lastNameChng = 0
		# combat
		obj.combatCounter = 0
		# system wide data
		obj.scannerPwrs = {}
		# mine field
		obj.minefield = {}

	def update(self, tran, obj):
		# check existence of all planets
		if 0:
			for planetID in obj.planets:
				if not tran.db.has_key(planetID):
					log.debug("CONSISTENCY - planet %d from system %d does not exists" % (planetID, obj.oid))
				elif tran.db[planetID].type != T_PLANET:
					log.debug("CONSISTENCY - planet %d from system %d is not a T_PLANET" % (planetID, obj.oid))
		if not hasattr(obj,'minefield'):
			obj.miefield = {}
		# check that all .fleet are in .closeFleets
		for fleetID in obj.fleets:
			if fleetID not in obj.closeFleets:
				log.debug("CONSISTENCY - fleet %d is in .fleet but not in .closeFleets - adding" % fleetID)
				obj.closeFleets.append(fleetID)
		# check existence of all fleets
		for fleetID in obj.closeFleets:
			if not tran.db.has_key(fleetID):
				log.debug("CONSISTENCY - fleet %d from system %d does not exists" % (fleetID, obj.oid))
			elif tran.db[fleetID].type not in (T_FLEET, T_ASTEROID):
				log.debug("CONSISTENCY - fleet %d from system %d is not a T_FLEET" % (fleetID, obj.oid))
		# delete nonexistent fleets
		index = 0
		while index < len(obj.closeFleets) and obj.closeFleets:
			fleet = tran.db.get(obj.closeFleets[index], None)
			if fleet == None:
				log.debug("CONSISTENCY - fleet %d does not exists" % obj.closeFleets[index])
				fleetID = obj.closeFleets[index]
				obj.closeFleets.remove(fleetID)
				obj.fleets.remove(fleetID)
			else:
				index += 1
		# check compOf
		if not tran.db.has_key(obj.compOf) or tran.db[obj.compOf].type != T_GALAXY:
			log.debug("CONSISTENCY invalid compOf for system", obj.oid)
		# rebuild closeFleets attribute
		old = obj.closeFleets
		obj.closeFleets = []
		for fleetID in old:
			fleet = tran.db.get(fleetID, None)
			if fleet and fleet.closeSystem == obj.oid and fleetID not in obj.closeFleets:
				obj.closeFleets.append(fleetID)
		if old != obj.closeFleets:
			log.debug("System close fleets fixed", obj.oid, old, obj.closeFleets)
		# try to find starting planets
		starting = 0
		free = 1
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.plStarting:
				starting = planetID
			if planet.owner != OID_NONE:
				free = 0
		if starting and free:
			# good starting position
			#@log.debug("Found starting position", obj.oid, starting)
			# get galaxy
			galaxy = tran.db[obj.compOf]
			if starting not in galaxy.startingPos:
				log.debug("Adding to starting positions of galaxy", galaxy.oid)
				galaxy.startingPos.append(starting)
		# check if system has planets
		hasHabitable = 0
		for planetID in obj.planets:
			if tran.db[planetID].plSlots > 0:
				hasHabitable = 1
				break
		if (not obj.planets or not hasHabitable) and obj.starClass[0] != "b" and obj.starClass != "wW0":
			log.debug("No planet for system", obj.oid, obj.name, obj.starClass)
			# delete old planets
			for planetID in obj.planets:
				del tran.db[planetID]
			obj.planets = []
			# find matching systems
			avail = []
			for systemID in tran.db[obj.compOf].systems:
				system = tran.db[systemID]
				if system.starClass[1] == obj.starClass[1] \
					or (obj.starClass[1] == "G" and system.starClass[1] == "F"):
					ok = 0
					for planetID in system.planets:
						planet = tran.db[planetID]
						if planet.plStarting:
							ok = 0
							break
						if planet.plSlots > 0:
							ok = 1
					if ok and system.planets:
						avail.append(systemID)
			# select random system
			import random
			log.debug("Can copy", avail)
			try:
				systemID = random.choice(avail)
				# copy it
				log.debug("Will copy system", systemID)
				nType = Utils.getPlanetNamesType()
				orbit = 1
				for planetID in tran.db[systemID].planets:
					orig = tran.db[planetID]
					planet = tran.db[self.createPlanet(tran, obj)]
					planet.name = Utils.getPlanetName(obj.name, nType, orbit - 1)
					planet.x = obj.x
					planet.y = obj.y
					planet.plDiameter = orig.plDiameter
					planet.plType = orig.plType
					planet.plMin = orig.plMin
					planet.plBio = orig.plBio
					planet.plEn = orig.plEn
					planet.plEnv = orig.plEnv
					planet.plSlots = orig.plSlots
					planet.plMaxSlots = orig.plMaxSlots
					planet.plStratRes = 0
					planet.plDisease = 0
					planet.plStarting = 0
					planet.orbit = orbit
					planet.storPop = 0
					planet.slots = []
					orbit += 1
			except:
				log.debug("Copy failed")

	update.public = 0

	def getReferences(self, tran, obj):
		return obj.planets

	getReferences.public = 0

	def getScanInfos(self, tran, obj, scanPwr, player):
		result = IDataHolder()
		results = [result]
		if scanPwr >= Rules.level1InfoScanPwr:
			result._type = T_SCAN
			result.scanPwr = scanPwr
			result.oid = obj.oid
			result.x = obj.x
			result.y = obj.y
			if hasattr(obj, 'destinationOid'):
				result.destinationOid = obj.destinationOid
			# multiply by 1000 to increase accuracy
			#~ result.dist = obj.dist * 1000
			#~ result.dAngle = obj.dAngle * 1000
			#~ result.sAngle = obj.sAngle * 1000
			result.signature = obj.signature
			result.type = obj.type
			result.compOf = obj.compOf
			result.starClass = obj.starClass
		if scanPwr >= Rules.level2InfoScanPwr:
			result.name = obj.name
			result.combatCounter = obj.combatCounter
		if scanPwr >= Rules.level3InfoScanPwr:
			result.planets = obj.planets
			result.owner = obj.owner
			for planetID in obj.planets:
				planet = tran.db[planetID]
				if planet.owner == player: ####### This was player.owner, which made no sense. Hope this change doesn't break something
					continue
				newPwr = scanPwr * planet.signature / obj.signature
				results.extend(self.cmd(planet).getScanInfos(tran, planet, newPwr, player))
		if scanPwr >= Rules.level4InfoScanPwr:
			result.fleets = obj.fleets
			for fleetID in obj.fleets:
				fleet = tran.db[fleetID]
				if fleet.owner == player:
					continue
				newPwr = scanPwr * fleet.signature / obj.signature
				results.extend(self.cmd(fleet).getScanInfos(tran, fleet, newPwr, player))
			result.hasmines = 0 #no
			if len(obj.minefield) > 0:
				result.hasmines = 1 #yes
			result.minefield = self.getMines(obj,player.oid) #only shows mines you own
			if len(obj.minefield) > 1 or (len(obj.minefield) == 1 and len(result.minefield) == 0):
				result.hasmines = 2 #yes, and some aren't my mines
		return results

	def processINITPhase(self, tran, obj, data):
		obj.scannerPwrs = {}

	processINITPhase.public = 1
	processINITPhase.accLevel = AL_ADMIN

	def processPRODPhase(self, tran, obj, data):
		#mine deployment
		owners = []
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner not in owners:
				owners.append(planet.owner)
		for ownerid in owners:
			tech,structtech = self.getSystemMineLauncher(tran,obj,ownerid)
			if tech==0: #no control structure
				continue
			owner = tran.db[ownerid]
			turn = tran.db[OID_UNIVERSE].turn
			minerate = int(tech.minerate * Rules.techImprEff[owner.techs.get(structtech, Rules.techBaseImprovement)])
			minenum = int(tech.minenum / Rules.techImprEff[owner.techs.get(structtech, Rules.techBaseImprovement)])
			if (turn%minerate)==0: #it is the launch turn
				self.addMine(obj,ownerid,tech.mineclass,minenum)
				log.debug('ISystem', 'Mine deployed for owner %d in system %d' % (ownerid, obj.oid))
		return obj.planets

	processPRODPhase.public = 1
	processPRODPhase.accLevel = AL_ADMIN

	def processACTIONPhase(self, tran, obj, data):
		# distribute resources
		planets = {}
		# group planets by owner
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner != OID_NONE:
				tmp = planets.get(planet.owner, [])
				tmp.append(planet)
				planets[planet.owner] = tmp
		# group planets if owners are allied
		# TODO
		# process each group
		for owner in planets.keys():
			# skip alone planets
			if len(planets[owner]) < 2:
				continue
			# process each resource
			for resName in ('Bio', 'En'):
				donors = []
				donees = []
				minRes = 'min%s' % resName
				maxRes = 'max%s' % resName
				storRes = 'stor%s' % resName
				donorsSum = 0
				doneesSum = 0
				# put planets into donors/donees
				for planet in planets[owner]:
					if getattr(planet, storRes) > getattr(planet, minRes):
						donors.append(planet)
						donorsSum += getattr(planet, storRes) - getattr(planet, minRes)
					elif getattr(planet, storRes) < getattr(planet, minRes):
						donees.append(planet)
						doneesSum += getattr(planet, minRes) - getattr(planet, storRes)
				#@log.debug('ISystem', obj.oid, 'Donors / donees for %s' % resName, donorsSum, doneesSum)
				# there are requests for donation and there is somebody able to donate
				if doneesSum > 0 and donorsSum > 0:
					#@log.debug('ISystem', 'Redistributin %s for' % resName, owner)
					# give
					balance = 0
					tmpRatio = min(float(doneesSum) / donorsSum, 1.0)
					for planet in donees:
						diff = getattr(planet, minRes) - getattr(planet, storRes)
						amount = int(float(diff) / doneesSum * donorsSum * tmpRatio)
						#@log.debug('ISystem', 'Give res', planet.oid, amount)
						balance -= amount
						setattr(planet, storRes, getattr(planet, storRes) + amount)
					# take
					assert donorsSum + balance >= 0
					lastPlanet = None
					tmpRatio = min(float(donorsSum) / doneesSum, 1.0)
					for planet in donors:
						diff = getattr(planet, storRes) - getattr(planet, minRes)
						amount = int(float(diff) / donorsSum * doneesSum * tmpRatio)
						balance += amount
						#@log.debug('ISystem', 'Take res', planet.oid, amount)
						setattr(planet, storRes, getattr(planet, storRes) - amount)
						lastPlanet = planet
					# fix rounding error
					setattr(lastPlanet, storRes, getattr(lastPlanet, storRes) + balance)
					#@log.debug('ISystem', 'Rounding error', balance)
				# try to move additional resources to the other planets
				for planet in planets[owner]:
					if getattr(planet, storRes) > getattr(planet, maxRes):
						excess = getattr(planet, storRes) - getattr(planet, maxRes)
						#@log.debug('ISystem', 'Trying to move excess rsrcs from', planet.oid, excess)
						for planet2 in planets[owner]:
							if planet == planet2:
								continue
							if getattr(planet2, storRes) < getattr(planet2, maxRes):
								space = getattr(planet2, maxRes) - getattr(planet2, storRes)
								amount = min(space, excess)
								#@log.debug('ISystem', 'Moved to', planet2.oid, amount)
								setattr(planet2, storRes, getattr(planet2, storRes) + amount)
								excess -= amount
								if excess == 0:
									break
						#@log.debug('ISystem', 'Cannot move excess rsrcs on', planet.oid, excess)
						setattr(planet, storRes, getattr(planet, maxRes) + excess)
		#~ # rotate system around the galaxy core
		#~ #log.debug("Rotate, old coords", obj.x, obj.y)
		#~ turn = tran.db[OID_UNIVERSE].turn
		#~ galaxy = tran.db[obj.compOf]
		#~ angle = obj.sAngle + (turn / Rules.rotationMod) * obj.dAngle
		#~ obj.x = galaxy.x + obj.dist * math.cos(angle)
		#~ obj.y = galaxy.y + obj.dist * math.sin(angle)
		#~ #log.debug("Rotate, new coords", obj.x, obj.y)
		#~ # change positions of planets and orbitting fleets
		#~ for planetID in obj.planets:
			#~ planet = tran.db[planetID]
			#~ planet.x = obj.x
			#~ planet.y = obj.y
		#~ for fleetID in obj.fleets:
			#~ fleet = tran.db[fleetID]
			#~ fleet.x = obj.x
			#~ fleet.y = obj.y
		# process planets and fleets
		#@log.debug("System close fleets", obj.oid, obj.closeFleets)
		return obj.planets[:] + obj.closeFleets[:]

	processACTIONPhase.public = 1
	processACTIONPhase.accLevel = AL_ADMIN

	def getObjectsInSpace(self, tran, obj):
		inSpace = obj.closeFleets[:]
		for fleetID in obj.fleets:
			try:
				inSpace.remove(fleetID)
			except ValueError:
				log.warning(obj.oid, "Cannot remove fleet from closeFleets", fleetID, obj.fleets, obj.closeFleets)
		return inSpace

	getObjectsInSpace.public = 1
	getObjectsInSpace.accLevel = AL_ADMIN
	
	def processBATTLEPhase(self, tran, obj, data):
		system = obj
		#@log.debug('ISystem', 'BATTLE - system', obj.oid)
		# we are processing fleets, planets, ...
		objects = obj.planets[:] + obj.fleets[:]
		# store owners of objects
		# find enemies and allies
		attack = {}
		allies = {}
		owners = {}
		ownerIDs = {}
		systemAtt = {}
		systemDef = {}
		hasMine = {}
		isOwnedObject = 0
		for objID in objects:
			attack[objID] = []
			allies[objID] = []
			owner = tran.db[objID].owner
			owners[objID] = owner
			ownerIDs[owner] = owner
			if owner != OID_NONE:
				isOwnedObject = 1
		for owner in ownerIDs:
			tempAtt, tempDef = self.getSystemCombatBonuses(tran,system,owner)
			systemAtt[owner] = tempAtt
			systemDef[owner] = tempDef
			hasMine[owner] = self.getSystemMineSource(tran,system,owner)
		if not isOwnedObject:
			#@log.debug('ISystem', 'No combat')
			# reset combat counters
			system.combatCounter = 0
			return
		# first - direct ones
		index = 1
		for obj1ID in objects:
			obj1 = tran.db[obj1ID]
			if obj1.owner == OID_NONE:
				index += 1
				continue
			commander = tran.db[obj1.owner]
			# relationships
			#for obj2ID in objects[index:]:
			for obj2ID in objects:
				obj2 = tran.db[obj2ID]
				if obj2.owner == OID_NONE or obj1 is obj2:
					continue
				if obj1.owner == obj2.owner:
					allies[obj1ID].append(obj2ID)
					allies[obj2ID].append(obj1ID)
					continue
				# planet and military object
				elif obj1.type == T_PLANET and obj2.isMilitary and \
					not self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_ALLOW_MILITARY_SHIPS):
					#@log.debug("ISystem pl - mil", obj1ID, obj2ID)
					if obj2ID not in attack[obj1ID]:
						attack[obj1ID].append(obj2ID)
					if obj1ID not in attack[obj2ID]:
						attack[obj2ID].append(obj1ID)
				# planet and civilian object
				elif obj1.type == T_PLANET and not obj2.isMilitary and \
					not self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_ALLOW_CIVILIAN_SHIPS):
					#@log.debug("ISystem pl - civ", obj1ID, obj2ID)
					if obj2ID not in attack[obj1ID]:
						attack[obj1ID].append(obj2ID)
					if obj1ID not in attack[obj2ID]:
						attack[obj2ID].append(obj1ID)
				# military and military object
				elif obj1.isMilitary and obj2.isMilitary and \
					not self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_ALLOW_MILITARY_SHIPS):
					#@log.debug("ISystem mil - mil", obj1ID, obj2ID)
					if obj2ID not in attack[obj1ID]:
						attack[obj1ID].append(obj2ID)
					if obj1ID not in attack[obj2ID]:
						attack[obj2ID].append(obj1ID)
				# military and civilian object
				elif obj1.isMilitary and not obj2.isMilitary and \
					not self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_ALLOW_CIVILIAN_SHIPS):
					#@log.debug("ISystem mil - civ", obj1ID, obj2ID)
					if obj2ID not in attack[obj1ID]:
						attack[obj1ID].append(obj2ID)
					if obj1ID not in attack[obj2ID]:
						attack[obj2ID].append(obj1ID)
				# planet and fleet
				#elif obj1.type == T_PLANET and obj2.type == T_FLEET and \
				#	self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_MUTUAL_DEFENCE):
				#	allies[obj1ID].append(obj2ID)
				#	allies[obj2ID].append(obj1ID)
				# fleet and fleet
				#elif obj1.type == T_FLEET and obj2.type == T_FLEET and \
				#	self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_MUTUAL_OFFENCE):
				#	allies[obj1ID].append(obj2ID)
				#	allies[obj2ID].append(obj1ID)
				# asteroid
				if obj2.type == T_ASTEROID:
					attack[obj1ID].append(obj2ID)
					attack[obj2ID].append(obj1ID)
			index += 1
		#@log.debug('ISystem', 'Targets:', targets)
		#@log.debug('ISystem', 'Allies:', allies)
		# find indirect a/e
		#for objID in objects:
		#	iTargets = []
		#	iAllies = []
		#	# find indirect a/e
		#	todo = allies[objID][:]
		#	while todo:
		#		id = todo.pop(0)
		#		iTargets.extend(targets[id])
		#		for tmpID in allies[id]:
		#			if tmpID not in iAllies:
		#				todo.append(tmpID)
		#				iAllies.append(tmpID)
		#	# remove allies from targets
		#	for id in iAllies:
		#		if id in iTargets:
		#			iTargets.remove(id)
		#	# IMPORTATNT preffer NOT to fire at possible allies
		#	# add my targets
		#	#for id in targets[objID]:
		#	#	if id not in iTargets:
		#	#		iTargets.append(id)
		#	# that's all folks
		#	for id in iTargets:
		#		if objID not in attack[id]:
		#			attack[id].append(objID)
		#		if id not in attack[objID]:
		#			attack[objID].append(id)
		# NOT VALID: objects with action ACTION_ATTACK will attack only their targets
		# check, if there are any targets
		isCombat = 0
		for objID in objects:
			if attack[objID]:
				isCombat = 1
				break #end loop
		if not isCombat:
			#@log.debug('ISystem', 'No combat')
			# reset combat counters
			system.combatCounter = 0
			for fleetID in system.fleets:
				tran.db[fleetID].combatCounter = 0
			return
		# increase combat counters
		system.combatCounter += 1
		for fleetID in system.fleets:
			tran.db[fleetID].combatCounter += 1
		# debug
		log.debug('ISystem', 'Final attacks in system %d:' % system.oid, attack)
		# mines detonate before battle
		shots = {}
		targets = {}
		firing = {}
		damageCaused = {}
		damageTaken = {}
		shipsLost = {}
		isCombat = False
		isMineCombat = False
		mineKills = 0
		for owner in ownerIDs:
			if not (owner in hasMine): #no planets
				continue
			if hasMine[owner] == 0: #no control structure
				continue
			objID = hasMine[owner]
			if len(self.getMines(system,owner))==0:
				continue #no mines, something broke
			log.debug('ISystem-Mines', 'Mines Found')
			if len(attack[objID])==0:
				continue #no targets
			fireMine = True
			mineTargets = copy.copy(attack[objID])
			while fireMine:
				while len(mineTargets) > 0:
					targetID = random.choice(mineTargets) #select random target
					targetobj = tran.db.get(targetID, None)
					try:
						if targetobj.type == T_FLEET:
							break #target found
						mineTargets.remove(targetID) #remove an object type that a mine can't hit from the temporary targets list
					except:
						mineTargets.remove(targetID) #remove a dead fleet from the temporary targets list

				if len(mineTargets) == 0:
 					break #no fleet targets for mines
				temp, temp, firing[targetID] = self.cmd(targetobj).getPreCombatData(tran, targetobj) #fix firing for "surrender to" section
				damage,att,ignoreshield = self.fireMine(system,owner)
				log.debug('ISystem-Mines', 'Mine Details (damage, att, ignore shield):',damage,att,ignoreshield)
				if not damage: #no more mines
					fireMine = False
					break
				isMineCombat = True
				#Process Combat
				dmg, destroyed = self.cmd(targetobj).applyMine(tran, targetobj, att, damage, ignoreshield)
				log.debug('ISystem-Mines', 'Actual Damage Done:',dmg)
				damageTaken[targetID] = damageTaken.get(targetID, 0) + dmg
				if destroyed > 0:
					shipsLost[targetID] = shipsLost.get(targetID, 0) + destroyed
					mineKills += destroyed
				if dmg > 0:
					damageCaused[objID] = damageCaused.get(objID, 0) + dmg
		# now to battle
		for objID in objects:
			obj = tran.db.get(objID, None)
			# get shots from object, should be sorted by weaponClass
			# shots = [ shot, ...], shot = (combatAtt, weaponID)
			# get target classes and numbers
			# (class1, class2, class3, class4)
			# cls0 == fighters, cls1 == midships, cls2 == capital ships, cls3 == planet installations
			#@log.debug(objID, obj.name, "getting pre combat data")
			if obj: # source already destroyed; ignore
				shots[objID], targets[objID], firing[objID] = self.cmd(obj).getPreCombatData(tran, obj)
				if firing[objID]:
					isCombat = True
		if not isCombat and not isMineCombat:
			# no shots has been fired
			#@log.debug('ISystem', 'No combat')
			# reset combat counters
			system.combatCounter = 0
			for fleetID in system.fleets:
				tran.db[fleetID].combatCounter = 0
			return
		#@log.debug("Shots:", shots)
		#@log.debug("Targets", targets)
		if isCombat:
			for shotIdx in (3, 2, 1, 0):
				for objID in objects:
					# obj CAN be deleted at this point
					obj = tran.db.get(objID, None)
					if obj == None:
						continue # source already destroyed; move to next source
					# if object is fleet, then it's signature is max
					if obj and obj.type == T_FLEET:
						obj.signature = Rules.maxSignature
					# target preselection
					totalClass = [0, 0, 0, 0]
					total = 0
					for targetID in attack[objID]:
						totalClass[0] += targets[targetID][0]
						totalClass[1] += targets[targetID][1]
						totalClass[2] += targets[targetID][2]
						totalClass[3] += targets[targetID][3]
					total = totalClass[0] + totalClass[1] + totalClass[2] + totalClass[3]
					# process shots
					for combatAtt, weaponID in shots[objID][shotIdx]:
						weapon = Rules.techs[weaponID]
						weaponClass = weapon.weaponClass
						if total == 0:
							# there are no targets
							break
						#@log.debug('ISystem', 'Processing shot', objID, weapon.name, weaponClass)
						# process from weaponClass up
						# never shoot on smaller ships than weaponClass
						applied = 0
						for tmpWpnClass in xrange(weaponClass, 4):
							#@log.debug('ISystem', 'Trying target class', tmpWpnClass, totalClass[tmpWpnClass])
							# select target
							if totalClass[tmpWpnClass]:
								target = Utils.rand(0, totalClass[tmpWpnClass])
								#@log.debug('ISystem', 'Target rnd num', target, totalClass[tmpWpnClass])
								for targetID in attack[objID]:
									if target < targets[targetID][tmpWpnClass]:
										#@log.debug(objID, 'attacks', targetID, tmpWpnClass)
										# targetID can be deleted at this point
										anObj = tran.db.get(targetID, None)
										if anObj:
											dmg, destroyed, destroyedClass = self.cmd(anObj).applyShot(tran, anObj, systemDef[owners[targetID]], combatAtt + systemAtt[owners[objID]], weaponID, tmpWpnClass, target)
											#@log.debug("ISystem result", dmg, destroyed, destroyedClass, tmpWpnClass)
											#@print objID, 'dmg, destroyed', dmg, destroyed
											damageTaken[targetID] = damageTaken.get(targetID, 0) + dmg
											if destroyed > 0:
												shipsLost[targetID] = shipsLost.get(targetID, 0) + destroyed
												total -= destroyed
												totalClass[destroyedClass] -= destroyed
											if dmg > 0 and obj:
												obj.combatExp += dmg
												damageCaused[objID] = damageCaused.get(objID, 0) + dmg
											applied = 1
										else:
											continue # target already destroyed, move to next target
										break
									else:
										#@log.debug('ISystem', 'Lovering target by', targets[targetID][tmpWpnClass])
										target -= targets[targetID][tmpWpnClass]
							if applied:
								break
		# send messages and modify diplomacy relations
		# distribute experience pts
		for objID in objects:
			obj = tran.db.get(objID, None)
			if obj:
				self.cmd(obj).distributeExp(tran, obj)
			if attack[objID]:
				source = obj or tran.db[owners[objID]]
				# collect players
				players = {}
				for attackerID in attack[objID]:
					players[owners[attackerID]] = None
				d1 = damageTaken.get(objID,0)
				d2 = damageCaused.get(objID,0)
				l = shipsLost.get(objID, 0)
				if d1 or d2 or l:
					# send only if damage is taken/caused
					Utils.sendMessage(tran, source, MSG_COMBAT_RESULTS, system.oid, (d1, d2, l, players.keys()))
				if not obj:
					# report DESTROYED status
					Utils.sendMessage(tran, source, MSG_DESTROYED_FLEET, system.oid, ())
				# modify diplomacy relations
				objOwner = tran.db[owners[objID]]
				for attackerID in attack[objID]:
					attOwner = tran.db.get(owners[attackerID], None)
					# owner of the fleet
					rel = self.cmd(objOwner).getDiplomacyWith(tran, objOwner, attOwner.oid)
					rel.relChng = Rules.relLostWhenAttacked
					# attacker
					rel = self.cmd(attOwner).getDiplomacyWith(tran, attOwner, objOwner.oid)
					rel.rechChng = Rules.relLostWhenAttacked
		# check if object surrenders
		for objID in objects:
			# object surrender IFF it and its allies had target and was not able
			# to fire at it, planet is not counted as ally in this case
			obj = tran.db.get(objID, None)
			if firing[objID] and obj:
				continue
			surrenderTo = []
			for attID in attack[objID]:
				if firing[attID] and tran.db.has_key(attID):
					surrenderTo.append(tran.db[attID].owner)
			for allyID in allies[objID]:
				if not tran.db.has_key(allyID):
					continue
				ally = tran.db[allyID]
				if firing[allyID] and ally.type != T_PLANET:
					surrenderTo = []
					break
			if surrenderTo:
				index = Utils.rand(0, len(surrenderTo))
				if obj:
					if self.cmd(obj).surrenderTo(tran, obj, surrenderTo[index]):
						winner = tran.db[surrenderTo[index]]
						source = tran.db.get(owners[objID], None)
						log.debug('ISystem', 'BATTLE - surrender', objID, surrenderTo[index], surrenderTo)
						if source:
							Utils.sendMessage(tran, source, MSG_COMBAT_LOST, system.oid, winner.oid)
							Utils.sendMessage(tran, winner, MSG_COMBAT_WON, system.oid, source.oid)
						else:
							Utils.sendMessage(tran, winner, MSG_COMBAT_WON, system.oid, obj.oid)
				else:
					winner = tran.db[surrenderTo[index]]
					source = tran.db[owners[objID]]
					log.debug('ISystem', 'BATTLE - surrender', objID, surrenderTo[index], surrenderTo)
					Utils.sendMessage(tran, source, MSG_COMBAT_LOST, system.oid, winner.oid)
					Utils.sendMessage(tran, winner, MSG_COMBAT_WON, system.oid, source.oid)
		return

	processBATTLEPhase.public = 1
	processBATTLEPhase.accLevel = AL_ADMIN

	def processFINALPhase(self, tran, obj, data):
		# TODO find new starting points
		# clean up mines if system ownership was lost
		owners = []
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner not in owners:
				owners.append(planet.owner)
		for ownerid in obj.minefield:
			if ownerid not in owners:
				self.removeMines(obj,ownerid)
		return obj.planets[:] + obj.closeFleets[:]

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	def cmpPlanetByEnergy(self, tran, planetID1, planetID2):
		planet1 = tran.db[planetID1]
		planet2 = tran.db[planetID2]
		return cmp(planet2.plEn, planet1.plEn)

	cmpPlanetByEnergy.public = 0

	def sortPlanets(self, tran, obj, data):
		obj.planets.sort(lambda x, y: self.cmpPlanetByEnergy(tran, x, y))
		orbit = 1
		for planetID in obj.planets:
			planet = tran.db[planetID]
			planet.orbit = orbit
			orbit += 1

	sortPlanets.public = 0

	def rename(self, tran, obj, newName, nType):
		newName = newName.strip()
		# you have to own all planets
		# TODO: Throw another cmdr exc AFTER you have no planet
		haveOne = 0
		anotherComm = 0
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner != tran.session.cid and planet.owner != OID_NONE:
				anotherComm = 1
			if planet.owner == tran.session.cid:
				haveOne = 1
		if not haveOne:
			raise GameException('You cannot change name of this system - you have no planet in this system.')
		if anotherComm:
			raise GameException('You cannot change name of this system - another commander in system.')
		# check validity of name
		if not Utils.isCorrectName(newName):
			raise GameException('Invalid name. Only characters, digits, space, dot and dash permitted, max. length is 30 characters.')
		# check if there is other system with this name
		galaxy = tran.db[obj.compOf]
		for systemID in galaxy.systems:
			if tran.db[systemID].name == newName and systemID != obj.oid:
				raise GameException('This name is already used.')
		# TODO you have to own this system longer than previous owner
		# one change per 1 day allowed
		turn = tran.db[OID_UNIVERSE].turn
		if obj.lastNameChng + Rules.turnsPerDay <= turn:
			# rename system
			obj.name = newName
			# rename planets
			newNames = [obj.name]
			for planetID in obj.planets:
				planet = tran.db[planetID]
				planet.name = Utils.getPlanetName(obj.name, nType, planet.orbit - 1)
				newNames.append(planet.name)
			obj.lastNameChng = turn
		else:
			raise GameException('You cannot change name of this system - name has been changed recently (try it one day later).')
		return newNames

	rename.public = 1
	rename.accLevel = AL_NONE

	def createPlanet(self, tran, obj):
		planet = self.new(T_PLANET)
		planet.compOf = obj.oid
		oid = tran.db.create(planet)
		obj.planets.append(oid)
		return oid

	def addMine(self,obj,ownerid,minetechid,maxnum): #add a mine for an owner
		if ownerid in obj.minefield:
			if len(obj.minefield[ownerid]) < maxnum:
				obj.minefield[ownerid].append(minetechid)
		else:
			obj.minefield[ownerid]= [minetechid]

	addMine.public = 1
	addMine.accLevel = AL_ADMIN

	def getMines(self,obj,ownerid): #get all mines of an owner
		if ownerid in obj.minefield:
			return obj.minefield[ownerid]
		else:
			return []

	getMines.public = 1
	getMines.accLevel = AL_ADMIN

	def removeMines(self,obj,ownerid): #remove all mines of an owner
		if ownerid in obj.minefield:
			obj.minefield.remove(ownerid)

	removeMines.public = 0

	def fireMine(self,obj,ownerid): #shoot the mine
		if ownerid in obj.minefield:
			mine = obj.minefield[ownerid].pop(random.randrange(0,len(obj.minefield[ownerid]))) #select a random mine to detonate
			if len(obj.minefield[ownerid]) == 0:
				obj.minefield.pop(ownerid) #delete the owner if no more mines
		else:
			return False,False,False
		tech = Rules.techs[mine]
		damage = random.randrange(tech.weaponDmgMin,tech.weaponDmgMax)
		attack = tech.weaponAtt
		ignoreshield = tech.weaponIgnoreShield
		return damage,attack,ignoreshield
		
	fireMine.public = 1
	fireMine.accLevel = AL_ADMIN

	def getSystemMineLauncher(self,tran,obj,playerID):
		launchtech = 0
		mineclass = 0
		structure = 0
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner == playerID:
				for struct in planet.slots:
					tech = Rules.techs[struct[STRUCT_IDX_TECHID]]
					if tech.mineclass > mineclass:
						if tech.mineclass > mineclass:
							mineclass = tech.mineclass
							launchtech = tech
							structure = struct[STRUCT_IDX_TECHID]
		return launchtech, structure

	getSystemMineLauncher.public = 0

	def getSystemMineSource(self,tran,obj,playerID):
		source = 0
		mineclass = 0
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner == playerID:
				for struct in planet.slots:
					tech = Rules.techs[struct[STRUCT_IDX_TECHID]]
					if tech.mineclass > mineclass:
						if tech.mineclass > mineclass:
							mineclass = tech.mineclass
							source = planetID
		return source

	getSystemMineSource.public = 0

	def getSystemCombatBonuses(self,tran,obj,playerID):
		systemAtt = 0;
		systemDef = 0;
		for planetID in obj.planets:
			planet = tran.db[planetID]
			if planet.owner == playerID:
                                for struct in planet.slots:
                                        tech = Rules.techs[struct[STRUCT_IDX_TECHID]]
                                        techEff = Utils.getTechEff(tran, struct[STRUCT_IDX_TECHID], planet.owner)
                                        if tech.systemAtt > 0 or tech.systemDef > 0:
                                                systemAtt = max(systemAtt,tech.systemAtt*techEff)
                                                systemDef = max(systemDef,tech.systemDef*techEff)
		return (systemAtt,systemDef)

	getSystemCombatBonuses.public = 0

	def loadDOMNode(self, tran, obj, xoff, yoff, node):
		obj.x = float(node.getAttribute('x')) + xoff
		obj.y = float(node.getAttribute('y')) + yoff
		orbit = 1
		nType = Utils.getPlanetNamesType()
		for elem in node.childNodes:
			if elem.nodeType == Node.ELEMENT_NODE:
				name = elem.tagName
				if name == 'properties':
					self.loadDOMAttrs(obj, elem)
				elif name == 'planet':
					# create planet
					planet = tran.db[self.createPlanet(tran, obj)]
					self.cmd(planet).loadDOMNode(tran, planet, obj.x, obj.y, orbit, elem)
					# planet.name = u'%s %s' % (obj.name, '-ABCDEFGHIJKLMNOPQRSTUVWXYZ'[orbit])
					planet.name = Utils.getPlanetName(obj.name, nType, orbit - 1)
					orbit += 1
				else:
					raise GameException('Unknown element %s' % name)
		#~ # compute rotational constants
		#~ galaxy = tran.db[obj.compOf]
		#~ dx = obj.x - galaxy.x
		#~ dy = obj.y - galaxy.y
		#~ obj.dist = math.sqrt(dx * dx + dy * dy)
		#~ if obj.dist > 0:
			#~ obj.dAngle = math.sqrt(galaxy.centerWeight / obj.dist) / obj.dist
		#~ else:
			#~ obj.dAngle = 0.0
		#~ if dx != 0:
			#~ obj.sAngle = math.atan(dy / dx)
			#~ if dx < 0: obj.sAngle += math.pi
		#~ elif dy > 0:
			#~ obj.sAngle = math.pi / 2
		#~ elif dx < 0:
			#~ obj.sAngle = math.pi * 3 / 2
		#~ # this is a check only
		#~ angle = obj.sAngle + (0 / 384.0) * obj.dAngle
		#~ x = galaxy.x + obj.dist * math.cos(angle)
		#~ y = galaxy.y + obj.dist * math.sin(angle)
		#~ if x != obj.x or y != obj.y:
			#~ log.warning(obj.name, obj.x, obj.y, dx, dy, obj.dist, obj.dAngle, obj.sAngle, x, y)
		return SUCC

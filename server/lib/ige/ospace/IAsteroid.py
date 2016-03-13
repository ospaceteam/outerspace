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

from IFleet import IFleet
from IPlanet import IPlanet
from Const import *
from ige.IDataHolder import IDataHolder
import Rules
import math
import Utils
from ige import GameException, log

class IAsteroid(IFleet):

	typeID = T_ASTEROID

	def init(self, obj):
		IFleet.init(self, obj)
		# other attrs
		obj.asDiameter = 0 # diameter
		obj.asHP = 0
		obj.impactDelay = 0
		obj.target = OID_NONE

	def create(self, tran, obj, x, y, targetID, speed, hp):
		obj.signature = hp / 50
		obj.x = x
		obj.y = y
		obj.oldX = x
		obj.oldY = y
		obj.maxSpeed = speed
		obj.speed = speed
		obj.asDiameter = max(1, hp / 10)
		obj.asHP = hp
		obj.target = targetID
		obj.owner = OID_NATURE
		nature = tran.db[OID_NATURE]
		nature.fleets.append(obj.oid)
		# create name
		counter = 1
		fleets = nature.fleets
		while fleets:
			name = u'Asteroid %d' % counter
			counter += 1
			foundSame = 0
			for fleetID in fleets:
				if tran.db[fleetID].name == name:
					foundSame = 1
					break
			if not foundSame:
				break
		obj.name = name
		# register with target system
		system = tran.db[tran.db[targetID].compOf]
		system.closeFleets.append(obj.oid)
		obj.closeSystem = system.oid
		# create script
		self.cmd(obj).addAction(tran, obj, 0, FLACTION_MOVE, targetID, None)
		#
		log.debug("Asteroid created", x, y, targetID, speed, hp)

	create.public = 1
	create.accLevel = AL_ADMIN

	def update(self, tran, obj):
		if obj.impactDelay > Rules.asteroidImpactDelay:
			# delete me
			self.cmd(obj).disbandFleet(tran, obj)
			return
		# closest system
		if not hasattr(obj, "closeSystem") or not tran.db.has_key(obj.closeSystem):
			if obj.orbiting == OID_NONE:
				log.warning("No close system for asteroid", obj.oid)
				# select any system
				systemID = tran.db[tran.db[OID_UNIVERSE].galaxies[0]].systems[0]
				obj.closeSystem = systemID
			else:
				obj.closeSystem = obj.orbiting
				system = tran.db[obj.closeSystem]
				if system.type == T_SYSTEM:
					if obj.oid not in system.closeFleets:
						system.closeFleets.append(obj.oid)
				else:
					log.debug("IAsteroid - invalid orbiting", obj.orbiting)
					self.cmd(obj).disbandFleet(tran, obj)
					return
		# verify close system
		if tran.db.has_key(obj.closeSystem):
			system = tran.db[obj.closeSystem]
			if system.type == T_SYSTEM:
				if obj.oid not in system.closeFleets:
					#@log.debug("Adding fleet", obj.oid, "into closeFleets", system.oid)
					system.closeFleets.append(obj.oid)
			else:
				obj.closeSystem = OID_NONE
		else:
			obj.closeSystem = OID_NONE

	update.public = 0

	def recordScanLevel(self, tran, obj, scanPwr, player, contactType):
		if obj.owner == player.oid:
			log.warning("Scan on own asteroid!", obj.oid)
			return
		if scanPwr >= Rules.level1InfoScanPwr:
			self.cmd(player).addObjectToMap(tran, player, obj, scanPwr, CONTACT_NONE)

	def getScanInfo(self, tran, obj, scanPwr):
		result = IDataHolder()
		result._type = T_SCAN
		result.scanPwr = scanPwr
		if scanPwr > Rules.level1InfoScanPwr:
			result.oid = obj.oid
			result.x = obj.x
			result.y = obj.y
			result.oldX = obj.oldX
			result.oldY = obj.oldY
			result.signature = obj.signature
			result.type = obj.type
			result.orbiting = obj.orbiting
			result.speed = obj.speed
			result.eta = obj.eta
		if scanPwr > Rules.level2InfoScanPwr:
			result.name = obj.name
		if scanPwr > Rules.level3InfoScanPwr:
			result.asDiameter = obj.asDiameter
			result.asHP = obj.asHP
		if scanPwr > Rules.level4InfoScanPwr:
			pass
		return result

	def processACTIONPhase(self, tran, obj, data):
		# ACTIONS
		if Utils.isIdleFleet(obj):
			#@log.debug('IAsteroid', obj.oid, 'idle')
			obj.impactDelay += 1
			return
		action, target, actionData = obj.actions[obj.actionIndex]
		#@log.debug('IAsteroid', obj.oid, 'processing action', action)
		if action == FLACTION_MOVE:
			if self.cmd(obj).moveToTarget(tran, obj, target):
				# we are there
				obj.actionIndex += 1
		else:
			raise GameException('Unsupported action %d' % action)

	processACTIONPhase.public = 1
	processACTIONPhase.accLevel = AL_ADMIN

	def processFINALPhase(self, tran, obj, data):
		if obj.impactDelay > Rules.asteroidImpactDelay:
			# delete me
			self.cmd(obj).disbandFleet(tran, obj)

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	##
	## Combat related functions
	##

	def getPreCombatData(self, tran, obj):
		if obj.impactDelay > Rules.asteroidImpactDelay:
			# modify target's environment and minerals
			planet = tran.db[obj.target]
			#planet.plBio = max(0, int(planet.plBio + obj.asHP * Rules.asteroidPerHPBioMod))
			#planet.plMin = min(200, int(planet.plMin + obj.asHP * Rules.asteroidPerHPMinMod))
			# special shots from asteroid
			hp = obj.asHP
			shots = []
			if hp > 1500:
				shots.append((Rules.asteroidAttack, Rules.Tech.ASTEROID1000))
				hp = hp % 1000
			if hp > 150:
				shots.append((Rules.asteroidAttack, Rules.Tech.ASTEROID100))
				hp = hp % 100
			if hp > 15:
				shots.append((Rules.asteroidAttack, Rules.Tech.ASTEROID10))
				hp = hp % 10
			if hp > 1:
				shots.append((Rules.asteroidAttack, Rules.Tech.ASTEROID1))
			# destroy asteroid
			self.cmd(obj).disbandFleet(tran, obj)
			return shots, [0, 0, 0, 1]
		else:
			obj.impactDelay += 1
			log.debug("Asteroid impact delay", obj.impactDelay)
			return [], [0, 0, 0, 1]

	getPreCombatData.public = 0

	def applyShot(self, tran, obj, attack, weaponID, targetClass, target):
		#@log.debug('IAsteroid', 'Apply shot', attack, weaponID, attack, cClass, count)
		# compute if asteroid has been hit
		weapon = Rules.techs[weaponID]
		if weapon.weaponIsMissile:
			defense = Rules.asteroidMisDef
		else:
			defense = Rules.asteroidDef
		destroyed = 0
		dmg = 0
		if Utils.rand(1, attack + defense + 1) > defense:
			# hit
			dmg = Utils.rand(weapon.weaponDmgMin, weapon.weaponDmgMax + 1)
			obj.asHP -= dmg
			if obj.asHP <= 0:
				destroyed = 1
				# destroy asteroid
				self.cmd(obj).disbandFleet(tran, obj)
		#@log.debug('IAsteroid', 'Shot applied', dmg, destroyed)
		return dmg, destroyed, 3

	applyShot.public = 0

	def addExp(self, tran, obj, shipTechID, dmg):
		pass

	addExp.public = 0

	def surrenderTo(self, tran, obj, newOwnerID):
		# never surrender
		return 0

	surrenderTo.public = 0

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
from Const import *
from ige.IDataHolder import IDataHolder
import Rules
import math
import random
import Utils, ShipUtils, math, copy
from sys import maxint
from ige import GameException, ServerException, log

class IFleet(IObject):

	typeID = T_FLEET

	def init(self, obj):
		IObject.init(self, obj)
		#
		obj.x = 0.0
		obj.y = 0.0
		obj.oldX = 0.0
		obj.oldY = 0.0
		obj.orbiting = OID_NONE
		obj.closeSystem = OID_NONE
		obj.speed = 0.0
		obj.maxSpeed = 0.0
		obj.signature = 0
		obj.eta = 0.0
		obj.target = OID_NONE
		#
		obj.operEn = 0
		obj.storEn = 0
		obj.maxEn = 0
		obj.operProd = 0.0
		obj.ships = []
		# action
		obj.actions = []
		obj.actionIndex = 0
		obj.actionWaitCounter = 1
		#
		obj.speedBoost = 1.0
		obj.combatPwr = 0
		obj.isMilitary = 0
		obj.scannerPwr = 0
		obj.origScannerPwr = 0
		obj.scannerOn = True
		obj.combatExp = 0
		obj.combatCounter = 0
		obj.combatRetreatWait = 0
		obj.lastUpgrade = 0

	def create(self, tran, obj, refObj, owner):
		obj.owner = owner
		obj.x = refObj.x
		obj.y = refObj.y
		if refObj.type == T_SYSTEM:
			obj.orbiting = refObj.oid
			obj.closeSystem = refObj.oid
			refObj.fleets.append(obj.oid)
			refObj.closeFleets.append(obj.oid)
			obj.target = OID_NONE
		elif refObj.type == T_FLEET:
			obj.oldX = refObj.oldX
			obj.oldY = refObj.oldY
			obj.orbiting = OID_NONE
			obj.closeSystem = refObj.closeSystem
			obj.actions = copy.deepcopy(refObj.actions)
			obj.actionIndex = refObj.actionIndex
			obj.actionWaitCounter = refObj.actionWaitCounter
			system = tran.db[obj.closeSystem]
			system.closeFleets.append(obj.oid)
			obj.target = refObj.target
		# collect used names
		names = {}
		for fleetID in tran.db[owner].fleets:
			names[tran.db[fleetID].name] = None
		# create name
		counter = 1
		name = u'Fleet %d' % counter
		while True:
			name = u'Fleet %d' % counter
			counter += 1
			if name not in names:
				break
		obj.name = name
		# insert fleet into owner's fleets
		tran.db[obj.owner].fleets.append(obj.oid)

	create.public = 0
	create.accLevel = AL_ADMIN

	def addNewShip(self, tran, obj, designID):
		spec = tran.db[obj.owner].shipDesigns[designID]
		obj.ships.append([designID, spec.maxHP, spec.shieldHP, 0])
		# new ship has full tanks
		obj.storEn += spec.storEn
		# update fleet info
		self.cmd(obj).update(tran, obj)

	addNewShip.public = 0

	def removeShips(self, tran, obj, ships):
		for ship in ships:
			obj.ships.remove(ship)
		if not obj.ships:
			log.debug('IFleet', 'removeShips removed last ship')
			self.cmd(obj).disbandFleet(tran, obj)
		else:
			self.cmd(obj).update(tran, obj)
		return obj

	removeShips.public = 1
	removeShips.accLevel = AL_OWNER

	def deleteDesign(self, tran, obj, designID):
		# remove design
		obj.ships = [ship for ship in obj.ships if ship[0] != designID]
		self.cmd(obj).update(tran, obj)

	deleteDesign.public = 0


	def disbandFleet(self, tran, obj):
		log.debug('IFleet', 'disbanding fleet', obj.oid, 'of player', obj.owner)
		# remove from player's fleets
		try:
			if obj.owner != OID_NONE:
				tran.db[obj.owner].fleets.remove(obj.oid)
		except Exception:
			log.warning('IFleet', 'disbandFleet: cannot remove fleet from owner\'s fleet')
			pass
		# remove from orbit
		# remove from index if necessary
		if obj.orbiting != OID_NONE:
			try:
				if tran.db.has_key(obj.orbiting):
					tran.db[obj.orbiting].fleets.remove(obj.oid)
			except Exception:
				log.warning('IFleet', 'disbandFleet: cannot remove fleet from system.')
				pass
		# remove from close fleets
		if obj.closeSystem != OID_NONE:
			try:
				if tran.db.has_key(obj.closeSystem):
					tran.db[obj.closeSystem].closeFleets.remove(obj.oid)
			except Exception:
				log.warning("IFleet", "disbandFleet: cannot remove fleet from the close system.")
		# delete from database
		try:
			tran.db.delete(obj.oid)
		except KeyError:
			log.warning('IFleet', 'disbandFleet: cannot remove fleet from database.')

	disbandFleet.public = 1
	disbandFleet.accLevel = AL_FULL

	def joinFleet(self, tran, obj, fleetID):
		if obj.orbiting == OID_NONE:
			# we are in space
			return
		if fleetID == OID_NONE:
			# find suitable fleet
			system = tran.db[obj.orbiting]
			player = tran.db[obj.owner]
			for tmpID in system.fleets:
				if tmpID == obj.oid:
					continue
				fleet = tran.db[tmpID]
				rel = self.cmd(player).getRelationTo(tran, player, fleet.owner)
				if rel == REL_UNITY and Utils.isIdleFleet(fleet):
					fleetID = tmpID
					break
		if fleetID == OID_NONE:
			return
		# join to selected fleet
		fleet = tran.db[fleetID]
		fleet.ships.extend(obj.ships)
		# transfer resources
		fleet.storEn += obj.storEn
		# update fleet's data
		self.cmd(fleet).update(tran, fleet)
		# disband this fleet
		log.debug(obj.oid, 'FLEET joinFleet, removing old fleet')
		self.cmd(obj).disbandFleet(tran, obj)

	joinFleet.public = 1
	joinFleet.accLevel = AL_FULL

	def splitFleet(self, tran, obj, ships, mEn):
		if not len(ships):
			raise GameException('No ships in the new fleet.')
		if len(ships) == len(obj.ships):
			raise GameException('No ships in the original fleet.')
		# check ships
		tmpShips = obj.ships[:]
		for ship in ships:
			if ship not in tmpShips:
				raise GameException("No such ship(s) in the original fleet.")
			tmpShips.remove(ship)
		# create new fleet
		fleet = self.new(T_FLEET)
		tran.db.create(fleet)
		log.debug(obj.oid, "FLEET -- split fleet, new fleet is", fleet.oid)
		if obj.orbiting != OID_NONE:
			refObj = tran.db[obj.orbiting]
		else:
			refObj = obj
		self.cmd(fleet).create(tran, fleet, refObj, obj.owner)
		# move ships
		for ship in ships:
			# use server data
			idx = obj.ships.index(ship)
			ship = obj.ships.pop(idx)
			fleet.ships.append(ship)
		# update fleet
		self.cmd(fleet).update(tran, fleet)
		# move en
		move = max(min(mEn, fleet.maxEn, obj.storEn), 0)
		fleet.storEn += move
		obj.storEn -= move
		# share speed boost
		fleet.speedBoost = obj.speedBoost
		# update fleets
		self.cmd(obj).update(tran, obj)
		self.cmd(fleet).update(tran, fleet)
		# return new fleet, old fleet and player's fleets
		return fleet, obj, tran.db[obj.owner].fleets

	splitFleet.public = 1
	splitFleet.accLevel = AL_FULL

	def update(self, tran, obj):
		# if there are no ships -> disband fleet
		if not len(obj.ships) or obj.owner == OID_NONE:
			log.warning(obj.oid, "FLEET - no ships in the fleet -- disbanding")
			self.cmd(obj).disbandFleet(tran, obj)
			return
		# check for duplicates (TODO: remove me, bug was fixed)
		#for ship1 in obj.ships:
		#	duplicates = 0
		#	for ship2 in obj.ships:
		#		if ship1 is ship2:
		#			duplicates += 1
		#	if duplicates != 1:
		#		# regenerate ships
		#		newShips = []
		#		for designID, hp, shield, exp in obj.ships:
		#			newShips.append([designID, hp, shield, exp])
		#		obj.ships = newShips
		#		raise ServerException("Ship duplicates in %s" % obj)
		#
		obj.origScannerPwr = 0
		obj.operEn = 0
		obj.operProd = 0.0
		obj.maxEn = 0
		obj.maxSpeed = 999999.9
		obj.combatPwr = 0
		obj.isMilitary = 0
		#ships = {}
		# find
		player = tran.db.get(obj.owner, None)
		if not player or player.type not in PLAYER_TYPES or obj.oid not in player.fleets:
			# disband fleet when owner is invalid
			log.warning(obj.oid, "Disbanding fleet - invalid owner", obj)
			self.cmd(obj).disbandFleet(tran, obj)
			return
		obj.signature = 0
		remove = []
		idx = 0
		for designID, hp, shield, exp in obj.ships:
			if designID in player.shipDesigns:
				tech = player.shipDesigns[designID]
				obj.origScannerPwr = max(tech.scannerPwr, obj.origScannerPwr)
				obj.operEn += tech.operEn
				obj.operProd += tech.buildProd * Rules.operProdRatio
				obj.maxEn += tech.storEn
				obj.maxSpeed = min(obj.maxSpeed, tech.speed)
				obj.signature += tech.signature
				obj.combatPwr += int(tech.combatPwr * float(hp + shield) / (tech.maxHP + tech.shieldHP))
				obj.isMilitary = obj.isMilitary or tech.isMilitary
				#ships[tech.signature] = ships.get(tech.signature, 0) + 1
				if obj.ships[idx][1] > tech.maxHP:
					log.debug(obj.oid, "Too high maxHP for ship, player", obj.owner)
					obj.ships[idx][1] = min(obj.ships[idx][1], tech.maxHP)
			else:
				# TODO track this problem
				log.warning("Player has not this designID", player.oid, designID)
				remove.append([designID, hp, shield, exp])
			idx += 1
		# delete ships intended for removal
		for shipSpec in remove:
			obj.ships.remove(shipSpec)
		# misc
		obj.signature = min(obj.signature, Rules.maxSignature)
		obj.signature = max(obj.signature,1) #require fleet signature to be at least 1 now that we removed that from a per-ship basis
		obj.speed = obj.maxSpeed
		# storage
		obj.storEn = min(obj.storEn, obj.maxEn)
		# sort ships by HPs
		# TODO: remove obj.ships.sort(lambda a, b: cmp(a[1], b[1]))
		obj.ships = ShipUtils.sortShips(obj.ships)
		# closest system
		if not tran.db.has_key(obj.closeSystem) or tran.db[obj.closeSystem].type not in (T_SYSTEM, T_WORMHOLE):
			if obj.orbiting == OID_NONE:
				log.debug("No close system for fleet", obj.oid)
				# select any system
				systemID = tran.db[tran.db[OID_UNIVERSE].galaxies[0]].systems[0]
				obj.closeSystem = systemID
				log.debug(obj.oid, "Setting NULL close system to", systemID)
			else:
				log.debug(obj.oid, "Generating close system from orbiting", obj.orbiting)
				obj.closeSystem = obj.orbiting
			system = tran.db[obj.closeSystem]
			if obj.oid not in system.closeFleets:
				system.closeFleets.append(obj.oid)
		# verify close system
		if tran.db.has_key(obj.closeSystem):
			system = tran.db[obj.closeSystem]
			if system.type in (T_SYSTEM, T_WORMHOLE):
				if obj.oid not in system.closeFleets:
					log.debug("Adding fleet", obj.oid, "into closeFleets of", system.oid)
					system.closeFleets.append(obj.oid)
			else:
				log.debug(obj.oid, "Close system is not a system")
				obj.closeSystem = OID_NONE
		else:
			log.debug(obj.oid, "Close system does not exists")
			obj.closeSystem = OID_NONE
		# compute scanner pwr
		if obj.closeSystem:
				system = tran.db[obj.closeSystem]
				emrLevel = tran.db[system.compOf].emrLevel
				obj.scannerPwr = int(obj.origScannerPwr * (2.0 - emrLevel))
		# replace obsolete commands
		for actionTuple in obj.actions[:]:
			try:
				action, target, actionData = actionTuple
			except:
				log.warning(obj.oid, "Removing action", actionTuple)
				obj.actions.remove(actionTuple)
		index = 0
		for action, target, actionData in obj.actions:
			if action >= 2 and action <= 100:
				# this is an old action -> replace it by move command if available
				if target != OID_NONE:
					log.debug(obj.oid, "Replacing action", action, "by action MOVE")
					obj.actions[index][0] = FLACTION_MOVE
				else:
					# replace by none action
					log.debug(obj.oid, "Replacing action", action, "by action NONE")
					obj.actions[index] = (FLACTION_NONE, None, None)
			if action == FLACTION_DEPLOY and actionData not in player.shipDesigns:
				# deployment of scrapped ship
				log.debug(obj.oid, "invalid ship to deploy")
				obj.actions[index] = (FLACTION_NONE, None, None)
			index += 1

	update.public = 0

	def getScanInfos(self, tran, obj, scanPwr, player):
		if obj.owner == player.oid:
			return []
		if scanPwr >= Rules.level1InfoScanPwr:
			result = IDataHolder()
			result._type = T_SCAN
			result.scanPwr = scanPwr
			result.oid = obj.oid
			result.x = obj.x
			result.y = obj.y
			result.oldX = obj.oldX
			result.oldY = obj.oldY
			result.eta = obj.eta
			result.signature = obj.signature
			result.type = obj.type
			result.orbiting = obj.orbiting
			if obj.orbiting == OID_NONE and obj.actionIndex < len(obj.actions):
				target = obj.actions[obj.actionIndex][1]
				targetObj = tran.db[target]
				if targetObj.type == T_PLANET:
					result.target = targetObj.compOf
				else:
					result.target = target
		else:
			return []
		if scanPwr >= Rules.level2InfoScanPwr:
			result.name = obj.name
			result.owner = obj.owner
		if scanPwr >= Rules.level3InfoScanPwr:
			result.isMilitary = obj.isMilitary
			result.combatPwr = obj.combatPwr
		if scanPwr >= Rules.level4InfoScanPwr:
			# provide less information
			result.shipScan = {}
			owner = tran.db[obj.owner]
			for designID, hp, shield, exp in obj.ships:
				tech = owner.shipDesigns[designID]
				key = tech.name, tech.combatClass, tech.isMilitary
				result.shipScan[key] = result.shipScan.get(key, 0) + 1
		if scanPwr >= Rules.partnerScanPwr:
			result.scannerPwr = obj.scannerPwr
		return [result]

	def addAction(self, tran, obj, index, action, targetID, aData):
		# check if target is valid
		if action == FLACTION_REDIRECT:
			if targetID != OID_NONE:
				raise GameException("This command has no target.")
		elif action == FLACTION_WAIT or action == FLACTION_REPEATFROM:
			if targetID != OID_NONE:
				raise GameException("This command has no target.")
			aData = int(aData)
			if aData < 0:
				raise GameException("Number equal or larger than 1 must be specified.")
		elif action == FLACTION_DECLAREWAR:
			if targetID != OID_NONE:
				raise GameException("This command has no target.")
			if aData == OID_NONE or aData == obj.owner:
				raise GameException("Invalid commander.")
		else:
			target = tran.db[targetID]
			if target.type not in (T_SYSTEM, T_WORMHOLE, T_PLANET):
				raise GameException('Can target wormholes, systems or planets only.')
			if action == FLACTION_ENTERWORMHOLE and target.type != T_WORMHOLE:
                                raise GameException('Can only traverse wormholes.')
			if action == FLACTION_DEPLOY and target.type != T_PLANET:
				raise GameException('Can build on/colonize planets only.')
			if len(obj.actions) + 1 > Rules.maxCmdQueueLen:
				raise GameException('Too many commands in the queue.')
		obj.actions.insert(index, (action, targetID, aData))
		if index <= obj.actionIndex:
			obj.actionIndex += 1
		if obj.actionIndex >= len(obj.actions) or obj.actionIndex < 0:
			obj.actionIndex = min(index, len(obj.actions) - 1)
		return obj.actions, obj.actionIndex

	addAction.public = 1
	addAction.accLevel = AL_FULL

	def deleteAction(self, tran, obj, index):
		if index >= len(obj.actions) or index < 0:
			raise GameException('Index out of bounds.')
		if index == obj.actionIndex and obj.orbiting == OID_NONE:
			if obj.actions[index][0] == FLACTION_MOVE:
				raise GameException('Move command in progress cannot be deleted.')
			else:
				# convert action to the move command
				action, targetID, aData = obj.actions[index]
				obj.actions[index] = (FLACTION_MOVE, targetID, aData)
				return obj.actions, obj.actionIndex
		if index == obj.actionIndex and obj.actions[index][0] == FLACTION_WAIT:
			# reset wait counters
			obj.actionWaitCounter = 1
		del obj.actions[index]
		if index <= obj.actionIndex and obj.actionIndex > 0:
			obj.actionIndex -= 1
		return obj.actions, obj.actionIndex

	deleteAction.public = 1
	deleteAction.accLevel = AL_FULL

	def setActionIndex(self, tran, obj, index):
		if index >= len(obj.actions) or index < 0:
			raise GameException('Index out of bounds.')
		if obj.orbiting == OID_NONE:
			raise GameException('Move command in progress cannot be changed.')
		obj.actionIndex = index
		return obj.actionIndex

	setActionIndex.public = 1
	setActionIndex.accLevel = AL_FULL

	def moveAction(self, tran, fleet, index, rel):
		if index >= len(fleet.actions):
			raise GameException('No such item in the command list.')
		if index + rel < 0 or index + rel >= len(fleet.actions):
			raise GameException('Cannot move.')
		if index == fleet.actionIndex:
			raise GameException('Cannot move active command.')
		if index < fleet.actionIndex:
			raise GameException('Cannot move processed command.')
		if index + rel <= fleet.actionIndex:
			raise GameException('Cannot move before active command.')
		action = fleet.actions[index]
		del fleet.actions[index]
		fleet.actions.insert(index + rel, action)
		return fleet.actions

	moveAction.public = 1
	moveAction.accLevel = AL_FULL

	def clearProcessedActions(self, tran, fleet):
		if fleet.actionIndex <= 0:
			return (fleet.actions, fleet.actionIndex)
		
		for actionIdx in range(0, fleet.actionIndex):
			del fleet.actions[0]
		
		fleet.actionIndex = 0
		
		return (fleet.actions, fleet.actionIndex)
	
	clearProcessedActions.public = 1
	clearProcessedActions.accLevel = AL_FULL

	def processACTIONPhase(self, tran, obj, data):
		#@log.debug("Fleet", obj.oid, "ACTION")
		# update fleet data
		self.cmd(obj).update(tran, obj)
		# consume support
		if obj.storEn >= obj.operEn:
			obj.storEn -= obj.operEn
			# refuel
			refuelled = self.cmd(obj).refuelAndRepairAndRecharge(tran, obj)
		else:
			# try to refuel fleet
			refuelled = self.cmd(obj).refuelAndRepairAndRecharge(tran, obj)
			# there is not enought support -> damage ships
			log.debug('IFleet', 'No support - damaging ships in fleet', obj.oid)
			index = 0
			player = tran.db[obj.owner]
			destroyed = []
			for designID, hp, shield, exp in obj.ships:
				spec = player.shipDesigns[designID]
				operEn = spec.operEn
				if obj.storEn >= spec.operEn:
					#@log.debug('IFleet', 'Ship SUPPORT OK', shipTechID)
					obj.storEn -= spec.operEn
				elif obj.storEn > 0:
					# consume remaining fuel
					obj.storEn = 0
				else:
					# apply damage
					dmg = max(int(spec.maxHP * Rules.shipDecayRatio), 1)
					if dmg >= hp:
						destroyed.append(obj.ships[index])
					else:
						obj.ships[index][SHIP_IDX_HP] -= dmg
				index += 1
			self.cmd(obj).removeShips(tran, obj, destroyed)
			# if fleet has been destroyed -> abort action processing
			if not tran.db.has_key(obj.oid):
				log.debug('IFleet', obj.oid, 'fleet destroyed')
				return
		# upgrade ships
		if obj.orbiting != OID_NONE:
			# autoRepair is part fo serviceShips
			self.cmd(obj).serviceShips(tran, obj)
			# record scanner into system scanner overview
			system = tran.db[obj.orbiting]
			system.scannerPwrs[obj.owner] = max(obj.scannerPwr, system.scannerPwrs.get(obj.owner, 0))
		# ACTIONS
		if Utils.isIdleFleet(obj):
			#@log.debug('IFleet', obj.oid, 'fleet idle')
			# reset retreat counter
			obj.combatRetreatWait = 0
			# there is nothing to do - try to join other fleets
			self.cmd(obj).joinFleet(tran, obj, OID_NONE)
			return
		#@log.debug('IFleet', obj.oid, 'processing action', action)
		while not Utils.isIdleFleet(obj):
			action, target, actionData = obj.actions[obj.actionIndex]
			if action == FLACTION_NONE:
				obj.actionIndex += 1
			elif action == FLACTION_DEPLOY:
				if self.cmd(obj).actionDeploy(tran, obj):
					obj.actionIndex += 1
				break
			elif action == FLACTION_WAIT:
				if obj.actionWaitCounter >= actionData:
					obj.actionWaitCounter = 1
					obj.actionIndex += 1
				else:
					obj.actionWaitCounter += 1
				break #wait should wait, not let move; deindented this to act for completed waits also --RC
			elif action == FLACTION_MOVE:
				if self.cmd(obj).moveToTarget(tran, obj, target):
					# we are there
					obj.actionIndex += 1
				break
			elif action == FLACTION_ENTERWORMHOLE:
				if self.cmd(obj).moveToWormhole(tran, obj, target):
					# we are there
					obj.actionIndex += 1
				break
			elif action == FLACTION_DECLAREWAR:
				# switch off pact allow military ships
				player = tran.db[obj.owner]
				self.cmd(player).changePactCond(tran, player, actionData,
					PACT_ALLOW_MILITARY_SHIPS, PACT_OFF, [PACT_ALLOW_MILITARY_SHIPS])
				# next action
				obj.actionIndex +=1
			elif action == FLACTION_REFUEL:
				# check current refuel level
				if self.cmd(obj).moveToTarget(tran, obj, target) and refuelled:
					# next action
					obj.actionIndex += 1
				else:
					break
			elif action == FLACTION_REDIRECT:
				# ok, let's do some magic
				if self.cmd(obj).actionRedirect(tran, obj, refuelled):
					obj.actionIndex += 1
				else:
					break
			elif action == FLACTION_REPEATFROM:
				log.debug(obj.oid, "Setting action index to", data)
				if actionData != None:
					obj.actionIndex = actionData
				else:
					obj.actionIndex += 1
				break # TODO fix me
			else:
				raise GameException('Unsupported action %d' % action)
				break
		# it there is nothing to do -> join other idle fleets
		# the fleet could joined with another fleet
		if tran.db.has_key(obj.oid) and Utils.isIdleFleet(obj):
			# reset retreat counter
			obj.combatRetreatWait = 0
			# try to join some fleet
			self.cmd(obj).joinFleet(tran, obj, OID_NONE)

	processACTIONPhase.public = 1
	processACTIONPhase.accLevel = AL_ADMIN

	def actionRedirect(self, tran, obj, refuelled):
		if obj.orbiting != OID_NONE:
			# try to find fleet with the redirect command (<10 ships)
			# and join it
			system = tran.db[obj.orbiting]
			for fleetID in system.fleets:
				fleet = tran.db[fleetID]
				if fleet.owner != obj.owner or obj.oid == fleetID:
					continue
				if Utils.isIdleFleet(fleet):
					continue
				action, target, actionData = fleet.actions[fleet.actionIndex]
				# same command, less than 20 ships in the resulting fleet
				if action == FLACTION_REDIRECT and len(fleet.ships) + len(obj.ships) <= 20:
					# join it
					log.debug("JOINING", obj.oid, fleetID)
					self.cmd(obj).joinFleet(tran, obj, fleetID)
					# "join" targets
					fleet.actions[fleet.actionIndex] = (
						action,
						max(obj.actions[obj.actionIndex][1], target),
						actionData,
					)
					return 0
		# move?
		action, target, actionData = obj.actions[obj.actionIndex]
		if obj.orbiting == OID_NONE or target != OID_NONE:
			# ok, the target was already selected
			if not self.cmd(obj).moveToTarget(tran, obj, target):
				# keep moving
				return 0
		# we are in the system - delete target
		obj.actions[obj.actionIndex] = (action, OID_NONE, actionData)
		# check if current system has a redirection
		player = tran.db[obj.owner]
		if obj.orbiting not in player.shipRedirections:
			# there is no redirection, we are done
			return 1
		# select a new target if tanks are full
		# departure every 6th turn
		turn = tran.db[OID_UNIVERSE].turn
		if refuelled and turn % 6 == 0:
			obj.actions[obj.actionIndex] = (action, player.shipRedirections[obj.orbiting], actionData)
		return 0

		# old code
		# check if current system has any redirection
		player = tran.db[obj.owner]
		if obj.orbiting not in player.shipRedirections:
			return 1
		# form new command queue
		obj.actions = [
			[FLACTION_REFUEL, player.shipRedirections[obj.orbiting], None],
			[FLACTION_REDIRECT, OID_NONE, None],
		]
		obj.actionIndex = 0
		return 0

	actionRedirect.public = 0

	def actionDeploy(self, tran, obj):
		action, target, actionData = obj.actions[obj.actionIndex]
		if not self.cmd(obj).moveToTarget(tran, obj, target):
			return 0
		# deploy ship
		log.debug('IFleet', 'Deploying on planet - tech', actionData)
		planet = tran.db[target]
		player = tran.db[obj.owner]
		# find ship containing specified building
		for designID, hp, shield, exp in obj.ships:
			tech = player.shipDesigns[designID]
			if designID == actionData:
				removeShip = 0
				for deployHandlerID in tech.deployHandlers: #do handlers first so that structures can deploy on new planets
					if not (type(deployHandlerID) in (str,int,long)): #just a double check...
					    continue
					if not deployHandlerID.isdigit():
                                            continue
					log.debug('IFleet -', 'Attempting deploy of',deployHandlerID)
					try:
					    deployHandlerID = int(deployHandlerID) #just a double check...
					except:
					    log.warning('IFleet -','Deployment failed: NAN')
					    continue
					deployHandler = Rules.techs[deployHandlerID]
					if deployHandler.deployHandlerValidator(tran, obj, planet, deployHandler):
					       try:
						      deployHandler.deployHandlerFunction(tran, obj, planet, deployHandler)
						      Utils.sendMessage(tran, obj, MSG_DELOY_HANDLER, planet.oid, deployHandlerID)
						      removeShip = 1
					       except GameException, e:
						      log.warning('IFleet -','Deploy handler error - internal error')
						      Utils.sendMessage(tran, obj, MSG_CANNOTBUILD_SHLOST, planet.oid, None)
					else:
					       log.debug('IFleet -', 'Deploy handler - validation failed')
					       Utils.sendMessage(tran, obj, MSG_CANNOTBUILD_SHLOST, planet.oid, None)
					    
				for structTechID in tech.deployStructs:
					if not (type(structTechID) in (int,long)): #just a double check...
					    continue
					structTech = Rules.techs[structTechID]
					# validate
					if structTech.validateConstrHandler(tran, obj, planet, structTech):
						# build it
						if len(planet.slots) < planet.plSlots:
							try:
								structTech.finishConstrHandler(tran, obj, planet, structTech)
								planet.slots.insert(0, Utils.newStructure(tran, structTechID, obj.owner))
								removeShip = 1
								Utils.sendMessage(tran, obj, MSG_COMPLETED_STRUCTURE, planet.oid, structTech.id)
							except GameException, e:
								# cannot build (planet already occupied?)
								log.warning('IFleet -', 'Build on planet - cannot complete')
								Utils.sendMessage(tran, obj, MSG_CANNOTBUILD_SHLOST, planet.oid, None)
						else:
							# no free slot
							log.debug('IFleet -', 'Build on planet - no free slot')
							Utils.sendMessage(tran, obj, MSG_CANNOTBUILD_NOSLOT, planet.oid, None)
					else:
						# cannot build this here TODO report it
						log.debug('IFleet -', 'Build on planet - cannot build here (validation)')
				if removeShip:
					self.cmd(obj).removeShips(tran, obj, [[designID, hp, shield, exp]])
					# ship has been deployed
					return 1
		# no suitable ship in fleet TODO report it
		log.debug('IFleet -', 'Deploy ship - no suitable ship')
		return 1

		actionDeploy.public = 0

	def refuelAndRepairAndRecharge(self, tran, obj):
		if obj.orbiting == OID_NONE:
			# we are in space
			return 0
		# find ALLIED PLANETS
		system = tran.db[obj.orbiting]
		player = tran.db[obj.owner]
		refuelMax = 0
		refuelInc = 0
		repairShip = 0.0
		for planetID in system.planets:
			planet = tran.db[planetID]
			if planet.owner == OID_NONE:
				continue
			if planet.owner == player.oid:
				refuelMax = max(refuelMax, planet.refuelMax)
				refuelInc = max(refuelInc, planet.refuelInc)
				repairShip = max(repairShip, planet.repairShip)
			elif self.cmd(player).isPactActive(tran, player, planet.owner, PACT_ALLOW_TANKING):
				refuelMax = max(refuelMax, planet.refuelMax)
				refuelInc = max(refuelInc, planet.refuelInc)
				repairShip = max(repairShip, planet.repairShip)
		# repair ships
		self.cmd(obj).autoRepairAndRecharge(tran, obj, forceRepairPerc = repairShip)
		# tank
		if refuelMax == 0:
			return 1
		currentLevel = int(100.0 * obj.storEn / obj.maxEn)
		#@log.debug(obj.oid, "Refuel", currentLevel, refuelMax)
		if currentLevel >= refuelMax:
			# don't burn any fuel if you can refuel
			obj.storEn = min(obj.maxEn, obj.storEn + obj.operEn)
			return 1
		obj.storEn = min(
			int(math.ceil(obj.maxEn * refuelInc / 100.0 + obj.operEn + obj.storEn)),
			int(math.ceil(obj.maxEn * refuelMax / 100.0)),
			obj.maxEn,
		)
		#@log.debug("Refuelling", obj.oid, refuelInc, refuelMax)
		currentLevel = 100.0 * obj.storEn / obj.maxEn
		#@log.debug(obj.oid, "After refuel", currentLevel, refuelMax)
		#@log.debug(obj.oid, "Tanks after refuel", obj.storEn, "/", obj.maxEn)
		return currentLevel >= refuelMax

	refuelAndRepairAndRecharge.public = 0

	def serviceShips(self, tran, obj):
		player = tran.db[obj.owner]
		# check conditions
		# no combat in the system
		system = tran.db[obj.orbiting]
		if system.combatCounter != 0:
			return
		# player's or ally's planet in the system and upgrade facility there
		# check for train facilities too
		upgrPlanets = []
		trainPlanets = []
		trainShipInc = 0.0
		trainShipMax = 0
		for planetID in system.planets:
			planet = tran.db[planetID]
			if planet.owner == player.oid and planet.upgradeShip > 0:
				upgrPlanets.append(planet)
			elif self.cmd(player).isPactActive(tran, player, planet.owner, PACT_ALLOW_TANKING):
				upgrPlanets.append(planet)
			if planet.owner == player.oid and planet.trainShipInc > 0.0:
				trainShipInc = max(trainShipInc, planet.trainShipInc)
				trainShipMax = max(trainShipMax, planet.trainShipMax)
		# train ships
		if trainShipInc > 0:
			for index, ship in enumerate(obj.ships):
				spec = player.shipDesigns[ship[SHIP_IDX_DESIGNID]]
				if ship[SHIP_IDX_EXP] / spec.baseExp < trainShipMax and spec.isMilitary:
					ship[SHIP_IDX_EXP] = min(
						spec.baseExp * trainShipMax,
						ship[SHIP_IDX_EXP] + max(int(trainShipInc * spec.baseExp), 1),
					)
		if not upgrPlanets:
			# no service facility
			return
		upgraded = 0
		# perform upgrade
		for designID in player.shipDesigns.keys():
			spec = player.shipDesigns[designID]
			if spec.upgradeTo:
				#@log.debug("Upgrading design", designID, "to", spec.upgradeTo, "for player", player.oid)
				upgradeToSpec = player.shipDesigns[spec.upgradeTo]
				player.fleetUpgradeInProgress = 1
				diff = max(
					Rules.shipMinUpgrade,
					int((upgradeToSpec.buildProd - spec.buildProd) * Rules.shipUpgradeMod),
				)
				if player.fleetUpgradePool < diff:
					continue
				# scan all ships for design
				designExists = 0
				for index in xrange(0, len(obj.ships)):
					if obj.ships[index][SHIP_IDX_DESIGNID] == designID:
						# find planet with free upgrade points
						needsUPts = Rules.shipUpgradePts[upgradeToSpec.combatClass]
						planet = None
						for tmpPlanet in upgrPlanets:
							if tmpPlanet.upgradeShip >= needsUPts:
								planet = tmpPlanet
								break
						if not planet:
							break
						# check strategic resources
						neededSR = {}
						# new design
						for sr in upgradeToSpec.buildSRes:
							if not sr in neededSR:
								neededSR[sr] = 0
							neededSR[sr] += 1
						# old desing
						for sr in spec.buildSRes:
							if not sr in neededSR:
								neededSR[sr] = 0
							neededSR[sr] -= 1
						# check player's resources
						ok = 1
						for sr in neededSR:
							if player.stratRes.get(sr, 0) < neededSR[sr]:
								Utils.sendMessage(tran, obj, MSG_CANNOT_UPGRADE_SR, obj.oid, (spec.name, upgradeToSpec.name, sr))
								# skip this ship
								ok = 0
						if not ok:
							# skip this ship
							break
						# consume strategic resources
						for sr in neededSR:
							player.stratRes[sr] -= neededSR[sr]
						# upgrade ship
						log.debug("Upgrading ship in fleet", obj.oid, needsUPts, planet.upgradeShip, planet.oid)
						maxHPRatio = max(0.01, 1.0 - max(upgradeToSpec.buildProd - spec.buildProd, 0) / float(upgradeToSpec.buildProd))
						obj.ships[index][SHIP_IDX_DESIGNID] = spec.upgradeTo
						obj.ships[index][SHIP_IDX_HP] = max(1, min(
							obj.ships[index][1],
							int(upgradeToSpec.maxHP * maxHPRatio)
						))
						obj.ships[index][SHIP_IDX_SHIELDHP] = upgradeToSpec.shieldHP
						upgraded += 1
						#@log.debug("HP penalty", diff, upgradeToSpec.buildProd, maxHPRatio)
						player.fleetUpgradePool -= diff
						designExists = 1
						# consume upgrade points
						planet.upgradeShip -= needsUPts
						# record last upgrade
						obj.lastUpgrade = tran.db[OID_UNIVERSE].turn
						# send a message to the player
						# Utils.sendMessage(tran, obj, MSG_UPGRADED_SHIP, obj.oid, (spec.name, player.shipDesigns[spec.upgradeTo].name))
						if player.fleetUpgradePool < diff:
							break
				if player.fleetUpgradePool < diff:
					break
		# fix fleet stats
		if upgraded > 0:
			self.cmd(obj).update(tran, obj)

	serviceShips.public = 0

	def autoRepairAndRecharge(self, tran, obj, forceRepairPerc = 0.0):
		player = tran.db[obj.owner]
		idx = 0
		for designID, hp, shields, exp in obj.ships:
			spec = player.shipDesigns[designID]
			if hp < spec.maxHP:
				repairFix = spec.autoRepairFix
				repairPerc = max(spec.autoRepairPerc, forceRepairPerc)
				if repairFix > 0 or repairPerc > 0:
					#@log.debug("IFleet - repairing ship", designID, hp, repairFix, repairPerc)
					obj.ships[idx][SHIP_IDX_HP] = int(min(
						spec.maxHP,
                                                spec.autoRepairMaxHP*spec.maxHP, #added 9/11/06 - RC
						hp + repairFix + max(1, spec.maxHP * repairPerc),
					))
			if shields < spec.shieldHP:
				#@log.debug("IFleet - recharging shields", designID, shields, spec.shieldRechargeFix, spec.shieldRechargePerc)
				obj.ships[idx][SHIP_IDX_SHIELDHP] = int(min(
					spec.shieldHP,
					shields + spec.shieldRechargeFix + max(1, spec.shieldHP * spec.shieldRechargePerc),
				))
			idx += 1

	def moveToWormhole(self, tran, obj, targetID):
                origin = tran.db[targetID]
                if not (obj.x==origin.x and obj.y==origin.y):
			if not self.cmd(obj).moveToTarget(tran, obj, targetID):
				return 0 #ship hasn't arrived
		# enter wormhole
                if origin.type == T_WORMHOLE: #is wormhole, now enter it!
			destinationWormHole = tran.db[origin.destinationOid]
			if destinationWormHole.oid == targetID:
				return 1
			if obj.oid not in destinationWormHole.fleets:
				destinationWormHole.fleets.append(obj.oid)
			if obj.oid not in destinationWormHole.closeFleets:
				destinationWormHole.closeFleets.append(obj.oid)
			if obj.oid in origin.fleets:
				origin.fleets.remove(obj.oid)
			if obj.oid in origin.closeFleets:
				origin.closeFleets.remove(obj.oid)
			obj.closeSystem = destinationWormHole.oid
                        log.debug('IFleet', 'Entering Wormhole - destination ', destinationWormHole.oid)
			obj.orbiting = destinationWormHole.oid
			obj.x = destinationWormHole.x
			obj.y = destinationWormHole.y
			destinationWormHole.scannerPwrs[obj.owner] = max(obj.scannerPwr, destinationWormHole.scannerPwrs.get(obj.owner, 0))
                        Utils.sendMessage(tran, obj, MSG_ENTERED_WORMHOLE, destinationWormHole.oid , (origin.name,destinationWormHole.name))
			arrived = 1
		else: #is not wormhole...how'd you ever execute this command? Or is there some weird "terraform wormhole" technology we never forsaw?
                        log.warning('IFleet', 'Cannot enter non-existant wormhole at location ', origin.oid)
                        #Utils.sendMessage(tran, obj, MSG_ENTERED_WORMHOLE, destinationWormHole.oid , (origin.name,destinationWormHole.name))
                        arrived = 1 #since the move part was successful, just ignore this problem for the player
                return arrived
	
				
	def moveToTarget(self, tran, obj, targetID): #added action passthrough for wormhole move...needed
		# DON'T move fleet with speed == 0
		if obj.speed <= 0:
			# they cannot arive (never)
			# reset retreat counter
			obj.combatRetreatWait = 0
			return 1
		if targetID == OID_NONE:
			# reset retreat counter
			obj.combatRetreatWait = 0
			return 1
		# reset/remember old values
		obj.oldX = obj.x
		obj.oldY = obj.y
		obj.eta = 0.0
		target = tran.db[targetID]
		# MOVE to target
		dx = target.x - obj.x
		dy = target.y - obj.y
		#if dx == 0 and dy == 0:
		#	return 1
		if obj.orbiting:
			system = tran.db[obj.orbiting]
			if system.combatCounter > 0:
				# well, there is a combat there -> wait a while and reduce ROF
				obj.combatRetreatWait += 1
				if obj.combatRetreatWait <= Rules.combatRetreatWait:
					return 0
				# ok, we suffered enough, move away
			# reset counter
			obj.combatRetreatWait = 0
			# speed boost?
			obj.speedBoost = Utils.getSpeedBoost(tran, tran.db[obj.owner], (system, target))
			#
			try:
				system.fleets.remove(obj.oid)
			except ValueError:
				log.warning('IFleet', 'Problem with removing fleet from system.')
			obj.orbiting = OID_NONE
			# change close system to target one
			if obj.closeSystem != OID_NONE: # TODO remove condition in 0.6
				system = tran.db[obj.closeSystem]
				try:
					system.closeFleets.remove(obj.oid)
				except ValueError:
					log.warning("IFleet", "Problem with changing the close system.")
			if target.type == T_PLANET:
				system = tran.db[target.compOf]
				system.closeFleets.append(obj.oid)
				obj.closeSystem = system.oid
			elif target.type in (T_SYSTEM, T_WORMHOLE):
				target.closeFleets.append(obj.oid)
				obj.closeSystem = target.oid
			else:
				raise GameException('Unsupported type of target %d for move command.' % target.type)
		dist = math.hypot(dx, dy)
		maxDelta = obj.speed / Rules.turnsPerDay * obj.speedBoost
		if not maxDelta:
			obj.combatRetreatWait = 0
			return 0
		arrived = 0
		# 0.01 acceptable error
		if dist <= maxDelta + 0.01:
			# we are at destination
			obj.x = target.x
			obj.y = target.y
			if target.type == T_PLANET:
				obj.orbiting = target.compOf
				system = tran.db[obj.orbiting]
				system.fleets.append(obj.oid)
				arrived = 1
			elif target.type == T_SYSTEM or target.type == T_WORMHOLE:
				#@log.debug('IFleet', obj.oid, 'is aproaching orbit of', targetID)
				obj.orbiting = target.oid
				system = tran.db[obj.orbiting]
				system.fleets.append(obj.oid)
				#@log.debug('IFleet', system.oid, 'system fleets', system.fleets)
				arrived = 1
			else:
				raise GameException('Unsupported type of target %d for move command.' % target.type)
		else:
			# move
			obj.x += dx / dist * maxDelta
			obj.y += dy / dist * maxDelta
			# (already moved 1 x maxDelta) (0.01 is acceptable error)
			obj.eta = math.ceil(dist / maxDelta - 1 - 0.01)
		if arrived:
			# just make sure that this is reset
			obj.combatRetreatWait = 0
			# turn scanner on
			obj.scannerOn = True
			# check the speed boost
			speedBoost = Utils.getSpeedBoost(tran, tran.db[obj.owner], (system,))
			if speedBoost < obj.speedBoost:
				# damage all ships in the fleet
				# damage is based on percentual difference
				percHull = 1.0 - Rules.starGateDamage * (obj.speedBoost / speedBoost - 1.0)
				log.debug(obj.oid, "fleet speed boost too low - damaging ships", speedBoost, obj.speedBoost, percHull)
				Utils.sendMessage(tran, obj, MSG_DAMAGE_BY_SG, obj.orbiting, int((1.0 - percHull) * 100))
				for ship in obj.ships:
					ship[SHIP_IDX_HP] = max(1, int(ship[SHIP_IDX_HP] * percHull))
				# TODO: send message to player
			obj.speedBoost = 1.0
			# add ship to the scanner pwrs of the system
			system.scannerPwrs[obj.owner] = max(obj.scannerPwr, system.scannerPwrs.get(obj.owner, 0))
		return arrived

	moveToTarget.public = 0

	def processFINALPhase(self, tran, obj, data):
		# stats
		player = tran.db[obj.owner]
		player.stats.fleetPwr += obj.combatPwr
		player.stats.fleetSupportProd += obj.operProd
		#
		galaxyID = tran.db[obj.closeSystem].compOf
		if galaxyID not in player.galaxies:
			player.galaxies.append(galaxyID)

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	##
	## Combat related functions
	##

	def getPreCombatData(self, tran, obj):
		# compute data
		shots = {0: [], 1: [], 2: [], 3: []}
		targets = [0, 0, 0, 0]
		player = tran.db[obj.owner]
		desCount = {}
		firing = False
		rofMod = 1.0
		# limit number of shots per ship
		obj.maxHits = {0: 0, 1: 0, 2: 0, 3: 0}
		obj.hitCounters = {0: 0, 1: 0, 2: 0, 3: 0}
		obj.lastHitClass = 3
		obj.hitMods = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0}

		if obj.combatRetreatWait > 0:
			# ROF penalty
			#@log.debug(obj.oid, "Fleet inactive", obj.combatRetreatWait)
			rofMod *= 0.33
		if obj.storEn == 0:
			rofMod *= 0.33
		for designID, hp, shield, exp in obj.ships:
			tech = player.shipDesigns[designID]
			targets[tech.combatClass] += 1
			desCount[designID] = desCount.get(designID, 0) + 1
			obj.maxHits[tech.combatClass] += 2
			wpnCount = {}
			for weaponID in tech.weaponIDs:
				firing = True
				weapon = Rules.techs[weaponID]
				wpnCount[weaponID] = wpnCount.get(weaponID, 0) + 1
				#
				weaponEff = Rules.techImprEff[player.techs.get(weaponID, Rules.techBaseImprovement)]
				# base attack
				attack = (tech.combatAtt + int(weapon.weaponAtt * weaponEff)) * tech.combatAttMultiplier #added multiplier part
				# correct using ship's level
				level = Rules.shipExpToLevel.get(int(exp / tech.baseExp), Rules.shipDefLevel)
				attack = int(attack * Rules.shipLevelEff[level])
				# because ALL counters starts at 1, subtract 3
				count = obj.combatCounter + desCount[designID] + wpnCount[weaponID] - 3
				# add to attacks
				#@log.debug('IFleet', obj.oid, designID, "Count", count, 'Shots', weapon.name, ShipUtils.getRounds(weapon.weaponROF, count))
				for round in xrange(0, ShipUtils.getRounds(weapon.weaponROF * rofMod, count)):
					shots[weapon.weaponClass].append((attack, weaponID))
		log.debug(obj.oid, "Combat limit settings", obj.maxHits)
		return shots, targets, firing

	getPreCombatData.public = 0

	def applyShot(self, tran, obj, defense, attack, weaponID, targetClass, target):
		#@log.debug(obj.oid, 'IFleet', 'Apply shot', attack, weaponID, targetClass, target)
		player = tran.db[obj.owner]
		# find correct ship to hit
		target = -1
		targetCiv = 0
		while target == -1:
			index = 0
			found = 0
			for designID, hp, shield, exp in obj.ships:
				design = player.shipDesigns[designID]
				if design.combatClass == targetClass and (design.isMilitary or targetCiv):
					found = 1
					if Utils.rand(1, 101) < Rules.shipTargetPerc[targetClass]:
						target = index
						break
				index += 1
			if not targetCiv:
				targetCiv = 1
				continue
			if not found and targetCiv:
				# no such target class - try to find another one
				log.warning("No such target class in the fleet", obj.oid, targetClass)
				targetClass = targetClass + 1
				targetCiv = 0
				if targetClass > 3:
					return 0, 0, 0
		designID, hp, shield, exp = obj.ships[target]
		ship = player.shipDesigns[designID]
		# compute if ship has been hit
		weapon = Rules.techs[weaponID]
		level = Rules.shipExpToLevel.get(int(exp / ship.baseExp), Rules.shipDefLevel)
		# add system defense bonus to ship inate defense
		if weapon.weaponIsMissile:
			defense += int(ship.missileDef * Rules.shipLevelEff[level])
		else:
			defense += int(ship.combatDef * Rules.shipLevelEff[level])
		destroyed = 0
		destroyedClass = ship.combatClass
		dmg = 0
		blocked = 0
		# limit number of shots
		cClass = weapon.weaponClass
		if cClass < obj.lastHitClass:
			#@log.debug(obj.oid, "Different class", obj.lastHitClass, cClass, obj.maxHits)
			for i in range(obj.lastHitClass - 1, cClass - 1, -1):
				if obj.hitMods[cClass] >= 0.99: # == 1.0
					#@log.debug(obj.oid, "Adding to", i, int(Rules.combatHitXferMod * (obj.maxHits[i + 1] - obj.hitCounters[i + 1])), obj.hitCounters[i + 1])
					obj.maxHits[i] += int(Rules.combatHitXferMod * (obj.maxHits[i + 1] - obj.hitCounters[i + 1]))
				else:
					#@log.debug(obj.oid, "Not transfering hits")
					pass
				obj.maxHits[i + 1] = 0
			#@log.debug(obj.oid, "max hits", obj.maxHits)
			obj.lastHitClass = cClass
		elif cClass > obj.lastHitClass:
			log.debug(obj.oid, "INCORRECT ORDER OF SHOTS", obj.lastHitClass, cClass)
		if weapon.weaponROF > 1:
			#@log.debug(obj.oid, "Increasing counter", cClass, 1.0 / weapon.weaponROF)
			obj.hitCounters[cClass] += 1.0 / weapon.weaponROF
		else:
			#@log.debug(obj.oid, "Increasing counter", cClass, 1)
			obj.hitCounters[cClass] += 1
		if obj.hitCounters[cClass] > obj.maxHits[cClass]:
			obj.hitCounters[cClass] = 0
			obj.hitMods[cClass] *= Rules.combatShipHitMod
			#@log.debug(obj.oid, "Increasing hit penalty", obj.hitMods[cClass], obj.maxHits[cClass], "class", cClass)
		#
		attack = attack+weapon.weaponAtt
		attackChance = obj.hitMods[cClass] * attack / (attack + defense)
		#@log.debug(obj.oid, "Chance to attack", attackChance, obj.hitMods[cClass],
		#@	 obj.hitCounters[cClass], obj.maxHits[cClass], "without penalty:", float(attack) / (attack + defense))
		if random.random() <= attackChance:
			# HIT! -> apply damage
			dmg = ShipUtils.computeDamage(weapon.weaponClass, ship.combatClass, weapon.weaponDmgMin, weapon.weaponDmgMax)
			#@log.debug(obj.oid, 'HIT! att=%d vs def=%d, dmg=%d '% (attack, defense, dmg))
			# shield
			if not weapon.weaponIgnoreShield and shield > 0:
				blocked = min(shield, dmg)
				obj.ships[target][2] -= blocked
				dmg -= blocked
			elif weapon.weaponIgnoreShield and ship.hardShield > 0 and shield > 0:
                                blocked = min(shield, int(dmg*(ship.hardShield))) #hard shields also reduce penetrating weapons
                                obj.ships[target][2] -= blocked
                                dmg -= blocked
                        #damage absorbsion by armor
                        if ship.damageAbsorb > 0 and dmg > 0:
                                dmg = max(0,dmg-ship.damageAbsorb)
			# armour
			if dmg >= hp:
				destroyed = 1
				self.cmd(obj).removeShips(tran, obj, [obj.ships[target]])
				dmg = hp
			else:
				obj.ships[target][1] -= dmg
		#@log.debug(obj.oid, "Damaged", dmg, blocked, destroyed)
		return dmg + blocked, destroyed, destroyedClass

	applyShot.public = 0

	def distributeExp(self, tran, obj):
		# TODO improve
		player = tran.db[obj.owner]
		while obj.combatExp > 0:
			haveMilitary = 0
			for ship in obj.ships:
				# ignore civilian ships
				if not player.shipDesigns[ship[0]].isMilitary:
					continue
				# add exp point
				haveMilitary = 1
				ship[3] += 1
				obj.combatExp -= 1
				if obj.combatExp == 0:
					break
			if not haveMilitary:
				break
		del obj.maxHits
		del obj.hitCounters
		del obj.lastHitClass
		del obj.hitMods

	distributeExp.public = 0

	def surrenderTo(self, tran, obj, newOwnerID):
		# we've lost the battle - issue MOVE command to the nearest player's star
		return 0

	surrenderTo.public = 0

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
from ige import log
from ige.IObject import IObject
from ige.IDataHolder import IDataHolder
from Const import *
import Rules, Utils, math, ShipUtils, time

class IPlayer(IObject):

	typeID = T_PLAYER
	resignTo = T_AIPLAYER
	forums = {"INBOX": 56, "OUTBOX": 56, "EVENTS": 4}

	def init(self, obj):
		IObject.init(self, obj)
		#
		obj.login = u''
		obj.fullName = u''
		#
		obj.buoys = {}
		obj.alliedBuoys = {}
		obj.planets = []
		obj.fleets = []
		obj.techs = {} # techs and their sublevel
		obj.rsrchQueue = []
		obj.sciPoints = 0
		obj.effSciPoints = 0
		obj.techLevel = 1
		obj.shipDesigns = {}
		obj.race = "H" # race Bionic, Human, Cyborg
		# bonuses
		obj.prodEff = 1.0
		obj.sciEff = 1.0
		#
		obj.govPwr = 0
		obj.govPwrCtrlRange = 1
		# fleet support
		obj.fleetUpgradePool = 0.0
		obj.fleetUpgradeInProgress = 0
		# production
		obj.prodIncreasePool = 0.0
		# diplomacy
		obj.diplomacyRels = {}
		obj.defaultRelation = Rules.defaultRelation
		obj.voteFor = OID_NONE
		obj.governorOf = OID_NONE
		obj.governors = []
		obj.alliance = OID_NONE
		obj.imperator = 0
		# combat
		# anti-small, anti-medium, anti-large, shield generator
		obj.planetWeapons = [None, None, None, None, None]
		#
		obj.staticMap = {}
		obj.dynamicMap = {}
		obj.galaxies = []
		#
		obj.stats = IDataHolder()
		obj.stats.type = T_STATS
		obj.timeEnabled = 0
		obj.stratRes = {}
		obj.lastLogin = 0.0
		#
		obj.shipRedirections = {}
		obj.buoys = {}

	def update(self, tran, obj):
		# update all designs
		for designID in obj.shipDesigns:
			old = obj.shipDesigns[designID]
			new = ShipUtils.makeShipMinSpec(obj, old.name, old.hullID,
				old.eqIDs, old.improvements, raiseExs = False)
			new.built = old.built
			if hasattr(old, "upgradeTo"):
				new.upgradeTo = old.upgradeTo
			obj.shipDesigns[designID] = new
		# check all diplomacyRels
		for partyID in obj.diplomacyRels.keys():
			party = tran.db.get(partyID, None)
			if not party or party.type not in PLAYER_TYPES:
				log.debug("Deleting party", obj.oid, partyID)
				del obj.diplomacyRels[partyID]
		# delete obj with low scan pwr
		# check type of the objects in the map
		for objID in obj.staticMap.keys():
			obj.staticMap[objID] = min(obj.staticMap[objID], Rules.maxScanPwr)
			if obj.staticMap[objID] < Rules.level1InfoScanPwr:
				del obj.staticMap[objID]
			if not tran.db.has_key(objID) or tran.db[objID].type not in (T_SYSTEM, T_WORMHOLE):
				log.debug("Deleting non system %d from static map of player %d" % (objID, obj.oid))
				del obj.staticMap[objID]
		for objID in obj.dynamicMap.keys():
			if obj.dynamicMap[objID] < Rules.level1InfoScanPwr:
				del obj.dynamicMap[objID]
			if not tran.db.has_key(objID) or tran.db[objID].type not in (T_FLEET, T_ASTEROID):
				log.debug("Deleting obj %d from dynamic map of player %d" % (objID, objID))
				del obj.dynamicMap[objID]
		# check if all planets are planets
		for objID in obj.planets[:]:
			try:
				if not tran.db.has_key(objID):
					log.debug("Planet does not exists - removing", obj.oid, objID)
					obj.planets.remove(objID)
				if tran.db[objID].type != T_PLANET:
					log.debug("Planet is not a planet - removing", obj.oid, objID)
					obj.planets.remove(objID)
			except:
				log.warning("There is a problem when processing planet - removing", obj.oid, objID)
				obj.planets.remove(objID)
		# check if systems in buoys are systems
		for objID in obj.buoys.keys():
			try:
				if not tran.db.has_key(objID):
					log.debug("System for buoy does not exists - removing", obj.oid, objID)
					del obj.buoys[objID]
				if tran.db[objID].type not in (T_SYSTEM, T_WORMHOLE):
					log.debug("System for buoy is not a system - removing", obj.oid, objID)
					del obj.buoys[objID]
			except:
				log.warning("There is a problem when processing system for buoy - removing", obj.oid, objID)
				del obj.buoys[objID]
		# check if fleets are fleets
		for objID in obj.fleets[:]:
			try:
				if not tran.db.has_key(objID):
					log.debug("Fleet does not exists - removing", obj.oid, objID)
					obj.fleets.remove(objID)
				if tran.db[objID].type not in  (T_FLEET, T_ASTEROID):
					log.debug("Fleet is not a fleet - removing", obj.oid, objID)
					obj.fleets.remove(objID)
			except:
				log.warning("There is a problem when processing planet - removing", obj.oid, objID)
		# check accessible technologies
		wip = 1
		while wip:
			wip = 0
			for techID in obj.techs.keys():
				if techID not in Rules.techs:
					wip = 1
					log.debug("Deleting nonexistent tech", techID, "player", obj.oid)
					del obj.techs[techID]
					continue
				tech = Rules.techs[techID]
				# check tech level
				if tech.level > obj.techLevel:
					wip = 1
					log.debug("Deleting tech", techID, "player", obj.oid)
					if techID in obj.techs: del obj.techs[techID]
				# disabled?
				#for tmpTechID in obj.techs.keys():
				#	if techID in Rules.techs[tmpTechID].researchDisables:
				#		wip = 1
				#		log.debug("Deleting tech", techID, "player", obj.oid)
				#		if techID in obj.techs: del obj.techs[techID]
				#		break
				# check requirements
				#for tmpTechID, improvement in tech.researchRequires:
				#	if not obj.techs.has_key(tmpTechID) or obj.techs[tmpTechID] < improvement:
				#		wip = 1
				#		log.debug("Deleting tech", techID, "player", obj.oid)
				#		if techID in obj.techs: del obj.techs[techID]
				#		break
		for rTask in obj.rsrchQueue[:]:
			if rTask.techID not in Rules.techs:
				log.debug("Deleting res task for nonexistent tech", rTask.techID, "player", obj.oid)
				obj.rsrchQueue.remove(rTask)
				continue
			tech = Rules.techs[rTask.techID]
			if tech.level == 99:
				log.debug("Deleting res task", rTask.techID, "player", obj.oid)
				obj.rsrchQueue.remove(rTask)
		# check if player is in the universe
		universe = tran.db[OID_UNIVERSE]
		if obj.oid not in universe.players and obj.oid not in (OID_NATURE, OID_ADMIN):
			log.debug(obj.oid, "Adding player to the universe")
			universe.players.append(obj.oid)
		# check nick (TODO remove in 0.5.33)
		if not hasattr(obj, "fullName"):
			obj.fullName = obj.name
		# check if player is a leader
		if not obj.galaxies:
			log.debug(obj.oid, obj.name, "IS NOT IN ANY GALAXY")
		else:
			galaxy = tran.db[obj.galaxies[0]]
			if galaxy.imperator != obj.oid and obj.imperator > 0:
				log.debug(obj.oid, "Removing imperator/leader bonus")
				obj.imperator = 0
		## NON VALIDATING CODE (DERIVED ATTRS AND SO ON)
		# get best technologies for planet weapons
		bestScores = [0, 0, 0, 0]
		obj.planetWeapons = [None, None, None, None, None]
		for techID in obj.techs:
			tech = Rules.techs[techID]
			if tech.isShipEquip and tech.weaponDmgMin > 0 and not tech.buildSRes\
				and tech.weaponGoodForFlak:
				# compute score
				score = (tech.weaponDmgMin + tech.weaponDmgMax) / 2.0 * \
					tech.weaponROF * tech.weaponAtt
				if score > bestScores[tech.weaponClass]:
					obj.planetWeapons[tech.weaponClass] = techID
					bestScores[tech.weaponClass] = score
		#@log.debug(obj.oid, "Planet weapons", obj.planetWeapons)
		# update all ship designs
		for designID in obj.shipDesigns:
			old = obj.shipDesigns[designID]
			new = ShipUtils.makeShipMinSpec(obj, old.name, old.hullID,
				old.eqIDs, old.improvements, raiseExs = False)
			new.built = old.built
			new.upgradeTo = old.upgradeTo
			obj.shipDesigns[designID] = new

	update.public = 0

	def getReferences(self, tran, obj):
		return obj.fleets

	getReferences.public = 0

	def loggedIn(self, tran, obj):
		obj.lastLogin = time.time()

	loggedIn.public = 0

	def resign(self, tran, obj):
		"""Remove player from the game. Give remaining planets, ... to the REBELS"""
		# cannot resign when time is stopped
		# TODO smarted conditions (like cannot resign twice a week or so)
		if not obj.timeEnabled:
			raise GameException('You cannot resign current game - time is stopped.')
		log.debug("Resigning player", obj.oid)
		# morph player to AI
		obj.type = self.resignTo
		self.cmd(obj).upgrade(tran, obj)
		self.cmd(obj).update(tran, obj)
		# reregister
		tran.gameMngr.removePlayer(obj.oid)
		self.cmd(obj).reregister(tran, obj)

	resign.public = 1
	resign.accLevel = AL_OWNER

	def delete(self, tran, obj):
		log.debug("Deleting player", obj.oid)
		# delete relations
		for playerID in tran.db[OID_UNIVERSE].players:
			player = tran.db[playerID]
			self.cmd(player).deleteDiplomacyWith(tran, player, obj.oid)
		# delete fleets
		for fleetID in obj.fleets:
			fleet = tran.db[fleetID]
			self.cmd(fleet).disbandFleet(tran, fleet)
		try:
			tran.gameMngr.removePlayer(obj.oid)
		except Exception:
			log.warning("Cannot remove player")

	delete.public = 1
	delete.accLevel = AL_ADMIN

	def giveUp(self, tran, obj, playerID):
		"""Remove player from the game. Give remaining planets, ... to the specified player"""
		# cannot resign when time is stopped
		# TODO smarted conditions (like cannot resign twice a week or so)
		if not obj.timeEnabled:
			raise GameException('You cannot resign current game - time is stopped.')
		player = tran.db[playerID]
		# give planets
		for planetID in obj.planets[:]: # needs a copy - changeOwner modifies this
			planet = tran.db[planetID]
			self.cmd(planet).changeOwner(tran, planet, playerID, force = 1)
		# give fleets
		for fleetID in obj.fleets[:]:
			fleet = tran.db[fleetID]
			fleet.owner = playerID
			player.fleets.append(fleetID)
		# remove player
		tran.gameMngr.removePlayer(obj.oid)
		try:
			tran.db[OID_UNIVERSE].players.remove(obj.oid)
		except ValueError:
			pass

	giveUp.public = 1
	giveUp.accLevel = AL_ADMIN

	def addShipDesign(self, tran, obj, name, hullID, eqIDs):
		"""Add ship design to the database of designs."""
		# normalize design
		name = name.strip()
		# check technologies
		if hullID not in obj.techs:
			raise GameException("You do not posses this hull type.")
		for techID in eqIDs:
			if techID not in obj.techs:
				raise GameException("You do not posses technology(ies) to construct this ship.")
		# create spec (throws exception for invad ones)
		spec = ShipUtils.makeShipMinSpec(obj, name, hullID, eqIDs, [])
		# check number of designs
		if len(obj.shipDesigns) > Rules.shipMaxDesigns:
			raise GameException("No space to store design.")
		# check name of designs
		for designID in obj.shipDesigns:
			if obj.shipDesigns[designID].name == name:
				raise GameException("Design name is already used.")
		# find free design id
		index = 1
		ids = obj.shipDesigns.keys()
		while 1:
			if index not in ids:
				break
			index += 1
		# add design
		obj.shipDesigns[index] = spec
		return obj.shipDesigns, index

	addShipDesign.public = 1
	addShipDesign.accLevel = AL_OWNER

	def addBuoy(self, tran, obj, systemID, text, type):
		"""Add new buoy to player buoys."""
		# delete buoy
		if not text:
			if systemID in obj.buoys:
				del obj.buoys[systemID]
				return obj.buoys
			else:
				raise GameException("Buoy at specified system does not exist.")

		if type not in (BUOY_PRIVATE, BUOY_TO_ALLY):
			raise GameException("Wrong bouy type.")

		# edit buoy
		if systemID in obj.buoys:
			obj.buoys[systemID] = (text, type)
			return obj.buoys

		if len(obj.buoys) >= 30:
			raise GameException("You cannot add more than 30 buoys.")

		if tran.db[systemID].type not in (T_SYSTEM, T_WORMHOLE):
			raise GameException("You can add buoy only to system.")

		# new buoy
		if len(text) > 0:
			obj.buoys[systemID] = (text, type)

		return obj.buoys

	addBuoy.public = 1
	addBuoy.accLevel = AL_OWNER

	def scrapShipDesign(self, tran, obj, designID):
		"""Remove ship design from the database of designs and remove all
			active ships using this design."""
		# check design ID
		if designID not in obj.shipDesigns:
			raise GameException("No such design.")
		# delete ships
		for fleetID in obj.fleets[:]: # make copy, fleet can be deleted
			fleet = tran.db[fleetID]
			self.cmd(fleet).deleteDesign(tran, fleet, designID)
		# delete tasks
		for planetID in obj.planets:
			planet = tran.db[planetID]
			self.cmd(planet).deleteDesign(tran, planet, designID)
		# clear upgradeTo
		for tmpDesignID in obj.shipDesigns:
			spec = obj.shipDesigns[tmpDesignID]
			if spec.upgradeTo == designID:
				spec.upgradeTo = 0
		# delete design
		del obj.shipDesigns[designID]
		return obj.shipDesigns, obj.fleets, obj.stratRes

	scrapShipDesign.public = 1
	scrapShipDesign.accLevel = AL_OWNER

	def getShipDesign(self,tran,obj,designID):
		if designID not in obj.shipDesigns:
			raise GameException("No such design.")
		return obj.shipDesigns[designID]

	def upgradeShipDesign(self, tran, obj, oldDesignID, newDesignID):
		# check designs ID
		if oldDesignID not in obj.shipDesigns:
			raise GameException("No such design.")
		if newDesignID not in obj.shipDesigns:
			raise GameException("No such design.")
		if oldDesignID == newDesignID:
			raise GameException("Designs are the same.")
		oldSpec = obj.shipDesigns[oldDesignID]
		newSpec = obj.shipDesigns[newDesignID]
		if oldSpec.upgradeTo:
			raise GameException("Old design has already been made obsolete.")
		if newSpec.upgradeTo:
			raise GameException("New design has already been made obsolete.")
		if oldSpec.combatClass != newSpec.combatClass:
			raise GameException("Designs must be of the same combat class.")
		# set old design as upgradable
		oldSpec.upgradeTo = newDesignID
		# if something is upgraded to oldDesign change it to new design
		for desID in obj.shipDesigns:
			if obj.shipDesigns[desID].upgradeTo == oldDesignID:
				obj.shipDesigns[desID].upgradeTo = newDesignID
		# compute strat res difference
		stratRes = {}
		for sr in oldSpec.buildSRes:
			stratRes[sr] = stratRes.get(sr, 0) - 1
		for sr in newSpec.buildSRes:
			stratRes[sr] = stratRes.get(sr, 0) + 1
			if stratRes[sr] == 0:
				del stratRes[sr]
		log.debug("upgradeShipDesign", obj.oid, stratRes)
		# modify tasks
		tasksUpgraded = False
		if not stratRes:
			log.debug("upgradeShipDesign - upgrading tasks")
			for planetID in obj.planets:
				planet = tran.db[planetID]
				self.cmd(planet).changeShipDesign(tran, planet, oldDesignID, newDesignID)
			tasksUpgraded = True
		else:
			log.debug("upgradeShipDesing - NOT upgrading tasks")
		return obj.shipDesigns, obj.stratRes, tasksUpgraded

	upgradeShipDesign.public = 1
	upgradeShipDesign.accLevel = AL_OWNER

	def cancelUpgradeShipDesign(self, tran, obj, designID):
		# check designs ID
		if designID not in obj.shipDesigns:
			raise GameException("No such design.")
		obj.shipDesigns[designID].upgradeTo = OID_NONE
		return obj.shipDesigns

	cancelUpgradeShipDesign.public = 1
	cancelUpgradeShipDesign.accLevel = AL_OWNER

	def startResearch(self, tran, obj, techID, improveToMax = 0):
		if len(obj.rsrchQueue) > Rules.maxRsrchQueueLen:
			GameException('Queue is full.')
		tech = Rules.techs[techID]
		# player has to be a right race
		if obj.race not in tech.researchRaces:
			raise GameException("Your race cannot research this technology.")
		# item cannot be researched twice
		for tmpTech in obj.rsrchQueue:
			if tmpTech.techID == techID:
				raise GameException('Technology is already sheduled for research.')
		# disabled?
		for tmpTechID in obj.techs:
			if techID in Rules.techs[tmpTechID].researchDisables:
				raise GameException("Previous research has disabled this technology.")
		# check requirements
		for tmpTechID, improvement in tech.researchRequires:
			if not obj.techs.has_key(tmpTechID) or obj.techs[tmpTechID] < improvement:
				raise GameException('You cannot research this technology yet.')
		improvement = obj.techs.get(techID, Rules.techBaseImprovement - 1) + 1
		if improvement > Rules.techMaxImprovement or improvement > tech.maxImprovement:
			raise GameException('You cannot improve this technology further.')
		if tech.level > obj.techLevel:
			raise GameException("Your technological level is insufficient.")
		# check strategic resources
		if improvement == 1:
			for stratRes in tech.researchReqSRes:
				if obj.stratRes.get(stratRes, 0) < 1:
					raise GameException("Required strategy resource missing.")
		item = IDataHolder()
		item.techID = techID
		item.improvement = improvement
		item.currSci = 0
		item.changeSci = 0
		item.improveToMax = improveToMax
		item.type = T_RESTASK
		obj.rsrchQueue.append(item)
		return obj.rsrchQueue

	startResearch.public = 1
	startResearch.accLevel = AL_FULL

	def abortResearch(self, tran, obj, index):
		if index >= len(obj.rsrchQueue) or index < 0:
			GameException('No such item in queue.')
		del obj.rsrchQueue[index]
		return obj.rsrchQueue

	abortResearch.public = 1
	abortResearch.accLevel = AL_FULL

	def editResearch(self, tran, obj, index, improveToMax = 0):
		if index >= len(obj.rsrchQueue) or index < 0:
			GameException('No such item in queue.')
		obj.rsrchQueue[index].improveToMax = improveToMax
		return obj.rsrchQueue

	editResearch.public = 1
	editResearch.accLevel = AL_FULL

	def moveResearch(self, tran, obj, index, rel):
		if index >= len(obj.rsrchQueue):
			raise GameException('No such item in the researcg queue.')
		if index + rel < 0 or index + rel >= len(obj.rsrchQueue):
			raise GameException('Cannot move.')
		item = obj.rsrchQueue[index]
		del obj.rsrchQueue[index]
		obj.rsrchQueue.insert(index + rel, item)
		return obj.rsrchQueue

	moveResearch.public = 1
	moveResearch.accLevel = AL_FULL

	def redirectShips(self, tran, obj, sourceSystemID, targetSystemID):
		# check sourceSystemID
		ok = 0
		for planetID in tran.db[sourceSystemID].planets:
			if tran.db[planetID].owner == obj.oid:
				ok = 1
		if not ok:
			raise GameException("You must own planet in the source system")
		# check targetSystemID
		if targetSystemID != OID_NONE and 0: # TODO: switch on
			ok = 0
			for planetID in tran.db[targetSystemID].planets:
				if tran.db[planetID].owner == obj.oid:
					ok = 1
			if not ok:
				raise GameException("You must own planet in the target system")
		# fine - record it
		log.debug(obj.oid, "Adding redirection", sourceSystemID, targetSystemID)
		if targetSystemID:
			obj.shipRedirections[sourceSystemID] = targetSystemID
		else:
			try:
				del obj.shipRedirections[sourceSystemID]
			except KeyError:
				pass
		return obj.shipRedirections

	redirectShips.public = 1
	redirectShips.accLevel = AL_FULL

	def getPublicInfo(self, tran, obj):
		result = IObject.getPublicInfo(self, tran, obj)
		result.type = obj.type
		result.name = obj.name
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE

	def changePactCond(self, tran, obj, playerID, pactID, state, conditions):
		log.debug("changePactCond", obj.oid, playerID, pactID)
		# must have a contact
		if playerID not in obj.diplomacyRels:
			raise GameException('No contact with this player.')
		player = tran.db[playerID]
		# must be a player
		if player.type not in PLAYER_TYPES and player.type != T_ALLIANCE:
			raise GameException('Pacts can be offered to players and aliances only.')
		# check pactID
		pact = Rules.pactDescrs.get(pactID, None)
		if not pact:
			raise GameException('No such pact type.')
		# check state
		if state not in (PACT_OFF, PACT_INACTIVE, PACT_ACTIVE):
			raise GameException("Wrong pact state")
		# check conditions
		for tmpPactID in conditions:
			pact = Rules.pactDescrs.get(tmpPactID, None)
			if not pact:
				raise GameException('No such pact type.')
		# record pact
		dipl = self.cmd(obj).getDiplomacyWith(tran, obj, playerID)
		dipl.pacts[pactID] = [state]
		dipl.pacts[pactID].extend(conditions)
		# if state if PACT_OFF, disable state on partner's side
		if state == PACT_OFF:
			partner = tran.db[playerID]
			dipl = self.cmd(partner).getDiplomacyWith(tran, partner, obj.oid)
			if pactID in dipl.pacts:
				dipl.pacts[pactID][0] = PACT_OFF
			else:
				dipl.pacts[pactID] = [PACT_OFF]
		return obj.diplomacyRels

	changePactCond.public = 1
	changePactCond.accLevel = AL_OWNER

	def getDiplomacyWith(self, tran, obj, playerID):
		if obj.governorOf:
			# player is a governor
			leader = tran.db[obj.governorOf]
			return self.cmd(leader).getDiplomacyWith(tran, leader, objID)
		# player is independent
		dipl = obj.diplomacyRels.get(playerID, None)
		if not dipl:
			# make default
			dipl = IDataHolder()
			dipl.type = T_DIPLREL
			dipl.pacts = {
				PACT_ALLOW_CIVILIAN_SHIPS: [PACT_ACTIVE, PACT_ALLOW_CIVILIAN_SHIPS]
			}
			dipl.relation = obj.defaultRelation
			dipl.relChng = 0
			dipl.lastContact = tran.db[OID_UNIVERSE].turn
			dipl.contactType = CONTACT_NONE
			dipl.stats = None
			if playerID != obj.oid:
				obj.diplomacyRels[playerID] = dipl
			else:
				log.debug("getDiplomacyWith myself", obj.oid)
		return dipl

	def getPartyDiplomacyRels(self, tran, obj, partyID):
		if partyID not in obj.diplomacyRels:
			return None, None
		if obj.diplomacyRels[partyID].contactType == CONTACT_NONE:
			return obj.diplomacyRels[partyID], None
		party = tran.db[partyID]
		return obj.diplomacyRels[partyID], party.diplomacyRels.get(obj.oid, None)

	getPartyDiplomacyRels.public = 1
	getPartyDiplomacyRels.accLevel = AL_OWNER

	def isPactActive(self, tran, obj, partnerID, pactID):
		#@log.debug("isPactActive", obj.oid, partnerID, pactID)
		if partnerID not in obj.diplomacyRels:
			return 0
		partner = tran.db[partnerID]
		partnerDipl = partner.diplomacyRels.get(obj.oid, None)
		if not partnerDipl:
			return 0
		return partnerDipl.pacts.get(pactID, [PACT_OFF])[0] == PACT_ACTIVE

	def deleteDiplomacyWith(self, tran, obj, playerID):
		if playerID in obj.diplomacyRels:
			del obj.diplomacyRels[playerID]

	def getRelationTo(self, tran, obj, objID):
		if objID == OID_NONE:
			return REL_UNDEF
		if obj.oid == objID:
			return REL_UNITY
		if obj.governorOf:
			leader = tran.db[obj.governorOf]
			return self.cmd(leader).getRelationTo(tran, leader, objID)
		dipl = obj.diplomacyRels.get(objID, None)
		if dipl:
			return dipl.relation
		else:
			return obj.defaultRelation

	getRelationTo.public = 1
	getRelationTo.accLevel = AL_FULL

	def setVoteFor(self, tran, obj, playerID):
		if playerID not in obj.diplomacyRels and playerID != obj.oid and playerID != OID_NONE:
			raise GameException("No contact with this commander.")
		# check type
		if playerID != OID_NONE:
			player = tran.db[playerID]
			if player.type != T_PLAYER:
				raise GameException("You cannot vote for this player.")
		# set
		obj.voteFor = playerID
		return obj.voteFor

	setVoteFor.public = 1
	setVoteFor.accLevel = AL_OWNER

	def processDIPLPhase(self, tran, obj, data):
		if not obj.timeEnabled:
			return
		turn = tran.db[OID_UNIVERSE].turn
		# record changes from valid pacts
		for partyID in obj.diplomacyRels:
			dipl = obj.diplomacyRels[partyID]
			# check contact
			if dipl.contactType == CONTACT_NONE:
				#@log.debug("Skipping contact", obj.oid, partyID)
				continue
			# base change of relation
			dipl.relChng += Rules.baseRelationChange
			# process pacts
			for pactID in dipl.pacts:
				#@log.debug("Processing pact", obj.oid, partyID, pactID, dipl.pacts[pactID])
				if dipl.pacts[pactID][0] != PACT_ACTIVE:
					continue
				pactSpec = Rules.pactDescrs[pactID]
				if dipl.relation < pactSpec.validityInterval[0] or \
					dipl.relation > pactSpec.validityInterval[1] or \
					dipl.relChng < Rules.relLostWhenAttacked / 2:
					# skip this non active pact, mark it as off
					# mark all pact off when attacked
					dipl.pacts[pactID][0] = PACT_OFF
					# TODO report it
					continue
				# pact is valid
				if dipl.relation < pactSpec.targetRel:
					#@log.debug("Affecting relation", pactSpec.relChng)
					dipl.relChng += min(pactSpec.targetRel - dipl.relation, pactSpec.relChng)
		# apply relation changes
		for partyID in obj.diplomacyRels:
			dipl = obj.diplomacyRels[partyID]
			dipl.relation += dipl.relChng
			dipl.relation = min(dipl.relation, REL_ALLY_HI)
			dipl.relation = max(dipl.relation, REL_ENEMY_LO)
			#@log.debug('IPlayer', 'Final relation', obj.oid, partyID, dipl.relation, dipl.relChng)

	processDIPLPhase.public = 1
	processDIPLPhase.accLevel = AL_ADMIN

	def getScannerMap(self, tran, obj):
		scanLevels = {}
		# full map for the admin
		if obj.oid == OID_ADMIN:
			universe = tran.db[OID_UNIVERSE]
			for galaxyID in universe.galaxies:
				galaxy = tran.db[galaxyID]
				for systemID in galaxy.systems:
					system = tran.db[systemID]
					obj.staticMap[systemID] = 111111
					for planetID in system.planets:
						obj.staticMap[planetID] = 111111
		# adding systems with buoys
		for objID in obj.buoys:
			scanLevels[objID] = Rules.level1InfoScanPwr
		# player's map
		for objID in obj.staticMap:
			scanLevels[objID] = max(scanLevels.get(objID, 0), obj.staticMap[objID])
		for objID in obj.dynamicMap:
			scanLevels[objID] = max(scanLevels.get(objID, 0), obj.dynamicMap[objID])
		# parties' map
		for partnerID in obj.diplomacyRels:
			if self.cmd(obj).isPactActive(tran, obj, partnerID, PACT_SHARE_SCANNER):
				# load partner's map
				partner = tran.db[partnerID]
				for objID in partner.staticMap:
					scanLevels[objID] = max(scanLevels.get(objID, 0), partner.staticMap[objID])
				for objID in partner.dynamicMap:
					scanLevels[objID] = max(scanLevels.get(objID, 0), partner.dynamicMap[objID])
				# partner's fleets and planets
				for objID in partner.fleets:
					scanLevels[objID] = Rules.partnerScanPwr
				for objID in partner.planets:
					scanLevels[objID] = Rules.partnerScanPwr

		# create map
		map = dict()
		for objID, level in scanLevels.iteritems():
			tmpObj = tran.db.get(objID, None)
			if not tmpObj:
				continue
			for info in self.cmd(tmpObj).getScanInfos(tran, tmpObj, level, obj):
				map[info.oid] = info

		return map

	getScannerMap.public = 1
	getScannerMap.accLevel = AL_OWNER

	def mergeScannerMap(self, tran, obj, map):
		#@log.debug(obj.oid, "Merging scanner map")
		contacts = {}
		for object, level in map.iteritems():
			objID = object.oid
			if object.type in (T_SYSTEM, T_WORMHOLE):
				obj.staticMap[objID] = max(obj.staticMap.get(objID, 0), level)
				contacts.update(object.scannerPwrs)
			elif object.type in (T_FLEET, T_ASTEROID):
				obj.dynamicMap[objID] = max(obj.dynamicMap.get(objID, 0), level)
				contacts[object.owner] = None
			else:
				raise GameException("Unsupported type %d" % object.type)
		if obj.oid in contacts:
			del contacts[obj.oid]
		if OID_NONE in contacts:
			del contacts[OID_NONE]
		for partyID in contacts:
			# add to player's contacts
			dipl = self.cmd(obj).getDiplomacyWith(tran, obj, partyID)
			dipl.contactType = max(dipl.contactType, CONTACT_DYNAMIC)
			dipl.lastContact = tran.db[OID_UNIVERSE].turn
			# add to detected owner's contacts
			owner = tran.db[partyID]
			assert owner.type in PLAYER_TYPES
			dipl = self.cmd(obj).getDiplomacyWith(tran, owner, obj.oid)
			dipl.contactType = max(dipl.contactType, CONTACT_DYNAMIC)
			dipl.lastContact = tran.db[OID_UNIVERSE].turn

	mergeScannerMap.public = 0
	mergeScannerMap.accLevel = AL_OWNER

	def processRSRCHPhase(self, tran, obj, data):
		if not obj.timeEnabled:
			return
		# sci pts from allies
		pts = obj.sciPoints
		for partnerID in obj.diplomacyRels:
			if self.cmd(obj).isPactActive(tran, obj, partnerID, PACT_MINOR_SCI_COOP):
				partner = tran.db[partnerID]
				pactSpec = Rules.pactDescrs[PACT_MINOR_SCI_COOP]
				pts += min(
					int(partner.sciPoints * pactSpec.effectivity),
					int(obj.sciPoints * pactSpec.effectivity),
				)
			if self.cmd(obj).isPactActive(tran, obj, partnerID, PACT_MAJOR_SCI_COOP):
				partner = tran.db[partnerID]
				pactSpec = Rules.pactDescrs[PACT_MAJOR_SCI_COOP]
				pts += min(
					int(partner.sciPoints * pactSpec.effectivity),
					int(obj.sciPoints * pactSpec.effectivity),
				)
		# compute effective sci pts
		obj.effSciPoints = epts = pts - int(obj.stats.storPop * Rules.sciPtsPerCitizen[obj.techLevel])
		index = 0
		while epts > 0 and obj.rsrchQueue and index < len(obj.rsrchQueue):
			item = obj.rsrchQueue[index]
			tech = Rules.techs[item.techID]
			# check requirements
			canResearch = 1
			# player has to be a right race
			if obj.race not in tech.researchRaces:
				canResearch = 0
			for stratRes in tech.researchReqSRes:
				if obj.stratRes.get(stratRes, 0) < 1 and item.improvement == 1:
					Utils.sendMessage(tran, obj, MSG_MISSING_STRATRES, OID_NONE, stratRes)
					canResearch = 0
					break
			for tmpTechID in obj.techs:
				if item.techID in Rules.techs[tmpTechID].researchDisables:
					canResearch = 0
					Utils.sendMessage(tran, obj, MSG_DELETED_RESEARCH, OID_NONE, item.techID)
					del obj.rsrchQueue[index]
					index -= 1
					break
			if tech.level > obj.techLevel:
				canResearch = 0
				Utils.sendMessage(tran, obj, MSG_DELETED_RESEARCH, OID_NONE, item.techID)
				del obj.rsrchQueue[index]
				index -= 1
			if not canResearch:
				index += 1
				continue
			researchSci = Utils.getTechRCost(obj, item.techID)
			wantSci = min(epts, researchSci - item.currSci,
				researchSci / tech.researchTurns)
			item.currSci += wantSci
			item.changeSci = wantSci
			epts -= wantSci
			if item.currSci >= researchSci:
				del obj.rsrchQueue[index]
				obj.techs[item.techID] = item.improvement
				# call finish handler
				tech = Rules.techs[item.techID]
				tech.finishResearchHandler(tran, obj, tech)
				Utils.sendMessage(tran, obj, MSG_COMPLETED_RESEARCH, OID_NONE, item.techID)
				# update derived attributes of player
				self.cmd(obj).update(tran, obj)
				# repeat research if required by player
				if item.improveToMax == 1 and item.improvement < Rules.techMaxImprovement:
					# reinsert the item on the top of the queue
					self.cmd(obj).startResearch(tran, obj, item.techID, improveToMax = 1)
					idx = len(obj.rsrchQueue) - 1
					self.cmd(obj).moveResearch(tran, obj, idx, - idx)
		if epts > 0 and 0: # TODO: remove me
			Utils.sendMessage(tran, obj, MSG_WASTED_SCIPTS, OID_NONE, epts)
			return
		# oops we have negative epts
		while epts < 0:
			log.debug("Not enought RP", epts, obj.oid)
			if obj.rsrchQueue:
				item = obj.rsrchQueue[0]
				if item.currSci > 0:
					wantSci = min(item.currSci, - epts)
					item.currSci -= wantSci
					item.changeSci = - wantSci
					epts += wantSci
				if item.currSci == 0:
					# remove item from the queue - TODO send message to player
					del obj.rsrchQueue[0]
				# at this point, epts can be zero
				if epts == 0:
					log.debug("RP deficit satisfied", obj.oid)
					break
				# try next project
				if obj.rsrchQueue:
					continue
			# oops we must find technology to degrade
			avail = obj.techs.keys()
			# do not degrade technologies, which enables others
			for techID in obj.techs:
				tech = Rules.techs[techID]
				for tmpTechID, impr in tech.researchRequires:
					if tmpTechID in avail:
						avail.remove(tmpTechID)
			log.debug("Techs avialable for degradation", avail)
			if not avail:
				# no technology...
				break
			# from hight to low IDs
			avail.sort()
			avail.reverse()
			degraded = 0
			for level in range(obj.techLevel, 0, -1):
				for techID in avail:
					tech = Rules.techs[techID]
					# check level
					if tech.level != level:
						continue
					# do not touch starting technologies
					if tech.isStarting and obj.techs[techID] <= 3:
						continue
					# ok we have one to degrade
					item = IDataHolder()
					item.techID = techID
					item.improvement = obj.techs[techID]
					item.currSci = Utils.getTechRCost(obj, techID, obj.techs[techID])
					item.changeSci = 0
					item.improveToMax = 0
					item.type = T_RESTASK
					obj.rsrchQueue.append(item)
					# degrade tech
					if obj.techs[techID] == 1:
						# TODO send message
						del obj.techs[techID]
					else:
						# TODO send message
						obj.techs[techID] -= 1
					if tech.recheckWhenTechLost:
						# reset some attributes
						plLevel = obj.techLevel
						obj.techLevel = 1
						# recheck remaining techs
						for level in range(1, plLevel + 1):
							for techID in obj.techs:
								tech = Rules.techs[techID]
								if tech.level != level:
									continue
								# call finish handler again
								tech.finishResearchHandler(tran, obj, tech)
					degraded = 1
					break
				if degraded: break
		return

	processRSRCHPhase.public = 1
	processRSRCHPhase.accLevel = AL_ADMIN

	def processACTIONPhase(self, tran, obj, data):
		return NotImplementedError()

	processACTIONPhase.public = 1
	processACTIONPhase.accLevel = AL_ADMIN

	def processINITPhase(self, tran, obj, data):
		# reset stats
		obj.stats.storPop = 0
		obj.stats.prodProd = 0
		obj.stats.effProdProd = 0
		obj.stats.prodSci = 0
		obj.stats.effProdSci = 0
		obj.stats.slots = 0
		obj.stats.structs = 0
		obj.stats.planets = 0
		obj.stats.fleetPwr = 0
		obj.stats.fleetSupportProd = 0
		obj.govPwr = Rules.baseGovPwr
		# update galaxies
		obj.galaxies = []
		# remove old messages
		self.cmd(obj).deleteOldMsgs(tran, obj)
		# clear fleet upgrade flag
		obj.fleetUpgradeInProgress = 0
		# clear production pool
		obj.prodIncreasePool = 0
		# clear map
		obj.dynamicMap.clear()
		# set empty population distribution
		obj.tmpPopDistr = {}
		# do not process other cmds if time disabled
		if not obj.timeEnabled:
			return
		# clear contacts and delete too old rels
		turn = tran.db[OID_UNIVERSE].turn
		for objID in obj.diplomacyRels.keys():
			dipl = obj.diplomacyRels[objID]
			# reset contact type
			obj.diplomacyRels[objID].contactType = CONTACT_NONE
			# delete old contacts
			if dipl.lastContact + Rules.contactTimeout < turn:
				del obj.diplomacyRels[objID]
				continue
		# lower scan powers in static map
		for objID in obj.staticMap:
			level = obj.staticMap[objID]
			if level > Rules.level3InfoScanPwr:
				obj.staticMap[objID] = max(
					Rules.level3InfoScanPwr,
					int(level * Rules.mapForgetScanPwr),
				)
				#@log.debug(obj.oid, "player static map fix", objID, level - obj.staticMap[objID])
		# clear relations change indicator
		for partyID in obj.diplomacyRels:
			obj.diplomacyRels[partyID].relChng = 0
		# reset science points
		obj.sciPoints = 0

	processINITPhase.public = 1
	processINITPhase.accLevel = AL_ADMIN

	def processFINALPhase(self, tran, obj, data):
		if obj.timeEnabled:
			self.cmd(obj).processRSRCHPhase(tran, obj, data)
			self.cmd(obj).processDIPLPhase(tran, obj, data)
		# efficiency
		obj.prodEff = 1.0
		obj.sciEff = 1.0
		if obj.imperator == 1:
			log.debug(obj.oid, "Leader bonus")
			obj.prodEff += Rules.galLeaderBonus
			obj.sciEff += Rules.galLeaderBonus
		elif obj.imperator >= 2:
			log.debug(obj.oid, "Imperator bonus")
			obj.prodEff += Rules.galImperatorBonus
			obj.sciEff += Rules.galImperatorBonus
		#@log.debug("Fleet upgrade pool", obj.oid, obj.fleetUpgradePool, obj.fleetUpgradeInProgress)
		# compute some stats
		# TODO remove, RAW SCI PTS represented now obj.stats.prodSci = obj.effSciPoints
		obj.stats.planets = len(obj.planets)
		# fleet support
		#@log.debug("Fleet support", obj.oid, obj.stats.fleetSupportProd, obj.stats.prodProd)
		if obj.stats.fleetSupportProd > 0 and obj.stats.prodProd > 0:
			# TODO 0.1 shall be dependend on the race / government type
			obj.prodEff += min(0.1 - float(obj.stats.fleetSupportProd + obj.fleetUpgradePool * Rules.operProdRatio) / obj.stats.prodProd, 0.0)
		# delete non active player
		if obj.lastLogin + Rules.playerTimeout < time.time():
			log.message("Resigning inactive player", obj.name, obj.oid)
			# TODO send a message?
			self.cmd(obj).resign(tran, obj)
		# delete nonactive newbie player
		if obj.lastLogin + Rules.novicePlayerTimeout < time.time() \
			and len(obj.planets) < 4:
			log.message("Resigning inactive novice player", obj.name, obj.oid)
			# TODO send a message?
			self.cmd(obj).resign(tran, obj)
		# acquire government power
		if obj.planets:
			planet = tran.db[obj.planets[0]]
			for slot in planet.slots:
				tech = Rules.techs[slot[STRUCT_IDX_TECHID]]
				if tech.govPwr > 0 and slot[STRUCT_IDX_STATUS] & STRUCT_STATUS_ON:
					eff = Utils.getTechEff(tran, slot[STRUCT_IDX_TECHID], obj.oid)
					obj.govPwr = max(int(tech.govPwr * eff * (slot[STRUCT_IDX_OPSTATUS] / 100.0)), obj.govPwr)
		# compute government controll range
		ranges = obj.tmpPopDistr.keys()
		ranges.sort()
		sum = 0
		range = 1
		for range in ranges:
			sum += obj.tmpPopDistr[range]
			if sum > obj.govPwr:
				break
		obj.govPwrCtrlRange = max(1, range)
		if sum < obj.govPwr and sum > 0:
			#@log.debug(obj.oid, "GovPwr compensation", obj.govPwrCtrlRange, obj.govPwr, sum)
			obj.govPwrCtrlRange = int(obj.govPwrCtrlRange * obj.govPwr / float(sum))
		#@log.debug(obj.oid, "GovPwr control range", obj.govPwrCtrlRange)
		# compute prodBonus and sciBonus
		sum = 0
		for range in ranges:
			sum += obj.tmpPopDistr[range]
		if sum < obj.govPwr and sum > 0:
			ratio = float(obj.govPwr - sum) / obj.govPwr
			#@log.debug(obj.oid, "SMALL EMPIRE BONUS", ratio, "govPwr", obj.govPwr, "sum", sum)
			# TODO let user to define how much to invest into prod and to sci
			obj.prodEff += ratio / 2
			obj.sciEff += ratio / 2
		del obj.tmpPopDistr # delete temporary attribute
		# increase prod eff from pacts
		# CPs from allies
		sum = 0
		for partnerID in obj.diplomacyRels:
			if self.cmd(obj).isPactActive(tran, obj, partnerID, PACT_MINOR_CP_COOP):
				partner = tran.db[partnerID]
				pactSpec = Rules.pactDescrs[PACT_MINOR_CP_COOP]
				sum += min(
					partner.stats.prodProd * pactSpec.effectivity,
					obj.stats.prodProd * pactSpec.effectivity,
				)
			if self.cmd(obj).isPactActive(tran, obj, partnerID, PACT_MAJOR_CP_COOP):
				partner = tran.db[partnerID]
				pactSpec = Rules.pactDescrs[PACT_MAJOR_CP_COOP]
				sum += min(
					partner.stats.prodProd * pactSpec.effectivity,
					obj.stats.prodProd * pactSpec.effectivity,
				)
		# apply production increase pool
		obj.prodIncreasePool += sum
		if obj.stats.prodProd > 0:
			ratio = (Rules.unusedProdMod * obj.prodIncreasePool) / obj.stats.prodProd
			real = min(ratio, math.sqrt(ratio))
			#@log.debug(obj.oid, "Increase production by", ratio, "real", real)
			obj.prodEff += real
		# clean up ship redirections
		systems = {}
		for planetID in obj.planets:
			systems[tran.db[planetID].compOf] = None
		for systemID in obj.shipRedirections.keys():
			if systemID not in systems:
				del obj.shipRedirections[systemID]

		# delete allied bouys
		obj.alliedBuoys = {}

		# find all allies
		for partnerID in obj.diplomacyRels.keys():
			dipl = obj.diplomacyRels[partnerID]
			if dipl.relation >= REL_ALLY_LO:
				partner = tran.db[partnerID]
				if hasattr(partner, "buoys"):
					for systemID in partner.buoys.keys():
						if partner.buoys[systemID][1] == BUOY_TO_ALLY:
							toAllyBuoy = (partner.buoys[systemID][0], BUOY_FROM_ALLY, partner.name)
							if systemID in obj.alliedBuoys:
								obj.alliedBuoys[systemID].append(toAllyBuoy)
							else:
								obj.alliedBuoys[systemID] = [toAllyBuoy]

		return None

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	## messaging
	def canSendMsg(self, tran, obj, oid, forum):
		if forum == "INBOX":
			sender = tran.db[oid]
			return oid == OID_ADMIN or (oid in obj.diplomacyRels) or \
				(obj.oid in sender.diplomacyRels)
		if forum == "OUTBOX":
			return obj.oid == oid
		return 0

	canSendMsg.public = 0

	def cleanUpMsgs(self, tran, obj):
		# get messages
		msgs = self.cmd(obj).getMsgs(tran, obj)
		# build list of events
		delete = []
		for msg in msgs:
			if msg["forum"] == "EVENTS":
				delete.append(msg["id"])
		# delete
		self.cmd(obj).deleteMsgs(tran, obj, delete)
		return 1

	cleanUpMsgs.public = 1
	cleanUpMsgs.accLevel = AL_OWNER

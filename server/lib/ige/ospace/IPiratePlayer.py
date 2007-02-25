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
from IPlayer import IPlayer
from ige.IDataHolder import IDataHolder
import Rules, Utils
from Const import *
import math, time, sys, random

class IPiratePlayer(IPlayer):

	typeID = T_PIRPLAYER
	resignTo = T_AIPIRPLAYER

	def init(self, obj):
		IPlayer.init(self, obj)
		obj.pirateFame = 0

	def XXXgetDiplomacyWith(self, tran, obj, playerID):
		if obj.oid == playerID:
			return REL_UNITY
		player = tran.db.get(playerID, None)
		if player.type == T_AIEDENPLAYER:
			dipl = obj.diplomacyRels.get(playerID, None)
			if not dipl:
				# make default
				dipl = IDataHolder()
				dipl.type = T_DIPLREL
				dipl.pacts = {
						PACT_ALLOW_CIVILIAN_SHIPS: [PACT_ACTIVE, PACT_ALLOW_CIVILIAN_SHIPS],
						PACT_ALLOW_MILITARY_SHIPS: [PACT_ACTIVE, PACT_ALLOW_MILITARY_SHIPS]
				}
				dipl.relation = REL_FRIENDLY
				dipl.relChng = 0
				dipl.lastContact = tran.db[OID_UNIVERSE].turn
				dipl.contactType = CONTACT_NONE
				dipl.stats = None
				if playerID != obj.oid:
					obj.diplomacyRels[playerID] = dipl
				else:
					log.debug("getDiplomacyWith myself", obj.oid)
			return dipl
		# this AI battles with overyone
		# make default
		dipl = IDataHolder()
		dipl.type = T_DIPLREL
		dipl.pacts = {}
		dipl.relation = REL_ENEMY
		dipl.relChng = 0
		dipl.lastContact = tran.db[OID_UNIVERSE].turn
		dipl.contactType = CONTACT_NONE
		dipl.stats = None
		return dipl

	def XXXisPactActive(self, tran, obj, partnerID, pactID):
		return 0

	def update(self, tran, obj):
		# call super method
		IPlayer.update(self, tran, obj)
		#
		obj.techLevel = 99
		# grant special technologies
		obj.techs[Rules.Tech.PIRATEBASE] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRATEDEN] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRATESD] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRATEBREWERY] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRATEPRISON] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRATEPRISON] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRSMCOLONYMOD] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRATEFTLENG] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.PIRCOLONYMOD] = Rules.techMaxImprovement
		# grant all TL1 ship techs except for colony module(s)
		for techID in Rules.techs:
			tech = Rules.techs[techID]
			if tech.level == 1 and (tech.isShipEquip or tech.isShipHull) and not tech.unpackStruct:
				obj.techs[techID] = Rules.techMaxImprovement
		# convert enslavedPop
		if hasattr(obj, "enslavedPop"):
			obj.pirateFame = int(obj.enslavedPop * 0.0005)
			log.debug(obj.oid, "New pirate fame is", obj.pirateFame, obj.enslavedPop)
			del obj.enslavedPop

	def processDIPLPhase(self, tran, obj, data):
		self.forceAllyWithEDEN(tran,obj)
		IPlayer.processDIPLPhase(self,tran, obj, data)

	def processFINALPhase(self, tran, obj, data):
		if not Rules.Tech.PIRATEBREWERY in obj.techs:
			log.warning('Adding new pirate structures to human pirate player.')
			self.cmd(obj).update(tran, obj) #grant the techs because something screwed up
		obj.govPwr = Rules.pirateGovPwr
		IPlayer.processFINALPhase(self, tran, obj, data)
		# get fame every 1:00 turns
		if tran.db[OID_UNIVERSE].turn % Rules.turnsPerDay == 0:
			Utils.sendMessage(tran, obj, MSG_GAINED_FAME, obj.oid, Rules.pirateSurvivalFame)
			obj.pirateFame += Rules.pirateSurvivalFame
		# fix goverment power
		obj.govPwrCtrlRange = 10000
		# bonus for gained fame
		obj.prodEff += obj.pirateFame / 100.0

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	def processRSRCHPhase(self, tran, obj, data):
		# do not research anything
		return

	processRSRCHPhase.public = 1
	processRSRCHPhase.accLevel = AL_ADMIN

	def capturePlanet(self, tran, obj, planet):
		# find distance to closes pirate's planet
		dist = sys.maxint
		for objID in obj.planets:
			pirPl = tran.db[objID]
			d = math.hypot(planet.x - pirPl.x, planet.y - pirPl.y)
			if d < dist:
				dist = d
		if random.random() <= Rules.pirateGainFamePropability(dist):
			log.debug(obj.oid, "Pirate captured planet + fame", dist, planet.oid)
			obj.pirateFame += Rules.pirateCaptureInRangeFame
			Utils.sendMessage(tran, obj, MSG_GAINED_FAME, planet.oid, Rules.pirateCaptureInRangeFame)
		elif random.random() <= Rules.pirateLoseFameProbability(dist):
			log.debug(obj.oid, "Pirate captured planet OUT OF range", dist, planet.oid)
			obj.pirateFame += Rules.pirateCaptureOutOfRangeFame
			Utils.sendMessage(tran, obj, MSG_LOST_FAME, planet.oid, Rules.pirateCaptureOutOfRangeFame)

	def stealTechs(self, tran, piratePlayer, oldOwnerID, stealFromPlanetID):
		if oldOwnerID == OID_NONE:
			return
		log.debug(piratePlayer.oid, "IPiratePlayer stealing techs")
		oldOwner = tran.db[oldOwnerID]
		canSteal = Rules.pirateCanStealImprovements
		while canSteal > 0:
			stealed = False
			for techID in oldOwner.techs:
				tech = Rules.techs[techID]
				if oldOwner.techs[techID] <= piratePlayer.techs.get(techID, 0):
					# skip techs that are already stealed
					continue
				if (tech.isShipEquip or tech.isShipHull) and not tech.unpackStruct and canSteal > 0:
					self.givePirateTech(tran, piratePlayer, oldOwner, techID, stealFromPlanetID)
					canSteal -= 1
					stealed = True
				if tech.isProject and canSteal > 0:
					self.givePirateTech(tran, piratePlayer, oldOwner, techID, stealFromPlanetID)
					canSteal -= 1
					stealed = True
			if not stealed:
				break
		# update techs
		self.cmd(piratePlayer).update(tran, piratePlayer)
		return

	def givePirateTech(self, tran, piratePlayer, oldOwner, techID, stealFromPlanetID):
		piratePlayer.techs[techID] = min(piratePlayer.techs.get(techID, 0) + 1, oldOwner.techs[techID])
		Utils.sendMessage(tran, piratePlayer, MSG_GAINED_TECH, stealFromPlanetID, (techID, piratePlayer.techs[techID]))

	def forceAllyWithEDEN(self,tran,obj):
		for partyID in obj.diplomacyRels.keys():
			party = tran.db.get(partyID, None)
			if party.type == T_AIEDENPLAYER:
				diplSelf = obj.diplomacyRels.get(party.oid, None)
				log.debug("Allying Pirate with EDEN (forced)", obj.oid, partyID)
				diplEDEN = IDataHolder()
				diplEDEN.type = T_DIPLREL
				diplEDEN.pacts = {
						PACT_ALLOW_CIVILIAN_SHIPS: [PACT_ACTIVE, PACT_ALLOW_CIVILIAN_SHIPS],
						PACT_ALLOW_MILITARY_SHIPS: [PACT_ACTIVE, PACT_ALLOW_MILITARY_SHIPS]
				}
				diplEDEN.relation = REL_FRIENDLY
				diplEDEN.relChng = 0
				diplEDEN.lastContact = tran.db[OID_UNIVERSE].turn
				diplEDEN.contactType = CONTACT_STATIC
				diplEDEN.stats = None

				diplSelf.relation = REL_FRIENDLY
				diplSelf.pacts = {
					PACT_ALLOW_CIVILIAN_SHIPS: [PACT_ACTIVE, PACT_ALLOW_CIVILIAN_SHIPS],
					PACT_ALLOW_MILITARY_SHIPS: [PACT_ACTIVE, PACT_ALLOW_MILITARY_SHIPS]
				}
				
				obj.diplomacyRels[party.oid] = diplSelf
				party.diplomacyRels[obj.oid] = diplEDEN
				

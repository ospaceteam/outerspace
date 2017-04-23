#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from ige import *
from xml.dom.minidom import Node
from IPlayer import IPlayer
from ige.IDataHolder import IDataHolder
import Rules, Utils
from Const import *
import math, time, random, os, sys
import hashlib

from ai_parser import AIList

class IAIPiratePlayer(IPlayer):

    typeID = T_AIPIRPLAYER
    resignTo = T_PIRPLAYER
    forums = {"INBOX": 56, "OUTBOX": 56, "EVENTS": 0}

    def init(self, obj):
        IPlayer.init(self, obj)
        #
        obj.name = u'Pirate'
        obj.login = '*'
        #
        obj.pirateFame = 0
        obj.techLevel = 99
        # grant technologies
        obj.techs[Rules.Tech.EMCANNONTUR] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.SSROCKET2] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.TORPEDO] = Rules.techMaxImprovement
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

    def register(self, tran, obj):
        log.debug("Registering player", obj.oid)
        counter = 1
        while 1:
            try:
                obj.name = u'Pirate faction %d' % counter
                obj.login = '*AIP*pirate%d' % counter
                password = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()
                tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
                tran.db[OID_UNIVERSE].players.append(obj.oid)
                tran.gameMngr.clientMngr.createAiAccount(None, obj.login, password, obj.name)
                break
            except CreatePlayerException:
                counter += 1
        # after succesfull registration, register it to the AI system
        aiList = AIList(tran.gameMngr.configDir, tran.gameMngr.gameName)
        aiList.add(obj.login, password, 'ais_pirate')
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

    def reregister(self, tran, obj):
        # nearly identical to register, just now we know the galaxy
        # to add this information tu AIList
        log.debug("Registering player", obj.oid)
        counter = 1
        while 1:
            try:
                obj.name = u'Pirate faction %d' % counter
                obj.login = '*AIP*pirate%d' % counter
                password = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()
                tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
                tran.db[OID_UNIVERSE].players.append(obj.oid)
                tran.gameMngr.clientMngr.createAiAccount(None, obj.login, password, obj.name)
                break
            except CreatePlayerException:
                counter += 1
        # after succesfull registration, register it to the AI system
        aiList = AIList(tran.gameMngr.configDir, tran.gameMngr.gameName)
        aiList.add(obj.login, password, 'ais_pirate')
        aiList.setGalaxy(obj.login, tran.db[obj.galaxies[0]].name)
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

    def processINITPhase(self, tran, obj, data):
        IPlayer.processINITPhase(self, tran, obj, data)
        # TODO -- remove following lines
        obj.lastLogin = time.time()
        # delete itself if there are no fleets and planets
        if not obj.fleets and not obj.planets:
            self.cmd(obj).delete(tran, obj)

    def update(self, tran, obj):
        # TODO: remove in 0.5.59
        if not hasattr(self, "techs"):
            self.techs = {}

        obj.techLevel = 99
        obj.race = "p"
        # call super method
        IPlayer.update(self, tran, obj)
        #
        obj.techLevel = 99
        # grant technologies
        obj.techs[Rules.Tech.EMCANNONTUR] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.SSROCKET2] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.TORPEDO] = Rules.techMaxImprovement
        # grant special technologies
        obj.techs[Rules.Tech.PIRATEBASE] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEDEN] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATESD] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEBREWERY] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEPRISON] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRSMCOLONYMOD] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEFTLENG] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRCOLONYMOD] = Rules.techMaxImprovement

    def getDiplomacyWith(self, tran, obj, playerID):
        if obj.oid == playerID:
            return REL_UNITY
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

    def isPactActive(self, tran, obj, partnerID, pactID):
        if partnerID == OID_NONE:
            return 0
        partner = tran.db.get(partnerID, None)
        if partner.type == T_AIEDENPLAYER:
            # force the peace!
            if pactID in (PACT_ALLOW_CIVILIAN_SHIPS, PACT_ALLOW_MILITARY_SHIPS):
                return PACT_ACTIVE
        return 0

    def processDIPLPhase(self, tran, obj, data):
        self.forceAllyWithEDEN(tran,obj)
        IPlayer.processDIPLPhase(self,tran, obj, data)

    def processFINALPhase(self, tran, obj, data):
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

    def distToNearestPiratePlanet(self,tran,obj,srcObj):
        # srcObj can be Planet or System type
        dist = sys.maxint
        for objID in obj.planets:
            pirPl = tran.db[objID]
            d = math.hypot(srcObj.x - pirPl.x, srcObj.y - pirPl.y)
            if d < dist:
                dist = d
        return dist

    def capturePlanet(self, tran, obj, planet):
        # find distance to closes pirate's planet
        dist = self.distToNearestPiratePlanet(tran,obj,planet)
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



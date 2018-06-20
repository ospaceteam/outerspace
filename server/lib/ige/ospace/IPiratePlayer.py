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
import math
import random
import sys

import Const
import Rules
import Utils

from ige import log
from ige.IDataHolder import IDataHolder
from ige.IObject import public
from IPlayer import IPlayer

class IPiratePlayer(IPlayer):

    typeID = Const.T_PIRPLAYER
    resignTo = Const.T_AIPIRPLAYER

    def init(self, obj):
        IPlayer.init(self, obj)
        obj.techLevel = 3
        obj.race = "p"
        obj.pirateFame = 0

    def update(self, tran, obj):
        # call super method
        IPlayer.update(self, tran, obj)

    def setStartingPlanet(self, planet):
        planet.plSlots = max(planet.plSlots, 2)
        planet.plMaxSlots = max(planet.plMaxSlots, 2)
        planet.plDiameter = max(planet.plDiameter, 2000)
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.PIRATEBASE, planet.owner, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.PIRATEDEN, planet.owner, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.storPop = 6000

    def setStartingTechnologies(self, obj):
        for techID in Rules.techs:
            tech = Rules.techs[techID]
            if tech.level == 1 and (tech.isShipEquip or tech.isShipHull) and not tech.unpackStruct:
                obj.techs[techID] = tech.MaxImprovement
        obj.techs[Rules.Tech.PIRATEBASE] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEDEN] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATESD] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEBREWERY] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEPRISON] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEPRISON] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRSMCOLONYMOD] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRATEFTLENG] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.PIRCOLONYMOD] = Rules.techMaxImprovement

    def setStartingShipDesigns(self, obj):
        pass

    @public(Const.AL_ADMIN)
    def processDIPLPhase(self, tran, obj, data):
        self.forceAllyWithEDEN(tran,obj)
        IPlayer.processDIPLPhase(self,tran, obj, data)

    @public(Const.AL_ADMIN)
    def processFINALPhase(self, tran, obj, data):
        if not Rules.Tech.PIRATEBREWERY in obj.techs:
            log.warning('Adding new pirate structures to human pirate player.')
            self.cmd(obj).update(tran, obj) #grant the techs because something screwed up
        obj.govPwr = Rules.pirateGovPwr
        IPlayer.processFINALPhase(self, tran, obj, data)
        # get fame every 1:00 turns
        if tran.db[Const.OID_UNIVERSE].turn % Rules.turnsPerDay == 0:
            Utils.sendMessage(tran, obj, Const.MSG_GAINED_FAME, obj.oid, Rules.pirateSurvivalFame)
            obj.pirateFame += Rules.pirateSurvivalFame
        # fix goverment power
        obj.govPwrCtrlRange = 10000
        # bonus for gained fame
        obj.prodEff += obj.pirateFame / 100.0

    @public(Const.AL_ADMIN)
    def processRSRCHPhase(self, tran, obj, data):
        # do not research anything
        return

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
            Utils.sendMessage(tran, obj, Const.MSG_GAINED_FAME, planet.oid, Rules.pirateCaptureInRangeFame)
        elif random.random() <= Rules.pirateLoseFameProbability(dist):
            log.debug(obj.oid, "Pirate captured planet OUT OF range", dist, planet.oid)
            obj.pirateFame += Rules.pirateCaptureOutOfRangeFame
            Utils.sendMessage(tran, obj, Const.MSG_LOST_FAME, planet.oid, Rules.pirateCaptureOutOfRangeFame)

    def stealTechs(self, tran, piratePlayer, oldOwnerID, stealFromPlanetID):
        if oldOwnerID == Const.OID_NONE:
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
        Utils.sendMessage(tran, piratePlayer, Const.MSG_GAINED_TECH, stealFromPlanetID, (techID, piratePlayer.techs[techID]))

    def forceAllyWithEDEN(self,tran,obj):
        for partyID in obj.diplomacyRels.keys():
            party = tran.db.get(partyID, None)
            if party.type == Const.T_AIEDENPLAYER:
                diplSelf = obj.diplomacyRels.get(party.oid, None)
                log.debug("Allying Pirate with EDEN (forced)", obj.oid, partyID)
                diplEDEN = IDataHolder()
                diplEDEN.type = Const.T_DIPLREL
                diplEDEN.pacts = {
                        Const.PACT_ALLOW_CIVILIAN_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_CIVILIAN_SHIPS],
                        Const.PACT_ALLOW_MILITARY_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_MILITARY_SHIPS]
                }
                diplEDEN.relation = Const.REL_FRIENDLY
                diplEDEN.relChng = 0
                diplEDEN.lastContact = tran.db[Const.OID_UNIVERSE].turn
                diplEDEN.contactType = Const.CONTACT_STATIC
                diplEDEN.stats = None

                diplSelf.relation = Const.REL_FRIENDLY
                diplSelf.pacts = {
                    Const.PACT_ALLOW_CIVILIAN_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_CIVILIAN_SHIPS],
                    Const.PACT_ALLOW_MILITARY_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_MILITARY_SHIPS]
                }

                obj.diplomacyRels[party.oid] = diplSelf
                party.diplomacyRels[obj.oid] = diplEDEN

    def isPactActive(self, tran, obj, partnerID, pactID):
        if partnerID == Const.OID_NONE:
            return 0
        partner = tran.db.get(partnerID, None)
        if partner.type == Const.T_AIEDENPLAYER:
            # force the peace!
            if pactID in (Const.PACT_ALLOW_CIVILIAN_SHIPS, Const.PACT_ALLOW_MILITARY_SHIPS):
                return Const.PACT_ACTIVE
        # for other situations, handle it as proper player
        return IPlayer.isPactActive(self, tran, obj, partnerID, pactID)

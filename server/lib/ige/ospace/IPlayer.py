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
import re
import time

import ige
import Rules
import Utils
import ShipUtils

from ige import log
from ige.IObject import IObject, public
from ige.IDataHolder import IDataHolder
import Const

class IPlayer(IObject):

    typeID = Const.T_PLAYER
    resignTo = Const.T_AIPLAYER
    forums = {"INBOX": 56, "OUTBOX": 56, "EVENTS": 4}

    def init(self, obj):
        IObject.init(self, obj)
        #
        obj.login = u''
        obj.name = u''
        obj.fullName = u''
        #
        obj.buoys = {}
        obj.alliedBuoys = {}
        obj.planets = []
        obj.fleets = []
        obj.techs = {} # techs and their sublevel
        obj.obsoleteTechs = set()
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
        obj.prodQueues = [[],[],[],[],[]]
        obj.prodIncreasePool = 0.0
        # diplomacy
        obj.diplomacyRels = {}
        obj.defaultRelation = Rules.defaultRelation
        obj.voteFor = Const.OID_NONE
        obj.governorOf = Const.OID_NONE
        obj.governors = []
        # obj.alliance = Const.OID_NONE # not utilized, but can be in DB somewhere
        obj.imperator = 0
        # combat
        # anti-small, anti-medium, anti-large, shield generator
        obj.planetWeapons = [None, None, None, None, None]
        #
        obj.staticMap = {}
        obj.dynamicMap = {}
        obj.galaxy = None
        obj.validSystems = []
        #
        obj.stats = IDataHolder()
        obj.stats.type = Const.T_STATS
        obj.timeEnabled = 0
        obj.stratRes = {}
        obj.lastLogin = 0.0
        #
        obj.shipRedirections = {}
        obj.buoys = {}
        #
        obj.clientStats = {}

    def update(self, tran, obj):
        # refresh technologies
        self.setStartingTechnologies(obj)
        # clean up obsoleted technologies
        obsoleted = set(obj.techs.keys()).difference(Rules.techs.keys())
        for techID in obsoleted:
            log.debug("Deleting obsoleted technology", obj.oid, techID)
            del obj.techs[techID]
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
            if not party or party.type not in Const.PLAYER_TYPES:
                log.debug("Deleting party", obj.oid, partyID)
                del obj.diplomacyRels[partyID]
        # delete obj with low scan pwr
        # check type of the objects in the map
        for objID in obj.staticMap.keys():
            obj.staticMap[objID] = min(obj.staticMap[objID], Rules.maxScanPwr)
            if obj.staticMap[objID] < Rules.level1InfoScanPwr:
                del obj.staticMap[objID]
            if objID not in tran.db or tran.db[objID].type not in (Const.T_SYSTEM, Const.T_WORMHOLE):
                log.debug("Deleting non system %d from static map of player %d" % (objID, obj.oid))
                del obj.staticMap[objID]
        for objID in obj.dynamicMap.keys():
            if obj.dynamicMap[objID] < Rules.level1InfoScanPwr:
                del obj.dynamicMap[objID]
            if objID not in tran.db or tran.db[objID].type != Const.T_FLEET:
                log.debug("Deleting obj %d from dynamic map of player %d" % (objID, objID))
                del obj.dynamicMap[objID]
        # check if all planets are planets
        for objID in obj.planets[:]:
            try:
                if objID not in tran.db:
                    log.debug("Planet does not exists - removing", obj.oid, objID)
                    obj.planets.remove(objID)
                if tran.db[objID].type != Const.T_PLANET:
                    log.debug("Planet is not a planet - removing", obj.oid, objID)
                    obj.planets.remove(objID)
            except:
                log.warning("There is a problem when processing planet - removing", obj.oid, objID)
                obj.planets.remove(objID)
        # check if systems in buoys are systems
        for objID in obj.buoys.keys():
            try:
                if objID not in tran.db:
                    log.debug("System for buoy does not exists - removing", obj.oid, objID)
                    del obj.buoys[objID]
                if tran.db[objID].type not in (Const.T_SYSTEM, Const.T_WORMHOLE):
                    log.debug("System for buoy is not a system - removing", obj.oid, objID)
                    del obj.buoys[objID]
            except:
                log.warning("There is a problem when processing system for buoy - removing", obj.oid, objID)
                del obj.buoys[objID]
        # check if fleets are fleets
        for objID in obj.fleets[:]:
            try:
                if objID not in tran.db:
                    log.debug("Fleet does not exists - removing", obj.oid, objID)
                    obj.fleets.remove(objID)
                if tran.db[objID].type != Const.T_FLEET:
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
        universe = tran.db[Const.OID_UNIVERSE]
        if obj.oid not in universe.players and obj.oid not in (Const.OID_NATURE, Const.OID_ADMIN):
            log.debug(obj.oid, "Adding player to the universe")
            universe.players.append(obj.oid)
        # check if player is a leader
        if not obj.galaxy:
            log.debug(obj.oid, obj.name, "IS NOT IN ANY GALAXY")
        else:
            galaxy = tran.db[obj.galaxy]
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
                weaponEff = Rules.techImprEff[obj.techs.get(techID, Rules.techBaseImprovement)]
                score = (tech.weaponDmgMin + tech.weaponDmgMax) / 2.0 * \
                    tech.weaponROF * (tech.weaponAtt + 10.0)/10 * weaponEff
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

    @staticmethod
    def setStartingPlanet(tran, playerID, planet):
        planet.plSlots = max(planet.plSlots, 9)
        planet.plMaxSlots = max(planet.plMaxSlots, 9)
        planet.plDiameter = max(planet.plDiameter, 9000)
        planet.slots = [
            Utils.newStructure(tran, Rules.Tech.PWRPLANTNUK1, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            Utils.newStructure(tran, Rules.Tech.FARM1, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            Utils.newStructure(tran, Rules.Tech.FARM1, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            Utils.newStructure(tran, Rules.Tech.ANCFACTORY, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            Utils.newStructure(tran, Rules.Tech.ANCFACTORY, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            Utils.newStructure(tran, Rules.Tech.ANCRESLAB, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            Utils.newStructure(tran, Rules.Tech.REPAIR1, playerID, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
        ]
        planet.storPop = Rules.startingPopulation
        planet.storBio = Rules.startingBio
        planet.storEn = Rules.startingEn
        planet.scannerPwr = Rules.startingScannerPwr
        planet.morale = Rules.maxMorale

    @staticmethod
    def setStartingTechnologies(obj):
        for techID, tech in Rules.techs.iteritems():
            if tech.isStarting and techID not in obj.techs:
                obj.techs[techID] = (Rules.techBaseImprovement + tech.maxImprovement) / 2

    @staticmethod
    def setStartingShipDesigns(obj):
        obj.shipDesigns[1] = ShipUtils.makeShipMinSpec(obj, 'Scout', Rules.Tech.SMALLHULL0,
                {Rules.Tech.SCOCKPIT0:1, Rules.Tech.SCANNERMOD0:1, Rules.Tech.FTLENG0:3}, [])
        obj.shipDesigns[2] = ShipUtils.makeShipMinSpec(obj, 'Fighter', Rules.Tech.SMALLHULL0,
                {Rules.Tech.SCOCKPIT0:1, Rules.Tech.CANNON0:2, Rules.Tech.FTLENG0:3}, [])
        obj.shipDesigns[3] = ShipUtils.makeShipMinSpec(obj, 'Bomber', Rules.Tech.SMALLHULL0,
                {Rules.Tech.SCOCKPIT0:1, Rules.Tech.CONBOMB0:1, Rules.Tech.FTLENG0:3}, [])
        obj.shipDesigns[4] = ShipUtils.makeShipMinSpec(obj, 'Patrol Corvette', Rules.Tech.SMALLHULL0,
                {Rules.Tech.SCOCKPIT0:1, Rules.Tech.CANNON0:3, Rules.Tech.FTLENG0:1, Rules.Tech.STLENG1:2}, [])
        obj.shipDesigns[5] = ShipUtils.makeShipMinSpec(obj, 'Colony Ship', Rules.Tech.MEDIUMHULL0,
                {Rules.Tech.SCOCKPIT0:1, Rules.Tech.COLONYMOD0:1, Rules.Tech.FTLENG0:5}, [])

    @staticmethod
    def setStartingFleet(tran, playerID, system):
        # add small fleet
        log.debug('Creating fleet')
        fleet = tran.gameMngr.cmdPool[Const.T_FLEET].new(Const.T_FLEET)
        tran.db.create(fleet)
        log.debug('Creating fleet - created', fleet.oid)
        tran.gameMngr.cmdPool[Const.T_FLEET].create(tran, fleet, system, playerID)
        log.debug('Creating fleet - addShips')
        # for IDs, see setStartingShipDesigns
        tran.gameMngr.cmdPool[Const.T_FLEET].addNewShip(tran, fleet, 1)
        tran.gameMngr.cmdPool[Const.T_FLEET].addNewShip(tran, fleet, 1)
        tran.gameMngr.cmdPool[Const.T_FLEET].addNewShip(tran, fleet, 2)
        tran.gameMngr.cmdPool[Const.T_FLEET].addNewShip(tran, fleet, 2)
        tran.gameMngr.cmdPool[Const.T_FLEET].addNewShip(tran, fleet, 5)

    @public(Const.AL_FULL)
    def startGlobalConstruction(self, tran, player, techID, quantity, isShip, reportFinished, queue):
        if len(player.prodQueues) <= queue:
            raise ige.GameException('Invalid queue.')
        if len(player.prodQueues[queue]) > Rules.maxProdQueueLen:
            raise ige.GameException('Queue is full.')
        if quantity < 1:
            raise ige.GameException("Quantity must be greater than 0")
        if techID not in player.techs and isShip == 0:
            raise ige.GameException('You do not own this kind of technology.')
        if techID not in player.shipDesigns and isShip == 1:
            raise ige.GameException('You do not own this ship design.')
        if isShip:
            tech = player.shipDesigns[techID]
            if tech.upgradeTo:
                raise ige.GameException("You cannot build obsolete ship design.")
        else:
            tech = Rules.techs[techID]
            if tech.isStructure or not tech.isProject:
                raise ige.GameException('You cannot construct this technology.')
            elif tech.globalDisabled:
                raise ige.GameException('You cannot construct targeted project.')
        neededSR = {}
        for sr in tech.buildSRes:
            nSR = neededSR.get(sr, 0) + tech.buildSRes[sr] * quantity
            if player.stratRes.get(sr, 0) < nSR:
                raise ige.GameException("You do not own required strategic resource(s)")
            neededSR[sr] = nSR
        # consume strategic resources
        for sr in neededSR:
            player.stratRes[sr] -= neededSR[sr]
        # start construction
        item = IDataHolder()
        item.techID = techID
        item.quantity = int(quantity)
        item.changePerc = 0
        item.isShip = bool(isShip)
        item.reportFin = bool(reportFinished)
        item.type = Const.T_TASK
        player.prodQueues[queue].append(item)
        return player.prodQueues[queue], player.stratRes

    @public(Const.AL_FULL)
    def changeGlobalConstruction(self, tran, player, queue, index, quantity):
        if index < 0 or index >= len(player.prodQueues[queue]):
            raise ige.GameException("No such item in the construction queue.")

        if quantity < 1:
            raise ige.GameException("Quantity must be greater than 0")

        item = player.prodQueues[queue][index]
        if item.isShip:
            tech = player.shipDesigns[item.techID]
        else:
            tech = Rules.techs[item.techID]

        quantityChange = quantity - player.prodQueues[queue][index].quantity

        neededSR = {}
        for sr in tech.buildSRes:
            nSR = neededSR.get(sr, 0) + tech.buildSRes[sr] * quantityChange
            if player.stratRes.get(sr, 0) < nSR:
                raise ige.GameException("You do not own required strategic resource(s)")
            neededSR[sr] = nSR
        # consume strategic resources
        for sr in neededSR:
            player.stratRes[sr] += (-1 * neededSR[sr])

        player.prodQueues[queue][index].quantity = quantity
        player.prodQueues[queue][index].const = tech.buildProd * quantity
        return player.prodQueues[queue], player.stratRes

    @public(Const.AL_FULL)
    def abortGlobalConstruction(self, tran, player, queue, index):
        if len(player.prodQueues) <= queue or queue < 0:
            raise ige.GameException('Invalid queue.')
        if len(player.prodQueues[queue]) <= index or index < 0:
            raise ige.GameException('Invalid task.')
        item = player.prodQueues[queue][index]
        # return strategic resources
        #is ship
        if item.techID < 1000:
            tech = player.shipDesigns[item.techID]
        else:
            tech = Rules.techs[item.techID]
        for sr in tech.buildSRes:
            player.stratRes[sr] += item.quantity * tech.buildSRes[sr]
        player.prodQueues[queue].pop(index)
        return player.prodQueues[queue], player.stratRes

    @public(Const.AL_FULL)
    def moveGlobalConstrItem(self, tran, player, queue, index, rel):
        if index >= len(player.prodQueues[queue]):
            raise ige.GameException('No such item in the construction queue.')
        if index + rel < 0 or index + rel >= len(player.prodQueues[queue]):
            raise ige.GameException('Cannot move.')
        item = player.prodQueues[queue][index]
        del player.prodQueues[queue][index]
        player.prodQueues[queue].insert(index + rel, item)
        return player.prodQueues[queue]

    def getReferences(self, tran, obj):
        return obj.fleets

    def loggedIn(self, tran, obj):
        obj.lastLogin = time.time()

    @public(Const.AL_OWNER)
    def resign(self, tran, obj):
        """Remove player from the game. Give remaining planets, ... to the REBELS"""
        # cannot resign when time is stopped
        # TODO smarted conditions (like cannot resign twice a week or so)
        galaxy = tran.db[obj.galaxy]
        if galaxy.scenario == Const.SCENARIO_SINGLE:
            raise ige.GameException('You cannot resign current game - it is single player game.')
        if not obj.timeEnabled:
            raise ige.GameException('You cannot resign current game - time is stopped.')
        log.debug("Resigning player", obj.oid)
        # morph player to AI
        obj.type = self.resignTo
        self.cmd(obj).upgrade(tran, obj)
        self.cmd(obj).update(tran, obj)
        # reregister
        tran.gameMngr.removePlayer(obj.oid)
        self.cmd(obj).register(tran, obj, obj.galaxy)

    @public(Const.AL_ADMIN)
    def delete(self, tran, obj):
        # check whether it is AI or normal player
        log.debug("Deleting player", obj.oid)
        # delete relations
        for playerID in tran.db[Const.OID_UNIVERSE].players:
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

    @public(Const.AL_ADMIN)
    def giveUp(self, tran, obj, playerID):
        """Remove player from the game. Give remaining planets, ... to the specified player"""
        # cannot resign when time is stopped
        # TODO smarted conditions (like cannot resign twice a week or so)
        if not obj.timeEnabled:
            raise ige.GameException('You cannot resign current game - time is stopped.')
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
            tran.db[Const.OID_UNIVERSE].players.remove(obj.oid)
        except ValueError:
            pass

    @public(Const.AL_OWNER)
    def addShipDesign(self, tran, obj, name, hullID, eqIDs):
        """Add ship design to the database of designs."""
        # normalize design
        name = name.strip()
        # check technologies
        if hullID not in obj.techs:
            raise ige.GameException("You do not posses this hull type.")
        for techID in eqIDs:
            if techID not in obj.techs:
                raise ige.GameException("You do not posses technology(ies) to construct this ship.")
        # create spec (throws exception for invad ones)
        spec = ShipUtils.makeShipMinSpec(obj, name, hullID, eqIDs, [])
        # check number of designs
        if len(obj.shipDesigns) > Rules.shipMaxDesigns:
            raise ige.GameException("No space to store design.")
        # check name of designs
        for designID in obj.shipDesigns:
            if obj.shipDesigns[designID].name == name:
                raise ige.GameException("Design name is already used.")
        if re.match("^\s*$",name):
            raise ige.GameException("Design name must not be entirely whitespace.")
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

    @public(Const.AL_OWNER)
    def addBuoy(self, tran, obj, systemID, text, type):
        """Add new buoy to player buoys."""
        # delete buoy
        if not text:
            if systemID in obj.buoys:
                del obj.buoys[systemID]
                return obj.buoys
            else:
                raise ige.GameException("Buoy at specified system does not exist.")

        if type not in (Const.BUOY_PRIVATE, Const.BUOY_TO_ALLY, Const.BUOY_TO_SCANNERSHARE):
            raise ige.GameException("Wrong bouy type.")

        # edit buoy
        if systemID in obj.buoys:
            obj.buoys[systemID] = (text, type)
            return obj.buoys

        if len(obj.buoys) >= 30:
            raise ige.GameException("You cannot add more than 30 buoys.")

        if tran.db[systemID].type not in (Const.T_SYSTEM, Const.T_WORMHOLE):
            raise ige.GameException("You can add buoy only to system.")

        # new buoy
        if len(text) > 0:
            obj.buoys[systemID] = (text, type)

        return obj.buoys

    @public(Const.AL_OWNER)
    def scrapShipDesign(self, tran, obj, designID):
        """Remove ship design from the database of designs and remove all
            active ships using this design."""
        # check design ID
        if designID not in obj.shipDesigns:
            raise ige.GameException("No such design.")
        # delete ships
        for fleetID in obj.fleets[:]: # make copy, fleet can be deleted
            fleet = tran.db[fleetID]
            self.cmd(fleet).deleteDesign(tran, fleet, designID)
        # delete tasks
        for planetID in obj.planets:
            planet = tran.db[planetID]
            self.cmd(planet).deleteDesign(tran, planet, designID)
        # delete from global queues
        for queueID in xrange(len(obj.prodQueues)):
            queue = obj.prodQueues[queueID][:]
            for taskID in xrange(len(queue)):
                if obj.prodQueues[queueID][taskID].techID == designID:
                    self.cmd(obj).abortGlobalConstruction(tran, obj, queueID, taskID)
        # clear upgradeTo
        for tmpDesignID in obj.shipDesigns:
            spec = obj.shipDesigns[tmpDesignID]
            if spec.upgradeTo == designID:
                spec.upgradeTo = 0
        # delete design
        del obj.shipDesigns[designID]
        return obj.shipDesigns, obj.fleets, obj.stratRes, obj.prodQueues

    def getShipDesign(self,tran,obj,designID):
        if designID not in obj.shipDesigns:
            raise ige.GameException("No such design.")
        return obj.shipDesigns[designID]

    @public(Const.AL_OWNER)
    def upgradeShipDesign(self, tran, obj, oldDesignID, newDesignID):
        # check designs ID
        if oldDesignID not in obj.shipDesigns:
            raise ige.GameException("No such design.")
        if newDesignID not in obj.shipDesigns:
            raise ige.GameException("No such design.")
        if oldDesignID == newDesignID:
            raise ige.GameException("Designs are the same.")
        oldSpec = obj.shipDesigns[oldDesignID]
        newSpec = obj.shipDesigns[newDesignID]
        if oldSpec.upgradeTo:
            raise ige.GameException("Old design has already been made obsolete.")
        if newSpec.upgradeTo:
            raise ige.GameException("New design has already been made obsolete.")
        if oldSpec.combatClass != newSpec.combatClass:
            raise ige.GameException("Designs must be of the same combat class.")
        # set old design as upgradable
        oldSpec.upgradeTo = newDesignID
        # if something is upgraded to oldDesign change it to new design
        for desID in obj.shipDesigns:
            if obj.shipDesigns[desID].upgradeTo == oldDesignID:
                obj.shipDesigns[desID].upgradeTo = newDesignID
        # compute strat res difference
        stratRes = {}
        for sr in oldSpec.buildSRes:
            stratRes[sr] = stratRes.get(sr, 0) - oldSpec.buildSRes[sr]
        for sr in newSpec.buildSRes:
            stratRes[sr] = stratRes.get(sr, 0) + newSpec.buildSRes[sr]
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
            # upgrade global queue as well
            for queue in obj.prodQueues:
                for task in queue:
                    if task.techID == oldDesignID:
                        task.techID = newDesignID
            tasksUpgraded = True
        else:
            log.debug("upgradeShipDesing - NOT upgrading tasks")
        return obj.shipDesigns, obj.stratRes, tasksUpgraded, obj.prodQueues

    @public(Const.AL_OWNER)
    def cancelUpgradeShipDesign(self, tran, obj, designID):
        # check designs ID
        if designID not in obj.shipDesigns:
            raise ige.GameException("No such design.")
        obj.shipDesigns[designID].upgradeTo = Const.OID_NONE
        return obj.shipDesigns

    @public(Const.AL_FULL)
    def startResearch(self, tran, obj, techID, improveToMax = 0):
        if len(obj.rsrchQueue) > Rules.maxRsrchQueueLen:
            ige.GameException('Queue is full.')
        tech = Rules.techs[techID]
        # player has to be a right race
        if obj.race not in tech.researchRaces:
            raise ige.GameException("Your race cannot research this technology.")
        # item cannot be researched twice
        for tmpTech in obj.rsrchQueue:
            if tmpTech.techID == techID:
                raise ige.GameException('Technology is already sheduled for research.')
        # disabled?
        for tmpTechID in obj.techs:
            if techID in Rules.techs[tmpTechID].researchDisables:
                raise ige.GameException("Previous research has disabled this technology.")
        # check requirements
        for tmpTechID, improvement in tech.researchRequires:
            if tmpTechID not in obj.techs or obj.techs[tmpTechID] < improvement:
                raise ige.GameException('You cannot research this technology yet.')
        improvement = obj.techs.get(techID, Rules.techBaseImprovement - 1) + 1
        if improvement > Rules.techMaxImprovement or improvement > tech.maxImprovement:
            raise ige.GameException('You cannot improve this technology further.')
        if tech.level > obj.techLevel:
            raise ige.GameException("Your technological level is insufficient.")
        # check strategic resources
        if improvement == 1:
            for stratRes in tech.researchReqSRes:
                if obj.stratRes.get(stratRes, 0) < 1:
                    raise ige.GameException("Required strategy resource missing.")
        item = IDataHolder()
        item.techID = techID
        item.improvement = improvement
        item.currSci = 0
        item.changeSci = 0
        item.improveToMax = improveToMax
        item.type = Const.T_RESTASK
        obj.rsrchQueue.append(item)
        return obj.rsrchQueue

    @public(Const.AL_FULL)
    def abortResearch(self, tran, obj, index):
        if index >= len(obj.rsrchQueue) or index < 0:
            ige.GameException('No such item in queue.')
        del obj.rsrchQueue[index]
        return obj.rsrchQueue

    @public(Const.AL_FULL)
    def editResearch(self, tran, obj, index, improveToMax = 0):
        if index >= len(obj.rsrchQueue) or index < 0:
            ige.GameException('No such item in queue.')
        obj.rsrchQueue[index].improveToMax = improveToMax
        return obj.rsrchQueue

    @public(Const.AL_FULL)
    def moveResearch(self, tran, obj, index, rel):
        if index >= len(obj.rsrchQueue):
            raise ige.GameException('No such item in the researcg queue.')
        if index + rel < 0 or index + rel >= len(obj.rsrchQueue):
            raise ige.GameException('Cannot move.')
        item = obj.rsrchQueue[index]
        del obj.rsrchQueue[index]
        obj.rsrchQueue.insert(index + rel, item)
        return obj.rsrchQueue

    @public(Const.AL_FULL)
    def redirectShips(self, tran, obj, sourceSystemID, targetSystemID):
        # check sourceSystemID
        ok = 0
        if sourceSystemID == targetSystemID:
            targetSystemID = Const.OID_NONE
        for planetID in tran.db[sourceSystemID].planets:
            if tran.db[planetID].owner == obj.oid:
                ok = 1
        if not ok:
            raise ige.GameException("You must own planet in the source system")
        # check targetSystemID
        if targetSystemID != Const.OID_NONE and 0: # TODO: switch on
            ok = 0
            for planetID in tran.db[targetSystemID].planets:
                if tran.db[planetID].owner == obj.oid:
                    ok = 1
            if not ok:
                raise ige.GameException("You must own planet in the target system")
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

    @public(Const.AL_NONE)
    def getPublicInfo(self, tran, obj):
        result = IObject.getPublicInfo(self, tran, obj)
        result.type = obj.type
        result.name = obj.name
        return result

    @public(Const.AL_OWNER)
    def changePactCond(self, tran, obj, playerID, pactID, state, conditions):
        log.debug("changePactCond", obj.oid, playerID, pactID)
        # must have a contact
        if playerID not in obj.diplomacyRels:
            raise ige.GameException('No contact with this player.')
        player = tran.db[playerID]
        # must be a player
        if player.type not in Const.PLAYER_TYPES:
            raise ige.GameException('Pacts can be offered to players only.')
        # check pactID
        pact = Rules.pactDescrs.get(pactID, None)
        if not pact:
            raise ige.GameException('No such pact type.')
        # check state
        if state not in (Const.PACT_OFF, Const.PACT_INACTIVE, Const.PACT_ACTIVE):
            raise ige.GameException("Wrong pact state")
        # check conditions
        for tmpPactID in conditions:
            pact = Rules.pactDescrs.get(tmpPactID, None)
            if not pact:
                raise ige.GameException('No such pact type.')
        # record pact
        dipl = self.cmd(obj).getDiplomacyWith(tran, obj, playerID)
        dipl.pacts[pactID] = [state]
        dipl.pacts[pactID].extend(conditions)
        # if state if Const.PACT_OFF, disable state on partner's side
        if state == Const.PACT_OFF:
            partner = tran.db[playerID]
            dipl = self.cmd(partner).getDiplomacyWith(tran, partner, obj.oid)
            if pactID in dipl.pacts:
                dipl.pacts[pactID][0] = Const.PACT_OFF
            else:
                dipl.pacts[pactID] = [Const.PACT_OFF]
        return obj.diplomacyRels

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
            dipl.type = Const.T_DIPLREL
            dipl.pacts = {
                Const.PACT_ALLOW_CIVILIAN_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_CIVILIAN_SHIPS]
            }
            dipl.relation = obj.defaultRelation
            dipl.relChng = 0
            dipl.lastContact = tran.db[Const.OID_UNIVERSE].turn
            dipl.contactType = Const.CONTACT_NONE
            dipl.stats = None
            if playerID != obj.oid:
                obj.diplomacyRels[playerID] = dipl
            else:
                log.debug("getDiplomacyWith myself", obj.oid)
        return dipl

    @public(Const.AL_OWNER)
    def getPartyDiplomacyRels(self, tran, obj, partyID):
        if partyID not in obj.diplomacyRels:
            return None, None
        if obj.diplomacyRels[partyID].contactType == Const.CONTACT_NONE:
            return obj.diplomacyRels[partyID], None
        party = tran.db[partyID]
        return obj.diplomacyRels[partyID], party.diplomacyRels.get(obj.oid, None)

    def isPactActive(self, tran, obj, partnerID, pactID):
        #@log.debug("isPactActive", obj.oid, partnerID, pactID)
        if partnerID not in obj.diplomacyRels:
            return 0
        partner = tran.db[partnerID]
        partnerDipl = partner.diplomacyRels.get(obj.oid, None)
        if not partnerDipl:
            return 0
        return partnerDipl.pacts.get(pactID, [Const.PACT_OFF])[0] == Const.PACT_ACTIVE

    def deleteDiplomacyWith(self, tran, obj, playerID):
        if playerID in obj.diplomacyRels:
            del obj.diplomacyRels[playerID]

    @public(Const.AL_FULL)
    def getRelationTo(self, tran, obj, objID):
        if objID == Const.OID_NONE:
            return Const.REL_UNDEF
        if obj.oid == objID:
            return Const.REL_UNITY
        if obj.governorOf:
            leader = tran.db[obj.governorOf]
            return self.cmd(leader).getRelationTo(tran, leader, objID)
        dipl = obj.diplomacyRels.get(objID, None)
        if dipl:
            return dipl.relation
        else:
            return obj.defaultRelation

    @public(Const.AL_OWNER)
    def setVoteFor(self, tran, obj, playerID):
        if playerID not in obj.diplomacyRels and playerID != obj.oid and playerID != Const.OID_NONE:
            raise ige.GameException("No contact with this commander.")
        # check type
        if playerID != Const.OID_NONE:
            player = tran.db[playerID]
            if player.type != Const.T_PLAYER:
                raise ige.GameException("You cannot vote for this player.")
        # set
        obj.voteFor = playerID
        return obj.voteFor

    @public(Const.AL_ADMIN)
    def processDIPLPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        turn = tran.db[Const.OID_UNIVERSE].turn
        # record changes from valid pacts
        for partyID in obj.diplomacyRels:
            dipl = obj.diplomacyRels[partyID]
            # check contact
            if dipl.contactType == Const.CONTACT_NONE:
                #@log.debug("Skipping contact", obj.oid, partyID)
                continue
            # base change of relation
            dipl.relChng += Rules.baseRelationChange
            # process pacts
            for pactID in dipl.pacts:
                #@log.debug("Processing pact", obj.oid, partyID, pactID, dipl.pacts[pactID])
                if dipl.pacts[pactID][0] != Const.PACT_ACTIVE:
                    continue
                pactSpec = Rules.pactDescrs[pactID]
                if dipl.relation < pactSpec.validityInterval[0] or \
                    dipl.relation > pactSpec.validityInterval[1] or \
                    dipl.relChng < Rules.relLostWhenAttacked / 2:
                    # skip this non active pact, mark it as off
                    # mark all pact off when attacked
                    dipl.pacts[pactID][0] = Const.PACT_OFF
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
            dipl.relation = min(dipl.relation, Const.REL_ALLY_HI)
            dipl.relation = max(dipl.relation, Const.REL_ENEMY_LO)
            #@log.debug('IPlayer', 'Final relation', obj.oid, partyID, dipl.relation, dipl.relChng)

    @public(Const.AL_OWNER)
    def getScannerMap(self, tran, obj):
        scanLevels = {}
        # full map for the admin
        if obj.oid == Const.OID_ADMIN:
            universe = tran.db[Const.OID_UNIVERSE]
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
        # fixing system scan level for mine fields
        systems = {}
        for planetID in obj.planets:
            systems[tran.db[planetID].compOf] = None
        for systemID in systems.keys():
            scanLevels[systemID] = Rules.partnerScanPwr
        # player's map
        for objID in obj.staticMap:
            scanLevels[objID] = max(scanLevels.get(objID, 0), obj.staticMap[objID])
        for objID in obj.dynamicMap:
            scanLevels[objID] = max(scanLevels.get(objID, 0), obj.dynamicMap[objID])
        # parties' map
        for partnerID in obj.diplomacyRels:
            if self.cmd(obj).isPactActive(tran, obj, partnerID, Const.PACT_SHARE_SCANNER):
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
            # add movement validation data
            if tmpObj.type in (Const.T_SYSTEM,Const.T_WORMHOLE) and objID not in obj.validSystems:
                obj.validSystems.append(objID)
            for info in self.cmd(tmpObj).getScanInfos(tran, tmpObj, level, obj):
                if (info.oid not in map) or (info.scanPwr > map[info.oid].scanPwr):
                    map[info.oid] = info

        return map

    #@public(Const.AL_OWNER)
    def mergeScannerMap(self, tran, obj, map):
        #@log.debug(obj.oid, "Merging scanner map")
        contacts = {}
        for object, level in map.iteritems():
            objID = object.oid
            if object.type in (Const.T_SYSTEM, Const.T_WORMHOLE):
                obj.staticMap[objID] = max(obj.staticMap.get(objID, 0), level)
                contacts.update(object.scannerPwrs)
            elif object.type == Const.T_FLEET:
                obj.dynamicMap[objID] = max(obj.dynamicMap.get(objID, 0), level)
                contacts[object.owner] = None
            else:
                raise ige.GameException("Unsupported type %d" % object.type)
        if obj.oid in contacts:
            del contacts[obj.oid]
        if Const.OID_NONE in contacts:
            del contacts[Const.OID_NONE]
        for partyID in contacts:
            # add to player's contacts
            dipl = self.cmd(obj).getDiplomacyWith(tran, obj, partyID)
            dipl.contactType = max(dipl.contactType, Const.CONTACT_DYNAMIC)
            dipl.lastContact = tran.db[Const.OID_UNIVERSE].turn
            # add to detected owner's contacts
            owner = tran.db[partyID]
            assert owner.type in Const.PLAYER_TYPES
            dipl = self.cmd(obj).getDiplomacyWith(tran, owner, obj.oid)
            dipl.contactType = max(dipl.contactType, Const.CONTACT_DYNAMIC)
            dipl.lastContact = tran.db[Const.OID_UNIVERSE].turn

    @public(Const.AL_ADMIN)
    def processRSRCHPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        # sci pts from allies
        pts = obj.sciPoints
        for partnerID in obj.diplomacyRels:
            if self.cmd(obj).isPactActive(tran, obj, partnerID, Const.PACT_MINOR_SCI_COOP):
                partner = tran.db[partnerID]
                pactSpec = Rules.pactDescrs[Const.PACT_MINOR_SCI_COOP]
                pts += min(
                    int(partner.sciPoints * pactSpec.effectivity),
                    int(obj.sciPoints * pactSpec.effectivity),
                )
            if self.cmd(obj).isPactActive(tran, obj, partnerID, Const.PACT_MAJOR_SCI_COOP):
                partner = tran.db[partnerID]
                pactSpec = Rules.pactDescrs[Const.PACT_MAJOR_SCI_COOP]
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
                    Utils.sendMessage(tran, obj, Const.MSG_MISSING_STRATRES, Const.OID_NONE, stratRes)
                    canResearch = 0
                    break
            for tmpTechID in obj.techs:
                if item.techID in Rules.techs[tmpTechID].researchDisables:
                    canResearch = 0
                    Utils.sendMessage(tran, obj, Const.MSG_DELETED_RESEARCH, Const.OID_NONE, item.techID)
                    del obj.rsrchQueue[index]
                    index -= 1
                    break
            if tech.level > obj.techLevel:
                canResearch = 0
                Utils.sendMessage(tran, obj, Const.MSG_DELETED_RESEARCH, Const.OID_NONE, item.techID)
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
                Utils.sendMessage(tran, obj, Const.MSG_COMPLETED_RESEARCH, Const.OID_NONE, item.techID)
                # update derived attributes of player
                self.cmd(obj).update(tran, obj)
                # repeat research if required by player
                if item.improveToMax == 1 and item.improvement < Rules.techMaxImprovement:
                    # reinsert the item on the top of the queue
                    self.cmd(obj).startResearch(tran, obj, item.techID, improveToMax = 1)
                    idx = len(obj.rsrchQueue) - 1
                    self.cmd(obj).moveResearch(tran, obj, idx, - idx)
        if epts > 0 and 0: # TODO: remove me
            Utils.sendMessage(tran, obj, Const.MSG_WASTED_SCIPTS, Const.OID_NONE, epts)
            return
        # oops we have negative epts (AI does not regress)
        isAI = obj.type in Const.AI_PLAYER_TYPES
        while epts < 0 and not isAI:
            log.debug("Not enough RP", epts, obj.oid)
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
                    item.type = Const.T_RESTASK
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

    @public(Const.AL_ADMIN)
    def processACTIONPhase(self, tran, obj, data):
        return NotImplementedError()

    @public(Const.AL_ADMIN)
    def processINITPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
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
        # clear contacts and delete too old rels
        turn = tran.db[Const.OID_UNIVERSE].turn
        for objID in obj.diplomacyRels.keys():
            dipl = obj.diplomacyRels[objID]
            # reset contact type
            obj.diplomacyRels[objID].contactType = Const.CONTACT_NONE
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

    @public(Const.AL_ADMIN)
    def processFINALPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        #try/except so that entire final process doesn't break on error in sub-phase
        try:
            self.cmd(obj).processRSRCHPhase(tran, obj, data)
        except:
            log.warning('Cannot execute FINAL/RSRCH on %d' % (obj.oid))
        try:
            self.cmd(obj).processDIPLPhase(tran, obj, data)
        except:
            log.warning('Cannot execute FINAL/DIPL on %d' % (obj.oid))
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
                tech = Rules.techs[slot[Const.STRUCT_IDX_TECHID]]
                if tech.govPwr > 0 and slot[Const.STRUCT_IDX_STATUS] & Const.STRUCT_STATUS_ON:
                    eff = Utils.getTechEff(tran, slot[Const.STRUCT_IDX_TECHID], obj.oid)
                    obj.govPwr = max(int(tech.govPwr * eff * (slot[Const.STRUCT_IDX_OPSTATUS] / 100.0)), obj.govPwr)
        # compute government controll range
        if not hasattr(obj,"tmpPopDistr"): #when player is force-resigned, tmpPopDistr is unset. This is easiest fix.
            obj.tmpPopDistr = {}
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
            if self.cmd(obj).isPactActive(tran, obj, partnerID, Const.PACT_MINOR_CP_COOP):
                partner = tran.db[partnerID]
                pactSpec = Rules.pactDescrs[Const.PACT_MINOR_CP_COOP]
                sum += min(
                    partner.stats.prodProd * pactSpec.effectivity,
                    obj.stats.prodProd * pactSpec.effectivity,
                )
            if self.cmd(obj).isPactActive(tran, obj, partnerID, Const.PACT_MAJOR_CP_COOP):
                partner = tran.db[partnerID]
                pactSpec = Rules.pactDescrs[Const.PACT_MAJOR_CP_COOP]
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
        # clean up prodEff if prodEff < 0 (prevent abuse)
        if obj.prodEff < 0:
            obj.prodEff = 0.0
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
            getAllyBuoys = False
            getScannerBuoys = False
            if dipl.relation >= Const.REL_ALLY_LO:
                getAllyBuoys = True
            if self.isPactActive(tran, obj, partnerID, Const.PACT_SHARE_SCANNER):
                getScannerBuoys = True
            if (getAllyBuoys or getScannerBuoys):
                partner = tran.db[partnerID]
                if hasattr(partner, "buoys"):
                    for systemID in partner.buoys.keys():
                        toAllyBuoy = Const.BUOY_NONE
                        if getAllyBuoys and partner.buoys[systemID][1] == Const.BUOY_TO_ALLY:
                            toAllyBuoy = (partner.buoys[systemID][0], Const.BUOY_FROM_ALLY, partner.name)
                        elif getScannerBuoys and partner.buoys[systemID][1] == Const.BUOY_TO_SCANNERSHARE:
                            toAllyBuoy = (partner.buoys[systemID][0], Const.BUOY_FROM_ALLY, partner.name)
                        if toAllyBuoy != Const.BUOY_NONE:
                            if systemID in obj.alliedBuoys:
                                obj.alliedBuoys[systemID].append(toAllyBuoy)
                            else:
                                obj.alliedBuoys[systemID] = [toAllyBuoy]
        return None

    ## messaging
    def canSendMsg(self, tran, obj, oid, forum):
        if forum == "INBOX":
            sender = tran.db[oid]
            return oid == Const.OID_ADMIN or (oid in obj.diplomacyRels) or \
                (obj.oid in sender.diplomacyRels)
        if forum == "OUTBOX":
            return obj.oid == oid
        return 0

    @public(Const.AL_OWNER)
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

    @public(Const.AL_OWNER)
    def setResolution(self, tran, obj, x, y):
        if not hasattr(obj,'clientStats'):
            obj.clientStats = {}
        obj.clientStats['x'] = x;
        obj.clientStats['y'] = y;

    def getResolution(self, obj):
        if not hasattr(obj,'clientStats'):
            obj.clientStats = {}
        if 'x' in obj.clientStats and 'y' in obj.clientStats:
            return ("%s,%s" % (obj.clientStats['x'],obj.clientStats['y']))
        else:
            return "0,0"

    @public(Const.AL_FULL)
    def addObsoleteTechs(self, tran, player, techID):
        # add tech
        temp = set([techID])
        player.obsoleteTechs = player.obsoleteTechs | temp
        return player.obsoleteTechs

    @public(Const.AL_FULL)
    def delObsoleteTechs(self, tran, player, techID):
        # del tech
        temp = set([techID])
        player.obsoleteTechs = player.obsoleteTechs - temp
        return player.obsoleteTechs


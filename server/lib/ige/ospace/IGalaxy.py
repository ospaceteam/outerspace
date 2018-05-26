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

import copy
import random

from ige.IObject import IObject
from ige import *
from Const import *
from xml.dom.minidom import Node, parse
from ige.IObject import IObject
from ISystem import ISystem
from ige.IDataHolder import IDataHolder
import os.path, time, Utils, Rules
from ige import log
from Rules import Tech
import IPlayer, IAIPlayer, IAIRenegadePlayer, IAIMutantPlayer, IAIPiratePlayer
import IAIEDENPlayer, IPiratePlayer

import Scanner

from ai_parser import AIList

class IGalaxy(IObject):

    typeID = T_GALAXY
    forums = {"PUBLIC": 112, "NEWS": 112}

    def init(self, obj):
        IObject.init(self, obj)
        #
        obj.name = ""
        obj.owner = OID_NONE
        obj.x = 0.0
        obj.y = 0.0
        obj.radius = 0.0
        obj.centerWeight = 250.0
        obj.systems = []
        obj.startingPos = []
        obj.numOfStartPos = 0
        obj.timeEnabled = 0 # TODO change to 0
        obj.creationTime = 0.0
        obj.imperator = OID_NONE
        obj.description = ""
        obj.scenario = SCENARIO_NONE
        obj.scenarioData = IDataHolder()
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
        # check compOf
        if not tran.db.has_key(obj.compOf) or tran.db[obj.compOf].type != T_UNIVERSE:
            log.debug("CONSISTENCY invalid compOf for galaxy", obj.oid, obj.compOf)
        # TODO: remove after 0.5.72
        if not hasattr(obj, 'scenario'):
            if obj.isSingle:
                obj.scenario = SCENARIO_SINGLE
            else:
                obj.scenario = SCENARIO_OUTERSPACE
        if not hasattr(obj, 'scenarioData'):
            obj.scenarioData = IDataHolder()
        if obj.scenario == SCENARIO_SINGLE and not getattr(obj, 'owner', OID_NONE):
            # singleplayer galaxy owner being the only player present
            players = set([])
            for systemID in obj.systems:
                for planetID in tran.db[systemID].planets:
                    players |= set([tran.db[planetID].owner])
            for playerID in players - set([OID_NONE]):
                player = tran.db[playerID]
                if player.type in [T_PLAYER, T_PIRPLAYER]:
                    obj.owner = playerID
                    break


    update.public = 0

    def getReferences(self, tran, obj):
        return obj.systems

    getReferences.public = 0

    @staticmethod
    def getFreeStartingPosition(db, obj):
        while 1:
            planetID = random.choice(obj.startingPos)
            obj.startingPos.remove(planetID)
            log.debug('Starting point', planetID)
            log.debug('Starting point - owner', db[planetID].owner)
            if db[planetID].owner == OID_NONE:
                return planetID
            if not obj.startingPos:
                raise GameException('No free starting point in the galaxy.')


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
        # remove old messages
        self.cmd(obj).deleteOldMsgs(tran, obj)
        return obj.systems

    processINITPhase.public = 1
    processINITPhase.accLevel = AL_ADMIN

    def processPRODPhase(self, tran, obj, data):
        if obj.timeEnabled:
            return obj.systems

    processPRODPhase.public = 1
    processPRODPhase.accLevel = AL_ADMIN

    def processACTIONPhase(self, tran, obj, data):
        if obj.timeEnabled:
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
        if obj.timeEnabled:
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
        #if obj.timeEnabled:
        return obj.systems

    processFINALPhase.public = 1
    processFINALPhase.accLevel = AL_ADMIN

    def processFINAL2Phase(self, tran, obj, data):
        # save history file
        turn = tran.db[OID_UNIVERSE].turn
        # TODO: reneable history when it's optimized
        if turn % 6 == 0 and False:
            log.debug("Saving history for galaxy", obj.oid, obj.name)
            fh = open(os.path.join(tran.config.configDir,"history/galaxy%d-%06d.xml" % (obj.oid, turn), "w+"))
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


    def loadFromXML(self, tran, obj, file, galaxyType, x, y, name):
        log.message('IGalaxy', 'Parsing XML file...')
        dom = parse(os.path.join('data', file))
        log.message('IGalaxy', 'XML file parsed.')
        assert dom.documentElement.tagName == 'universe'
        for node in dom.documentElement.childNodes:
            if node.nodeType == Node.ELEMENT_NODE and node.tagName == 'galaxy':
                if node.getAttribute('galaxyType') == galaxyType:
                    self.loadDOMNode(tran, obj, node, x, y, name)
                    self.connectWormHoles(tran, obj)
                    return SUCC
        raise GameException('No such id %s in resource' % galaxyType)

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

    def toggleTime(self, tran, obj):
        player = tran.db[obj.owner]
        obj.timeEnabled = 1 - obj.timeEnabled
        self.trickleTimeToPlayers(tran, obj)
        return obj.timeEnabled

    toggleTime.public = 1
    toggleTime.accLevel = AL_OWNER

    def trickleTimeToPlayers(self, tran, obj):
        # enable time for players
        for systemID in obj.systems:
            system = tran.db[systemID]
            for planetID in system.planets:
                planet = tran.db[planetID]
                if planet.owner != OID_NONE:
                    player = tran.db[planet.owner]
                    if player.timeEnabled != obj.timeEnabled:
                        player.timeEnabled = obj.timeEnabled
                        player.lastLogin = time.time()
                        if player.timeEnabled:
                            Utils.sendMessage(tran, player, MSG_ENABLED_TIME, player.oid, None)
                        else:
                            Utils.sendMessage(tran, player, MSG_DISABLED_TIME, player.oid, None)

    def enableTime(self, tran, obj, force = 0, deleteSP = 0, enable = 1):
        log.debug('IGalaxy', 'Checking for time...')
        if not force:
            if obj.timeEnabled:
                return
            canRun = 0
            # We have to give players some time to prepare
            # (as they might be waiting for very long time for this galaxy to be created).
            if obj.creationTime < time.time() - 2 * 24 * 3600:
                log.debug("Two days passed", obj.creationTime, time.time() - 2 * 24 * 3600)
                canRun = 1
            elif obj.scenario == SCENARIO_SINGLE:
                canRun = 1
            if not canRun:
                return 0
        # spawn rebel player on all vacant starting positions
        for positionID in copy.copy(obj.startingPos):
            obj.startingPos.remove(positionID)
            # create new player
            log.debug("Creating new Rebel player", T_AIPLAYER)
            player = self.new(T_AIPLAYER)
            self.cmd(player).register(tran, player, obj.oid)
            player.galaxies.append(obj.oid)
            playerID = player.oid
            # TODO tweak more planet's attrs
            planet = tran.db[positionID]
            # Grant starting technologies (at medium improvement)
            for techID in Rules.techs.keys():
                if Rules.techs[techID].isStarting:
                    player.techs[techID] = (Rules.techBaseImprovement + Rules.techMaxImprovement) / 2
            self.cmd(planet).changeOwner(tran, planet, playerID, 1)
            planet.slots = [
                Utils.newStructure(tran, Tech.PWRPLANTNUK1, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.FARM1, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.FARM1, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.FARM1, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.ANCFACTORY, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.ANCFACTORY, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.ANCRESLAB, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
                Utils.newStructure(tran, Tech.REPAIR1, playerID, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio),
            ]
            planet.storPop = Rules.startingPopulation
            planet.storBio = Rules.startingBio
            planet.storEn = Rules.startingEn
            planet.scannerPwr = Rules.startingScannerPwr
            planet.morale = Rules.maxMorale
            # fleet
            # add basic ships designs
            tempTechs = [Tech.FTLENG1, Tech.SCOCKPIT1, Tech.SCANNERMOD1, Tech.CANNON1,
                Tech.CONBOMB1, Tech.SMALLHULL1, Tech.MEDIUMHULL2, Tech.COLONYMOD2]
            for techID in tempTechs:
                player.techs[techID] = 1
            dummy, scoutID = tran.gameMngr.cmdPool[T_AIPLAYER].addShipDesign(tran, player, "Scout", Tech.SMALLHULL1,
                {Tech.FTLENG1:3, Tech.SCOCKPIT1:1, Tech.SCANNERMOD1:1})
            dummy, fighterID = tran.gameMngr.cmdPool[T_AIPLAYER].addShipDesign(tran, player, "Fighter", Tech.SMALLHULL1,
                {Tech.FTLENG1:3, Tech.SCOCKPIT1:1, Tech.CANNON1:1})
            dummy, bomberID = tran.gameMngr.cmdPool[T_AIPLAYER].addShipDesign(tran, player, "Bomber", Tech.SMALLHULL1,
                {Tech.FTLENG1:3, Tech.SCOCKPIT1:1, Tech.CONBOMB1:1})
            dummy, colonyID = tran.gameMngr.cmdPool[T_AIPLAYER].addShipDesign(tran, player, "Colony Ship", Tech.MEDIUMHULL2,
                {Tech.FTLENG1:4, Tech.SCOCKPIT1:1, Tech.COLONYMOD2:1})
            for techID in tempTechs:
                del player.techs[techID]
            # add small fleet
            log.debug('Creating fleet')
            system = tran.db[planet.compOf]
            fleet = tran.gameMngr.cmdPool[T_FLEET].new(T_FLEET)
            tran.db.create(fleet)
            log.debug('Creating fleet - created', fleet.oid)
            tran.gameMngr.cmdPool[T_FLEET].create(tran, fleet, system, playerID)
            log.debug('Creating fleet - addShips')
            tran.gameMngr.cmdPool[T_FLEET].addNewShip(tran, fleet, scoutID)
            tran.gameMngr.cmdPool[T_FLEET].addNewShip(tran, fleet, scoutID)
            tran.gameMngr.cmdPool[T_FLEET].addNewShip(tran, fleet, fighterID)
            tran.gameMngr.cmdPool[T_FLEET].addNewShip(tran, fleet, fighterID)
            tran.gameMngr.cmdPool[T_FLEET].addNewShip(tran, fleet, colonyID)
            system.scannerPwrs[playerID] = Rules.startingScannerPwr
        # do scanner evaluation because of all new players
        self.cmd(obj).processSCAN2Phase(tran, obj, None)
            # add player to universe
#            log.debug('Adding player to universe')
#            universe = tran.db[OID_UNIVERSE]
#            universe.players.append(playerID)

        # ok, enable time
        log.message('IGalaxy', 'Enabling time for', obj.oid)
        obj.timeEnabled = enable
        # close galaxy
        if deleteSP:
            obj.startingPos = []
        self.trickleTimeToPlayers(tran, obj)

    enableTime.public = 1
    enableTime.accLevel = AL_ADMIN

    def deleteSingle(self, tran, obj):
        if obj.scenario != SCENARIO_SINGLE:
            raise GameException('Only Single Player galaxies can be deleted this way')
        log.debug(obj.oid, "GALAXY - singleplayer delete")
        self.delete(tran, obj)

    deleteSingle.public = 1
    deleteSingle.accLevel = AL_OWNER

    def delete(self, tran, obj):
        log.debug(obj.oid, "GALAXY - delete")
        universe = tran.db[OID_UNIVERSE]
        aiList = AIList(tran.gameMngr.configDir, tran.gameMngr.gameName)
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
            aiList.removeGalaxy(player.login, obj.name)
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
        result.x = obj.x
        result.y = obj.y
        result.radius = obj.radius
        result.type = obj.type
        result.name = obj.name
        result.emrLevel = obj.emrLevel
        result.scenario = obj.scenario
        result.scenarioData = obj.scenarioData
        result.timeEnabled = obj.timeEnabled
        return result

    getPublicInfo.public = 1
    getPublicInfo.accLevel = AL_NONE

    def getDescription(self,obj):
        return obj.description

    getPublicInfo.public = 1
    getPublicInfo.accLevel = AL_NONE

    def setupEnvironment(self, tran, obj):
        universe = tran.db[OID_UNIVERSE]
        # we will first scan galaxy, to determine which environments are available
        # this way, we will create only players that are needed, and not all types
        vacant_planets = {}
        for systemID in obj.systems:
            system = tran.db[systemID]
            for planetID in system.planets:
                planet = tran.db[planetID]
                # renegades
                if planet.plStratRes in (SR_TL1A, SR_TL1B) and planet.owner == OID_NONE:
                    try:
                        vacant_planets[T_AIRENPLAYER] += [planetID]
                    except KeyError:
                        vacant_planets[T_AIRENPLAYER] = [planetID]
                # pirates
                if planet.plStratRes in (SR_TL3A, SR_TL3B, SR_TL3C) and planet.owner == OID_NONE:
                    try:
                        vacant_planets[T_AIPIRPLAYER] += [planetID]
                    except KeyError:
                        vacant_planets[T_AIPIRPLAYER] = [planetID]
                # EDEN
                if planet.plStratRes in (SR_TL5A, SR_TL5B, SR_TL5C) and planet.owner == OID_NONE:
                    try:
                        vacant_planets[T_AIEDENPLAYER] += [planetID]
                    except KeyError:
                        vacant_planets[T_AIEDENPLAYER] = [planetID]
                # mutants
                if planet.plDisease != 0 and planet.owner == OID_NONE:
                    try:
                        vacant_planets[T_AIMUTPLAYER] += [planetID]
                    except KeyError:
                        vacant_planets[T_AIMUTPLAYER] = [planetID]
        # iterate over types, create players if needed (it should be) and fill in vacant planets
        for playerType in vacant_planets:
            found = 0
            for playerID in universe.players:
                player = tran.db[playerID]
                if obj.oid in player.galaxies and player.type == playerType:
                    found = 1
                    break
            if not found:
                # create new player
                log.debug("Creating new player", playerType)
                player = self.new(playerType)
                self.cmd(player).register(tran, player, obj.oid)
                player.galaxies.append(obj.oid)
            # now we have a player, let's iterate over vacant planets and set them up
            for planetID in vacant_planets[playerType]:
                planet = tran.db[planetID]
                self.cmd(planet).changeOwner(tran, planet, player.oid, 1)
                if playerType == T_AIRENPLAYER:
                    IAIRenegadePlayer.IAIRenegadePlayer.setStartingPlanet(tran, planet)
                elif playerType == T_AIPIRPLAYER:
                    IAIPiratePlayer.IAIPiratePlayer.setStartingPlanet(tran, planet)
                elif playerType == T_AIEDENPLAYER:
                    IAIEDENPlayer.IAIEDENPlayer.setStartingPlanet(tran, planet)
                elif playerType == T_AIMUTPLAYER:
                    IAIMutantPlayer.IAIMutantPlayer.setStartingPlanet(tran, planet)

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

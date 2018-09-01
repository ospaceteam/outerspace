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

import os.path
import time
import copy
import random

from xml.dom.minidom import Node, parse

import ige
from IAIPlayer import IAIPlayer
from IAIEDENPlayer import IAIEDENPlayer
from IAIMutantPlayer import IAIMutantPlayer
from IAIPiratePlayer import IAIPiratePlayer
from IAIRenegadePlayer import IAIRenegadePlayer
import Const
import Rules
import Scanner
import Utils

from ige import log
from ige.IObject import IObject
from ige.IDataHolder import IDataHolder
from ige.IObject import public
from ISystem import ISystem
from Rules import Tech


class IGalaxy(IObject):

    typeID = Const.T_GALAXY
    forums = {"PUBLIC": 112, "NEWS": 112}

    def init(self, obj):
        IObject.init(self, obj)
        #
        obj.name = ""
        obj.owner = Const.OID_NONE
        obj.x = 0.0
        obj.y = 0.0
        obj.radius = 0.0
        obj.centerWeight = 250.0
        obj.systems = []
        obj.startingPos = []
        obj.numOfStartPos = 0
        obj.timeEnabled = None # none instead of False, to know when first enablement is happening
        obj.timePaused = False # this is only used for player-initiated pause, prevents autoenablement
        obj.creationTurn = 0
        obj.imperator = Const.OID_NONE
        obj.description = ""
        obj.scenario = Const.SCENARIO_NONE
        obj.scenarioData = IDataHolder()
        # electromagnetic radiation
        obj.emrLevel = 1.0
        obj.emrTrend = 1.0
        obj.emrTime = 0
        # galaxy keeps track of it's own time as well (because of pauses)
        obj.galaxyTurn = 0

    def update(self, tran, obj):
        # check existence of all systems
        if 0:
            for systemID in obj.systems:
                if not tran.db.has_key(systemID):
                    log.debug("CONSISTENCY - system %d from galaxy %d does not exists" % (systemID, obj.oid))
                elif tran.db[systemID].type not in (Const.T_SYSTEM, Const.T_WORMHOLE):
                    log.debug("CONSISTENCY - system %d from galaxy %d is not a Const.T_SYSTEM or Const.T_WORMHOLE" % (systemID, obj.oid))
        # validate starting positions
        for planetID in obj.startingPos[:]:
            if not tran.db.has_key(planetID):
                log.debug("REMOVING nonexistent obj from start pos", planetID)
                obj.startingPos.remove(planetID)
                continue
            planet = tran.db[planetID]
            if planet.type != Const.T_PLANET:
                log.debug("REMOVING ??? from start pos", planetID)
                obj.startingPos.remove(planetID)
        # check compOf
        if not tran.db.has_key(obj.compOf) or tran.db[obj.compOf].type != Const.T_UNIVERSE:
            log.debug("CONSISTENCY invalid compOf for galaxy", obj.oid, obj.compOf)

    def getReferences(self, tran, obj):
        return obj.systems

    @staticmethod
    def getFreeStartingPosition(db, obj):
        while 1:
            planetID = random.choice(obj.startingPos)
            obj.startingPos.remove(planetID)
            log.debug('Starting point', planetID)
            log.debug('Starting point - owner', db[planetID].owner)
            if db[planetID].owner == Const.OID_NONE:
                return planetID
            if not obj.startingPos:
                raise ige.GameException('No free starting point in the galaxy.')

    @public(Const.AL_ADMIN)
    def processINITPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        # compute emr level
        turn = tran.db[Const.OID_UNIVERSE].turn
        # galaxy keeps track of it's own time (because of pauses)
        obj.galaxyTurn += 1
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
                        "data": (obj.oid, Const.MSG_GNC_EMR_FORECAST, obj.oid, turn, (obj.emrTrend, obj.emrTime)),
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

    @public(Const.AL_ADMIN)
    def processPRODPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        return obj.systems

    @public(Const.AL_ADMIN)
    def processACTIONPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        return obj.systems

    @public(Const.AL_ADMIN)
    def processSCAN2Phase(self, tran, obj, data):
        # data == True means forced scan (first after generating the galaxy)
        if not obj.timeEnabled and not data:
            return
        # compute scanner for all objects on the map
        playerMap = Scanner.computeMap(self, tran, obj)
        # distribute map
        for playerID, map in playerMap.iteritems():
            player = tran.db[playerID]
            self.cmd(player).mergeScannerMap(tran, player, map)
        return

    @public(Const.AL_ADMIN)
    def processBATTLEPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        return obj.systems

    @public(Const.AL_ADMIN)
    def processFINALPhase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        # validate starting positions
        remove = []
        for planetID in obj.startingPos:
            planet = tran.db[planetID]
            if planet.owner != Const.OID_NONE:
                remove.append(planetID)
        for planetID in remove:
            obj.startingPos.remove(planetID)
        return obj.systems

    @public(Const.AL_ADMIN)
    def processFINAL2Phase(self, tran, obj, data):
        if not obj.timeEnabled:
            return
        # save history file
        turn = tran.db[Const.OID_UNIVERSE].turn
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
                    if ownerID != Const.OID_NONE:
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


    @public(Const.AL_ADMIN)
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
                    return Const.SUCC
        raise ige.GameException('No such id %s in resource' % galaxyType)

    def loadDOMNode(self, tran, obj, node, x, y, name):
        obj.name = name
        obj.x = float(x)
        obj.y = float(y)
        xoff = x - float(node.getAttribute('x'))
        yoff = y - float(node.getAttribute('y'))
        obj.creationTurn = tran.db[Const.OID_UNIVERSE].turn
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
                    raise ige.GameException('Unknown element %s' % name)
        return Const.SUCC

    def connectWormHoles(self, tran, obj):
        wormHoles = {}
        for holeID in obj.systems:
            wormHole = tran.db[holeID]
            if wormHole.type == Const.T_WORMHOLE:
                wormHoles[wormHole.name] = holeID

        for holeID in obj.systems:
            wormHole = tran.db[holeID]
            if wormHole.type != Const.T_WORMHOLE:
                continue
            if len(wormHole.destination) == 0:
                raise ige.GameException('Wrong WormHole(%d) definition' % holeID)
            if wormHole.destination == wormHole.name:
                raise ige.GameException('Same destination as position for WormHole(%d)' % holeID)
            destinationOid = wormHoles[wormHole.destination]
            if destinationOid == Const.OID_NONE:
                raise ige.GameException('WormHole(%d) has wrong destination ''%s''' % (holeID, wormHole.destination))
            wormHole.destinationOid = destinationOid

    def createSystem(self, tran, obj):
        system = self.new(Const.T_SYSTEM)
        system.compOf = obj.oid
        oid = tran.db.create(system)
        obj.systems.append(oid)
        return oid

    def createWormHole(self, tran, galaxy):
        hole = self.new(Const.T_WORMHOLE)
        hole.compOf = galaxy.oid
        oid = tran.db.create(hole)
        galaxy.systems.append(oid)
        return oid

    @public(Const.AL_OWNER)
    def toggleTime(self, tran, obj):
        player = tran.db[obj.owner]
        obj.timeEnabled = not obj.timeEnabled
        obj.timePaused = not obj.timeEnabled
        self._trickleTimeToPlayers(tran, obj)
        return obj.timeEnabled

    def _trickleTimeToPlayers(self, tran, obj):
        # enable time for players
        playerIDs = set()
        for systemID in obj.systems:
            system = tran.db[systemID]
            for planetID in system.planets:
                planet = tran.db[planetID]
                playerIDs.add(planet.owner)
        playerIDs.discard(Const.OID_NONE)
        for playerID in playerIDs:
            player = tran.db[playerID]
            if player.timeEnabled != obj.timeEnabled:
                player.timeEnabled = obj.timeEnabled
                player.lastLogin = time.time()
                if player.timeEnabled:
                    Utils.sendMessage(tran, player, Const.MSG_ENABLED_TIME, player.oid, None)
                else:
                    Utils.sendMessage(tran, player, Const.MSG_DISABLED_TIME, player.oid, None)

    def _isEligibleEnableTime(self, tran, obj):
        if obj.timeEnabled or obj.timePaused:
            # explicitly paused galaxy needs to be explicitly unpaused
            return False
        # We have to give players some time to prepare
        # (as they might be waiting for very long time for this galaxy to be created).
        currentTurn = tran.db[Const.OID_UNIVERSE].turn
        if obj.creationTurn + Rules.galaxyStartDelay <= currentTurn:
            log.debug("Time to prepare has passed", obj.creationTurn, currentTurn)
            return True
        elif obj.scenario == Const.SCENARIO_SINGLE:
            return True
        return False

    def _firstEnableTime(self, tran, obj):
        # spawn rebel player on all vacant starting positions
        for positionID in copy.copy(obj.startingPos):
            obj.startingPos.remove(positionID)
            # create new player
            log.debug("Creating new Rebel player", Const.T_AIPLAYER)
            player = self.new(Const.T_AIPLAYER)
            self.cmd(player).register(tran, player, obj.oid)
            player.galaxy = obj.oid
            playerID = player.oid
            # TODO tweak more planet's attrs
            planet = tran.db[positionID]
            self.cmd(planet).changeOwner(tran, planet, playerID, 1)
            IAIPlayer.setStartingTechnologies(player)
            # fleet
            # add basic ships designs
            # add small fleet
            system = tran.db[planet.compOf]
            IAIPlayer.setStartingShipDesigns(player)
            IAIPlayer.setStartingPlanet(tran, playerID, planet)
            IAIPlayer.setStartingFleet(tran, playerID, system)
            system.scannerPwrs[playerID] = Rules.startingScannerPwr
        # do scanner evaluation because of all new players
        self.cmd(obj).processSCAN2Phase(tran, obj, None)

    @public(Const.AL_ADMIN)
    def enableTime(self, tran, obj, force = False):
        log.debug('IGalaxy', 'Checking for time...')
        if not force and not self._isEligibleEnableTime(tran, obj):
            return
        if obj.timeEnabled is None:
            self._firstEnableTime(tran, obj)
        # ok, enable time
        log.message('IGalaxy', 'Enabling time for', obj.oid)
        obj.timeEnabled = True
        self._trickleTimeToPlayers(tran, obj)

    @public(Const.AL_OWNER)
    def deleteSingle(self, tran, obj):
        if obj.scenario != Const.SCENARIO_SINGLE:
            raise ige.GameException('Only Single Player galaxies can be deleted this way')
        log.debug(obj.oid, "GALAXY - singleplayer delete")
        self.delete(tran, obj)

    @public(Const.AL_ADMIN)
    def delete(self, tran, obj):
        log.debug(obj.oid, "GALAXY - delete")
        universe = tran.db[Const.OID_UNIVERSE]
        # delete systems and planets
        for systemID in obj.systems:
            log.debug("Deleting system", systemID)
            system = tran.db[systemID]
            log.debug("-- planets", system.planets)
            log.debug("-- fleets", system.fleets, system.closeFleets)
            for planetID in system.planets[:]:
                planet = tran.db[planetID]
                self.cmd(planet).changeOwner(tran, planet, Const.OID_NONE, force = 1)
                del tran.db[planetID]
            for fleetID in system.closeFleets[:]:
                fleet = tran.db[fleetID]
                # this will modify system fleet and closeFleets attrs
                self.cmd(fleet).disbandFleet(tran, fleet)
            del tran.db[systemID]
        # delete all remaining fleets
        for playerID in universe.players[:]:
            player = tran.db[playerID]
            if obj.oid != player.galaxy:
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
        tran.db[Const.OID_UNIVERSE].galaxies.remove(obj.oid)
        del tran.db[obj.oid]
        return 1

    @public(Const.AL_NONE)
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

    @public(Const.AL_NONE)
    def getDescription(self,obj):
        return obj.description

    def _environmentGetVacantPlanets(self, tran, obj):
        vacantPlanets = {}
        for systemID in obj.systems:
            system = tran.db[systemID]
            for planetID in system.planets:
                planet = tran.db[planetID]
                if planet.owner != Const.OID_NONE:
                    continue
                if planet.plStratRes in (Const.SR_TL1A, Const.SR_TL1B):
                    playerType = Const.T_AIRENPLAYER
                elif planet.plStratRes in (Const.SR_TL3A, Const.SR_TL3B, Const.SR_TL3C):
                    playerType = Const.T_AIPIRPLAYER
                elif planet.plStratRes in (Const.SR_TL5A, Const.SR_TL5B, Const.SR_TL5C):
                    playerType = Const.T_AIEDENPLAYER
                elif planet.plDisease != 0:
                    playerType = Const.T_AIMUTPLAYER
                else:
                    continue
                try:
                    vacantPlanets[playerType].append(planetID)
                except KeyError:
                    vacantPlanets[playerType] = [planetID]
        return vacantPlanets

    def _searchForPlayer(self, tran, obj, playerType):
        universe = tran.db[Const.OID_UNIVERSE]
        for playerID in universe.players:
            player = tran.db[playerID]
            if obj.oid == player.galaxy and player.type == playerType:
                return player
        # create new player
        log.debug("Creating new player", playerType)
        player = self.new(playerType)
        self.cmd(player).register(tran, player, obj.oid)
        player.galaxy = obj.oid
        return player

    def _setupEnvironmentUniquePerPlanet(self, tran, obj, vacantPlanets, aiClass):
        try:
            planets = vacantPlanets.pop(aiClass.typeID)
        except KeyError:
            return
        for planetID in planets:
            planet = tran.db[planetID]
            log.debug("Creating new ai, type", aiClass.typeID)
            player = self.new(aiClass.typeID)
            self.cmd(player).register(tran, player, obj.oid)
            player.galaxy = obj.oid
            self.cmd(planet).changeOwner(tran, planet, player.oid, 1)
            aiClass.setStartingPlanet(tran, planet)

    @public(Const.AL_ADMIN)
    def setupEnvironment(self, tran, obj):
        vacantPlanets = self._environmentGetVacantPlanets(tran, obj)
        self._setupEnvironmentUniquePerPlanet(tran, obj, vacantPlanets, IAIRenegadePlayer)
        self._setupEnvironmentUniquePerPlanet(tran, obj, vacantPlanets, IAIMutantPlayer)
        # iterate over types, create players if needed (it should be) and fill in vacant planets
        for playerType in vacantPlanets:
            player = self._searchForPlayer(tran, obj, playerType)
            # now we have a player, let's iterate over vacant planets and set them up
            for planetID in vacantPlanets[playerType]:
                planet = tran.db[planetID]
                self.cmd(planet).changeOwner(tran, planet, player.oid, 1)
                if playerType == Const.T_AIPIRPLAYER:
                    IAIPiratePlayer.setStartingPlanet(tran, planet)
                elif playerType == Const.T_AIEDENPLAYER:
                    IAIEDENPlayer.setStartingPlanet(tran, planet)

    ## messaging
    def canGetMsgs(self, tran, obj, oid):
        return 1

    def canSendMsg(self, tran, obj, oid, forum):
        if forum == "PUBLIC":
            return 1
        elif forum == "NEWS":
            return 1
        return 0

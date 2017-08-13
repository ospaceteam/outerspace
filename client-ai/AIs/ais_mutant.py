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
import random, copy, math

from ige import log, GameException
from ige.ospace.Const import *
import ige.ospace.Rules as Rules
import ige.ospace.Utils as Utils

from ai_tools import *

client = None
db = None
playerID = None
player = None

def systemManager():
    global data, player, db
    for planetID in data.myPlanets:
        sortStructures(client, db, planetID)
    for systemID in data.mySystems:
        system = db[systemID]
        # creation of final system plans
        finalSystemPlan = {}
        actualStats = getSystemStructStats(client, db, systemID)
        buildStats = getSystemStructStats(client, db, systemID, False)
        # create appropriate build plans
        for planetID in data.freePlanets & set(system.planets):
            finalSystemPlan[planetID] = {Rules.Tech.MUTANTBASE:1}
        # is the minefield in the system?
        hasMines = False
        possibleSlots = 0
        for planetID in data.myPlanets & set(system.planets):
            planet = db[planetID]
            if Rules.Tech.MUTANTMINES in actualStats.planets[planetID]:
                hasMines = True
                possibleSlots += planet.plSlots
        for planetID in data.myPlanets & set(system.planets):
            planet = db[planetID]
            mines = 0
            space = planet.plSlots - 1 # the main building is there every time
            if planet.plType == u"I":
                # preserve minefield position, and in case there is no
                # minefield in the system, try to place it on the first planet
                # available
                if Rules.Tech.MUTANTMINES in actualStats.planets[planetID] or\
                        (not hasMines and planet.plSlots >= 2 and possibleSlots > 6):
                    mines = 1
                    space -= 1
                    hasMines = True
                noOfPPs = math.ceil(space / 6.0)
                noOfFacts = space - noOfPPs
                finalSystemPlan[planetID] = {Rules.Tech.MUTANTBASE4:1,
                                            Rules.Tech.MUTANTMINES:mines,
                                            Rules.Tech.MUTANTPP2:noOfPPs,
                                            Rules.Tech.MUTANTFACT2:noOfFacts}
                continue
            elif planet.plType == u"E":
                # preserve minefield position, and in case there is no
                # minefield in the system, try to place it on the first planet
                # available
                if Rules.Tech.MUTANTMINES in actualStats.planets[planetID] or\
                        (not hasMines and planet.plSlots >= 2):
                    mines = 1
                    space -= 1
                    hasMines = True
                noOfPPs = math.ceil(space / 5.0)
                noOfFacts = space - noOfPPs
                finalSystemPlan[planetID] = {Rules.Tech.MUTANTBASE3:1,
                                            Rules.Tech.MUTANTMINES:mines,
                                            Rules.Tech.MUTANTPP2:noOfPPs,
                                            Rules.Tech.MUTANTFACT2:noOfFacts}
                continue
            elif planet.plType == u"M":
                # preserve minefield position, and in case there is no
                # minefield in the system, try to place it on the first planet
                # available
                if Rules.Tech.MUTANTMINES in actualStats.planets[planetID] or\
                        (not hasMines and planet.plSlots >= 2):
                    mines = 1
                    space -= 1
                    hasMines = True
                noOfPPs = math.ceil(space / 7.0)
                noOfFacts = space - noOfPPs
                finalSystemPlan[planetID] = {Rules.Tech.MUTANTBASE2:1,
                                            Rules.Tech.MUTANTMINES:mines,
                                            Rules.Tech.MUTANTPP2:noOfPPs,
                                            Rules.Tech.MUTANTFACT1:noOfFacts}
                continue
            else: # all sub-marginal types
                # preserve minefield position, and in case there is no
                # minefield in the system, try to place it on the first planet
                # available
                if Rules.Tech.MUTANTMINES in actualStats.planets[planetID] or\
                        (not hasMines and planet.plSlots >= 2):
                    mines = 1
                    space -= 1
                    hasMines = True
                noOfPPs = math.ceil(space / 5.0)
                noOfFacts = space - noOfPPs
                finalSystemPlan[planetID] = {Rules.Tech.MUTANTBASE:1,
                                            Rules.Tech.MUTANTMINES:mines,
                                            Rules.Tech.MUTANTPP1:noOfPPs,
                                            Rules.Tech.MUTANTFACT1:noOfFacts}
                continue
        idlePlanets = buildSystem(client, db, systemID, data.myProdPlanets & set(system.planets), finalSystemPlan)
        # rest of the planets build ships
        for planetID in idlePlanets:
            planet = db[planetID]
            systemFleets = getattr(system, 'fleets', [])
            hasSeeders = False
            hasSeekers = False
            for fleetID in systemFleets:
                fleet = db[fleetID]
                if getattr(fleet, 'owner', OID_NONE) == playerID:
                    if fleetContains(fleet, {2:2}):
                        hasSeeders = True
                    if fleetContains(fleet, {3:2}):
                        hasSeekers = True
            shipDraw = random.randint(1, 10)
            if not hasSeeders or not hasSeekers:
                # 20 %
                if shipDraw < 3:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 1, 2, planetID, True, False, OID_NONE)
                else:
                    if not hasSeeders:
                        planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 2, 1, planetID, True, False, OID_NONE)
                    elif not hasSeekers:
                        planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 3, 1, planetID, True, False, OID_NONE)
            else:
                # 40 %
                if shipDraw < 5:
                    # build bombers
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 4, 2, planetID, True, False, OID_NONE)
                # 60 %
                else:
                    # build fighters
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 1, 3, planetID, True, False, OID_NONE)

def expansionManager():
    global data, db
    shouldRepeat = True
    seederFleets = data.myFleetsWithDesign.get(2, set())
    seekerFleets = data.myFleetsWithDesign.get(3, set())
    while shouldRepeat:
        shouldRepeat = False
        for fleetID in copy.copy(seekerFleets & data.idleFleets):
            maxRange = subfleetMaxRange(client, db, {3:1}, fleetID)
            nearest = findNearest(db, db[fleetID], data.unknownSystems, maxRange)
            if len(nearest) > 0:
                systemID = nearest[0]
                # send the fleet
                fleet, newFleet, myFleets = orderPartFleet(client, db,
                    {3:1}, True, fleetID, FLACTION_MOVE, systemID, None)
                data.myFleetSheets[fleetID][3] -= 1
                if data.myFleetSheets[fleetID][3] == 0:
                    del data.myFleetSheets[fleetID][3]
                    seekerFleets.remove(fleetID)
                else:
                    shouldRepeat = True
                data.unknownSystems.remove(systemID)
        for fleetID in copy.copy(seederFleets & data.idleFleets):
            maxRange = subfleetMaxRange(client, db, {2:1}, fleetID)
            nearest = findNearest(db, db[fleetID], data.freeSystems, maxRange)
            if len(nearest) > 0:
                systemID = nearest[0]
                # finding best planet for deployment
                system = db[systemID]
                noOfSlots = 0
                biggestPlanet = None
                for planetID in system.planets:
                    planet = db[planetID]
                    if noOfSlots < planet.plSlots:
                        noOfSlots = planet.plSlots
                        biggestPlanet = planetID
                        # send the fleet
                fleet, newFleet, myFleets = orderPartFleet(client, db,
                    {2:1}, True, fleetID, FLACTION_DEPLOY, biggestPlanet, 2)
                data.myFleetSheets[fleetID][2] -= 1
                if data.myFleetSheets[fleetID][2] == 0:
                    del data.myFleetSheets[fleetID][2]
                    seederFleets.remove(fleetID)
                else:
                    shouldRepeat = True
                data.freeSystems.remove(systemID)
            # if there is no free system to go to, does the ship levitate over
            # the system partly occupied by someone else, and partly free?
            else:
                fleet = db[fleetID]
                orbitingID = fleet.orbiting
                if not orbitingID == OID_NONE:
                    orbiting = db[orbitingID]
                    if set(orbiting.planets) & data.freePlanets and orbitingID in data.otherSystems:
                        noOfSlots = 0
                        biggestPlanet = None
                        for planetID in set(orbiting.planets) & data.freePlanets:
                            planet = db[planetID]
                            if noOfSlots < planet.plSlots:
                                noOfSlots = planet.plSlots
                                biggestPlanet = planetID
                        # issue the deploy order
                        fleet, newFleet, myFleets = orderPartFleet(client, db,
                            {2:1}, True, fleetID, FLACTION_DEPLOY, biggestPlanet, 2)
                        data.myFleetSheets[fleetID][2] -= 1
                        if data.myFleetSheets[fleetID][2] == 0:
                            del data.myFleetSheets[fleetID][2]
                            seederFleets.remove(fleetID)


def shipDesignManager():
    # there are 2 basic designs    created by the server
    # 1: Swarmer [Small hull, Cockpit, 2x EMCannon, 2xFTL]
    # 2: Seeder [Medium hull, Cockpit, Mutant Colony Pod, 4xFTL]
    # 3: Seeker [Small hull, Cockpit, 1x ActiveScan, 2xFTL]
    # 4: Sower [Small hull, Cockpit, 1x Conv.Bomb, 2xFTL]
    pass

def attackManager():
    global data, db
    attackFleets = set()
    for fleetID in copy.copy(data.myFleets):
        fleet = db.get(fleetID, None)
        if getattr(fleet, 'target', OID_NONE) == OID_NONE and getattr(fleet, 'ships', []):
            if fleetContains(fleet, {1:12, 4:12}):
                attackFleets.add(fleetID)
    for fleetID in copy.copy(attackFleets):
        fleet = db[fleetID]
        # send the attack fleet, if in range
        sheet = getFleetSheet(fleet)
        noOfSowers = sheet[4]
        noOfSwarmers = min(sheet[1], math.ceil(noOfSowers * 1.5))
        maxRange = 0.8 * subfleetMaxRange(client, db, {1:noOfSwarmers, 4:noOfSowers}, fleetID)
        # four nearest systems are considered, with probability to be chosen based on order
        nearest = findNearest(db, fleet, data.otherSystems, maxRange, 4)
        if len(nearest):
            # range is adjusted to flatten probabilities a bit
            probability_map = map(lambda x: x ** 2, range(6, 2, -1))
            target = weightedRandom(nearest, probability_map)

            fleet, newFleet, myFleets = orderPartFleet(client, db,
                {1:noOfSwarmers, 4:noOfSowers}, True,
                fleetID, FLACTION_MOVE, target, None)
            attackFleets.remove(fleetID)

def logisticsManager():
    global data, db, client
    for systemID in data.mySystems - data.myRelevantSystems:
        system = db[systemID]
        relDist = data.distanceToRelevance[systemID]
        for fleetID in set(system.fleets) & data.idleFleets:
            fleet = db[fleetID]
            subfleet = getSubfleet(fleet, {1:0, 4:0}, False)
            if len(subfleet):
                fleetRange = subfleetMaxRange(client, db, {1:0, 4:0}, fleetID)
                relevantSysID = findNearest(db, system, data.myRelevantSystems, fleetRange)
                if relevantSysID:
                    relevantSysID = relevantSysID[0]
                    fleet, newFleet, myFleets = orderPartFleet(client, db,
                        {1:0, 4:0}, True, fleetID, FLACTION_MOVE, relevantSysID, None)
                    data.idleFleets -= set([fleetID])
                else:
                    minDist = fleetRange
                    minDistSysID = None
                    minDistRel = data.distanceToRelevance[systemID]
                    for tempID, dist in data.distanceToRelevance.items():
                        temp = db[tempID]
                        distance = math.hypot(temp.x - system.x, temp.y - system.y)
                        if distance < minDist and dist < minDistRel:
                            minDist = distance
                            minDistSysID = tempID
                            minDistRel = dist
                    if minDistSysID:
                        fleet, newFleet, myFleets = orderPartFleet(client, db,
                            {1:0, 4:0}, True, fleetID, FLACTION_MOVE, minDistSysID, None)
                        data.idleFleets -= set([fleetID])


def run(aclient):
    global client, db, player, playerID
    client = aclient
    db = client.db
    player = client.getPlayer()
    playerID = client.getPlayerID()

    tool_parseDB(client, db)
    doRelevance(client, db, 10)
    shipDesignManager()

    logisticsManager()
    expansionManager()
    systemManager()

    attackManager()

    client.saveDB()

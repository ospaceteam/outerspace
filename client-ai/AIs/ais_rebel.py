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
from ige import log
from ige.ospace.Const import PACT_ALLOW_CIVILIAN_SHIPS, PACT_ALLOW_TANKING, PACT_MINOR_SCI_COOP, PACT_MAJOR_SCI_COOP, PACT_MINOR_CP_COOP, PACT_MAJOR_CP_COOP, PACT_ACTIVE, PACT_INACTIVE
import ige.ospace.Rules as Rules
import ige.ospace.Utils as Utils
import ige.ospace.TechHandlers as TechHandlers

from ai_tools import *

import copy, random, math

client = None
db = None
playerID = None
player = None
designs = {}

def planetManager():
    global data,  player, db
    for planetID in data.myPlanets:
        sortStructures(client, db, planetID)
    for systemID in data.mySystems:
        system = db[systemID]
        sharedSystem = len(set(system.planets) & data.otherPlanets) > 0
        getSystemStructStats(client, db, systemID)
        systemEn = 0
        systemBio = 0
        for planetID in data.myPlanets & set(system.planets):
            planet = db[planetID]
            for techID, hp, something, eff in planet.slots:
                tech = client.getFullTechInfo(techID)
                systemEn -= tech.operEn
                systemBio -= tech.operWorkers / 100
                systemEn += tech.prodEn * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodEnMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
                systemBio += tech.prodBio * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodBioMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
            for task in getattr(planet, 'prodQueue', []):
                if not task.isShip:
                    techID = task.techID
                    tech = client.getFullTechInfo(task.techID)
                    if tech.isStructure:
                        target = db[task.targetID]
                        systemEn -= tech.operEn
                        systemBio -= tech.operWorkers / 100
                        systemEn += tech.prodEn * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodEnMod, [target.plBio, target.plMin, target.plEn, 100])])
                        systemBio += tech.prodBio * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodBioMod, [target.plBio, target.plMin, target.plEn, 100])])
        idlePlanets = data.myProdPlanets & set(system.planets)
        # build production buildings if nothing is needed, or outposts
        for planetID in copy.copy(idlePlanets):
            planet = db[planetID]
            if getattr(planet, 'prodQueue', None):
                # something in the build queue, skip the planet
                idlePlanets.remove(planetID)
                continue
            if planet.plMin < 100:
                prodTech = client.getFullTechInfo(Rules.Tech.RESCENTRE1)
            else:
                prodTech = client.getFullTechInfo(Rules.Tech.FACTORY1)
            # now we ignore all already build structures, and try to satisfy
            # outpost/fact or outpost/labs ration [on free slots]
            if planet.plSlots > len(planet.slots):
                if systemEn > prodTech.operEn and systemBio > prodTech.operWorkers / 100:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planet.oid,
                        prodTech.id, 1, planetID, prodTech.id < 1000, 0, OID_NONE)
                    idlePlanets.remove(planetID)
                else:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.OUTPOST1, 1, planetID, Rules.Tech.OUTPOST1 < 1000, 0, OID_NONE)
                    idlePlanets.remove(planetID)
        toColonize = data.freePlanets & set(system.planets)
        # colonize remaining planets
        for planetID in copy.copy(idlePlanets):
            planet = db[planetID]
            if toColonize:
                targetID = toColonize.pop()
                target = db[targetID]
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.OUTPOST1, 1,
                    targetID, Rules.Tech.OUTPOST1 < 1000, 0, OID_NONE)
                idlePlanets.remove(planetID)

        for planetID in copy.copy(idlePlanets):
            systemFleets = getattr(system, 'fleets', [])
            hasCS = False
            hasScouts = False
            for fleetID in systemFleets:
                fleet = db[fleetID]
                if getattr(fleet, 'owner', OID_NONE) == playerID:
                    if fleetContains(fleet, {designs[3]:1}):
                        hasCS = True
                    if fleetContains(fleet, {designs[0]:1}):
                        hasScouts = True
            if not hasCS:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    designs[3], 1, planetID, designs[3] < 1000, 0, OID_NONE)
            elif not hasScouts:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    designs[0], 1, planetID, designs[0] < 1000, 0, OID_NONE)
            elif not sharedSystem:
                # build fighters
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    designs[1], 1, planetID, designs[1] < 1000, 0, OID_NONE)

def empireManager():
    global player, db, data
    if not Rules.Tech.GOVCENTER1 in player.techs.keys():
        return
    candidates = findPopCenterPlanets(db, data.myPlanets)
    candidatePlanets = candidates[:10]
    govPosition = OID_NONE
    govProductions = []
    for planetID in data.myPlanets:
        # find build gov center
        planet = db[planetID]
        for struct in planet.slots:
            if struct[0] in set([1000, 3010, 3011]):
                govPosition = planetID
        for task in getattr(planet, 'prodQueue', []):
            if task.techID in set([1000, 3010, 3011]):
                govProductions.append(planetID)
    needsChange = True
    for planetID in candidatePlanets:
        if planetID in set([govPosition]) | set(govProductions):
            needsChange = False
            break
    if needsChange:
        # cancel all tasks
        for planetID in govProductions:
            planet = db[planetID]
            indexes = []
            i = 0
            for task in planet.prodQueue:
                if task.techID in set([1000, 3010, 3011]):
                    indexes.append(i)
                i += 1
            indexes.reverse()
            for index in indexes:
                client.cmdProxy.abortConstruction(planetID, index)
        # find best place for the gov center [planet with at least 2 slots
        # filled with factories or labs]
        for planetID in candidatePlanets:
            planet = db[planetID]
            if planet.prodProd == 0:
                continue
            energy = planet.changeEn
            food = planet.changeBio
            tech = client.getTechInfo(1000)
            energy -= tech.operEn
            food -= tech.operWorkers / 100.0
            qtyRes = 0
            qtyFact = 0
            for struct in planet.slots:
                if struct[0] == Rules.Tech.RESCENTRE1:
                    qtyRes += 1
                elif struct[0] == Rules.Tech.FACTORY1:
                    qtyFact += 1
            if qtyFact >= 2:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.GOVCENTER1, 1, planetID, Rules.Tech.GOVCENTER1 < 1000, 0, Rules.Tech.FACTORY1)
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.OUTPOST1, 1, planetID, Rules.Tech.OUTPOST1 < 1000, 0, Rules.Tech.FACTORY1)
                return
            elif qtyRes >= 2:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.GOVCENTER1, 1, planetID, Rules.Tech.GOVCENTER1 < 1000, 0, Rules.Tech.RESCENTRE1)
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.OUTPOST1, 1, planetID, Rules.Tech.OUTPOST1 < 1000, 0, Rules.Tech.RESCENTRE1)
                return
    else:
        return

def shipDesignManager():
    global player, designs
    for desID in player.shipDesigns:
        design = player.shipDesigns[desID]
        if design.name == 'Scout':
            designs[0] = desID
        elif design.name == 'Fighter':
            designs[1] = desID
        elif design.name == 'Bomber':
            designs[2] = desID
        elif design.name == 'Colony Ship':
            designs[3] = desID
    if 0 not in designs:
        designs[0] = client.cmdProxy.addShipDesign(playerID, 'Scout',
                Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.SCANNERMOD1:1, Rules.Tech.FTLENG1:3})
    if 1 not in designs:
        designs[1] = client.cmdProxy.addShipDesign(playerID, 'Fighter',
                Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.CANNON1:1, Rules.Tech.FTLENG1:3})
    if 2 not in designs:
        designs[2] = client.cmdProxy.addShipDesign(playerID, 'Bomber',
                Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.CONBOMB1:1, Rules.Tech.FTLENG1:3})
    if 3 not in designs:
        designs[3] = client.cmdProxy.addShipDesign(playerID, 'Colony Ship',
                Rules.Tech.MEDIUMHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.COLONYMOD2:1, Rules.Tech.FTLENG1:4})

def expansionManager():
    global data, db, designs
    shouldRepeat = True
    colonyFleets = data.myFleetsWithDesign.get(designs[3], set())
    scoutFleets = data.myFleetsWithDesign.get(designs[0], set())
    pirateInfluencedSystems = findInfluence(client, db, Rules.pirateInfluenceRange, data.pirateSystems)
    while shouldRepeat:
        shouldRepeat = False
        for fleetID in copy.copy(scoutFleets & data.idleFleets):
            maxRange = subfleetMaxRange(client, db, {designs[0]:1}, fleetID)
            nearest = findNearest(db, db[fleetID], data.unknownSystems & data.relevantSystems, maxRange)
            if len(nearest) > 0:
                systemID = nearest[0]
                # send the fleet
                fleet, newFleet, myFleets = orderPartFleet(client, db,
                    {designs[0]:1}, True, fleetID, FLACTION_MOVE, systemID, None)
                data.myFleetSheets[fleetID][designs[0]] -= 1
                if data.myFleetSheets[fleetID][designs[0]] == 0:
                    del data.myFleetSheets[fleetID][designs[0]]
                    scoutFleets.remove(fleetID)
                else:
                    shouldRepeat = True
                data.unknownSystems.remove(systemID)
        for fleetID in copy.copy(colonyFleets & data.idleFleets):
            maxRange = subfleetMaxRange(client, db, {designs[3]:1}, fleetID)
            nearest = findNearest(db, db[fleetID], (data.freeSystems & data.relevantSystems) - pirateInfluencedSystems, maxRange)
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
                    {designs[3]:1}, True, fleetID, FLACTION_DEPLOY, biggestPlanet, designs[3])
                data.myFleetSheets[fleetID][designs[3]] -= 1
                if data.myFleetSheets[fleetID][designs[3]] == 0:
                    del data.myFleetSheets[fleetID][designs[3]]
                    colonyFleets.remove(fleetID)
                else:
                    shouldRepeat = True
                data.freeSystems.remove(systemID)

def attackManager():
    pass

def researchManager():
    researchable = set()
    if len(player.rsrchQueue) < 2:
        for techID in player.techs.keys():
            tech = client.getTechInfo(techID)
            improvement = player.techs[techID]
            if improvement < Rules.techMaxImprovement and\
                    improvement < tech.maxImprovement:
                researchable.add(techID)
        for techID in client.getAllTechIDs():
            tech = client.getTechInfo(techID)
            if not hasattr(tech, "partialData") or not hasattr(tech, 'researchMod'):
                continue
            else:
                researchable.add(techID)
        for task in player.rsrchQueue:
            researchable -= set([task.techID])
        # some less useful technologies for AI
        lessTechs = set([1102, 1104, 1107, 1110, 1112, 1404, 1510, 1800, 1801, 1802])
        if len(researchable - (lessTechs | set([1990, 1991, 1992]))) > 0:
            researchable -= lessTechs
        # do not advance, for now
        researchable -= set([1990, 1991, 1992])
        if len(researchable) > 0:
            if Rules.Tech.OUTPOST1 in researchable:
                player.rsrchQueue = client.cmdProxy.startResearch(playerID, Rules.Tech.OUTPOST1)
                return
            possibilities = list(researchable)
            random.shuffle(possibilities)
            techID = possibilities[0]
            player.rsrchQueue = client.cmdProxy.startResearch(playerID, techID)

def diplomacyManager():
    global client, db, player, playerID
#    if not player.voteFor == playerID:
#        client.cmdProxy.setVoteFor(playerID, playerID)
#    rebels cannot be voted
    for contactID in player.diplomacyRels:
        dipl = client.getDiplomacyWith(contactID)
        for pactID in [PACT_ALLOW_CIVILIAN_SHIPS, PACT_ALLOW_TANKING, PACT_MINOR_SCI_COOP, PACT_MAJOR_SCI_COOP, PACT_MINOR_CP_COOP, PACT_MAJOR_CP_COOP]:
            pactSpec = Rules.pactDescrs[pactID]
            if dipl.relation < pactSpec.validityInterval[0] or dipl.relation > pactSpec.validityInterval[1]:
                # not friendly enough
                continue
            if pactID in dipl.pacts and dipl.pacts[pactID][0] in [PACT_ACTIVE, PACT_INACTIVE]:
                # nothing more to do, move along
                continue
            # hey, we should enable this pact!
            conditions = [pactID]
            player.diplomacyRels = client.cmdProxy.changePactCond(playerID, contactID, pactID, PACT_INACTIVE, conditions)


def defenseManager():
    global client, db, designs, data
    doDanger(client, db)
    pirateInfluencedSystems = findInfluence(client, db, Rules.pirateInfluenceRange, data.pirateSystems)
    oneFighterMP = player.shipDesigns[designs[1]].combatPwr
    for systemID in set(data.endangeredSystems) - set(pirateInfluencedSystems):
        milPwr, shipQuantity = data.endangeredSystems[systemID]
        milPwr = -milPwr
        if systemID in data.myMPPerSystem:
            milPwr += data.myMPPerSystem[systemID]
        if milPwr < 0:
            system = db[systemID]
            nearest = findNearest(db, system, data.mySystems, 99999, 20)[1:]
            for tempID in nearest:
                if tempID in data.myMPPerSystem:
                    tmpMP = data.myMPPerSystem[tempID]
                else:
                    tmpMP = 0
                    data.myMPPerSystem[tempID] = 0
                if tempID in data.endangeredSystems:
                    a, b = data.endangeredSystems[tempID]
                    tmpMP -= a * 1.5
                    if tmpMP <= 0: continue
                orig = tmpMP = min(-milPwr, tmpMP) * 1.25
                # this is just prototype, working only with Fighters
                quantity = int(math.ceil(tmpMP / float(oneFighterMP)))
                if quantity == 0:
                    continue
                shipsLeft, milPwrSend = orderFromSystem(client, db,
                    {designs[1]:quantity}, tempID, FLACTION_MOVE, systemID, None)
                milPwr += milPwrSend
                data.myMPPerSystem[tempID] -= milPwrSend
                if milPwr > 0: break

def logisticsManager():
    global client, db, data
    for fleetID in data.idleFleets:
        fleet = db[fleetID]
        # fleets orbiting in systems not belonging to the player
        if fleet.orbiting and fleet.orbiting not in data.mySystems:
            nearest = findNearest(db, fleet, data.mySystems, 99999, 1)
            if len(nearest):
                targetID = nearest[0]
                orderFleet(client, db, fleetID, FLACTION_MOVE, targetID, None)

def run(aclient):
    global client, db, player, playerID
    client = aclient
    db = client.db
    player = client.getPlayer()
    playerID = client.getPlayerID()

    tool_parseDB(client, db)
    doRelevance(client, db, 10)
    researchManager()

    shipDesignManager()
    expansionManager()

    empireManager()
    planetManager()

    diplomacyManager()
    defenseManager()
    attackManager()
    logisticsManager()
    client.saveDB()


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
import math
from ige import log
from ige.IDataHolder import IDataHolder
from ige.ospace import Const
from ige.ospace import Rules
from ige.ospace import Utils



def tool_parseDB(client, db, enemyTypes):
    """ Parses all data in db for needs of other tools. Other in the name
    means other players.

    """
    data = IDataHolder()
    data.myPlanets = set()
    data.myProdPlanets = set()
    data.mySystems = set()
    data.freePlanets = set()
    data.freeSystems = set()
    data.nonhabPlanets = set()
    data.unknownSystems = set()
    data.otherPlanets = set()
    data.enemyPlanets = set()
    data.otherSystems = set()
    data.enemySystems = set()
    data.systems = set()
    data.myFleets = set()
    data.myMPPerSystem = {}
    data.myTargetedSystems = set()
    data.endangeredSystems = {}
    data.otherFleets = set()
    data.otherInboundFleets = set()
    data.idleFleets = set()
    data.myFleetsWithDesign = {}
    data.myFleetSheets = {}
    data.pirateSystems = set()
    data.relevantSystems = set()
    data.myRelevantSystems = set()
    data.distanceToRelevance = {}
    playerID = client.getPlayerID()
    player = client.getPlayer()
    owners = {}
    for objID in db.keys():
        try:
            obj = db[objID]
        except KeyError:
            # TODO find out why there are these errors
            continue
        objType = getattr(obj, 'type', None)
        if objType == Const.T_PLANET:
            ownerID = getattr(obj, 'owner', None)
            plSlots = getattr(obj, 'plSlots', 0)
            slots = getattr(obj, 'slots', [])
            prodProd = getattr(obj, 'prodProd', 0)
            plType = getattr(obj, 'plType', None)
            if plType == u'G' or plType == u'A':
                data.nonhabPlanets.add(objID)
                continue
            if ownerID == playerID and prodProd:
                data.myProdPlanets.add(objID)
                data.mySystems.add(obj.compOf)
            elif ownerID == playerID and not prodProd:
                # myPlanets are later joined by myProdPlanets
                data.myPlanets.add(objID)
                data.mySystems.add(obj.compOf)
            elif ownerID == Const.OID_NONE and plSlots:
                data.freePlanets.add(objID)
            elif not plSlots:
                data.unknownSystems.add(obj.compOf)
            else:
                # systems with owner other than myself, ignore EDEN planets
                if not ownerID:
                    continue
                elif ownerID not in owners:
                    owners[ownerID] = client.get(ownerID, publicOnly = 1)

                if not getattr(owners[ownerID], 'type', Const.OID_NONE) == Const.T_AIEDENPLAYER:
                    data.otherSystems.add(db[objID].compOf)
                    data.otherPlanets.add(objID)
                if getattr(owners[ownerID], 'type', Const.OID_NONE) in enemyTypes:
                    data.enemySystems.add(db[objID].compOf)
                    data.enemyPlanets.add(objID)
                if getattr(owners[ownerID], 'type', Const.OID_NONE) in (Const.T_AIPIRPLAYER, Const.T_PIRPLAYER):
                    data.pirateSystems.add(db[objID].compOf)
        elif objType == Const.T_SYSTEM:
            if getattr(obj, "starClass", "a")[0] == 'b':
                # black hole -> nothing to see here, let's ignore it completely
                continue
            data.systems.add(objID)
            if not hasattr(db[objID], 'planets'):
                data.unknownSystems.add(objID)
        elif objType == Const.T_FLEET:
            ownerID = getattr(obj, 'owner', None)
            if ownerID == playerID:
                data.myFleets.add(objID)
                data.myFleetSheets[objID] = getFleetSheet(obj)
                if len(obj.actions[obj.actionIndex:]) == 0:
                    data.idleFleets.add(objID)
                for designID in data.myFleetSheets[objID].keys():
                    if not data.myFleetsWithDesign.get(designID, set()):
                        data.myFleetsWithDesign[designID] = set([objID])
                    else:
                        data.myFleetsWithDesign[designID] |= set([objID])
            else:
                data.otherFleets.add(objID)
    # ==================
    # second phase
    # analyzing fleet action queues
    for fleetID in data.myFleets:
        fleet = db[fleetID]
        for orType, orTargID, orData in fleet.actions[fleet.actionIndex:]:
            if orType == Const.FLACTION_WAIT:
                continue
            elif orType == Const.FLACTION_REPEATFROM:
                continue
            elif orType == Const.FLACTION_REDIRECT:
                if orTargID == Const.OID_NONE:
                    continue
            orTarg = db[orTargID]
            if orTarg.type == Const.T_SYSTEM:
                data.unknownSystems -= set([orTargID])
            elif orTarg.type == Const.T_PLANET:
                data.unknownSystems -= set([orTarg.compOf])
            # deploy order removes target from free planets set
            # if deploying to non-free planet, change order TODO [non-systematic]
            if orType == Const.FLACTION_DEPLOY:
                if orTargID in data.freePlanets:
                    data.freePlanets -= set([orTargID])
                else:
                    client.cmdProxy.deleteAction(fleetID, fleet.actionIndex)
        # fill data.myMPPerSystem
        if len(fleet.actions[fleet.actionIndex:]) == 0:
            if fleet.orbiting in data.mySystems:
                try:
                    data.myMPPerSystem[fleet.orbiting] += fleet.combatPwr
                except KeyError:
                    data.myMPPerSystem[fleet.orbiting] = fleet.combatPwr
        else:
            lastOrder = fleet.actions[len(fleet.actions)-1]
            targetID = lastOrder[1]
            if targetID in data.myPlanets:
                sysID = db[targetID].compOf
                try:
                    data.myMPPerSystem[sysID] += fleet.combatPwr
                except KeyError:
                    data.myMPPerSystem[sysID] = fleet.combatPwr
            elif targetID in data.mySystems:
                try:
                    data.myMPPerSystem[targetID] += fleet.combatPwr
                except KeyError:
                    data.myMPPerSystem[targetID] = fleet.combatPwr

    data.myPlanets |= data.myProdPlanets
    # only systems with free or nonhabitable planets are considered free
    for systemID in data.systems:
        isEmpty = True
        hasEmpty = False
        planets = set(getattr(db[systemID], 'planets', []))
        if planets and not planets - data.freePlanets - data.nonhabPlanets:
            data.freeSystems.add(systemID)
    # find attacking fleets
    for fleetID in data.otherFleets:
        fleet = db[fleetID]
        if getattr(fleet, 'target', None):
            targetID = getattr(fleet, 'target', None)
        elif not getattr(fleet, 'orbiting', Const.OID_NONE) == Const.OID_NONE:
            targetID = getattr(fleet, 'orbiting', Const.OID_NONE)
        if targetID:
            if targetID in data.myPlanets:
                data.myTargetedSystems.add(db[targetID].compOf)
                data.otherInboundFleets.add(fleetID)
            elif targetID in data.mySystems:
                data.myTargetedSystems.add(targetID)
                data.otherInboundFleets.add(fleetID)
    return data

def doRelevance(data, client, db, rangeOfRelevance):
    """ This function finds all systems, which are nearer to the players
    system than is defined in rangeOfRelevance. This is saved in
    data.relevantSystems.
        Then, it saves all players planets in relevant distance from any
    planet in data.otherSystems. And finally, it fills dictionary
    data.distanceToRelevance, where each system of the player got its
    distance to nearest relevant system of the player.

    """
    for systemID in data.systems:
        system = db[systemID]
        for tempID in data.mySystems:
            temp = db[tempID]
            distance = math.hypot(system.x - temp.x, system.y - temp.y)
            if distance <= rangeOfRelevance:
                data.relevantSystems.add(systemID)
                break
    for systemID in data.mySystems:
        system = db[systemID]
        for tempID in data.otherSystems:
            temp = db[tempID]
            distance = math.hypot(system.x - temp.x, system.y - temp.y)
            if distance <= rangeOfRelevance:
                data.myRelevantSystems.add(systemID)
                break
    for systemID in data.mySystems - data.myRelevantSystems:
        system = db[systemID]
        relDist = 99999
        for tempID in data.myRelevantSystems:
            temp = db[tempID]
            distance = math.hypot(system.x - temp.x, system.y - temp.y)
            relDist = min(relDist, distance)
        data.distanceToRelevance[systemID] = relDist

def findInfluence(data, client, db, rangeOfInfluence, objectIDList):
    """ Returns list of all systems, which distance to any object
    from the objectList    is less than rangeOfInfluence.

    objectList -- iterable of IDs, and each    of the objects in the db has
                  to have .x and .y numeric parameters.

    """
    influencedSystems = set()
    for systemID in data.systems:
        system = db[systemID]
        for tempID in objectIDList:
            temp = db[tempID]
            distance = math.hypot(system.x - temp.x, system.y - temp.y)
            if distance <= rangeOfInfluence:
                influencedSystems.add(systemID)
    return influencedSystems

def doDanger(data, client, db):
    """ Fills data.endangeredSystems dictionary. Each system of the player,
    to which is heading some fleet of other player with military power
    got its own record consisting of military power and number of ships heading
    there. (It is the sum of all fleets).
        Medium and large ships are counted as 2 and 4 ships each respectively.

    """
    for fleetID in data.otherInboundFleets:
        fleet = db[fleetID]
        if not getattr(fleet, 'combatPwr', 0):
            continue
        if not getattr(fleet, 'orbiting', Const.OID_NONE) == Const.OID_NONE:
            targID = fleet.orbiting
        elif hasattr(fleet, 'target'):
            targID = fleet.target
        else:
            continue
        if targID in data.endangeredSystems:
            milPow, ships = data.endangeredSystems[targID]
        else:
            milPow = ships = 0
        milPow += fleet.combatPwr
        if hasattr(fleet, 'shipScan'):
            for (name, shipClass, isMilitary), quantity in fleet.shipScan.items():
                if isMilitary:
                    ships += quantity * (shipClass + 1) ** 2
            data.endangeredSystems[targID] = (milPow, ships)
        elif milPow > 0:
            data.endangeredSystems[targID] = (milPow, ships)

def orderFleet(client, db, fleetID, order, targetID, orderData):
    """ Orders fleet to do something. It removes old actions
    to prevent queue overflow.
    """
    fleet = db[fleetID]
    fleet.actions, fleet.actionIndex = client.cmdProxy.clearProcessedActions(fleetID)
    client.cmdProxy.addAction(fleetID, fleet.actionIndex+1, order, targetID, orderData)
    return

def getFleetSheet(fleet):
    """ Returns dictionary with key being design number, and value
    number of ships in the fleet of that design.
    """

    sheet = {}
    for ship in fleet.ships:
        try:
            sheet[ship[0]] += 1
        except KeyError:
            sheet[ship[0]] = 1
    return sheet

def getSubfleet(fleet, ships, needsExact):
    """ Returns subfleet roster.

    fleet - fleet object from which the subfleet is taken
    ships - is dictionary with keys being design IDs, values are
            demanded quantities, with value = 0 meaning "return all of the type"
            None value means "return whole fleet"
    needsExact - if true, all items in ships has to be in place to return
                 the roster, except 0 value, which means "all"
    """

    newShips = {}
    wholeFleet = getFleetSheet(fleet)
    if not ships:
        return wholeFleet
    for desID in ships:
        if ships[desID] == 0:
            try:
                newShips[desID] = wholeFleet[desID]
            except KeyError:
                continue
        else:
            try:
                if needsExact and wholeFleet[desID] < ships[desID]:
                    return None
                newShips[desID] = min(ships[desID], wholeFleet[desID])
            except KeyError:
                if needsExact:
                    return None
    return newShips

def fleetContains(fleet, ships):
    """ Tests whether fleet contains all ships in "ships" dictionary.

    Returns boolean value.
    """

    sheet = getFleetSheet(fleet)
    for desID in ships:
        try:
            if ships[desID] > sheet[desID]:
                return False
        except KeyError:
            return False
    return True

def orderPartFleet(client, db, ships, needsExact, fleetID, order, targetID, orderData):
    """ Splits part of the fleet and assign it the order.

    ships - is dictionary with keys being design IDs, value is
            demanded integer, with value = 0 it means "send all"
    needsExact - if true, send all ships in the "ships" or don't
            send anything, if false, send at least what you have,
            if you don't have all of them
    """

    sheet = getFleetSheet(db[fleetID])
    for key in ships:
        try:
            if ships[key] == 0:
                ships[key] = sheet[key]
        except KeyError:
            continue
    if sheet == ships:
        orderFleet(client, db, fleetID, order, targetID, orderData)
        return None, db[fleetID], client.getPlayer().fleets
    isValid = True
    sendShips = {}
    for key in ships:
        try:
            if ships[key] > sheet[key] and needsExact:
                return None, db[fleetID], client.getPlayer().fleets
            elif ships[key] == 0:
                sendShips[key] = sheet[key]
            else:
                sendShips[key] = min(ships[key], sheet[key])
        except KeyError:
            if needsExact:
                return None, db[fleetID], client.getPlayer().fleets
    if sendShips:
        newShips = []
        newMaxEn = 0
        for ship in db[fleetID].ships:
            if sendShips.get(ship[0], 0) > 0:
                sendShips[ship[0]] -= 1
                newShips.append(ship)
                newMaxEn += client.getPlayer().shipDesigns[ship[0]].storEn
        if newShips:
            newFleet, origFleet, fleetsout = client.cmdProxy.splitFleet(fleetID,
                                                                        newShips,
                                                                        newMaxEn)
            db[newFleet.oid] = newFleet
            db[origFleet.oid] = origFleet
            orderFleet(client, db, newFleet.oid, order, targetID, orderData)
            return newFleet, origFleet, fleetsout
        return None, db[fleetID], client.getPlayer().fleets
    else:
        None, db[fleetID], client.getPlayer().fleets

def subfleetMaxRange(client, db, ships, fleetID, canDamage=False):
    """ Counts range of subfleet in parsecs

    ships - is dictionary with keys being design IDs, value is
            demanded number, with value = 0 it means "send all of the type"
            None value means "send all" ships
    """

    fleet = db[fleetID]
    subfleet = getSubfleet(fleet, ships, True)
    if not subfleet:
        return 0.0
    player = client.getPlayer()
    storEn = 0
    operEn = 0
    speed = 99999
    for desID in subfleet:
        design = player.shipDesigns[desID]
        storEn += design.storEn * subfleet[desID]
        operEn += design.operEn * subfleet[desID]
        speed = min(design.speed, speed)
        storEn = min(storEn, fleet.storEn)
    return storEn / operEn * speed / 24

def findNearest(db, obj, targets, maxDist=99999, number=1):
    """ Searches through the targets, and returns list consisting of number of
    the nearest objects to the objID, sorted from the nearest to the farthest.
    Only requirement is that every item    needs to have attributes x and y.

    obj - the _object_ [not ID!] we try to find neighbours for
    targets - set of object IDs
    maxDist - maximum allowed distance
    number - size of the required set, when number of targets is lesser
            than number, it will just sort the targetIDs accordingly
    """
    distances = {}
    x, y = obj.x, obj.y
    for targID in targets:
        target = db[targID]
        distance = math.hypot(x - target.x, y - target.y)
        if distance not in distances:
            distances[distance] = set([targID])
        else:
            distances[distance] |= set([targID])
    relevantKeys = sorted(distances.keys())[:number]
    final = []
    for key in relevantKeys:
        if key > maxDist:
            break
        for targID in distances[key]:
            final.append(targID)
            number -= 1
            if not number: break
        if not number: break
    return final

def findPopCenterPlanets(db, planetsIDs):
    """ It finds "center of mass" of population.

    Returns sorted list    of all planets, beginning with those nearest to the
    found center.

    """
    x = 0
    y = 0
    population = 0
    for planetID in planetsIDs:
        planet = db[planetID]
        x += planet.x * planet.storPop
        y += planet.y * planet.storPop
        population += planet.storPop
    x /= population
    y /= population
    fakeObj = IDataHolder()
    fakeObj.x = x
    fakeObj.y = y
    return findNearest(db, fakeObj, planetsIDs, maxDist=99999, number=len(planetsIDs))

def orderFromSystem(data, client, db, ships, systemID, order, targetID, orderData):
    """ Tries to send ships defined by ships dictionary, and using all
    idle fleets in the system.
    ships - is dictionary with keys being design IDs, value is
            demanded number, with value = 0 it means "send all of the type"
            None value means "send all" ships
    systemID - ID of the system from which are fleets send
    order, targetID, orderData - parameters of the order

    Returns dictionary of ships _which remains to be send_, ie what of the
    ships dictionary wasn't available in the system, and military power of
    the send ships.

    """
    log.debug('ai_tools orderFromSystem', ships, systemID)
    system = db[systemID]
    fleetsIDs = set(system.fleets) & data.idleFleets
    milPow = 0
    if len(fleetsIDs) == 0:
        return ships, 0
    for fleetID in fleetsIDs:
        if ships == None:
            orderFleet(client, db, fleetID, order, targetID, orderData)
            continue
        fleet = db[fleetID]
        sheet = getFleetSheet(fleet)
        toSend = {}
        for key in copy.copy(ships):
            try:
                toSend[key] = min(ships[key], sheet[key])
                ships[key] = max(ships[key] - sheet[key], 0)
                if ships[key] == 0:
                    del ships[key]
            except KeyError:
                continue
        if toSend == {}:
            continue
        log.debug('ai_tools orderFromSystem - sending', toSend, fleetID)
        newFleet, origFleet, fleetsout = orderPartFleet(client, db, toSend, False, fleetID, order, targetID, orderData)
        milPow += getattr(newFleet, 'combatPwr', 0)
        hasAll = True
        for key in ships:
            if not ships[key] == 0:
                hasAll = False
                break
        if hasAll: break
    return ships, milPow

def sortStructures(client, db, planetID):
    """ Moves structures on the planet, so on the left are buildings producing
    food, then buildings producing electricity, then buildings producing CPs.
    Those with more than one relevant parameters "such as food + CPs" are
    in the more important group [food > en > CP > rest].

    """
    planet = db[planetID]
    player = client.getPlayer()
    structs = {}
    bioStructs = []
    enStructs = []
    prodStructs = []
    # fill the groups with positions of relevant structures
    for techID, hp, something, eff in planet.slots:
        techBio, techEn, techProd = getSystemStatsChange(client, db, techID, planetID, 0)
        if techBio > 0:
            bioStructs.append(techID)
        elif techEn > 0:
            enStructs.append(techID)
        elif techProd > 0:
            prodStructs.append(techID)
    # how many moves are necessary? As we move each group separately, we
    # assume, that structure in "bio" group has to be in
    # position < len(bioStructs), same with other groups
    needMoves = len(planet.slots)
    pos = 0
    for techID, hp, something, eff in planet.slots:
        if pos < len(bioStructs) and techID not in bioStructs:
            needMoves = pos
            break
        elif pos >= len(bioStructs) and pos < len(bioStructs) + len(enStructs) and techID not in enStructs:
            needMoves = pos
            break
        elif pos >= len(bioStructs) + len(enStructs) and pos < len(bioStructs) + len(enStructs) + len(prodStructs) and techID not in prodStructs:
            needMoves = pos
            break
        else:
            pos += 1
    # pos will be used once again
    # we are correcting the order from left to right, so next struct won't
    # get its position changed until it is moved itself
    # move is made to the leftmost position of the group
    for techID, hp, something, eff in planet.slots[needMoves:]:
        if techID in bioStructs:
            client.cmdProxy.moveStruct(planetID, pos, 0 - pos)
        pos += 1
    pos = max(needMoves, len(bioStructs))
    needMoves = pos
    for techID, hp, something, eff in planet.slots[needMoves:]:
        if techID in enStructs:
            client.cmdProxy.moveStruct(planetID, pos, len(bioStructs) - pos)
        pos += 1
    pos = max(needMoves, len(bioStructs) + len(enStructs))
    needMoves = pos
    for techID, hp, something, eff in planet.slots[needMoves:]:
        if techID in prodStructs:
            client.cmdProxy.moveStruct(planetID, pos, len(bioStructs) + len(enStructs) - pos)
        pos += 1
    return

def getSystemStructStats(data, client, db, systemID, processQueues=True):
    """ It go through all planets and structures, and creates IDataHolder
    object, with roster of buildings, surplus of bio and en.

    processQueues - if True, it go through all buildQueues and adjust all
                    statistics as it would be all done already.

    Returns IDataHolder with parameters:
        .bio - system surplus of biomass
        .en - system surplus of en
        .planets - dictionary, keys are planetIDs of players or free planets,
                   and values are dictionaries (huh) with keys being techIDs
                   and values being number of those structs.

    """
    systemStats = IDataHolder()
    system = db[systemID]
    player = client.getPlayer()
    myPlanets = set(system.planets) & data.myPlanets
    systemStats.planets = {}
    for planetID in myPlanets:
        systemStats.planets[planetID] = {}
    for planetID in set(system.planets) & data.freePlanets:
        systemStats.planets[planetID] = {}
    # creation of the .planets dictionary
    for planetID in myPlanets:
        planet = db[planetID]
        for techID, hp, something, eff in planet.slots:
            try:
                systemStats.planets[planetID][techID] += 1
            except KeyError:
                systemStats.planets[planetID][techID] = 1
        if not processQueues:
            # do not look into the queue
            continue
        for task in getattr(planet, 'prodQueue', []):
            if not task.isShip:
                techID = task.techID
                tech = client.getFullTechInfo(task.techID)
                if tech.isStructure:
                    if task.targetID not in systemStats.planets.keys():
                        continue
                    try:
                        systemStats.planets[task.targetID][techID] += 1
                    except KeyError:
                        systemStats.planets[task.targetID][techID] = 1
                    if task.demolishStruct:
                        try:
                            systemStats.planets[task.targetID][task.demolishStruct] -= 1
                        except KeyError:
                            systemStats.planets[task.targetID][task.demolishStruct] = -1
    # by parsing .planets object, fill the .bio and .en parameters
    systemStats.bio = 0
    systemStats.en = 0
    for planetID in systemStats.planets:
        planet = db[planetID]
        if planetID not in myPlanets:
            continue
        for techID in systemStats.planets[planetID]:
            quantity = systemStats.planets[planetID][techID]
            deltaBio, deltaEn, deltaProd = getSystemStatsChange(client, db, techID, planetID, 0)
            tech = client.getFullTechInfo(techID)
            systemStats.en += quantity * deltaEn
            systemStats.bio += quantity * deltaBio
    return systemStats

def getSystemStatsChange(client, db, techID, targetPlanetID, targetTechID):
    """ Find out, how are the stats going to change with build of structure
    with techID, on targetPlanetID, over targetTechID.

    deltaProd - it is RAW production, ie no morale bonuses etc.

    """
    planet = db[targetPlanetID]
    player = client.getPlayer()
    deltaBio = 0
    deltaEn = 0
    tech = client.getFullTechInfo(techID)
    deltaEn -= tech.operEn
    deltaBio -= tech.operWorkers / 100
    deltaEn += tech.prodEn * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodEnMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
    deltaBio += tech.prodBio * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodBioMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
    deltaProd = tech.prodProd * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodProdMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
    if targetTechID:
        tech = client.getFullTechInfo(targetTechID)
        deltaEn += tech.operEn
        deltaBio += tech.operWorkers / 100
        deltaEn -= tech.prodEn * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodEnMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
        deltaBio -= tech.prodBio * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodBioMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
        deltaProd -= tech.prodProd * Rules.techImprEff[player.techs.get(techID, 1)] * sum([x*y/100.0 for x, y in zip(tech.prodProdMod, [planet.plBio, planet.plMin, planet.plEn, 100])])
    return deltaBio, deltaEn, deltaProd

def checkBuildQueues(data, client, db, systemID, prodPlanets):
    system = db[systemID]
    player = client.getPlayer()
    for planetID in prodPlanets:
        planet = db[planetID]
        validTasks = 0
        while len(planet.prodQueue) > validTasks:
            # validTasks is effectively the actual index
            task = planet.prodQueue[validTasks]
            if task.targetID in data.myPlanets | data.freePlanets | set([Const.OID_NONE, None]):
                validTasks += 1
            else:
                planet.prodQueue, player.stratRes = client.cmdProxy.abortConstruction(planetID, validTasks)

def buildSystem(data, client, db, systemID, prodPlanets, finalSystemPlan):
    """ Assigns tasks to all idle planets with CP > 0 in one system, according
    to object finalSystemPlan. There is NO guaranty it will rebuild it correctly
    as no math model was made for it. It just try to build most effectively,
    with keeping system in each step self sufficient.
        For functioning correctly, it is probably necessary to have some
    reserves [one planets builds slowly big farm, another knowing it builds
    factory over only outpost, .. :)]

    finalSystemPlan - dictionary, keys are planetIDs of players or free planets,
                      and values are dictionaries with keys being techIDs
                      and values being number of those structs.

    """
    system = db[systemID]
    player = client.getPlayer()
    structStats = getSystemStructStats(data, client, db, systemID)
    structsToBuild = {}
    structsToDemolish = {}
    difference = {}
    checkBuildQueues(data, client, db, systemID, prodPlanets)
    # parse final plan to set buildings which need to be build and those that
    # may be demolished
    for planetID in finalSystemPlan:
        difference[planetID] = Utils.dictSubtraction(finalSystemPlan[planetID], structStats.planets[planetID])
    for planetID in difference:
        structsToBuild[planetID] = {}
        structsToDemolish[planetID] = {}
        for techID in difference[planetID]:
            if difference[planetID][techID] > 0:
                structsToBuild[planetID][techID] = difference[planetID][techID]
            elif difference[planetID][techID] < 0:
                structsToDemolish[planetID][techID] = difference[planetID][techID]
    idlePlanets = copy.copy(prodPlanets)
    for planetID in prodPlanets:
        planet = db[planetID]
        if getattr(planet, 'prodQueue', None):
            # something in the build queue, skip the planet
            idlePlanets.remove(planetID)
            continue
        # start the most effective project [CP-wise], which is still leaving
        # sustainable system
        toBuild = getStructBuildEffectivity(client, db, planetID, structsToBuild.keys(), structsToBuild, structsToDemolish)
        for techID, targetPlanetID, targetTechID in toBuild:
            targetPlanet = db[targetPlanetID]
            if len(targetPlanet.slots) == targetPlanet.plSlots and targetTechID == Const.OID_NONE:
                continue
            deltaBio, deltaEn, deltaProd = getSystemStatsChange(client, db, techID, targetPlanetID, targetTechID)
            if structStats.bio + deltaBio >= 0 and structStats.en + deltaEn >= 0:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    techID, 1, targetPlanetID, techID < 1000, 0, targetTechID)
                idlePlanets.remove(planetID)
                # remove this struct from possibility list
                structsToBuild[targetPlanetID][techID] -= 1
                if structsToBuild[targetPlanetID][techID] == 0:
                    del structsToBuild[targetPlanetID][techID]
                break
    return idlePlanets

def getStructBuildEffectivity(client, db, planetID, targetIDs, structsToBuild, structsToDemo):
    """ Tries to sort all possible projects given the limits by parameters by
    their CP-wise effectivity

    targetIDs - iterable of all planets, on which are defined structsToBuild,
                and structsToDemo.
    structToBuild, structsToDemo - dictionaries, keys are planetIDs of players
                      or free planets, and values are dictionaries with keys
                      being techIDs and values being number of those structs.

    Returns list of tuples (techID, targetPlanetID, targetTechID), sorted by
    how long it takes to "pay back itself" from fastest to longest. Negative
    values are valued differently, but order is made with same principle.

    """
    planet = db[planetID]
    player = client.getPlayer()
    possibilitiesBuild = {}
    for targetID in targetIDs:
        target = db[targetID]
        if planetID == targetID:
            coeff = 1
        else:
            coeff = 2
        # if build on empty slot
        for techID in structsToBuild[targetID]:
            tech = client.getFullTechInfo(techID)
            techEff = Rules.techImprEff[player.techs.get(techID, 1)]
            eff = float(tech.prodProd) * techEff / (tech.buildProd * coeff) * sum([x*y/100.0 for x, y in zip(tech.prodProdMod, [target.plBio, target.plMin, target.plEn, 100])])
            eff = round(eff, 3)
            try:
                possibilitiesBuild[eff].append((techID, targetID, Const.OID_NONE))
            except KeyError:
                possibilitiesBuild[eff] = [(techID, targetID, Const.OID_NONE)]
        # if build over the another structure
        for targTechID in structsToDemo[targetID]:
            targTech = client.getFullTechInfo(targTechID)
            targTechEff = Rules.techImprEff[player.techs.get(targTechID, 1)]
            prod = targTech.prodProd * targTechEff * sum([x*y/100.0 for x, y in zip(targTech.prodProdMod, [target.plBio, target.plMin, target.plEn, 100])])
            for techID in structsToBuild[targetID]:
                tech = client.getFullTechInfo(techID)
                techEff = Rules.techImprEff[player.techs.get(techID, 1)]
                finalProd = float(tech.prodProd) * techEff - prod
                if finalProd > 0:
                    eff = finalProd / (tech.buildProd * coeff) * sum([x*y/100.0 for x, y in zip(tech.prodProdMod, [target.plBio, target.plMin, target.plEn, 100])])
                # negative values are handled separately, as division creates illogical coefficient
                else:
                    eff = finalProd * tech.buildProd * coeff * sum([x*y/100.0 for x, y in zip(tech.prodProdMod, [target.plBio, target.plMin, target.plEn, 100])])
                eff = round(eff, 3)
                try:
                    possibilitiesBuild[eff].append((techID, targetID, targTechID))
                except KeyError:
                    possibilitiesBuild[eff] = [(techID, targetID, targTechID)]
    toBuild = []
    toDemo = []
    for infoTuple in [possibilitiesBuild[x] for x in sorted(possibilitiesBuild, reverse=True)]:
        toBuild += infoTuple
    return toBuild

def compareBuildStructPlans(plan1, plan2):
    """ Compare both dictionaries. Only difference from normal comparison
    is that not having key is the same, as having key with value 0.

    Returns Bool value

    """
    plan1Keys = set(plan1.keys())
    plan2Keys = set(plan2.keys())
    for key in plan1Keys - plan2Keys:
        if plan1[key]:
            return False
    for key in plan2Keys - plan1Keys:
        if plan2[key]:
            return False
    for key in plan1Keys & plan2Keys:
        if not plan1[key] == plan2[key]:
            return False
    return True


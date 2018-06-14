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

from ige import log
from ige.ospace import Const
from ige.ospace import Rules
from ige.ospace import Utils

from ai_tools import *

client = None
db = None
playerID = None
player = None

def planetManager():
    global player, data
    for planetID in data.myPlanets:
        sortStructures(client, db, planetID)
    for systemID in data.mySystems:
        system = db[systemID]
        # my planets in the system
        noOfBreweries = 0
        noOfShipyards = 0
        noOfPrisons = 0
        noOfDensSystem = {}
        idlePlanets = data.myPlanets & set(system.planets)
        for planetID in copy.copy(idlePlanets):
            planet = db[planetID]
            noOfBases = 0
            noOfDens = 0
            otherStructID = None
            noOfDensSystem[planetID] = 0
            for struct in planet.slots:
                if struct[0] == Rules.Tech.PIRATEBASE:
                    noOfBases += 1
                elif struct[0] == Rules.Tech.PIRATEBREWERY:
                    noOfBreweries += 1
                elif struct[0] == Rules.Tech.PIRATEDEN:
                    noOfDens += 1
                    noOfDensSystem[planetID] += 1
                elif struct[0] == Rules.Tech.PIRATESD:
                    noOfShipyards += 1
                elif struct[0] == Rules.Tech.PIRATEPRISON:
                    noOfPrisons += 1
                else:
                    otherStructID = struct[0]
            if getattr(planet, 'prodQueue', None):
                # something is in the production queue, account it and do next
                for task in planet.prodQueue:
                    if task.techID == Rules.Tech.PIRATEBREWERY:
                        noOfBreweries += task.quantity
                    elif task.techID == Rules.Tech.PIRATESD:
                        noOfShipyards += task.quantity
                    elif task.techID == Rules.Tech.PIRATEPRISON:
                        noOfPrisons += task.quantity
                    elif task.techID == Rules.Tech.PLCOND5 or\
                            task.techID == Rules.Tech.PLASSEMBL5:
                        data.nonhabPlanets.remove(task.targetID)
                idlePlanets.remove(planetID)
                continue
            # fill all free slots with pirate dens [super cheap production building]
            if planet.plSlots > len(planet.slots):
                log.debug(playerID, "PIRATEAI - building pirate den", planet.oid)
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planet.oid,
                    Rules.Tech.PIRATEDEN, planet.plSlots - len(planet.slots),
                    planet.oid, Rules.Tech.PIRATEDEN < 1000, 0, Const.OID_NONE)
                idlePlanets.remove(planetID)
                noOfDensSystem[planetID] += planet.plSlots - len(planet.slots)
                continue
            # make sure every planet has two Pirate Bases [basic defense]
            if noOfBases < 2 and planet.plSlots >= 2:
                # build on the other structure [something nonpiratish :)] or
                # pirate den
                if otherStructID:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planet.oid,
                        Rules.Tech.PIRATEBASE, 1, planet.oid, Rules.Tech.PIRATEBASE < 1000,
                        0, otherStructID)
                    idlePlanets.remove(planetID)
                    continue
                elif noOfDens:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planet.oid,
                        Rules.Tech.PIRATEBASE, min(noOfDens, 2 - noOfBases),
                        planet.oid, Rules.Tech.PIRATEBASE < 1000, 0,
                        Rules.Tech.PIRATEDEN)
                    idlePlanets.remove(planetID)
                    noOfDensSystem[planetID] -= min(noOfDens, 2 - noOfBases)
                    continue
        # rest of the management will be system wide
        # first - build pirate base on all free systems, if the free system
        # has your population, build there a Den
        toColonize = data.freePlanets & set(system.planets)
        for planetID in copy.copy(idlePlanets):
            planet = db[planetID]
            if toColonize:
                targetID = toColonize.pop()
                target = db[targetID]
                if target.owner == playerID:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PIRATEDEN, 1,
                        targetID, Rules.Tech.PIRATEDEN < 1000, 0, Const.OID_NONE)
                    idlePlanets.remove(planetID)
                    noOfDensSystem[targetID] = 1
                    continue
                else:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PIRATEBASE, 1,
                        targetID, Rules.Tech.PIRATEBASE < 1000, 0, Const.OID_NONE)
                    idlePlanets.remove(planetID)
                    continue
        # second - build brewery, if not present in the system
        if not noOfBreweries:
            for planetID in copy.copy(idlePlanets) & set(noOfDensSystem.keys()):
                if noOfDensSystem[planetID] < 1:
                    # there was den, but it is not anymore, try another planet
                    continue
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.PIRATEBREWERY, 1, planetID,
                    Rules.Tech.PIRATEBASE < 1000, 0, Rules.Tech.PIRATEDEN)
                idlePlanets.remove(planetID)
                noOfDensSystem[planetID] -= 1
                noOfBreweries += 1
                break
        # third - build some Prisons over the Dens [but be aware of the energy]
        sumOfDens = sum(noOfDensSystem.values())
        denTech = Rules.techs[Rules.Tech.PIRATEDEN]
        prisonTech = Rules.techs[Rules.Tech.PIRATEPRISON]
        energy = sumOfDens * denTech.prodEn * 1.25 - noOfPrisons * prisonTech.operEn
        possiblePrisons = math.floor(energy / (denTech.prodEn * 1.25 + prisonTech.operEn))
        for planetID in copy.copy(idlePlanets) & set(noOfDensSystem.keys()):
            if noOfDensSystem[planetID] < 1 or possiblePrisons < 1:
                # there was a Den, but it is not there anymore, try another planet
                continue
            planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                Rules.Tech.PIRATEPRISON, 1, planetID,
                Rules.Tech.PIRATEBASE < 1000, 0, Rules.Tech.PIRATEDEN)
            idlePlanets.remove(planetID)
            noOfDensSystem[planetID] -= 1
            possiblePrisons -= 1
        # fourth - build a Shipyard, if there is more than 10 slots in the system
        slots = 0
        for planetID in system.planets:
            slots += db[planetID].plSlots
        if slots > 10 and not noOfShipyards:
            for planetID in copy.copy(idlePlanets) & set(noOfDensSystem.keys()):
                if noOfDensSystem[planetID] < 1:
                    # there was a Den, but it is not there anymore, try another planet
                    continue
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                    Rules.Tech.PIRATESD, 1, planetID,
                    Rules.Tech.PIRATEBASE < 1000, 0, Rules.Tech.PIRATEDEN)
                idlePlanets.remove(planetID)
                noOfDensSystem[planetID] -= 1
                noOfShipyards = 1
                break
        # fifth - expand slots, if available
        if Rules.Tech.ADDSLOT3 in player.techs:
            for planetID in copy.copy(idlePlanets):
                planet = db[planetID]
                if planet.plSlots < planet.plMaxSlots:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.ADDSLOT3, 1, planetID,
                        Rules.Tech.ADDSLOT3 < 1000, 0, Const.OID_NONE)
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PIRATEDEN, 1, planetID,
                        Rules.Tech.PIRATEDEN < 1000, 0, Const.OID_NONE)
                    idlePlanets.remove(planetID)
        # sixth - condensate and assembly all other planets
        for targetID in copy.copy(data.nonhabPlanets & set(system.planets)):
            target = db[targetID]
            if Rules.Tech.PLCOND5 in player.techs and target.plType == u'G':
                if idlePlanets:
                    planetID = idlePlanets.pop()
                    planet = db[planetID]
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PLCOND5, 1, targetID,
                        Rules.Tech.PLCOND5 < 1000, 0, Const.OID_NONE)
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PIRATEBASE, 1, targetID,
                        Rules.Tech.PIRATEBASE < 1000, 0, Const.OID_NONE)
                    data.nonhabPlanets.remove(targetID)
            elif Rules.Tech.PLASSEMBL5 in player.techs and target.plType == u'A':
                if idlePlanets:
                    planetID = idlePlanets.pop()
                    planet = db[planetID]
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PLASSEMBL5, 1, targetID,
                        Rules.Tech.PLASSEMBL5 < 1000, 0, Const.OID_NONE)
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID,
                        Rules.Tech.PIRATEBASE, 1, targetID,
                        Rules.Tech.PIRATEBASE < 1000, 0, Const.OID_NONE)
                    data.nonhabPlanets.remove(targetID)
        # ===============
        # last - remaining idle planets should start producing ships
        systemFleets = getattr(system, 'fleets', [])
        hasScout = False
        for fleetID in systemFleets:
            fleet = db[fleetID]
            if getattr(fleet, 'owner', Const.OID_NONE) == playerID:
                if fleetContains(fleet, {4:1}):
                    hasScout = True
        for planetID in idlePlanets:
            if not hasScout:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 4, 1, planetID, True, False, Const.OID_NONE)
            else:
                dice = random.randint(1, 3)
                if dice == 1:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 1, 3, planetID, True, False, Const.OID_NONE)
                elif dice == 2:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 2, 3, planetID, True, False, Const.OID_NONE)
                else:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 3, 2, planetID, True, False, Const.OID_NONE)

def shipDesignManager():
    global client
    # there are 4 basic designs
    # anti-small fighter
    # anti-medium fighter
    # bomber
    # scout

    if len(player.shipDesigns.keys()) < 4:
        # add the basic designs
        client.cmdProxy.addShipDesign(playerID, 'Brawler',
                Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.CANNON1:2, Rules.Tech.PIRATEFTLENG:3})
        client.cmdProxy.addShipDesign(playerID, "Enforcer",
                Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.SSROCKET2:2, Rules.Tech.PIRATEFTLENG:3})
        client.cmdProxy.addShipDesign(playerID, "Raider",
                 Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                 Rules.Tech.CONBOMB1:1, Rules.Tech.PIRATEFTLENG:3})
        client.cmdProxy.addShipDesign(playerID, "Squeal",
                Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                Rules.Tech.SCANNERMOD1:1, Rules.Tech.PIRATEFTLENG:3})

def fleetsManager():
    global db, client, data
    attackFleets = set()
    attackMinimum = {1:10, 2:10, 3:10, 4:1}
    for fleetID in copy.copy(data.myFleets & data.idleFleets):
        fleet = db.get(fleetID, None)
        if fleet.combatCounter and fleet.orbiting not in data.mySystems:
            # Send the fighting fleet back, if even the nearest system
            # is out of range
            maxRange = subfleetMaxRange(client, db, None, fleetID)
            nearestSysIDs = findNearest(db, fleet, data.mySystems)
            if len(nearestSysIDs):
                nearestSysID = nearestSysIDs[0]
                targSys = db[nearestSysID]
                distance = math.hypot(targSys.x-fleet.x, targSys.y-fleet.y)
                if distance >= maxRange:
                    orderFleet(client, db, fleetID, Const.FLACTION_MOVE, nearestSysID, None)
        elif not fleet.orbiting in data.mySystems:
            if fleetContains(fleet, attackMinimum):
                attackFleets.add(fleetID)
            else:
                nearestSysIDs = findNearest(db, fleet, data.mySystems)

                if len(nearestSysIDs):
                    nearestSysID = nearestSysIDs[0]
                    orderFleet(client, db, fleetID, Const.FLACTION_MOVE, nearestSysID, None)
        else:
            if fleetContains(fleet, attackMinimum):
                attackFleets.add(fleetID)
    for fleetID in copy.copy(attackFleets):
        fleet = db.get(fleetID, None)
        sheet = getFleetSheet(fleet)
        ships = {}
        if fleet.orbiting in data.mySystems:
            ships[3] = min(sheet[1], sheet[2], sheet[3])
            ships[1] = ships[2] = ships[3]
            ships[4] = 1
            maxRange = subfleetMaxRange(client, db, ships, fleetID)
            nearestSysIDs = findNearest(db, fleet, data.otherSystems & data.relevantSystems, maxRange * 0.45)
            if len(nearestSysIDs):
                nearestSys = nearestSysIDs[0]
                orderPartFleet(client, db, ships, False, fleetID, Const.FLACTION_MOVE, nearestSys, None)
        else:
            maxRange = max(0, fleet.storEn - fleet.maxEn / 2) * fleet.speed / 24.0
            nearestSysIDs = findNearest(db, fleet, data.otherSystems & data.relevantSystems, maxRange)
            if len(nearestSysIDs):
                nearestSysID = nearestSysIDs[0]
                orderFleet(client, db, fleetID, Const.FLACTION_MOVE, nearestSysID, None)
            else:
                nearestSysIDs = findNearest(db, fleet, data.mySystems)
                if len(nearestSysIDs):
                    nearestSysID = nearestSysIDs[0]
                    orderFleet(client, db, fleetID, Const.FLACTION_MOVE, nearestSysID, None)


def run(aclient):
    global client, db, player, playerID
    client = aclient
    db = client.db
    player = client.getPlayer()
    playerID = client.getPlayerID()

    tool_parseDB(client, db)
    doRelevance(client, db, Rules.pirateInfluenceRange)

    shipDesignManager()
    planetManager()

    fleetsManager()

    client.saveDB()


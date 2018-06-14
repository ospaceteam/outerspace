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
import random

from ige import log
from ige.ospace import Const
from ige.ospace import Rules
from ige.ospace import Utils

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
            finalSystemPlan[planetID] = {Rules.Tech.RENEGADEBASE:1}
        for planetID in data.myPlanets & set(system.planets):
            planet = db[planetID]
            if Rules.Tech.RENEGADECOSMODROME in actualStats.planets[planetID] or\
                    Rules.Tech.RENEGADEBASE3 in actualStats.planets[planetID] or\
                    Rules.Tech.RENEGADEBASE3MINOR in actualStats.planets[planetID]:
                finalSystemPlan[planetID] = {Rules.Tech.RENEGADEBASE3:1,
                                        Rules.Tech.RENEGADECOSMODROME:min(planet.plSlots - 1, 1),
                                        Rules.Tech.RENEGADEBASE3MINOR:max(planet.plSlots - 2, 0)}
                continue
            elif planet.plStratRes and\
                    compareBuildStructPlans(actualStats.planets[planetID], {
                                                Rules.Tech.RENEGADEBASE2:1,
                                                Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}):
                finalSystemPlan[planetID] = {Rules.Tech.RENEGADEBASE3:1,
                                            Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}
                continue
            elif Rules.Tech.RENEGADEBASE2 in actualStats.planets[planetID]:
                finalSystemPlan[planetID] = {Rules.Tech.RENEGADEBASE2:1,
                                            Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}
                continue
            elif actualStats.planets[planetID].setdefault(Rules.Tech.RENEGADEBASE, 0) > 0:
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, Rules.Tech.RENEGADEBASE2,
                        1, planetID, False, False, Rules.Tech.RENEGADEBASE)
                finalSystemPlan[planetID] = actualStats.planets[planetID]
                continue
            else:
                finalSystemPlan[planetID] = {Rules.Tech.RENEGADEBASE:1}
                continue
        idlePlanets = buildSystem(client, db, systemID, data.myProdPlanets & set(system.planets), finalSystemPlan)
        # build ships just in case cosmodrome is present
        hasCosmodrome = False
        for planetID in data.myPlanets & set(system.planets):
            if Rules.Tech.RENEGADECOSMODROME in buildStats.planets[planetID]:
                hasCosmodrome = True
                break
        if hasCosmodrome:
            for planetID in idlePlanets:
                # there is our airbase in the system - we can build some random ship
                shipDraw = random.randint(1, 10)
                # 1/10 - Frigate
                # 2/10 - Corvette
                # 7/10 - Fighter
                if shipDraw == 1:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 3, 1, planetID, True, False, Const.OID_NONE)
                elif shipDraw <= 3:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 2, 1, planetID, True, False, Const.OID_NONE)
                else:
                    planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(planetID, 1, 1, planetID, True, False, Const.OID_NONE)

def shipDesignManager():
    # there are 3 basic designs    created by the server
    # 1: Fighter [Small hull, Cockpit, 1x Cannon]
    # 2: Corvette [Small hull, Cockpit, 2x Cannon, 1x Steel Armor
    # 3: Frigate [Medium hull, Bridge, 2x Cannon, 2x SS Rocket]
    pass

def researchManager():
    pass

def attackManager():
    pass

def run(aclient):
    global client, db, player, playerID
    client = aclient
    db = client.db
    player = client.getPlayer()
    playerID = client.getPlayerID()

    tool_parseDB(client, db)

    researchManager()
    shipDesignManager()
    systemManager()

    attackManager()
    client.saveDB()


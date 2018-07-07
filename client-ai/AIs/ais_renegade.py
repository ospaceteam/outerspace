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

from ais_base import AI
import ai_tools as tool


class Renegade(AI):
    """ Renegade is purely defensive AI, very static. It allows CP pacts and refuel
    for civilian ships, and has 5 pregenerated designs.

    1: Fighter [Small hull, Cockpit, 1x Cannon, 2x STL Engine]
    2: Corvette [Small hull, Cockpit, 2x Cannon, 1x Steel Armor, 1x STL Engine]
    3: Frigate [Medium hull, Bridge, 2x Cannon, 2x SS Rocket, 2x STL Engine]
    special using uranium:
    4: Destroyer [Medium hull, Bridge, 4x Cannon, 2x SS Rocket, 3x Nuclear STL Engine]
    special using titanium:
    5: Frigate [Crude Titanium Medium hull, Bridge, 5x Cannon, 3x SS Rocket, 4x STL Engine]
    """

    def _buildSpecialShips(self, planet):
        uraniumSpec = self.player.shipDesigns[4]
        titaniumSpec = self.player.shipDesigns[5]
        if self.player.stratRes.get(Const.SR_TL1A, 0) >= uraniumSpec.buildSRes[Const.SR_TL1A]:
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 4, 1, planet.oid, True, False, Const.OID_NONE)
            return True
        elif self.player.stratRes.get(Const.SR_TL1B, 0) >= titaniumSpec.buildSRes[Const.SR_TL1B]:
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 5, 1, planet.oid, True, False, Const.OID_NONE)
            return True

    def _buildNormalShips(self, planet):
            shipDraw = random.randint(1, 10)
            # if there is enough special resources for our unique designs, build those!
            # 1/10 - Frigate
            # 3/10 - Corvette
            # 6/10 - Fighter
            if shipDraw == 1:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 3, 1, planet.oid, True, False, Const.OID_NONE)
            elif shipDraw <= 4:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 2, 1, planet.oid, True, False, Const.OID_NONE)
            else:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 1, 1, planet.oid, True, False, Const.OID_NONE)

    def _buildShips(self, idlePlanets):
        for planetID in idlePlanets:
            planet = self.db[planetID]
            if self._buildSpecialShips(planet):
                continue
            self._buildNormalShips(planet)

    def _preparePlanetPlan(self, actualStats, planetID):
        planet = self.db[planetID]
        if Rules.Tech.RENEGADECOSMODROME in actualStats.planets[planetID] or\
                Rules.Tech.RENEGADEBASE3 in actualStats.planets[planetID] or\
                Rules.Tech.RENEGADEBASE3MINOR in actualStats.planets[planetID]:
            return {Rules.Tech.RENEGADEBASE3:1,
                    Rules.Tech.RENEGADECOSMODROME:min(planet.plSlots - 1, 1),
                    Rules.Tech.RENEGADEBASE3MINOR:max(planet.plSlots - 2, 0)}
        elif planet.plStratRes and\
                tool.compareBuildStructPlans(actualStats.planets[planetID], {
                                            Rules.Tech.RENEGADEBASE2:1,
                                            Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}):
            return {Rules.Tech.RENEGADEBASE3:1,
                    Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}
        elif Rules.Tech.RENEGADEBASE2 in actualStats.planets[planetID]:
            return {Rules.Tech.RENEGADEBASE2:1,
                    Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}
        elif actualStats.planets[planetID].setdefault(Rules.Tech.RENEGADEBASE, 0) > 0:
            planet.prodQueue, self.player.stratRes = \
                    self.client.cmdProxy.startConstruction(planetID, Rules.Tech.RENEGADEBASE2,
                                                      1, planetID, False, False, Rules.Tech.RENEGADEBASE)
            return actualStats.planets[planetID]
        else:
            return {Rules.Tech.RENEGADEBASE:1}

    def system_manager(self):
        for planetID in self.data.myPlanets:
            tool.sortStructures(self.client, self.db, planetID)
        for systemID in self.data.mySystems:
            system = self.db[systemID]
            # creation of final system plans
            finalSystemPlan = {}
            actualStats = tool.getSystemStructStats(self.data, self.client, self.db, systemID)
            buildStats = tool.getSystemStructStats(self.data, self.client, self.db, systemID, False)
            for planetID in (self.data.myPlanets | self.data.freePlanets) & set(system.planets):
                finalSystemPlan[planetID] = self._preparePlanetPlan(actualStats, planetID)
            idlePlanets = tool.buildSystem(self.data, self.client, self.db, systemID, self.data.myProdPlanets & set(system.planets), finalSystemPlan)
            # build ships just in case cosmodrome is present, or being build, in the system
            hasCosmodrome = False
            for planetID in self.data.myPlanets & set(system.planets):
                if Rules.Tech.RENEGADECOSMODROME in buildStats.planets[planetID]:
                    hasCosmodrome = True
                    break
            if hasCosmodrome:
                self._buildShips(idlePlanets)

    def diplomacy_manager(self):
        # renegades are friendly, want to trade, and can help refuel civilian ships
        for contactID in self.player.diplomacyRels:
            dipl = self.client.getDiplomacyWith(contactID)
            for pactID in [Const.PACT_ALLOW_CIVILIAN_SHIPS, Const.PACT_ALLOW_TANKING, Const.PACT_MINOR_CP_COOP, Const.PACT_MAJOR_CP_COOP]:
                pactSpec = Rules.pactDescrs[pactID]
                if dipl.relation < pactSpec.validityInterval[0] or dipl.relation > pactSpec.validityInterval[1]:
                    # not friendly enough
                    continue
                if pactID in dipl.pacts and dipl.pacts[pactID][0] in [Const.PACT_ACTIVE, Const.PACT_INACTIVE]:
                    # nothing more to do, move along
                    continue
                # hey, we should enable this pact!
                conditions = [pactID]
                self.player.diplomacyRels = self.client.cmdProxy.changePactCond(self.player.oid, contactID, pactID, Const.PACT_INACTIVE, conditions)

    def run(self):
        self.system_manager()
        self.diplomacy_manager()


def run(aclient):
    ai = Renegade(aclient)
    ai.run()
    aclient.saveDB()


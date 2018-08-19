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

from ai import AI
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

    def _build_special_ships(self, planet):
        uranium_spec = self.player.shipDesigns[4]
        titanium_spec = self.player.shipDesigns[5]
        if self.player.stratRes.get(Const.SR_TL1A, 0) >= uranium_spec.buildSRes[Const.SR_TL1A]:
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 4, 1, planet.oid, True, False, Const.OID_NONE)
            return True
        elif self.player.stratRes.get(Const.SR_TL1B, 0) >= titanium_spec.buildSRes[Const.SR_TL1B]:
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 5, 1, planet.oid, True, False, Const.OID_NONE)
            return True

    def _build_normal_ships(self, planet):
            ship_draw = random.randint(1, 10)
            # if there is enough special resources for our unique designs, build those!
            # 1/10 - Frigate
            # 3/10 - Corvette
            # 6/10 - Fighter
            if ship_draw == 1:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 3, 1, planet.oid, True, False, Const.OID_NONE)
            elif ship_draw <= 4:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 2, 1, planet.oid, True, False, Const.OID_NONE)
            else:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid, 1, 1, planet.oid, True, False, Const.OID_NONE)

    def _build_ships(self, idle_planets):
        for planet_id in idle_planets:
            planet = self.db[planet_id]
            if self._build_special_ships(planet):
                continue
            self._build_normal_ships(planet)

    def _prepare_free_planet_plan(self, planet_id):
        planet = self.db[planet_id]
        if planet.plStratRes:
            return {Rules.Tech.RENEGADEBASE3:1}
        else:
            return {Rules.Tech.RENEGADEBASE2:1}

    def _prepare_planet_plan(self, actual_stats, planet_id):
        planet = self.db[planet_id]
        if Rules.Tech.RENEGADECOSMODROME in actual_stats.planets[planet_id] or\
                Rules.Tech.RENEGADEBASE3 in actual_stats.planets[planet_id] or\
                Rules.Tech.RENEGADEBASE3MINOR in actual_stats.planets[planet_id]:
            return {Rules.Tech.RENEGADEBASE3:1,
                    Rules.Tech.RENEGADECOSMODROME:min(planet.plSlots - 1, 1),
                    Rules.Tech.RENEGADEBASE3MINOR:max(planet.plSlots - 2, 0)}
        elif planet.plStratRes and\
                tool.compareBuildStructPlans(actual_stats.planets[planet_id], {
                                            Rules.Tech.RENEGADEBASE2:1,
                                            Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}):
            return {Rules.Tech.RENEGADEBASE3:1,
                    Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}
        elif Rules.Tech.RENEGADEBASE2 in actual_stats.planets[planet_id]:
            return {Rules.Tech.RENEGADEBASE2:1,
                    Rules.Tech.RENEGADEBASE2MINOR:planet.plSlots - 1}
        elif Rules.Tech.RENEGADEBASE in actual_stats.planets[planet_id] and planet_id in self.data.myPlanets:
            planet.prodQueue, self.player.stratRes = \
                    self.client.cmdProxy.startConstruction(planet_id, Rules.Tech.RENEGADEBASE2,
                                                      1, planet_id, False, False, Rules.Tech.RENEGADEBASE)
            return actual_stats.planets[planet_id]
        else:
            return {Rules.Tech.RENEGADEBASE:1}

    def economy_manager(self):
        for planet_id in self.data.myPlanets:
            tool.sortStructures(self.client, self.db, planet_id)
        for system_id in self.data.mySystems:
            system = self.db[system_id]
            # creation of final system plans
            final_system_plan = {}
            actual_stats = tool.getSystemStructStats(self.data, self.client, self.db, system_id)
            build_stats = tool.getSystemStructStats(self.data, self.client, self.db, system_id, False)
            for planet_id in self.data.myPlanets & set(system.planets):
                final_system_plan[planet_id] = self._prepare_planet_plan(actual_stats, planet_id)
            for planet_id in self.data.freePlanets & set(system.planets):
                final_system_plan[planet_id] = self._prepare_free_planet_plan(planet_id)
            idle_planets = tool.buildSystem(self.data, self.client, self.db, system_id, self.data.myProdPlanets & set(system.planets), final_system_plan)
            # build ships just in case cosmodrome is present, or being build, in the system
            has_cosmodrome = False
            for planet_id in self.data.myPlanets & set(system.planets):
                if Rules.Tech.RENEGADECOSMODROME in build_stats.planets[planet_id]:
                    has_cosmodrome = True
                    break
            if has_cosmodrome:
                self._build_ships(idle_planets)

    def run(self):
        top_prio_tech = [Rules.Tech.RENEGADEBASE2MINOR,
                         Rules.Tech.RENEGADEBASE3MINOR,
                         Rules.Tech.RENEGADEBASE3,
                         Rules.Tech.RENEGADEBASE2]
        mid_importance_tech = [Rules.Tech.SMALLHULL1,
                               Rules.Tech.STLENG1,
                               Rules.Tech.CANNON1,
                               Rules.Tech.SCOCKPIT1]
        low_prio_tech = [Rules.Tech.MEDIUMHULL2,
                   Rules.Tech.SBRIDGE1,
                   Rules.Tech.SSROCKET,
                   Rules.Tech.STEELARM2,
                   Rules.Tech.NSTLENG2,
                   Rules.Tech.RENEGADETITANIUMMHULL,
                   Rules.Tech.RENEGADECOSMODROME]
        ignored_tech = [Rules.Tech.RENEGADEBASE]
        tech_prio = {10: top_prio_tech,
                     3: mid_importance_tech,
                     1: low_prio_tech,
                     0: ignored_tech}
        self.research_manager(tech_prio)
        self.economy_manager()
        self.diplomacy_manager(friendly_types=[Const.T_PLAYER, Const.T_AIPLAYER, Const.T_AIRENPLAYER],
                               pacts=[Const.PACT_ALLOW_CIVILIAN_SHIPS, Const.PACT_ALLOW_TANKING,
                                      Const.PACT_MINOR_SCI_COOP, Const.PACT_MAJOR_SCI_COOP,
                                      Const.PACT_MINOR_CP_COOP, Const.PACT_MAJOR_CP_COOP])


def run(aclient):
    ai = Renegade(aclient)
    ai.run()
    aclient.saveDB()


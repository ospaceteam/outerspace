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

import ai_tools as tool
from ai import AI

class Mutant(AI):
    def __init__(self, client):
        enemy_types = [Const.T_PLAYER, Const.T_AIPLAYER, Const.T_PIRPLAYER, Const.T_AIPIRPLAYER, Const.T_AIRENPLAYER]
        super(Mutant, self).__init__(client, enemy_types)
        tool.doRelevance(self.data, self.client, self.db, 10)

    def _system_worthiness(self, system, weights):
        """ Scans system, and based on planetary composition and weights returns constant.
        Weights are expected to be quadruplet of numbers, for [gaia, terrestial, marginal, rest]
        """
        worth = 0
        for planet_id in self.data.myPlanets & set(system.planets):
            planet = self.db[planet_id]
            if planet.plType == u"I":  # gaia
                worth += weights[0]
            elif planet.plType == u"E":  # terrestial
                worth += weights[1]
            elif planet.plType == u"M":  # marginal
                worth += weights[2]
            else:  # junk
                worth += weights[3]
        return worth

    def _create_gaia_blueprint(self, space):
        # preserve minefield position, and in case there is no
        # minefield in the system, try to place it on the first planet
        # available
        power_plants = math.ceil(max(space - 1, 0) / 6.0)
        factories = space - power_plants
        return {Rules.Tech.MUTANTBASE4:1,
                Rules.Tech.MUTANTPP2:power_plants,
                Rules.Tech.MUTANTFACT2:factories}

    def _create_terrestial_blueprint(self, space):
        # preserve minefield position, and in case there is no
        # minefield in the system, try to place it on the first planet
        # available
        power_plants = math.ceil(max(space - 1, 0) / 5.0)
        factories = space - power_plants
        return {Rules.Tech.MUTANTBASE3:1,
                Rules.Tech.MUTANTPP2:power_plants,
                Rules.Tech.MUTANTFACT2:factories}

    def _create_marginal_blueprint(self, space):
        # preserve minefield position, and in case there is no
        # minefield in the system, try to place it on the first planet
        # available
        power_plants = math.ceil(max(space - 1, 0) / 7.0)
        factories = space - power_plants
        return {Rules.Tech.MUTANTBASE2:1,
                Rules.Tech.MUTANTPP2:power_plants,
                Rules.Tech.MUTANTFACT1:factories}

    def _create_submarginal_blueprint(self, space):
        # preserve minefield position, and in case there is no
        # minefield in the system, try to place it on the first planet
        # available
        power_plants = math.ceil(max(space - 1, 0) / 5.0)
        factories = space - power_plants
        return {Rules.Tech.MUTANTBASE:1,
                Rules.Tech.MUTANTPP1:power_plants,
                Rules.Tech.MUTANTFACT1:factories}

    def _insert_minefield(self, system, system_blueprint):
        # pick worst possible planet to put minefield on, don't waste
        # precious gaia space if possible
        # also ignore actual state - don't be afraid to rebuild if planet is
        # promoted
        for avoided_types in [(u"I", u"E", u"M"), (u"I", u"E"), (u"I",), ()]:
            # sorting, to avoid rebuilds between equivalent planets
            for planet_id in sorted(system_blueprint):
                planet = self.db[planet_id]
                if planet.plType in avoided_types or planet.plSlots == 1:
                    continue
                if Rules.Tech.MUTANTFACT1 in system_blueprint[planet_id]:
                    assert system_blueprint[planet_id][Rules.Tech.MUTANTFACT1] > 0
                    system_blueprint[planet_id][Rules.Tech.MUTANTFACT1] -= 1
                elif Rules.Tech.MUTANTFACT2 in system_blueprint[planet_id]:
                    assert system_blueprint[planet_id][Rules.Tech.MUTANTFACT2] > 0
                    system_blueprint[planet_id][Rules.Tech.MUTANTFACT2] -= 1
                else:
                    continue
                system_blueprint[planet_id][Rules.Tech.MUTANTMINES] = 1
                return

    def _cleanup_dict(self, dict_):
        for key in dict_.keys():
            if not dict_[key]:
                del dict_[key]

    def _create_system_blueprint(self, system):
        # create appropriate build plans
        system_blueprint = {}
        for planet_id in self.data.freePlanets & set(system.planets):
            system_blueprint[planet_id] = {Rules.Tech.MUTANTBASE:1}
        for planet_id in self.data.myPlanets & set(system.planets):
            planet = self.db[planet_id]
            space = planet.plSlots - 1 # the main building is there every time
            if planet.plType == u"I":  # gaia
                system_blueprint[planet_id] = self._create_gaia_blueprint(space)
                continue
            elif planet.plType == u"E":  # terrestial
                system_blueprint[planet_id] = self._create_terrestial_blueprint(space)
                continue
            elif planet.plType == u"M":  # marginal
                system_blueprint[planet_id] = self._create_marginal_blueprint(space)
                continue
            else: # all sub-marginal types
                system_blueprint[planet_id] = self._create_submarginal_blueprint(space)
                continue
        self._cleanup_dict(system_blueprint)
        self._insert_minefield(system, system_blueprint)
        return system_blueprint

    def _system_manager(self):
        for planet_id in self.data.myPlanets:
            tool.sortStructures(self.client, self.db, planet_id)
        for system_id in self.data.mySystems:
            system = self.db[system_id]
            # creation of final system plans
            system_blueprint = self._create_system_blueprint(system)
            idle_planets = tool.buildSystem(self.data, self.client, self.db, system_id, self.data.myProdPlanets & set(system.planets), system_blueprint)
            # rest of the planets build ships
            # first get all our ships in the system
            system_fleet = {}
            for fleet_id in getattr(system, 'fleets', []):
                fleet = self.db[fleet_id]
                if getattr(fleet, 'owner', Const.OID_NONE) == self.player.oid:
                    system_fleet = Utils.dictAddition(system_fleet, tool.getFleetSheet(fleet))
            hasSeeders = False
            hasSeekers = False
            try:
                if system_fleet[2] >= 2: hasSeeders = True
            except KeyError:
                pass
            try:
                if system_fleet[3] >= 2: hasSeekers = True
            except KeyError:
                pass
            # this variable will gather how valuable system is in regards of fighter defense
            # in general, mutant has quite significant planetary defense, so our target is
            # to have only about 10 % production spend on support
            fighters_to_defend = self._system_worthiness(system, [15,8,5,3])

            for planet_id in idle_planets:
                planet = self.db[planet_id]
                shipDraw = random.randint(1, 10)
                if (not hasSeeders or not hasSeekers) and shipDraw < 9:
                    # there is 20% chance it won't build civilian ships, but military one
                    if not hasSeeders:
                        planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, 2, 1, planet_id, True, False, Const.OID_NONE)
                        continue
                    elif not hasSeekers:
                        planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, 3, 1, planet_id, True, False, Const.OID_NONE)
                        continue
                # rest is creation of ships based on current state + expected guard fighters
                try:
                    fighters = system_fleet[1]
                except KeyError:
                    fighters = 0
                try:
                    bombers = system_fleet[4]
                except KeyError:
                    bombers = 0
                expected_fighters = bombers * 1.5 + fighters_to_defend
                weight_fighter = 3
                weight_bomber = 2
                if expected_fighters > fighters:
                    # we have to build more fighters
                    weight_fighter += 1
                elif expected_fighters < fighters:
                    # we have too many fighters - let's prefer bombers for now
                    weight_bomber += 1
                choice = Utils.weightedRandom([1,4], [weight_fighter, weight_bomber])
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, choice, 2, planet_id, True, False, Const.OID_NONE)

    def _colonize_occupied_systems(self, seeder_id):
        seeder_fleets = self.data.myFleetsWithDesign.get(seeder_id, set())
        should_repeat = False
        for fleet_id in copy.copy(seeder_fleets & self.data.idleFleets):
            fleet = self.db[fleet_id]
            orbit_id = fleet.orbiting
            if orbit_id != Const.OID_NONE:
                orbit = self.db[orbit_id]
                if set(orbit.planets) & self.data.freePlanets and orbit_id in self.data.otherSystems:
                    target_id = self._find_best_planet(set(orbit.planets) & self.data.freePlanets)
                    fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                        {seeder_id:1}, True, fleet_id, Const.FLACTION_DEPLOY, target_id, seeder_id)
                    self.data.myFleetSheets[fleet_id][seeder_id] -= 1
                    if self.data.myFleetSheets[fleet_id][seeder_id] == 0:
                        del self.data.myFleetSheets[fleet_id][seeder_id]
                        seeder_fleets.remove(fleet_id)
        return should_repeat

    def _expansion_manager(self):
        should_repeat = True
        seeker_id = 3
        seeder_id = 2
        while should_repeat:
            should_repeat = False
            should_repeat |= self._explore(seeker_id)
            should_repeat |= self._colonize_free_systems(copy.copy(self.data.freeSystems), seeder_id)
            should_repeat |= self._colonize_occupied_systems(seeder_id)

    def _ship_design_manager(self):
        # there are 4 basic designs    created by the server
        # 1: Swarmer [Small hull, Cockpit, 2x EMCannon, 2xFTL]
        # 2: Seeder [Medium hull, Cockpit, Mutant Colony Pod, 4xFTL]
        # 3: Seeker [Small hull, Cockpit, 1x ActiveScan, 2xFTL]
        # 4: Sower [Small hull, Cockpit, 1x Conv.Bomb, 2xFTL]
        pass

    def _logistics_manager(self):
        for system_id in self.data.mySystems - self.data.myRelevantSystems:
            system = self.db[system_id]
            for fleet_id in set(system.fleets) & self.data.idleFleets:
                fleet = self.db[fleet_id]
                subfleet = tool.getSubfleet(fleet, {1:0, 4:0}, False)
                if len(subfleet):
                    fleet_range = tool.subfleetMaxRange(self.client, self.db, {1:0, 4:0}, fleet_id)
                    relevant_sys_id = tool.findNearest(self.db, system, self.data.myRelevantSystems, fleet_range)
                    if relevant_sys_id:
                        relevant_sys_id = relevant_sys_id[0]
                        fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                            {1:0, 4:0}, True, fleet_id, Const.FLACTION_MOVE, relevant_sys_id, None)
                        self.data.idleFleets -= set([fleet_id])
                    else:
                        min_dist = fleet_range
                        min_dist_sys_id = None
                        min_dist_rel = self.data.distanceToRelevance[system_id]
                        for temp_id, dist in self.data.distanceToRelevance.items():
                            temp = self.db[temp_id]
                            distance = math.hypot(temp.x - system.x, temp.y - system.y)
                            if distance < min_dist and dist < min_dist_rel:
                                min_dist = distance
                                min_dist_sys_id = temp_id
                                min_dist_rel = dist
                        if min_dist_sys_id:
                            fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                                {1:0, 4:0}, True, fleet_id, Const.FLACTION_MOVE, min_dist_sys_id, None)
                            self.data.idleFleets -= set([fleet_id])

    def _get_attack_fleets(self):
        attack_fleets = set()
        for fleet_id in copy.copy(self.data.myFleets):
            fleet = self.db.get(fleet_id, None)
            # minimal size of attack fleet is determined by size of originating system - larger
            # more developed systems will stage stronger attack fleets
            try:
                system = self.db[fleet.orbiting]
            except KeyError:
                # this fleet is not on orbit, set legacy value
                minimum = 12
            else:
                minimum = self._system_worthiness(system, [8,5,3,2]) + 10
            if getattr(fleet, 'target', Const.OID_NONE) == Const.OID_NONE and getattr(fleet, 'ships', []):
                # this also covers fleets fighting over enemy systems - in that case, there
                # is slight chance the fleet will continue to the next system without conquering
                # the system first
                if fleet.orbiting in self.data.enemySystems and Utils.weightedRandom([True, False], [9,1]):
                    continue
                if tool.fleetContains(fleet, {1:minimum, 4:minimum}):
                    attack_fleets.add(fleet_id)
        return attack_fleets

    def _attack_manager(self):
        for fleet_id in self._get_attack_fleets():
            fleet = self.db[fleet_id]
            # send the attack fleet, if in range
            sheet = tool.getFleetSheet(fleet)
            sowers = sheet[4]
            swarmers = min(sheet[1], math.ceil(sowers * 1.5))
            max_range = 0.8 * tool.subfleetMaxRange(self.client, self.db, {1:swarmers, 4:sowers}, fleet_id)
            # four nearest systems are considered, with probability to be chosen based on order
            nearest = tool.findNearest(self.db, fleet, self.data.enemySystems, max_range, 4)
            if len(nearest):
                # range is adjusted to flatten probabilities a bit
                probability_map = map(lambda x: x ** 2, range(2 + len(nearest), 2, -1))
                target = Utils.weightedRandom(nearest, probability_map)

                fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                    {1:swarmers, 4:sowers}, True,
                    fleet_id, Const.FLACTION_MOVE, target, None)

    def economy_manager(self):
        self._expansion_manager()
        self._system_manager()

    def offense_manager(self):
        self._ship_design_manager()
        self._logistics_manager()
        self._attack_manager()

    def run(self):
        self.diplomacy_manager(friendly_types=[Const.T_AIMUTPLAYER],
                               pacts=[Const.PACT_ALLOW_CIVILIAN_SHIPS, Const.PACT_ALLOW_MILITARY_SHIPS,
                                      Const.PACT_ALLOW_TANKING, Const.PACT_SHARE_SCANNER,
                                      Const.PACT_MINOR_SCI_COOP, Const.PACT_MAJOR_SCI_COOP,
                                      Const.PACT_MINOR_CP_COOP, Const.PACT_MAJOR_CP_COOP])
        top_prio_tech = [Rules.Tech.MUTANTBASE,
                         Rules.Tech.MUTANTBASE2,
                         Rules.Tech.MUTANTBASE3,
                         Rules.Tech.MUTANTBASE4,
                         Rules.Tech.MUTANTPP1,
                         Rules.Tech.MUTANTPP2,
                         Rules.Tech.MUTANTFACT1,
                         Rules.Tech.MUTANTFACT2,
                         Rules.Tech.MUTANTMINES,
                         Rules.Tech.FTLENG1,
                         ]
        mid_prio_tech = [Rules.Tech.SMALLHULL1,
                         Rules.Tech.SCOCKPIT1,
                         Rules.Tech.SCANNERMOD1,
                         Rules.Tech.CONBOMB1,
                         Rules.Tech.EMCANNON,
                         Rules.Tech.TORPEDO,
                         Rules.Tech.SSROCKET2,
                         Rules.Tech.STLENG1,
                         Rules.Tech.MUTANTPOD,
                         ]
        low_prio_tech = [Rules.Tech.CANNON1,
                         Rules.Tech.SSROCKET,
                         ]
        tech_prio = {10: top_prio_tech,
                     5: mid_prio_tech,
                     1: low_prio_tech,
                     }
        self.research_manager(tech_prio)
        self.economy_manager()
        self.offense_manager()

def run(aclient):
    ai = Mutant(aclient)
    ai.run()
    aclient.saveDB()


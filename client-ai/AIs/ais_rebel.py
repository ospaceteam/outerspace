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
from ige.ospace import Const
from ige.ospace import Rules
from ige.ospace import Utils
from ige.ospace import TechHandlers

import ai_tools as tool
from ai import AI

import copy, random, math

class Rebel(AI):
    def __init__(self, client):
        super(Rebel, self).__init__(client)
        tool.doRelevance(self.data, self.client, self.db, 10)
        self.designs = {}

    def offense_manager(self):
        # rebel is not suited for attacks, yet
        pass

    def _get_idle_planets(self, system):
        idle_planets = set()
        for planet_id in self.data.myProdPlanets & set(system.planets):
            planet = self.db[planet_id]
            if not getattr(planet, 'prodQueue', None):
                idle_planets.add(planet_id)
                continue
        return idle_planets

    def _fill_planets(self, system, idle_planets):
        system_stats = tool.getSystemStructStats(self.data, self.client, self.db, system.oid)
        for planet_id in copy.copy(idle_planets):
            planet = self.db[planet_id]
            prod_tech_id = Rules.Tech.RESCENTRE1 if planet.plMin < 100 else Rules.Tech.FACTORY1
            prod_tech = self.client.getFullTechInfo(prod_tech_id)
            # now we ignore all already build structures, and try to satisfy
            # outpost/fact or outpost/labs ration [on free slots]
            if planet.plSlots > len(planet.slots):
                if system_stats.en > prod_tech.operEn and system_stats.bio > prod_tech.operWorkers / 100:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                        prod_tech.id, 1, planet_id, prod_tech.id < 1000, 0, Const.OID_NONE)
                    idle_planets.remove(planet_id)
                else:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                        Rules.Tech.OUTPOST1, 1, planet_id, Rules.Tech.OUTPOST1 < 1000, 0, Const.OID_NONE)
                    idle_planets.remove(planet_id)

    def _colonize_planets(self, system, idle_planets):
        toColonize = self.data.freePlanets & set(system.planets)
        # colonize remaining planets
        for planet_id in copy.copy(idle_planets):
            planet = self.db[planet_id]
            if toColonize:
                targetID = toColonize.pop()
                target = self.db[targetID]
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    Rules.Tech.OUTPOST1, 1,
                    targetID, Rules.Tech.OUTPOST1 < 1000, 0, Const.OID_NONE)
                idle_planets.remove(planet_id)

    def _build_ships(self, system, idle_planets):
        for planet_id in copy.copy(idle_planets):
            planet = self.db[planet_id]
            systemFleets = getattr(system, 'fleets', [])
            has_colony = False
            has_scouts = False
            shared_system = len(set(system.planets) & self.data.otherPlanets) > 0
            for fleetID in systemFleets:
                fleet = self.db[fleetID]
                if getattr(fleet, 'owner', Const.OID_NONE) == self.player.oid:
                    has_colony |= tool.fleetContains(fleet, {self.designs["colony"]:1})
                    has_scouts |= tool.fleetContains(fleet, {self.designs["scout"]:1})
            if not has_colony:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    self.designs["colony"], 1, planet_id, self.designs["colony"] < 1000, 0, Const.OID_NONE)
            elif not has_scouts:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    self.designs["scout"], 1, planet_id, self.designs["scout"] < 1000, 0, Const.OID_NONE)
            elif Rules.Tech.UPGRADESHIPS in self.player.techs and self.player.fleetUpgradePool < 2000:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    Rules.Tech.UPGRADESHIPS, 1, planet_id, Rules.Tech.UPGRADESHIPS < 1000, 0, Const.OID_NONE)

            elif not shared_system:
                # build fighters
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    self.designs["fighter"], 1, planet_id, self.designs["fighter"] < 1000, 0, Const.OID_NONE)

    def _planet_manager(self):
        for planet_id in self.data.myPlanets:
            tool.sortStructures(self.client, self.db, planet_id)
        for system_id in self.data.mySystems:
            system = self.db[system_id]
            idle_planets = self._get_idle_planets(system)
            # build production buildings if nothing is needed, or outposts
            self._fill_planets(system, idle_planets)
            self._colonize_planets(system, idle_planets)
            self._build_ships(system, idle_planets)

    def _place_gov_center(self, candidate_planets):
        PLACEHOLDERS = (Rules.Tech.RESCENTRE1, Rules.Tech.FACTORY1)
        for planet_id in candidate_planets:
            planet = self.db[planet_id]
            if planet.prodProd == 0:
                continue
            gov_placeholder = None
            for struct in [x for x in planet.slots if x[0] in PLACEHOLDERS]:
                if gov_placeholder is not None:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                        Rules.Tech.GOVCENTER1, 1, planet_id, Rules.Tech.GOVCENTER1 < 1000, 0, gov_placeholder)
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                        Rules.Tech.OUTPOST1, 1, planet_id, Rules.Tech.OUTPOST1 < 1000, 0, struct[0])
                    return
                gov_placeholder = struct[0]

    def _cancel_gov_tasks(self, planet_ids):
        # cancel all tasks
        for planet_id in planet_ids:
            planet = self.db[planet_id]
            indexes = []
            i = 0
            for task in planet.prodQueue:
                if task.techID in set([1000, 3010, 3011]):
                    indexes.append(i)
                i += 1
            indexes.reverse()
            for index in indexes:
                self.client.cmdProxy.abortConstruction(planet_id, index)

    def _get_current_gov(self):
        gov_position = Const.OID_NONE
        gov_productions = []
        for planet_id in self.data.myPlanets:
            # find build gov center
            planet = self.db[planet_id]
            for struct in planet.slots:
                if struct[0] in set([1000, 3010, 3011]):
                    gov_position = planet_id
                    break
            for task in getattr(planet, 'prodQueue', []):
                if task.techID in set([1000, 3010, 3011]):
                    gov_productions.append(planet_id)
                    break
        return gov_position, gov_productions

    def _empire_manager(self):
        if not Rules.Tech.GOVCENTER1 in self.player.techs.keys():
            return
        candidates = tool.findPopCenterPlanets(self.db, self.data.myPlanets)
        candidate_planets = candidates[:10]
        gov_position, gov_productions = self._get_current_gov()
        if not set(candidate_planets) & (set([gov_position]) | set(gov_productions)):
            self._cancel_gov_tasks(gov_productions)
            self._place_gov_center(candidate_planets)
        return

    def _expansion_manager(self):
        should_repeat = True
        pirate_influenced_systems = tool.findInfluence(self.data, self.client, self.db, Rules.pirateInfluenceRange, self.data.pirateSystems)
        while should_repeat:
            should_repeat = False
            should_repeat |= self._explore(self.designs["scout"])
            safe_systems = (self.data.freeSystems & self.data.relevantSystems) - pirate_influenced_systems
            should_repeat |= self._colonize_free_systems(safe_systems, self.designs["colony"])

    def _identify_basic_designs(self):
        for desID in self.player.shipDesigns:
            design = self.player.shipDesigns[desID]
            if design.name == 'Scout':
                self.designs["scout"] = desID
            elif design.name == 'Fighter':
                self.designs["fighter"] = desID
            elif design.name == 'Bomber':
                self.designs["bomber"] = desID
            elif design.name == 'Colony Ship':
                self.designs["colony"] = desID

    def _identify_advanced_designs(self):
        for desID in self.player.shipDesigns:
            design = self.player.shipDesigns[desID]
            if design.name == 'Fighter 2':
                self.designs["fighter0"] = self.designs["fighter"]
                self.designs["fighter"] = desID
            elif design.name == 'Bomber 2':
                self.designs["bomber0"] = self.designs["bomber"]
                self.designs["bomber"] = desID
            elif design.name == 'Colony Ship 2':
                self.designs["colony0"] = self.designs["colony"]
                self.designs["colony"] = desID

    def _add_design(self, name, hull_id, equip):
        self.player.shipDesigns, index = self.client.cmdProxy.addShipDesign(self.player.oid, name, hull_id, equip)
        return index

    def _create_basic_designs(self):
        if "scout" not in self.designs:
            self.designs["scout"] = self._add_design('Scout',
                    Rules.Tech.SMALLHULL0, {Rules.Tech.SCOCKPIT0:1,
                    Rules.Tech.SCANNERMOD0:1, Rules.Tech.FTLENG0:3})
        if "fighter" not in self.designs:
            self.designs["fighter"] = self._add_design('Fighter',
                    Rules.Tech.SMALLHULL0, {Rules.Tech.SCOCKPIT0:1,
                    Rules.Tech.CANNON0:2, Rules.Tech.FTLENG0:3})
        if "bomber" not in self.designs:
            self.designs["bomber"] = self._add_design('Bomber',
                    Rules.Tech.SMALLHULL0, {Rules.Tech.SCOCKPIT0:1,
                    Rules.Tech.CONBOMB0:1, Rules.Tech.FTLENG0:3})
        if "colony" not in self.designs:
            self.designs["colony"] = self._add_design('Colony Ship',
                    Rules.Tech.MEDIUMHULL0, {Rules.Tech.SCOCKPIT0:1,
                    Rules.Tech.COLONYMOD0:1, Rules.Tech.FTLENG0:5})

    def _create_advanced_designs(self):
        needed_tech = set([Rules.Tech.SMALLHULL1, Rules.Tech.SCOCKPIT1, Rules.Tech.CANNON1, Rules.Tech.FTLENG1])
        if needed_tech.issubset(self.player.techs) and "fighter0" not in self.designs:
            self.designs["fighter0"] = self.designs["fighter"]
            self.designs["fighter"] = self._add_design('Fighter 2',
                    Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                    Rules.Tech.CANNON1:2, Rules.Tech.FTLENG1:3})
        needed_tech = set([Rules.Tech.SMALLHULL1, Rules.Tech.SCOCKPIT1, Rules.Tech.CONBOMB1, Rules.Tech.FTLENG1])
        if needed_tech.issubset(self.player.techs) and "bomber0" not in self.designs:
            self.designs["bomber0"] = self.designs["bomber"]
            self.designs["bomber"] = self._add_design('Bomber 2',
                    Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                    Rules.Tech.CONBOMB1:1, Rules.Tech.FTLENG1:3})
        needed_tech = set([Rules.Tech.MEDIUMHULL0, Rules.Tech.SCOCKPIT1, Rules.Tech.COLONYMOD0, Rules.Tech.FTLENG1])
        if needed_tech.issubset(self.player.techs) and "colony0" not in self.designs:
            self.designs["colony0"] = self.designs["colony"]
            self.designs["colony"] = self._add_design('Colony Ship 2',
                    Rules.Tech.MEDIUMHULL0, {Rules.Tech.SCOCKPIT1:1,
                    Rules.Tech.COLONYMOD0:1, Rules.Tech.FTLENG1:5})

    def _upgrade_obsolete_design(self, old_code_name, new_code_name):
        if old_code_name in self.designs:
            old_design_id = self.designs[old_code_name]
            new_design_id = self.designs[new_code_name]
            old_design = self.player.shipDesigns[old_design_id]
            if not old_design.upgradeTo:
                self.player.shipDesigns, self.player.stratRes, tasksUpgraded, self.player.prodQueues = \
                        self.client.cmdProxy.upgradeShipDesign(self.player.oid, old_design_id, new_design_id)

    def _get_service_centers(self):
        service_centers = []
        for planet in [self.db[planetID] for planetID in self.data.myPlanets]:
            # assumption: if it repairs, it also upgrades
            if not planet.repairShip: continue
            service_centers.append(planet.compOf)
        return service_centers

    def _get_outdated_fleets(self, obsolete_designs):
        outdated_fleets = []
        for fleet in [self.db[fleetID] for fleetID in self.data.idleFleets]:
            if set(obsolete_designs).intersection([ship[0] for ship in fleet.ships]):
                outdated_fleets.append(fleet)
        return outdated_fleets

    def _recall_to_upgrade(self, service_centers, outdated_fleets, obsolete_designs):
        for fleet in outdated_fleets:
            if fleet.orbiting in service_centers: continue
            subfleet_sheet = {}.fromkeys(obsolete_designs, 0)
            max_range = tool.subfleetMaxRange(self.client, self.db, subfleet_sheet, fleet.oid)
            nearest = tool.findNearest(self.db, fleet, service_centers, max_range)
            if not nearest: continue
            nearest_service = nearest[0]
            fleet, new_fleet, my_fleets = tool.orderPartFleet(self.client, self.db,
                subfleet_sheet, True, fleet.oid, Const.FLACTION_MOVE, nearest_service, None)

    def _upgrade_manager(self):
        UPGRADABLE = ["fighter", "bomber", "colony"]
        OBSOL_FUNC = lambda x: x + "0"
        obsoleted = set(map(OBSOL_FUNC, UPGRADABLE)).intersection(self.designs)
        obsolete_designs = [self.designs[obsol] for obsol in obsoleted]
        if not obsolete_designs: return

        service_centers = self._get_service_centers()
        outdated_fleets = self._get_outdated_fleets(obsolete_designs)
        self._recall_to_upgrade(service_centers, outdated_fleets, obsolete_designs)
        for code_name in UPGRADABLE:
            self._upgrade_obsolete_design(OBSOL_FUNC(code_name), code_name)

    def _ship_design_manager(self):
        self._identify_basic_designs()
        self._identify_advanced_designs()
        self._create_basic_designs()
        self._create_advanced_designs()

    def _help_system(self):
        tool.doDanger(self.data, self.client, self.db)
        pirate_influenced_systems = tool.findInfluence(self.data, self.client, self.db, Rules.pirateInfluenceRange, self.data.pirateSystems)
        one_fighter_mp = self.player.shipDesigns[self.designs["fighter"]].combatPwr
        for system_id in set(self.data.endangeredSystems) - set(pirate_influenced_systems):
            mil_pwr, shipQuantity = self.data.endangeredSystems[system_id]
            mil_pwr = -mil_pwr
            if system_id in self.data.myMPPerSystem:
                mil_pwr += self.data.myMPPerSystem[system_id]
            if mil_pwr < 0:
                system = self.db[system_id]
                nearest = tool.findNearest(self.db, system, self.data.mySystems, 99999, 20)[1:]
                for temp_id in nearest:
                    if temp_id in self.data.myMPPerSystem:
                        temp_mp = self.data.myMPPerSystem[temp_id]
                    else:
                        temp_mp = 0
                        self.data.myMPPerSystem[temp_id] = 0
                    if temp_id in self.data.endangeredSystems:
                        a, b = self.data.endangeredSystems[temp_id]
                        temp_mp -= a * 1.5
                        if temp_mp <= 0: continue
                    orig = temp_mp = min(-mil_pwr, temp_mp) * 1.25
                    # this is just prototype, working only with Fighters
                    quantity = int(math.ceil(temp_mp / float(one_fighter_mp)))
                    if quantity == 0:
                        continue
                    ships_left, mil_pwrSend = tool.orderFromSystem(self.data, self.client, self.db,
                        {self.designs["fighter"]:quantity}, temp_id, Const.FLACTION_MOVE, system_id, None)
                    mil_pwr += mil_pwrSend
                    self.data.myMPPerSystem[temp_id] -= mil_pwrSend
                    if mil_pwr > 0: break

    def _return_strays(self):
        for fleetID in self.data.idleFleets:
            fleet = self.db[fleetID]
            # fleets orbiting in systems not belonging to the self.player
            if fleet.orbiting and fleet.orbiting not in self.data.mySystems:
                nearest = tool.findNearest(self.db, fleet, self.data.mySystems, 99999, 1)
                if len(nearest):
                    targetID = nearest[0]
                    tool.orderFleet(self.client, self.db, fleetID, Const.FLACTION_MOVE, targetID, None)

    def defense_manager(self):
        self._help_system()
        self._return_strays()

    def economy_manager(self):
        self._empire_manager()
        self._planet_manager()
        self._expansion_manager()
        self._upgrade_manager()

    def run(self):
        self._ship_design_manager() # this fills self.designs, needs to go first
        top_prio_tech = [Rules.Tech.OUTPOST1,
                         Rules.Tech.GOVCENTER1,
                         Rules.Tech.FACTORY1,
                         Rules.Tech.RESCENTRE1,
                         Rules.Tech.FTLENG1,
                         ]
        mid_prio_tech = [Rules.Tech.SMALLHULL1,
                         Rules.Tech.SCOCKPIT1,
                         Rules.Tech.CANNON1,
                         Rules.Tech.UPGRADESHIPS,
                         ]
        low_prio_tech = [Rules.Tech.PWRPLANTOIL1,
                         Rules.Tech.FARM1,
                         Rules.Tech.COMSCAN1,
                         Rules.Tech.PWRPLANTSOL1,
                         Rules.Tech.SPACEPORT,
                         Rules.Tech.SCANNERMOD1,
                         Rules.Tech.SCANNERMOD2,
                         Rules.Tech.CONBOMB1,
                         Rules.Tech.HOLIDAYS1,
                         Rules.Tech.DEEPSPACESCAN,
                         ]
        ignored_tech = [Rules.Tech.BIONICTL2,
                        Rules.Tech.HUMANTL2,
                        Rules.Tech.ROBOTTL2,
                        ]
        tech_prio = {10: top_prio_tech,
                     3: mid_prio_tech,
                     1: low_prio_tech,
                     0: ignored_tech}
        self.research_manager(tech_prio)
        self.diplomacy_manager(friendly_types=[Const.T_PLAYER, Const.T_AIPLAYER, Const.T_AIRENPLAYER],
                               pacts=[Const.PACT_ALLOW_CIVILIAN_SHIPS, Const.PACT_ALLOW_TANKING,
                                      Const.PACT_MINOR_SCI_COOP, Const.PACT_MAJOR_SCI_COOP,
                                      Const.PACT_MINOR_CP_COOP, Const.PACT_MAJOR_CP_COOP])
        self.economy_manager()
        self.defense_manager()
        self.offense_manager()


def run(aclient):
    ai = Rebel(aclient)
    ai.run()
    aclient.saveDB()


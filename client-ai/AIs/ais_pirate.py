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
from ige.IDataHolder import IDataHolder

import ai_tools as tool
from ai import AI

class Pirate(AI):
    def __init__(self, client):
        enemy_types = [Const.T_PLAYER, Const.T_AIPLAYER, Const.T_AIRENPLAYER, Const.T_AIMUTPLAYER]
        super(Pirate, self).__init__(client, enemy_types)
        tool.doRelevance(self.data, self.client, self.db, Rules.pirateInfluenceRange)

    def _fill_with_dens(self, system_info):
        for planet_id in copy.copy(system_info.idle_planets):
            planet = self.db[planet_id]
            if planet.plSlots > len(planet.slots):
                log.debug(self.player.oid, "PIRATEAI - building pirate den", planet.oid)
                dens_to_build = planet.plSlots - len(planet.slots)
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                    Rules.Tech.PIRATEDEN, dens_to_build,
                    planet.oid, Rules.Tech.PIRATEDEN < 1000, 0, Const.OID_NONE)
                system_info.idle_planets.remove(planet_id)
                system_info.dens[planet_id] += dens_to_build
                continue

    def _build_defensive_bases(self, system_info):
        for planet_id in copy.copy(system_info.idle_planets):
            planet = self.db[planet_id]
            if system_info.bases[planet_id] < 2 and planet.plSlots >= 2:
                dens_sum = sum(system_info.dens.values())
                # build on the other structure [something nonpiratish :)] or
                # pirate den
                if system_info.other_struct_id[planet_id]:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                        Rules.Tech.PIRATEBASE, 1, planet.oid, Rules.Tech.PIRATEBASE < 1000,
                        0, system_info.other_struct_id[planet_id])
                    system_info.idle_planets.remove(planet_id)
                    return
                elif dens_sum:
                    bases_to_build = min(dens_sum, 2 - system_info.bases[planet_id])
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                        Rules.Tech.PIRATEBASE, bases_to_build,
                        planet.oid, Rules.Tech.PIRATEBASE < 1000, 0,
                        Rules.Tech.PIRATEDEN)
                    system_info.idle_planets.remove(planet_id)
                    system_info.dens[planet_id] -= bases_to_build
                    return

    def _build_bases(self, system_info):
        to_colonize = self.data.freePlanets & set(system_info.system.planets)
        for planet_id in copy.copy(system_info.idle_planets):
            planet = self.db[planet_id]
            for target_id in to_colonize:
                target = self.db[target_id]
                if target.owner == self.player.oid:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                        Rules.Tech.PIRATEDEN, 1,
                        target_id, Rules.Tech.PIRATEDEN < 1000, 0, Const.OID_NONE)
                    system_info.idle_planets.remove(planet_id)
                    system_info.dens[target_id] = 1
                    break
                else:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                        Rules.Tech.PIRATEBASE, 1,
                        target_id, Rules.Tech.PIRATEBASE < 1000, 0, Const.OID_NONE)
                    system_info.idle_planets.remove(planet_id)
                    break

    def _build_brewery(self, system_info):
        for planet_id in copy.copy(system_info.idle_planets) & set(system_info.dens.keys()):
            planet = self.db[planet_id]
            if system_info.dens[planet_id] < 1:
                # there was den, but it is not anymore, try another planet
                continue
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                Rules.Tech.PIRATEBREWERY, 1, planet_id,
                Rules.Tech.PIRATEBASE < 1000, 0, Rules.Tech.PIRATEDEN)
            system_info.idle_planets.remove(planet_id)
            system_info.dens[planet_id] -= 1
            system_info.breweries += 1
            return

    def _build_prisons(self, system_info):
        sumOfDens = sum(system_info.dens.values())
        denTech = Rules.techs[Rules.Tech.PIRATEDEN]
        prisonTech = Rules.techs[Rules.Tech.PIRATEPRISON]
        energy = sumOfDens * denTech.prodEn * 1.25 - system_info.prisons * prisonTech.operEn
        possiblePrisons = math.floor(energy / (denTech.prodEn * 1.25 + prisonTech.operEn))
        for planet_id in copy.copy(system_info.idle_planets) & set(system_info.dens.keys()):
            planet = self.db[planet_id]
            if system_info.dens[planet_id] < 1 or possiblePrisons < 1:
                # there was a Den, but it is not there anymore, try another planet
                continue
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                Rules.Tech.PIRATEPRISON, 1, planet_id,
                Rules.Tech.PIRATEBASE < 1000, 0, Rules.Tech.PIRATEDEN)
            system_info.idle_planets.remove(planet_id)
            system_info.dens[planet_id] -= 1
            possiblePrisons -= 1

    def _build_shipyard(self, system_info):
        slots = 0
        for planet_id in system_info.system.planets:
            slots += self.db[planet_id].plSlots
        if slots <= 10 or system_info.shipyards:
            return
        for planet_id in copy.copy(system_info.idle_planets) & set(system_info.dens.keys()):
            planet = self.db[planet_id]
            if system_info.dens[planet_id] < 1:
                # there was a Den, but it is not there anymore, try another planet
                continue
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                Rules.Tech.PIRATESD, 1, planet_id,
                Rules.Tech.PIRATEBASE < 1000, 0, Rules.Tech.PIRATEDEN)
            system_info.idle_planets.remove(planet_id)
            system_info.dens[planet_id] -= 1
            system_info.shipyards = 1
            return

    def _expand_slots(self, system_info):
        if Rules.Tech.ADDSLOT3 not in self.player.techs:
            return
        for planet_id in copy.copy(system_info.idle_planets):
            planet = self.db[planet_id]
            if planet.plSlots < planet.plMaxSlots:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    Rules.Tech.ADDSLOT3, 1, planet_id,
                    Rules.Tech.ADDSLOT3 < 1000, 0, Const.OID_NONE)
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id,
                    Rules.Tech.PIRATEDEN, 1, planet_id,
                    Rules.Tech.PIRATEDEN < 1000, 0, Const.OID_NONE)
                system_info.idle_planets.remove(planet_id)

    def _condensePlanet(self, planet, target):
        if Rules.Tech.PLCOND5 in self.player.techs:
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                Rules.Tech.PLCOND5, 1, target.oid,
                Rules.Tech.PLCOND5 < 1000, 0, Const.OID_NONE)
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                Rules.Tech.PIRATEBASE, 1, target.oid,
                Rules.Tech.PIRATEBASE < 1000, 0, Const.OID_NONE)
            self.data.nonhabPlanets.remove(target.oid)

    def _assemblePlanet(self, planet, target):
        if Rules.Tech.PLASSEMBL5 in self.player.techs:
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                Rules.Tech.PLASSEMBL5, 1, target.oid,
                Rules.Tech.PLASSEMBL5 < 1000, 0, Const.OID_NONE)
            planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet.oid,
                Rules.Tech.PIRATEBASE, 1, target.oid,
                Rules.Tech.PIRATEBASE < 1000, 0, Const.OID_NONE)
            self.data.nonhabPlanets.remove(target.oid)

    def _create_planets(self, system_info):
        for target_id in copy.copy(self.data.nonhabPlanets & set(system_info.system.planets)):
            target = self.db[target_id]
            try:
                planet_id = system_info.idle_planets.pop()
            except KeyError:
                return
            planet = self.db[planet_id]
            if target.plType == u'G':
                self._condensePlanet(planet, target)
            elif target.plType == u'A':
                self._assemblePlanet(planet, target)

    def _build_ships(self, system_info):
        system_fleets = getattr(system_info.system, 'fleets', [])
        has_scout = False
        for fleet_id in system_fleets:
            fleet = self.db[fleet_id]
            if getattr(fleet, 'owner', Const.OID_NONE) == self.player.oid:
                if tool.fleetContains(fleet, {4:1}):
                    has_scout = True
        for planet_id in system_info.idle_planets:
            planet = self.db[planet_id]
            if not has_scout:
                planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, 4, 1, planet_id, True, False, Const.OID_NONE)
            else:
                dice = random.randint(1, 3)
                if dice == 1:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, 1, 3, planet_id, True, False, Const.OID_NONE)
                elif dice == 2:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, 2, 3, planet_id, True, False, Const.OID_NONE)
                else:
                    planet.prodQueue, self.player.stratRes = self.client.cmdProxy.startConstruction(planet_id, 3, 2, planet_id, True, False, Const.OID_NONE)

    def _get_system_info(self, system):
        system_info = IDataHolder()
        # my planets in the system
        system_info.system = system
        system_info.breweries = 0
        system_info.shipyards = 0
        system_info.prisons = 0
        system_info.dens = {}
        system_info.bases = {}
        system_info.other_struct_id = {}
        system_info.idle_planets = self.data.myPlanets & set(system.planets)
        for planet_id in copy.copy(system_info.idle_planets):
            planet = self.db[planet_id]
            system_info.bases[planet_id] = 0
            system_info.other_struct_id[planet_id] = None
            system_info.dens[planet_id] = 0
            for struct in planet.slots:
                if struct[0] == Rules.Tech.PIRATEBASE:
                    system_info.bases[planet_id] += 1
                elif struct[0] == Rules.Tech.PIRATEBREWERY:
                    system_info.breweries += 1
                elif struct[0] == Rules.Tech.PIRATEDEN:
                    system_info.dens[planet_id] += 1
                elif struct[0] == Rules.Tech.PIRATESD:
                    system_info.shipyards += 1
                elif struct[0] == Rules.Tech.PIRATEPRISON:
                    system_info.prisons += 1
                else:
                    system_info.other_struct_id[planet_id] = struct[0]
            if getattr(planet, 'prodQueue', None):
                # something is in the production queue, account it and do next
                for task in planet.prodQueue:
                    if task.techID == Rules.Tech.PIRATEBREWERY:
                        system_info.breweries += task.quantity
                    elif task.techID == Rules.Tech.PIRATESD:
                        system_info.shipyards += task.quantity
                    elif task.techID == Rules.Tech.PIRATEPRISON:
                        system_info.prisons += task.quantity
                    elif task.techID in (Rules.Tech.PLCOND5, Rules.Tech.PLASSEMBL5):
                        self.data.nonhabPlanets.remove(task.targetID)
                system_info.idle_planets.remove(planet_id)
                continue
        return system_info

    def _retreat_fleet(self, fleet):
        max_range = tool.subfleetMaxRange(self.client, self.db, None, fleet.oid)
        nearest_sys_ids = tool.findNearest(self.db, fleet, self.data.mySystems)
        if len(nearest_sys_ids):
            nearest_sys_id = nearest_sys_ids[0]
            target = self.db[nearest_sys_id]
            distance = math.hypot(target.x-fleet.x, target.y-fleet.y)
            if distance >= max_range:
                tool.orderFleet(self.client, self.db, fleet.oid, Const.FLACTION_MOVE, nearest_sys_id, None)

    def _return_fleet(self, fleet):
        nearest_sys_ids = tool.findNearest(self.db, fleet, self.data.mySystems)
        if len(nearest_sys_ids):
            nearest_sys_id = nearest_sys_ids[0]
            tool.orderFleet(self.client, self.db, fleet.oid, Const.FLACTION_MOVE, nearest_sys_id, None)

    def _commence_attack(self, fleet):
        sheet = tool.getFleetSheet(fleet)
        ships = {}
        ships[3] = min(sheet[1], sheet[2], sheet[3])
        ships[1] = ships[2] = ships[3]
        ships[4] = 1
        max_range = tool.subfleetMaxRange(self.client, self.db, ships, fleet.oid)
        nearest_sys_ids = tool.findNearest(self.db, fleet, self.data.enemySystems & self.data.relevantSystems, max_range * 0.45)
        if len(nearest_sys_ids):
            nearestSys = nearest_sys_ids[0]
            tool.orderPartFleet(self.client, self.db, ships, False, fleet.oid, Const.FLACTION_MOVE, nearestSys, None)

    def _followup_attack(self, fleet):
        max_range = tool.subfleetMaxRange(self.client, self.db, None, fleet.oid)
        nearest_sys_ids = tool.findNearest(self.db, fleet, self.data.enemySystems & self.data.relevantSystems, max_range)
        if len(nearest_sys_ids):
            nearest_sys_id = nearest_sys_ids[0]
            tool.orderFleet(self.client, self.db, fleet.oid, Const.FLACTION_MOVE, nearest_sys_id, None)
        else:
            self._return_fleet(fleet)

    def fleets_manager(self):
        attack_fleets = set()
        attack_minimum = {1:10, 2:10, 3:10, 4:1}
        for fleet_id in self.data.myFleets & self.data.idleFleets:
            fleet = self.db.get(fleet_id, None)
            if fleet.combatCounter and fleet.orbiting not in self.data.mySystems:
                self._retreat_fleet(fleet)
            elif not fleet.orbiting in self.data.mySystems:
                if tool.fleetContains(fleet, attack_minimum):
                    attack_fleets.add(fleet)
                else:
                    self._return_fleet(fleet)
            else:
                if tool.fleetContains(fleet, attack_minimum):
                    attack_fleets.add(fleet)
        for fleet in attack_fleets:
            if fleet.orbiting in self.data.mySystems:
                self._commence_attack(fleet)
            else:
                self._followup_attack(fleet)

    def planet_manager(self):
        for planet_id in self.data.myPlanets:
            tool.sortStructures(self.client, self.db, planet_id)
        for systemID in self.data.mySystems:
            system = self.db[systemID]
            system_info = self._get_system_info(system)
            self._fill_with_dens(system_info)
            self._build_defensive_bases(system_info)
            self._build_bases(system_info)
            self._build_brewery(system_info)
            self._build_prisons(system_info)
            self._build_shipyard(system_info)
            self._expand_slots(system_info)
            self._create_planets(system_info)
            self._build_ships(system_info)

    def ship_design_manager(self):
        if len(self.player.shipDesigns.keys()) < 4:
            self.client.cmdProxy.addShipDesign(self.player.oid, 'Brawler',
                    Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                    Rules.Tech.CANNON1:2, Rules.Tech.PIRATEFTLENG:3})
            self.client.cmdProxy.addShipDesign(self.player.oid, "Enforcer",
                    Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                    Rules.Tech.SSROCKET2:2, Rules.Tech.PIRATEFTLENG:3})
            self.client.cmdProxy.addShipDesign(self.player.oid, "Raider",
                     Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                     Rules.Tech.CONBOMB1:1, Rules.Tech.PIRATEFTLENG:3})
            self.client.cmdProxy.addShipDesign(self.player.oid, "Squeal",
                    Rules.Tech.SMALLHULL1, {Rules.Tech.SCOCKPIT1:1,
                    Rules.Tech.SCANNERMOD1:1, Rules.Tech.PIRATEFTLENG:3})

    def offense_manager(self):
        self.ship_design_manager()
        self.fleets_manager()

    def economy_manager(self):
        self.planet_manager()

    def run(self):
        self.offense_manager()
        self.economy_manager()

def run(aclient):
    ai = Pirate(aclient)
    ai.run()
    aclient.saveDB()






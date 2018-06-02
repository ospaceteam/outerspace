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

import os
import time

import data
import ige
import log

from ige import GameException
from ige.Transaction import Transaction
from ige.IDataHolder import IDataHolder
from ige.ospace.GalaxyGenerator import GalaxyGenerator
import ige.ospace.Const as Const

class BookingMngrException(Exception):
    pass

class Booking(object):
    def __init__(self):
        self.booked_players = set([])
        self.last_creation = None
        self.capacity = None

    def toggle_booking(self, player, threshold):
        try:
            self.booked_players.remove(player)
        except KeyError:
            self.booked_players.add(player)
        return self.is_filled(threshold)

    def discard_booking(self, player):
        self.booked_players.discard(player)

    def is_filled(self, threshold):
        return len(self.booked_players) >= self.capacity * min(1.0, threshold)

    def answer(self, player):
        answer = IDataHolder()
        answer.bookings = len(self.booked_players)
        answer.last_creation = self.last_creation
        answer.is_booked = player in self.booked_players
        return answer

class BookingMngr(object):
    def __init__(self, clientMngr, gameMngr, database, threshold):
        self.clientMngr = clientMngr
        self.gameMngr = gameMngr
        self.database = database
        self.threshold = threshold
        self.offerings = GalaxyGenerator().templates
        self.init_bookings()

    def init_bookings(self):
        for gal_type in self.offerings:
            if not self.database.has_key(gal_type):
                self.database.create(Booking(), gal_type)
            if self.offerings[gal_type].scenario == Const.SCENARIO_SINGLE:
                # hardcoded 1, as some galaxies has rebels in them
                self.database[gal_type].capacity = 1
            else:
                self.database[gal_type].capacity = self.offerings[gal_type].players
        # cleanup of those not used anymore
        for gal_type in self.database.keys():
            if gal_type not in self.offerings:
                del self.database[gal_type]

    def shutdown(self):
        log.message('Shutdown')
        self.database.shutdown()

    def checkpoint(self):
        self.database.checkpoint()

    def clear(self):
        self.database.clear()

    def backup(self, basename):
        self.database.backup(basename)

    def upgrade(self):
        return

    def _get_challenges(self, template):
        challenges = []
        if template.scenario == Const.SCENARIO_SINGLE and template.players > 1:
            challenges.append(Const.T_AIPLAYER)
        if set([Const.SR_TL1A, Const.SR_TL1B]).intersection(template.resources):
            challenges.append(Const.T_AIRENPLAYER)
        if set([Const.DISEASE_MUTANT]).intersection(template.diseases):
            challenges.append(Const.T_AIMUTPLAYER)
        if set([Const.SR_TL3A, Const.SR_TL3B, Const.SR_TL3C]).intersection(template.resources):
            challenges.append(Const.T_AIPIRPLAYER)
        if set([Const.SR_TL5A, Const.SR_TL5B, Const.SR_TL5C]).intersection(template.resources):
            challenges.append(Const.T_AIEDENPLAYER)
        return challenges

    def get_booking_offers(self, sid):
        hideSingle = self.gameMngr.singleGamesLimit(sid)
        answers = {}
        # TODO: filter single player for users with limit
        for gal_type, template in self.offerings.iteritems():
            if hideSingle and template.scenario == Const.SCENARIO_SINGLE:
                continue
            answer = IDataHolder()
            answer.scenario = template.scenario
            answer.minPlanets = template.minPlanets
            answer.maxPlanets = template.maxPlanets
            answer.radius = template.radius
            answer.players = template.players
            answer.resources = template.resources.keys()
            answer.challenges = self._get_challenges(template)

            if not template.startR[0] or not template.startR[1]:
                # that means grouping is used to maximize distance between players
                # most likely brawl scenario
                answer.playerGroup = 1
            else:
                answer.playerGroup = template.playerGroup

            answers[gal_type] = answer
        return answers, None

    def get_booking_answers(self, sid):
        offers = self.get_booking_offers(sid)[0].keys()
        player = self.clientMngr.getSession(sid).login
        answers = {}
        for key in self.database.keys():
            if key not in offers:
                # most likely single player limit reached
                continue
            answers[key] = self.database[key].answer(player)
        return answers, None

    def toggle_booking(self, sid, gal_type):
        # we have to check single player limit
        scenario = self.offerings[gal_type].scenario
        if scenario == Const.SCENARIO_SINGLE and self.gameMngr.singleGamesLimit(sid):
            # limit reached, no toggling allowed
            raise GameException('Limit of single player galaxies reached.')

        player = self.clientMngr.getSession(sid).login
        log.debug("Player '{0}' toggled booking of '{1}'".format(player, gal_type))
        triggered = False
        if self.database[gal_type].toggle_booking(player, self.threshold):
            self.trigger_galaxy_start(gal_type)
            triggered = True
        # get_booking_answers returns tuple, we only need first part
        answers = self.get_booking_answers(sid)[0]
        answers[None] = triggered
        return answers, None

    def trigger_galaxy_start(self, gal_type):
        log.debug("Triggering new subscribed galaxy '{0}'".format(gal_type))
        # triggers galaxy start regardless booking numbers
        booking = self.database[gal_type]

        players = list(booking.booked_players)

        # TODO: I don't know what I am doing, this seems to be a terrible hack
        universe = self.gameMngr.db[ige.Const.OID_UNIVERSE]
        tran = Transaction(self.gameMngr, ige.Const.OID_ADMIN)
        name = self._find_galaxy_name(gal_type, players)
        newGalaxyID = self.gameMngr.cmdPool[universe.type].createNewSubscribedGalaxy(tran, universe, name, gal_type, players)
        # update booking data
        booking.booked_players = set([])
        booking.last_creation = time.time()

        # for now, we need to remove bookings of player from other queues
        # TODO: remove after decoupling account and player objects
        for player in players:
            log.debug("Removing other bookings of player '{0}'".format(player))
            for key in self.database.keys():
                self.database[key].discard_booking(player)
        return newGalaxyID, None

    def _find_galaxy_name(self, gal_type, players):
        scenario = self.offerings[gal_type].scenario
        universe = self.gameMngr.db[ige.Const.OID_UNIVERSE]
        names_in_use = set([])
        # fetch list of used galaxy names
        for galaxy_id in universe.galaxies:
            galaxy = self.gameMngr.db[galaxy_id]
            names_in_use.add(galaxy.name)

        if scenario == Const.SCENARIO_SINGLE:
            player_name = players[0]
            name = "{0}-{1}-{2}".format(gal_type, player_name, universe.turn)
            if name not in names_in_use:
                return name
            iterator = 1
            while True:
                name = "{0}-{1}-{2}.{3}".format(gal_type, player_name, universe.turn, iterator)
                if name in names_in_use:
                    iterator += 1
                    continue
                # found new name!
                return name
        elif scenario in [Const.SCENARIO_COOP, Const.SCENARIO_BRAWL]:
            name = "{0}-{1}".format(gal_type, universe.turn)
            if name not in names_in_use:
                return name
            iterator = 1
            while True:
                name = "{0}-{1}.{2}".format(gal_type, universe.turn, iterator)
                if name in names_in_use:
                    iterator += 1
                    continue
                # found new name!
                return name
        # Outer Space has privilege of having traditional galaxy names
        log.debug("Searching for available galaxy name")
        all_names = []
        for name in open(data.GALAXY_NAMES_FILE):
            all_names.append(name.strip())

        for name in all_names:
            if name in names_in_use:
                continue
            return name
        # no name available
        return None


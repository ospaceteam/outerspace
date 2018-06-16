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
from ige.ospace import Const
from ige.ospace import Utils

from ige import GameException
from ige.Transaction import Transaction
from ige.IDataHolder import IDataHolder
from ige.ospace.GalaxyGenerator import GalaxyGenerator

class BookingMngrException(Exception):
    pass

class Booking(object):
    def __init__(self, gal_type):
        self.players = set([])
        self.gal_type = gal_type
        self.last_creation = None
        self.capacity = None
        self.owner = None
        self.pw_hash = None

    def toggle_booking(self, player):
        try:
            self.players.remove(player)
        except KeyError:
            self.players.add(player)
        return self.is_filled()

    def discard_booking(self, player):
        self.players.discard(player)

    def is_filled(self):
        return len(self.players) == self.capacity

    def answer(self, player):
        answer = IDataHolder()
        answer.bookings = len(self.players)
        answer.last_creation = self.last_creation
        answer.is_booked = player in self.players
        answer.owner = self.owner
        answer.gal_type = self.gal_type
        answer.capacity = self.capacity
        return answer

class BookingMngr(object):
    def __init__(self, clientMngr, gameMngr, db):
        self.clientMngr = clientMngr
        self.gameMngr = gameMngr
        self.db = db
        self.db.nextID = ige.Const.BID_FREESTART
        self.offerings = GalaxyGenerator().templates
        self.init_bookings()

    def init_bookings(self):
        for gal_type in self.offerings:
            bookings = self._get_type_bookings(gal_type)
            if not bookings:
                book = Booking(gal_type)
                self.db.create(book)
                bookings.append(book)
                if self.offerings[gal_type].scenario == Const.SCENARIO_SINGLE:
                    # hardcoded 1, as some galaxies has rebels in them
                    book.capacity = 1
                else:
                    book.capacity = self.offerings[gal_type].players

        # cleanup of those not used anymore
        for bookID in self.db.keys():
            gal_type = self.db[bookID].gal_type
            if gal_type not in self.offerings:
                del self.db[bookID]

    def shutdown(self):
        log.message('Shutdown')
        self.db.shutdown()

    def checkpoint(self):
        self.db.checkpoint()

    def clear(self):
        self.db.clear()

    def backup(self, basename):
        self.db.backup(basename)

    def upgrade(self):
        return

    def _get_type_bookings(self, gal_type):
        bookings = []
        for bookID in self.db.keys():
            book = self.db[bookID]
            if book.gal_type == gal_type:
                bookings.append(book)
        return bookings

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

    def _createAnswer(self, gal_type):
        template = self.offerings[gal_type]
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
        return answer

    def _is_valid_offer(self, sid, gal_type):
        hideSingle = self.gameMngr.singleGamesLimit(sid)
        template = self.offerings[gal_type]
        if gal_type == "Test":
            return False
        if hideSingle and template.scenario == Const.SCENARIO_SINGLE:
            return False
        return True

    def get_booking_offers(self, sid):
        answers = {}
        for gal_type in self.offerings:
            if not self._is_valid_offer(sid, gal_type):
                continue
            answers[gal_type] = self._createAnswer(gal_type)
        return answers, None

    def _get_booking_answers(self, sid):
        player = self.clientMngr.getSession(sid).login
        answers = {}
        for bookID in self.db.keys():
            book = self.db[bookID]
            if not self._is_valid_offer(sid, book.gal_type):
                continue
            answers[bookID] = book.answer(player)
        return answers

    def get_booking_answers(self, sid):
        return self._get_booking_answers(sid), None

    def toggle_booking(self, sid, bookID):
        book = self.db[bookID]
        template = self.offerings[book.gal_type]
        if not self._is_valid_offer(sid, book.gal_type):
            # limit reached, no toggling allowed
            raise GameException('Cannot toggle, limit of single player galaxies reached?')

        player = self.clientMngr.getSession(sid).login
        log.debug("Player '{0}' toggled booking of '{1}/{2}'".format(player, book.gal_type, book.owner))
        triggered = False
        if book.toggle_booking(player):
            self.trigger_galaxy_start(bookID)
            triggered = True
        # get_booking_answers returns tuple, we only need first part
        answers = self._get_booking_answers(sid)
        answers[ige.Const.BID_TRIGGERED] = triggered
        return answers, None

    def trigger_galaxy_start(self, bookID):
        book = self.db[bookID]
        log.debug("Triggering new subscribed galaxy '{0}'".format(book.gal_type))
        # triggers galaxy start regardless booking numbers

        # TODO: I don't know what I am doing, this seems to be a terrible hack
        universe = self.gameMngr.db[ige.Const.OID_UNIVERSE]
        tran = Transaction(self.gameMngr, ige.Const.OID_ADMIN)
        name = self._find_galaxy_name(book.gal_type, list(book.players))
        newGalaxyID = self.gameMngr.cmdPool[universe.type].createNewSubscribedGalaxy(tran, universe, name, book.gal_type, list(book.players))

        if book.owner:
            del self.db[bookID]
        else:
            book.players = set([])
            book.last_creation = time.time()

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


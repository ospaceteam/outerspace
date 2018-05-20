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

from ige.Transaction import Transaction
from ige.IDataHolder import IDataHolder
from ige.ospace.GalaxyGenerator import GalaxyGenerator

class BookingMngrException(Exception):
    pass

class Booking(object):
    def __init__(self):
        self.booked_players = set([])
        self.last_creation = None
        self.capacity = None
        self.info_text = None

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
        answer.info_text = self.info_text
        answer.capacity = self.capacity
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
        self.init_bookings()

    def init_bookings(self):
        gal_gen = GalaxyGenerator()
        gal_types = gal_gen.getGalaxyTypes()
        for gal_type in gal_types:
            if not self.database.has_key(gal_type):
                self.database.create(Booking(), gal_type)
            self.database[gal_type].capacity = gal_types[gal_type][0]
            self.database[gal_type].info_text = gal_types[gal_type][1]

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

    def get_booking_answers(self, sid):
        player = self.clientMngr.getSession(sid).login
        answers = {}
        for key in self.database.keys():
            answers[key] = self.database[key].answer(player)
        return answers, None

    def toggle_booking(self, sid, gal_type):
        player = self.clientMngr.getSession(sid).login
        log.debug("Player '{0}' toggled booking of '{1}'".format(player, gal_type))
        if self.database[gal_type].toggle_booking(player, self.threshold):
            self.trigger_galaxy_start(gal_type)
        return self.get_booking_answers(sid)

    def trigger_galaxy_start(self, gal_type):
        log.debug("Triggering new subscribed galaxy '{0}'".format(gal_type))
        # triggers galaxy start regardless booking numbers
        booking = self.database[gal_type]

        players = list(booking.booked_players)

        # TODO: I don't know what I am doing, this seems to be a terrible hack
        universe = self.gameMngr.db[ige.Const.OID_UNIVERSE]
        tran = Transaction(self.gameMngr, ige.Const.OID_ADMIN)
        name = self._find_galaxy_name()
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

    def _find_galaxy_name(self):
        log.debug("Searching for available galaxy name")
        all_names = []
        names_in_use = set([])
        for name in open(data.GALAXY_NAMES_FILE):
            all_names.append(name.strip())
        # fetch list of used galaxy names
        universe = self.gameMngr.db[ige.Const.OID_UNIVERSE]
        for galaxy_id in universe.galaxies:
            galaxy = self.gameMngr.db[galaxy_id]
            names_in_use.add(galaxy.name)
        
        for name in all_names:
            if name in names_in_use:
                continue
            return name
        # no name available
        return None
        

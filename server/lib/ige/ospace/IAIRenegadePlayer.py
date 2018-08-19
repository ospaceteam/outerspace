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
import time

import Const
import Rules
import ShipUtils
import Utils

from ige import log
from ige.IDataHolder import IDataHolder
from ige.IObject import public
from IPlayer import IPlayer

class IAIRenegadePlayer(IPlayer):

    typeID = Const.T_AIRENPLAYER
    forums = {"INBOX": 56, "OUTBOX": 56, "EVENTS": 0}

    def init(self, obj):
        IPlayer.init(self, obj)
        #
        obj.name = u'Renegade'
        obj.race = "r"
        obj.login = '*'

    def register(self, tran, obj, galaxyID):
        log.debug("Registering player", obj.oid)
        counter = 1
        while 1:
            obj.name = u'Renegade faction %d' % counter
            obj.login = '*AIP*renegade%d' % counter
            if galaxyID in tran.gameMngr.accountGalaxies(obj.login):
                counter += 1
                continue
            tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
            tran.db[Const.OID_UNIVERSE].players.append(obj.oid)
            tran.gameMngr.clientMngr.createAIAccount(obj.login, obj.name, 'ais_renegade')
            break
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

    @public(Const.AL_ADMIN)
    def processINITPhase(self, tran, obj, data):
        IPlayer.processINITPhase(self, tran, obj, data)

        obj.lastLogin = time.time()
        # delete itself if there are no fleets and planets
        # delete the account as well
        # unregister it from the AI system
        if not obj.fleets and not obj.planets:
            self.cmd(obj).delete(tran, obj)

    def update(self, tran, obj):
        self.setStartingTechnologies(obj)
        self.setStartingShipDesigns(obj)
        IPlayer.update(self, tran, obj)

    @staticmethod
    def setStartingPlanet(tran, planet):
        planet.plSlots = max(planet.plSlots, 9)
        planet.plMaxSlots = max(planet.plMaxSlots, 9)
        planet.plDiameter = max(planet.plDiameter, 9000)
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.RENEGADEBASE2, planet.owner, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.storPop = 3000

    @staticmethod
    def setStartingTechnologies(obj):
        obj.techLevel = 2
        # primitives, which Renegade won't use (it's for tech tree to be correct)
        be_one = [# primitives, which Renegade won't use (it's for tech tree usage only)
                  Rules.Tech.SMALLHULL0,
                  Rules.Tech.MEDIUMHULL0,
                  Rules.Tech.SCOCKPIT0,
                  Rules.Tech.SBRIDGE0,
                  Rules.Tech.CANNON0,
                  Rules.Tech.SSROCKET0,
                  # rest
                  Rules.Tech.SMALLHULL1,
                  Rules.Tech.SCOCKPIT1,
                  Rules.Tech.MEDIUMHULL2,
                  Rules.Tech.SBRIDGE1,
                  Rules.Tech.CANNON1,
                  Rules.Tech.SSROCKET,
                  Rules.Tech.STEELARM2,
                  Rules.Tech.NSTLENG2,
                  Rules.Tech.RENEGADETITANIUMMHULL,
                  Rules.Tech.RENEGADEBASE3,
                  Rules.Tech.RENEGADEBASE3MINOR,
                  Rules.Tech.RENEGADECOSMODROME,
                  Rules.Tech.RENEGADEBASE2,
                  Rules.Tech.RENEGADEBASE2MINOR]
        be_three = [Rules.Tech.STLENG1,
                    Rules.Tech.RENEGADEBASE]

        for tech in be_one:
            if tech in obj.techs: continue
            obj.techs[tech] = 1
        for tech in be_three:
            if tech in obj.techs: continue
            obj.techs[tech] = 3

    @staticmethod
    def setStartingShipDesigns(obj):
        obj.shipDesigns[1] = ShipUtils.makeShipMinSpec(obj, 'Fighter', Rules.Tech.SMALLHULL1,
            {Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:1, Rules.Tech.STLENG1:2}, [])
        obj.shipDesigns[2] = ShipUtils.makeShipMinSpec(obj, 'Corvette', Rules.Tech.SMALLHULL1,
            {Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:2, Rules.Tech.STLENG1:1, Rules.Tech.STEELARM2:1}, [])
        obj.shipDesigns[3] = ShipUtils.makeShipMinSpec(obj, 'Frigate', Rules.Tech.MEDIUMHULL2,
            {Rules.Tech.SBRIDGE1:1, Rules.Tech.CANNON1:2, Rules.Tech.SSROCKET:2, Rules.Tech.STLENG1:2}, [])
        obj.shipDesigns[4] = ShipUtils.makeShipMinSpec(obj, 'Destroyer', Rules.Tech.MEDIUMHULL2,
            {Rules.Tech.SBRIDGE1:1, Rules.Tech.CANNON1:4, Rules.Tech.SSROCKET:2, Rules.Tech.NSTLENG2:3}, [])
        obj.shipDesigns[5] = ShipUtils.makeShipMinSpec(obj, 'Armored Cruiser', Rules.Tech.RENEGADETITANIUMMHULL,
            {Rules.Tech.SBRIDGE1:1, Rules.Tech.CANNON1:5, Rules.Tech.SSROCKET:3, Rules.Tech.STLENG1:4}, [])


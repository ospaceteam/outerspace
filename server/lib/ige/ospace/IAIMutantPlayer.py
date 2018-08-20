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

import Rules
import ShipUtils
import Utils

import Const
from ige import log
from IPlayer import IPlayer
from ige.IObject import public
from ige.IDataHolder import IDataHolder

class IAIMutantPlayer(IPlayer):

    typeID = Const.T_AIMUTPLAYER
    forums = {"INBOX": 56, "OUTBOX": 56, "EVENTS": 0}

    def init(self, obj):
        IPlayer.init(self, obj)
        #
        obj.name = u'Mutant'
        obj.race = "m"
        obj.login = '*'

    def register(self, tran, obj, galaxyID):
        log.debug("Registering player", obj.oid)
        counter = 1
        while 1:
            obj.name = u'Mutant faction %d' % counter
            obj.login = '*AIP*mutant%d' % counter
            if galaxyID in tran.gameMngr.accountGalaxies(obj.login):
                counter += 1
                continue
            tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
            tran.db[Const.OID_UNIVERSE].players.append(obj.oid)
            tran.gameMngr.clientMngr.createAIAccount(obj.login, obj.name, 'ais_mutant')
            break
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

    @staticmethod
    def setStartingPlanet(tran, planet):
        planet.plSlots = max(planet.plSlots, 9)
        planet.plMaxSlots = max(planet.plMaxSlots, 9)
        planet.plDiameter = max(planet.plDiameter, 9000)
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.MUTANTBASE, planet.owner, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.storPop = 3000

    @staticmethod
    def setStartingTechnologies(obj):
        obj.techLevel = 3
        # grant technologies
        starting_techs = [Rules.Tech.SMALLHULL0,
                          Rules.Tech.MEDIUMHULL0,
                          Rules.Tech.SCOCKPIT0,
                          Rules.Tech.SBRIDGE0,
                          Rules.Tech.CANNON0,
                          Rules.Tech.CONBOMB0,
                          Rules.Tech.TORPEDO0,
                          Rules.Tech.SSROCKET0,
                          Rules.Tech.FTLENG0,
                          Rules.Tech.SCANNERMOD0,
                          # technologies for ship design creation
                          Rules.Tech.SMALLHULL1,
                          Rules.Tech.SCOCKPIT1,
                          Rules.Tech.SCANNERMOD1,
                          Rules.Tech.CONBOMB1,
                          Rules.Tech.EMCANNON,
                          Rules.Tech.STLENG1,
                          Rules.Tech.FTLENG1,
                          Rules.Tech.MUTANTPOD,
                          # structures
                          Rules.Tech.MUTANTBASE,
                          Rules.Tech.MUTANTBASE2,
                          Rules.Tech.MUTANTBASE3,
                          Rules.Tech.MUTANTBASE4,
                          Rules.Tech.MUTANTPP1,
                          Rules.Tech.MUTANTPP2,
                          Rules.Tech.MUTANTFACT1,
                          Rules.Tech.MUTANTFACT2,
                          Rules.Tech.MUTANTMINES,
                          ]
        for tech in starting_techs:
            if tech in obj.techs: continue
            obj.techs[tech] = 1

    @staticmethod
    def setStartingShipDesigns(obj):
        obj.shipDesigns[1] = ShipUtils.makeShipMinSpec(obj, 'Swarmer', Rules.Tech.SMALLHULL1,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.EMCANNON:2, Rules.Tech.STLENG1:1, Rules.Tech.FTLENG1:2}, [])
        obj.shipDesigns[2] = ShipUtils.makeShipMinSpec(obj, 'Seeder', Rules.Tech.MEDIUMHULL2,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.MUTANTPOD:1, Rules.Tech.FTLENG1:4}, [])
        obj.shipDesigns[3] = ShipUtils.makeShipMinSpec(obj, 'Seeker', Rules.Tech.SMALLHULL1,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.SCANNERMOD1:1, Rules.Tech.FTLENG1:2}, [])
        obj.shipDesigns[4] = ShipUtils.makeShipMinSpec(obj, 'Sower', Rules.Tech.SMALLHULL1,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.CONBOMB1:1, Rules.Tech.STLENG1:1, Rules.Tech.FTLENG1:2}, [])

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
        # create two basic designs [they use modules not available to the
        # player otherwise so it has to be done this way]
        # call super method
        IPlayer.update(self, tran, obj)

    def processFINALPhase(self, tran, obj, data):
        IPlayer.processFINALPhase(self, tran, obj, data)
        # fix goverment power
        obj.govPwrCtrlRange = 10000


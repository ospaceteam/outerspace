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

from Const import *
from ige import log
from IPlayer import IPlayer
from ige.IDataHolder import IDataHolder

class IAIMutantPlayer(IPlayer):

    typeID = T_AIMUTPLAYER
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
            tran.db[OID_UNIVERSE].players.append(obj.oid)
            tran.gameMngr.clientMngr.createAIAccount(obj.login, obj.name, 'ais_mutant')
            break
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

    @staticmethod
    def setStartingPlanet(tran, planet):
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.MUTANTBASE, planet.owner, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.storPop = 3000

    @staticmethod
    def setStartingTechnologies(obj):
        obj.techLevel = 3
        # grant technologies
        obj.techs[Rules.Tech.EMCANNON] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.SSROCKET] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.TORPEDO] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.FTLENG1] = 3
        obj.techs[Rules.Tech.SMALLHULL1] = 3
        obj.techs[Rules.Tech.SCOCKPIT1] = 3
        obj.techs[Rules.Tech.SCANNERMOD1] = 3
        obj.techs[Rules.Tech.CONBOMB1] = 3
        obj.techs[Rules.Tech.MUTANTBASE] = 3
        obj.techs[Rules.Tech.MUTANTBASE2] = 3
        obj.techs[Rules.Tech.MUTANTBASE3] = 3
        obj.techs[Rules.Tech.MUTANTBASE4] = 3
        obj.techs[Rules.Tech.MUTANTPP1] = 3
        obj.techs[Rules.Tech.MUTANTPP2] = 3
        obj.techs[Rules.Tech.MUTANTFACT1] = 3
        obj.techs[Rules.Tech.MUTANTFACT2] = 3
        obj.techs[Rules.Tech.MUTANTMINES] = 3

    @staticmethod
    def setStartingShipDesigns(obj):
        obj.shipDesigns[1] = ShipUtils.makeShipMinSpec(obj, 'Swarmer', Rules.Tech.SMALLHULL1,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.EMCANNON:2, Rules.Tech.FTLENG1:2}, [])
        obj.shipDesigns[2] = ShipUtils.makeShipMinSpec(obj, 'Seeder', Rules.Tech.MEDIUMHULL2,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.MUTANTPOD:1, Rules.Tech.FTLENG1:4}, [])
        obj.shipDesigns[3] = ShipUtils.makeShipMinSpec(obj, 'Seeker', Rules.Tech.SMALLHULL1,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.SCANNERMOD1:1, Rules.Tech.FTLENG1:2}, [])
        obj.shipDesigns[4] = ShipUtils.makeShipMinSpec(obj, 'Sower', Rules.Tech.SMALLHULL1,
                {Rules.Tech.SCOCKPIT1:1, Rules.Tech.CONBOMB1:1, Rules.Tech.FTLENG1:2}, [])

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

    def processRSRCHPhase(self, tran, obj, data):
        # do not research anything
        return

    processRSRCHPhase.public = 1
    processRSRCHPhase.accLevel = AL_ADMIN

    def processFINALPhase(self, tran, obj, data):
        IPlayer.processFINALPhase(self, tran, obj, data)
        # fix goverment power
        obj.govPwrCtrlRange = 10000

    def getDiplomacyWith(self, tran, obj, playerID):
        if obj.oid == playerID:
            return REL_UNITY
        # this AI battles with overyone
        # make default
        dipl = IDataHolder()
        dipl.type = T_DIPLREL
        dipl.pacts = {}
        dipl.relation = REL_ENEMY
        dipl.relChng = 0
        dipl.lastContact = tran.db[OID_UNIVERSE].turn
        dipl.contactType = CONTACT_NONE
        dipl.stats = None
        return dipl

    # allow normal pacts
    #def isPactActive(self, tran, obj, partnerID, pactID):
    #    return 0

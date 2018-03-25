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

from ige import *
from xml.dom.minidom import Node
from IPlayer import IPlayer
from ige.IDataHolder import IDataHolder
import ShipUtils
import Rules, Utils
from Const import *
import math, time, random, os
import hashlib



from ai_parser import AIList

class IAIRenegadePlayer(IPlayer):

    typeID = T_AIRENPLAYER
    forums = {"INBOX": 56, "OUTBOX": 56, "EVENTS": 0}

    def init(self, obj):
        IPlayer.init(self, obj)
        #
        obj.name = u'Renegade'
        obj.race = "r"
        obj.login = '*'

    def register(self, tran, obj):
        log.debug("Registering player", obj.oid)
        counter = 1
        while 1:
            try:
                obj.name = u'Renegade faction %d' % counter
                obj.login = '*AIP*renegade%d' % counter
                password = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()
                tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
                tran.db[OID_UNIVERSE].players.append(obj.oid)
                tran.gameMngr.clientMngr.createAiAccount(None, obj.login, password, obj.name)
                break
            except CreatePlayerException:
                counter += 1
        # after succesfull registration, register it to the AI system
        aiList = AIList(tran.gameMngr.configDir, tran.gameMngr.gameName)
        aiList.add(obj.login, password, 'ais_renegade')
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

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
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.RENEGADEBASE, planet.owner, STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.storPop = 3000

    @staticmethod
    def setStartingTechnologies(obj):
        obj.techLevel = 2
        obj.techs[Rules.Tech.CANNON1] = 3
        obj.techs[Rules.Tech.SSROCKET] = 3
        obj.techs[Rules.Tech.RENEGADEBASE] = 3
        obj.techs[Rules.Tech.RENEGADEBASE2] = 3
        obj.techs[Rules.Tech.RENEGADEBASE2MINOR] = 3
        obj.techs[Rules.Tech.RENEGADEBASE3] = 3
        obj.techs[Rules.Tech.RENEGADEBASE3MINOR] = 3
        obj.techs[Rules.Tech.RENEGADECOSMODROME] = 3

    @staticmethod
    def setStartingShipDesigns(obj):
        obj.shipDesigns[1] = ShipUtils.makeShipMinSpec(obj, 'Fighter', Rules.Tech.SMALLHULL1,
            {Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:1}, [])
        obj.shipDesigns[2] = ShipUtils.makeShipMinSpec(obj, 'Corvette', Rules.Tech.SMALLHULL1,
            {Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:2, Rules.Tech.STEELARM2:1}, [])
        obj.shipDesigns[3] = ShipUtils.makeShipMinSpec(obj, 'Frigate', Rules.Tech.MEDIUMHULL2,
            {Rules.Tech.SBRIDGE1:1, Rules.Tech.CANNON1:2, Rules.Tech.SSROCKET:2}, [])

    def getDiplomacyWith(self, tran, obj, playerID):
        if obj.oid == playerID:
            return REL_UNITY
        # renegade battles with overyone
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

    def processFINALPhase(self, tran, obj, data):
        IPlayer.processFINALPhase(self, tran, obj, data)
        # fix goverment power
        obj.govPwrCtrlRange = 10000

    # allow normal pacts
    #def isPactActive(self, tran, obj, partnerID, pactID):
    #    return 0

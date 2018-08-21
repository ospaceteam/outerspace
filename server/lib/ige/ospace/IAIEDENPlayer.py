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
import Utils

from ige import log
from ige.IDataHolder import IDataHolder
from ige.IObject import public
from IPlayer import IPlayer

class IAIEDENPlayer(IPlayer):

    typeID = Const.T_AIEDENPLAYER

    def init(self, obj):
        IPlayer.init(self, obj)
        #
        obj.name = u'E.D.E.N.'
        obj.race = "e"
        obj.login = '*'

    def register(self, tran, obj, galaxyID):
        log.debug("Registering player", obj.oid)
        counter = 1
        while 1:
            obj.name = u'E.D.E.N. %d' % counter
            obj.login = '*AIP*eden%d' % counter
            if galaxyID in tran.gameMngr.accountGalaxies(obj.login):
                counter += 1
                continue
            tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
            tran.db[Const.OID_UNIVERSE].players.append(obj.oid)
            tran.gameMngr.clientMngr.createAIAccount(obj.login, obj.name, 'ais_eden')
            break
        # grant techs and so on
        self.cmd(obj).update(tran, obj)

    def update(self, tran, obj):
        self.setStartingTechnologies(obj)
        self.setStartingShipDesigns(obj)
        IPlayer.update(self, tran, obj)

    @staticmethod
    def setStartingPlanet(tran, planet):
        planet.plSlots = max(planet.plSlots, 2)
        planet.plMaxSlots = max(planet.plMaxSlots, 2)
        planet.plDiameter = max(planet.plDiameter, 2000)
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.EDENBASE, planet.owner, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.slots.append(Utils.newStructure(tran, Rules.Tech.EDENSTATION, planet.owner, Const.STRUCT_STATUS_ON, Rules.structNewPlayerHpRatio))
        planet.storPop = 3000

    @staticmethod
    def setStartingTechnologies(obj):
        obj.techLevel = 7
        obj.techs[Rules.Tech.LASCANNONTUR3] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.SSROCKET2] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.TORPEDO] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.EDENCANNON] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.EDENMISSILE] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.EDENTORP] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.EDENBOMB] = Rules.techMaxImprovement
        obj.techs[Rules.Tech.EDENSTATION] = Rules.techMaxImprovement

    @staticmethod
    def setStartingShipDesigns(obj):
        pass

    @public(Const.AL_ADMIN) 
    def processINITPhase(self, tran, obj, data):
        IPlayer.processINITPhase(self, tran, obj, data)
        obj.lastLogin = time.time()
        # delete itself if there are no fleets and planets
        # delete the account as well
        # unregister it from the AI system
        if not obj.fleets and not obj.planets:
            self.cmd(obj).delete(tran, obj)

    def getDiplomacyWith(self, tran, obj, playerID):
        if obj.oid == playerID:
            return Const.REL_UNITY
        player = tran.db.get(playerID, None)
        if player.type in (Const.T_AIPIRPLAYER, Const.T_PIRPLAYER):
            dipl = obj.diplomacyRels.get(playerID, None)
            if not dipl:
                # make default
                dipl = IDataHolder()
                dipl.type = Const.T_DIPLREL
                dipl.pacts = {
                        Const.PACT_ALLOW_CIVILIAN_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_CIVILIAN_SHIPS],
                        Const.PACT_ALLOW_MILITARY_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_MILITARY_SHIPS]
                }
                dipl.relation = Const.REL_FRIENDLY
                dipl.relChng = 0
                dipl.lastContact = tran.db[Const.OID_UNIVERSE].turn
                dipl.contactType = Const.CONTACT_NONE
                dipl.stats = None
                if playerID != obj.oid:
                    obj.diplomacyRels[playerID] = dipl
                else:
                    log.debug("getDiplomacyWith myself", obj.oid)
            return dipl
        # this AI battles with overyone
        # make default
        dipl = IDataHolder()
        dipl.type = Const.T_DIPLREL
        dipl.pacts = {}
        dipl.relation = Const.REL_ENEMY
        dipl.relChng = 0
        dipl.lastContact = tran.db[Const.OID_UNIVERSE].turn
        dipl.contactType = Const.CONTACT_NONE
        dipl.stats = None
        return dipl

    def isPactActive(self, tran, obj, partnerID, pactID):
        if partnerID == Const.OID_NONE:
            return 0
        partner = tran.db.get(partnerID, None)
        if partner.type in (Const.T_AIPIRPLAYER, Const.T_PIRPLAYER):
            # force the peace!
            if pactID in (Const.PACT_ALLOW_CIVILIAN_SHIPS, Const.PACT_ALLOW_MILITARY_SHIPS):
                return Const.PACT_ACTIVE
        return 0

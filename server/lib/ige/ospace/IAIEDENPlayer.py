#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from ige import *
from xml.dom.minidom import Node
from IPlayer import IPlayer
from ige.IDataHolder import IDataHolder
import Rules, Utils
from Const import *
import math, time

class IAIEDENPlayer(IPlayer):

	typeID = T_AIEDENPLAYER

	def init(self, obj):
		IPlayer.init(self, obj)
		#
		obj.name = u'E.D.E.N.'
		obj.login = '*'

	def register(self, tran, obj):
		log.debug("Registering player", obj.oid)
		counter = 1
		while 1:
			try:
				obj.name = u'E.D.E.N. [%d]' % counter
				obj.login = '*AIP*eden%d' % counter
				tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
				tran.db[OID_UNIVERSE].players.append(obj.oid)
				return
			except CreatePlayerException:
				counter += 1

	def update(self, tran, obj):
		obj.techLevel = 3
		# grant technologies
		obj.techs[Rules.Tech.LASCANNONTUR3] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.SSROCKET2] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.TORPEDO] = Rules.techMaxImprovement
		# call super method
		IPlayer.update(self, tran, obj)
		#add TL99 techs
		obj.techLevel = 99
		obj.techs[Rules.Tech.EDENCANNON] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.EDENMISSILE] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.EDENTORP] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.EDENBOMB] = Rules.techMaxImprovement
		obj.techs[Rules.Tech.EDENSTATION] = Rules.techMaxImprovement

	def processINITPhase(self, tran, obj, data):
		IPlayer.processINITPhase(self, tran, obj, data)
		obj.lastLogin = time.time()
		# delete itself if there are no fleets and planets
		if not obj.fleets and not obj.planets:
			self.cmd(obj).delete(tran, obj)

	def getDiplomacyWith(self, tran, obj, playerID):
		if obj.oid == playerID:
			return REL_UNITY
		player = tran.db.get(playerID, None)
		if player.type in (T_AIPIRPLAYER, T_PIRPLAYER):
			dipl = obj.diplomacyRels.get(playerID, None)
			if not dipl:
				# make default
				dipl = IDataHolder()
				dipl.type = T_DIPLREL
				dipl.pacts = {
						PACT_ALLOW_CIVILIAN_SHIPS: [PACT_ACTIVE, PACT_ALLOW_CIVILIAN_SHIPS],
						PACT_ALLOW_MILITARY_SHIPS: [PACT_ACTIVE, PACT_ALLOW_MILITARY_SHIPS]
				}
				dipl.relation = REL_FRIENDLY
				dipl.relChng = 0
				dipl.lastContact = tran.db[OID_UNIVERSE].turn
				dipl.contactType = CONTACT_NONE
				dipl.stats = None
				if playerID != obj.oid:
					obj.diplomacyRels[playerID] = dipl
				else:
					log.debug("getDiplomacyWith myself", obj.oid)
			return dipl
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

	def isPactActive(self, tran, obj, partnerID, pactID):
		return 0

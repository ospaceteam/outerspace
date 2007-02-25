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

class IAIRenegadePlayer(IPlayer):

	typeID = T_AIRENPLAYER

	def init(self, obj):
		IPlayer.init(self, obj)
		#
		obj.name = u'Renegade'
		obj.login = '*'

	def register(self, tran, obj):
		log.debug("Registering player", obj.oid)
		counter = 1
		while 1:
			try:
				obj.name = u'Renegade faction %d' % counter
				obj.login = '*AIP*renegade%d' % counter
				tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
				tran.db[OID_UNIVERSE].players.append(obj.oid)
				return
			except CreatePlayerException:
				counter += 1

	def processINITPhase(self, tran, obj, data):
		IPlayer.processINITPhase(self, tran, obj, data)
		obj.lastLogin = time.time()
		# delete itself if there are no fleets and planets
		if not obj.fleets and not obj.planets:
			self.cmd(obj).delete(tran, obj)

	def update(self, tran, obj):
		obj.techLevel = 1
		# grant technologies
		obj.techs[Rules.Tech.CANNON1] = Rules.techMaxImprovement
		# call super method
		IPlayer.update(self, tran, obj)

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

	# allow normal pacts
	#def isPactActive(self, tran, obj, partnerID, pactID):
	#	return 0

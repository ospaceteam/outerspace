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

class INature(IPlayer):

	typeID = T_NATURE

	def init(self, obj):
		IPlayer.init(self, obj)
		#
		obj.name = u'NATURE'
		obj.login = '*NATURE*'

	def processINITPhase(self, tran, obj, data):
		IPlayer.processINITPhase(self, tran, obj, data)
		obj.lastLogin = time.time()
		log.debug("NATURE - asteroids", len(obj.fleets), obj.fleets)

	processINITPhase.public = 1
	processINITPhase.accLevel = AL_ADMIN

	def processPRODPhase(self, tran, obj, data):
		return None

	processPRODPhase.public = 1
	processPRODPhase.accLevel = AL_ADMIN

	def processBATTLEPhase(self, tran, obj, data):
		return None

	processBATTLEPhase.public = 1
	processBATTLEPhase.accLevel = AL_ADMIN

	def getDiplomacyWith(self, tran, obj, playerID):
		# this AI battles with overyone
		# make default
		dipl = IDataHolder()
		dipl.type = T_DIPLREL
		dipl.pacts = {}
		if obj.oid == playerID:
			dipl.relation = REL_UNITY
		else:
			dipl.relation = REL_ENEMY
		dipl.relChng = 0
		dipl.lastContact = tran.db[OID_UNIVERSE].turn
		dipl.contactType = CONTACT_NONE
		dipl.stats = None
		return dipl

	def isPactActive(self, tran, obj, partnerID, pactID):
		return 0

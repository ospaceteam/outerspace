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

class IAIPlayer(IPlayer):

	typeID = T_AIPLAYER

	def init(self, obj):
		IPlayer.init(self, obj)
		#
		obj.name = u'Rebels'
		obj.login = '*'

	def reregister(self, tran, obj):
		log.debug("Reregistering player", obj.oid)
		counter = 1
		while 1:
			try:
				obj.name = u'Rebel faction %d' % counter
				obj.login = '*AIP*rebels%d' % counter
				log.debug("Trying", obj.name)
				tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
				log.debug("Player registered")
				tran.db[OID_UNIVERSE].players.append(obj.oid)
				return
			except CreatePlayerException:
				log.debug("Name exists")
				counter += 1

	def processINITPhase(self, tran, obj, data):
		IPlayer.processINITPhase(self, tran, obj, data)
		obj.lastLogin = time.time()
		# delete itself if there are no fleets and planets
		if not obj.fleets and not obj.planets:
			self.cmd(obj).delete(tran, obj)

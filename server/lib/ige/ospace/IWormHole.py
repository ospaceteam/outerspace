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
from ISystem import ISystem
from Const import *

class IWormHole(ISystem):

    typeID = T_WORMHOLE

    def init(self, obj):
        ISystem.init(self, obj)
        #
        obj.destinationOid = OID_NONE
        obj.destination = u'---'
        obj.starClass = u'wW0'

    def loadDOMNode(self, tran, obj, xoff, yoff, node):
        obj.x = float(node.getAttribute('x')) + xoff
        obj.y = float(node.getAttribute('y')) + yoff
        for elem in node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                name = elem.tagName
                if name == 'properties':
                    self.loadDOMAttrs(obj, elem)
                else:
                    raise GameException('Unknown element %s' % name)
        return SUCC

	def getScanInfos(self, tran, obj, scanPwr, player):
		log.debug('Generating wormhole scan data',obj.oid)
		result = IDataHolder()
		results = [result]
		if scanPwr >= Rules.level1InfoScanPwr:
			result._type = T_SCAN
			result.scanPwr = scanPwr
			result.oid = obj.oid
			result.x = obj.x
			result.y = obj.y
			# multiply by 1000 to increase accuracy
			#~ result.dist = obj.dist * 1000
			#~ result.dAngle = obj.dAngle * 1000
			#~ result.sAngle = obj.sAngle * 1000
			result.signature = obj.signature
			result.type = obj.type
			result.compOf = obj.compOf
			result.starClass = obj.starClass
			result.destinationOid = obj.destinationOid
		if scanPwr >= Rules.level2InfoScanPwr:
			result.name = obj.name
			result.combatCounter = obj.combatCounter
		if scanPwr >= Rules.level4InfoScanPwr:
			result.fleets = obj.fleets
			for fleetID in obj.fleets:
				fleet = tran.db[fleetID]
				if fleet.owner == player:
					continue
				newPwr = scanPwr * fleet.signature / obj.signature
				results.extend(self.cmd(fleet).getScanInfos(tran, fleet, newPwr, player))
		return results

	def getPublicInfo(self, tran, obj):
		result = ISystem.getPublicInfo(self, tran, obj)
		log.debug('here!');
		result.type = obj.type
		result.name = obj.name
		result.destinationOid = obj.destinationOid
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE

	def getInfo(self, tran, obj):
		result = ISystem.getInfo(self, tran, obj)
		log.debug('there!');
		result.type = obj.type
		result.name = obj.name
		result.destinationOid = obj.destinationOid
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_INFO


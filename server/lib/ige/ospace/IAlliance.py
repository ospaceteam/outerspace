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
from ige.IObject import IObject
from ige.IDataHolder import IDataHolder
from Const import *
import Rules

class IAlliance(IObject):

	typeID = T_ALLIANCE

	def init(self, obj):
		IObject.init(self, obj)
		obj.members = []
		#
		obj.relations = {}
		obj.alliance = OID_NONE
		obj.defRelation = REL_NEUTRAL
		obj.relationsCache = {}

	def getPublicInfo(self, tran, obj):
		result = IObject.getPublicInfo(self, tran, obj)
		result.type = obj.type
		result.name = obj.name
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE

	def setRelation(self, tran, obj, objID, relation):
		anObj = tran.db[objID]
		if anObj.type != T_PLAYER and anObj.type != T_ALIANCE:
			raise GameException('Relations can be set/changed only for players and aliances.')
		if relation == REL_UNDEF:
			if obj.relations.has_key(objID):
				del obj[objID]
				return
			else:
				raise GameException('No such relation to delete.')
		obj.relations[objID] = relation

	setRelation.public = 1
	setRelation.accLevel = AL_FULL

	def getRelationTo(self, tran, obj, objID):
		# check cache
		relation = obj.relationsCache.get(objID, REL_UNDEF)
		if relation != REL_UNDEF:
			return relation
		# compute relation - player preferences first
		anObj = tran.db[objID]
		relation = min(obj.relations.get(objID, REL_UNDEF),	anObj.relations.get(obj.oid, REL_UNDEF))
		if relation != REL_UNDEF:
			obj.relationsCache[objID] = relation
			anObj.relationsCache[obj.oid] = relation
			return relation
		# check alliance(s) and default relations
		if not obj.alliance:
			if anObj.relation:
				# check alliance on anObj
				relation = min(obj.defRelation,
					self.cmd(anObj.alliance).getRelationTo(tran, anObj.alliance, obj.oid))
			else:
				# default relations
				relation = min(obj.defRelation, anObj.defRelation)
			obj.relationsCache[objID] = relation
			anObj.relationsCache[obj.oid] = relation
			return relation
		# let alliance resolve this problem
		relation = self.cmd(obj.alliance).getRelationTo(tran, alliance, objID)
		obj.relationsCache[objID] = relation
		anObj.relationsCache[obj.oid] = relation
		return relation


	getRelationTo.public = 1
	getRelationTo.accLevel = AL_ADMIN

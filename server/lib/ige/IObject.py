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

from Const import *
from ige import GameException, SecurityException
from ige.IDataHolder import IDataHolder
import types
import log

class IObject:

	typeID = T_OBJECT
	forums = []

	def __init__(self, gameMngr):
		self.gameMngr = gameMngr
		self._cmd = gameMngr.cmdPool

	def cmd(self, obj):
		return self._cmd[obj.type]

	def new(self, type):
		obj = IDataHolder()
		self._cmd[type].init(obj)
		return obj

	def init(self, obj):
		# call superclass
		pass
		# define new attributes
		obj.oid = OID_NONE
		obj.type = self.typeID
		obj.owner = OID_NONE
		obj.compOf = OID_NONE
		obj.name = u'Unnamed'
		# not needed
		# obj.accRights = {}

	def getReferences(self, tran, obj):
		return None

	def upgrade(self, tran, obj):
		# call update method
		try:
			self.cmd(obj).update(tran, obj)
		except:
			log.warning("Cannot execute update method on", obj.oid)
		refObj = self.new(obj.type)
		new = refObj.__dict__.keys()
		old = obj.__dict__.keys()
		changed = 0
		# change attributes
		# remove old
		for attr in old:
			if attr in new:
				#if type(getattr(obj, attr)) != type(getattr(refObj, attr)):
					#@log.debug('IObject', 'Upgrade - chng', obj.oid, obj.type, attr, type(getattr(obj, attr)), 'to', type(getattr(refObj, attr)))
					# TODO - enable
					#setattr(obj, attr, getattr(refObj, attr))
					#changed = 1
				new.remove(attr)
			else:
				log.debug('IObject', 'Upgrade - del', obj.oid, obj.type, attr)
				delattr(obj, attr)
				changed = 1
		# set new
		for attr in new:
			log.debug('IObject', 'Upgrade - new', obj.oid, obj.type, attr)
			setattr(obj, attr, getattr(refObj, attr))
			changed = 1

	def update(self, tran, obj):
		pass

	update.public = 0

	def loadDOMAttrs(self, obj, elem):
		for index in xrange(0, elem.attributes.length):
			attr = elem.attributes.item(index)
			if hasattr(obj, attr.nodeName):
				attrType = type(getattr(obj, attr.nodeName))
				if attrType == types.IntType:
					value = int(attr.nodeValue)
				elif attrType == types.FloatType:
					value = float(attr.nodeValue)
				elif attrType == types.UnicodeType:
					value = attr.nodeValue
				elif attrType == types.StringType:
					value = attr.nodeValue
				else:
					raise 'Unsupported attribute type %s' % attrType
				setattr(obj, attr.nodeName, value)
			else:
				raise GameException('Unsupported attribute %s' % attr.nodeName)

	def getInfo(self, tran, obj):
		return obj

	getInfo.public = 1
	getInfo.accLevel = AL_INFO

	def get(self, tran, obj):
		return self.cmd(obj).getInfo(tran, obj)

	get.public = 1
	get.accLevel = AL_INFO

	def getPublicInfo(self, tran, obj):
		result = IDataHolder()
		result.oid = obj.oid
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE

	def set(self, tran, obj, attr, value):
		if hasattr(obj, attr):
			setattr(obj, attr, value)
			return 1
		raise GameException('No such attribute.')

	set.public = 1
	set.accLevel = AL_ADMIN


	## messaging api
	def sendMsg(self, tran, obj, message):
		if tran.session.cid != OID_ADMIN:
			message["sender"] = tran.session.nick
			message["senderID"] = tran.session.cid
		# check attributes
		if "forum" not in message:
			raise GameException("Forum not specified.")
		if message["forum"] not in self.forums:
			raise GameException("No such forum.")
		if "topic" not in message:
			raise GameException("Topic not specified.")
		if "data" not in message and "text" not in message:
			raise GameException("Text or structured data not specified.")
		# check permissions
		if tran.session.cid != OID_ADMIN and \
			not self.canSendMsg(tran, obj, message["senderID"], message["forum"]):
			raise SecurityException("You cannot send message to this entity.")
		#
		message["recipient"] = obj.name
		message["recipientID"] = obj.oid
		# send message
		return tran.gameMngr.msgMngr.send(tran.gameMngr.gameID, obj.oid, message)

	sendMsg.public = 1
	sendMsg.accLevel = AL_NONE

	def sendAdminMsg(self, tran, obj, message):
		# check attributes
		if "forum" not in message:
			raise GameException("Forum not specified.")
		if message["forum"] not in self.forums:
			raise GameException("No such forum.")
		if "topic" not in message:
			raise GameException("Topic not specified.")
		if "data" not in message and "text" not in message:
			raise GameException("Text or structured data not specified.")
		#
		message["recipient"] = obj.name
		message["recipientID"] = obj.oid
		# send message
		return tran.gameMngr.msgMngr.send(tran.gameMngr.gameID, obj.oid, message)

	sendAdminMsg.public = 1
	sendAdminMsg.accLevel = AL_ADMIN

	def getMsgs(self, tran, obj, lastID = -1):
		if not self.canGetMsgs(tran, obj, tran.session.cid):
			raise SecurityException("You cannot read messages of this entity.")
		# get messages
		return tran.gameMngr.msgMngr.get(tran.gameMngr.gameID, obj.oid, lastID)

	getMsgs.public = 1
	getMsgs.accLevel = AL_NONE

	def deleteMsgs(self, tran, obj, ids):
		if not self.canManageMsgs(tran, obj, tran.session.cid):
			raise SecurityException("You cannot manage messages of this entity.")
		# get messages
		return tran.gameMngr.msgMngr.delete(tran.gameMngr.gameID, obj.oid, ids)

	deleteMsgs.public = 1
	deleteMsgs.accLevel = AL_NONE

	def deleteOldMsgs(self, tran, obj):
		for forum in self.forums:
			tran.gameMngr.msgMngr.deleteOld(tran.gameMngr.gameID, obj.oid, forum, maxAge = self.forums[forum])

	deleteOldMsgs.public = 1
	deleteOldMsgs.accLevel = AL_ADMIN

	def canSendMsg(self, tran, obj, oid, forum):
		return 0

	canSendMsg.public = 0

	def canGetMsgs(self, tran, obj, oid):
		return oid == obj.oid

	canGetMsgs.public = 0

	def canManageMsgs(self, tran, obj, oid):
		return oid == obj.oid or oid == OID_ADMIN

	canManageMsgs.public = 0

	def getMailboxName(self, tran, obj):
		return (tran.gameMngr.gameID, obj.oid)

	getMailboxName.public = 0

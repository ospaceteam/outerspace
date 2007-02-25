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

import time, log, ige

class MsgMngrException(Exception):
	pass

class MsgMngr:

	MAILBOXROOT_ID = "#MAILBOXROOT#"
	
	def __init__(self, database):
		# init object space root
		self.database = database
		self.deleted = 0

	def shutdown(self):
		log.message('Shutdown')
		self.database.shutdown()

	def checkpoint(self):
		self.database.checkpoint()

	def clear(self):
		self.database.clear()

	def backup(self, basename):
		self.database.backup(basename)

	def upgrade(self):
		return
		# not needed if everything goes well
		log.debug("UPGRADE mailboxes")
		for name in self.getMailboxes():
			log.debug("Checking mailbox", name)
			try:
				self.getMailbox(name, recreate = False).upgrade()
			except MsgMngrException:
				log.warning("Cannot upgrade mailbox")
		# check for old style mailboxes
		log.debug("Checking for old-style mailboxes")
		for name in self.database.keys():
			if len(name.split("-")) == 2:
				log.debug("Checking mailbox", name)
				try:
					self.getMailbox(name, recreate = False).upgrade()
					self.mailboxRoot.addMailbox(name)
				except MsgMngrException:
					log.warning("Cannot upgrade mailbox")

	def getMailboxRoot(self):
		mailboxRoot = self.database.get(self.MAILBOXROOT_ID, None)
		if not mailboxRoot:
			mailboxRoot = MailboxRoot()
			mailboxRoot.scan(self.database)
			self.database.create(mailboxRoot, id = self.MAILBOXROOT_ID)
		return mailboxRoot

	def getMailbox(self, gameID, oid, recreate = True):
		name = "%s-%s" % (gameID, oid)
		try:
			mailbox = self.database.get(name, None)
		except:
			log.warning("Cannot read the mailbox", name)
			# force recreation
			mailbox = None
		if mailbox:
			#if hasattr(mailbox, "setDatabase"):
			mailbox.setDatabase(self.database)
			return mailbox
		if not recreate:
			raise MsgMngrException("No such mailbox")
		# create mailbox
		log.message("Creating mailbox", name)
		mailbox = Mailbox(name)
		self.database.create(mailbox, id = name)
		mailbox.setDatabase(self.database)
		self.getMailboxRoot().addMailbox(name)
		return mailbox

	# send message
	def send(self, gameID, oid, messageDict):
		self.getMailbox(gameID, oid).add(messageDict)
		return 1

	# get messages from mailbox
	def get(self, gameID, oid, lastID):
		response = self.getMailbox(gameID, oid).get(lastID)
		return response

	# delete messages from mailbox
	def delete(self, gameID, oid, msgIDs):
		self.getMailbox(gameID, oid).delete(msgIDs)
		return 1

	# delete old messages from mailbox
	def deleteOld(self, gameID, oid, forum, maxAge):
		log.debug("Compresing mailbox", gameID, oid, forum)
		self.deleted += self.getMailbox(gameID, oid).deleteOld(forum, maxAge)
		if self.deleted >= 200:
			self.database.checkpoint()
			self.deleted = 0
		#@log.debug("Compression finished", gameID, oid, forum)
		return 1

	# delete unused mailboxes
	def trashUnusedMailboxes(self, mailboxes):
		trash = self.getMailboxes()
		#@log.debug("Mailboxes:", trash)
		#@log.debug("Used:", mailboxes)
		for mailbox in mailboxes:
			if mailbox in trash:
				trash.remove(mailbox)
		for gameID, oid in trash:
			log.message("Removing mailbox", gameID, oid)
			box = self.getMailbox(gameID, oid)
			box.deleteAll()
			del self.database[box.name]
			self.getMailboxRoot().removeMailbox(box.name)

	def getMailboxes(self):
		mailboxes = self.getMailboxRoot().getAll()
		result = []
		for mailbox in mailboxes:
			gameID, oid = mailbox.split("-")
			result.append((gameID, int(oid)))
		return result

class MailboxRoot:

	def __init__(self):
		self.mailboxNames = []

	def scan(self, db):
		log.debug("*** SCANNING MAILBOXES ***")
		self.mailboxNames = []
		for key in db.keys():
			if key.count("-") == 1:
				# mailbox
				self.mailboxNames.append(key)
			else:
				#skip ordinal mails and mailboxroot
				continue
	
	def addMailbox(self, name):
		if name not in self.mailboxNames:
			self.mailboxNames.append(name)

	def removeMailbox(self, name):
		self.mailboxNames.remove(name)

	def getAll(self):
		return self.mailboxNames

class Mailbox:

	def __init__(self, name):
		self.oid = 0
		self.name = name
		self.msgIds = 0
		self.messageIDs = []
		self.database = None

	def setDatabase(self, database):
		self.database = database

	def add(self, message, msgID = None):
		if msgID == None:
			msgID = self.msgIds
			self.msgIds += 1
		dbID = "%s-%d" % (self.name, msgID)
		message['time'] = time.time()
		message['dbID'] = dbID
		message['id'] = msgID
		self.messageIDs.append(msgID)
		try:
			self.database.create(message, dbID)
		except ige.ServerException:
			log.warning("Message not added to the database")

	def get(self, lastID = -1):
		result = []
		# are there any new messages?
		if lastID + 1 == self.msgIds:
			return result
		# create list of new messages
		result = [
			self.database["%s-%d" % (self.name, msgID)]
			for msgID in self.messageIDs if msgID > lastID
		]
		return result

	def delete(self, msgIDs):
		for msgID in msgIDs:
			dbID = "%s-%d" % (self.name, msgID)
			#@log.debug("MsgMngr - deleting message", dbID)
			del self.database[dbID]
			self.messageIDs.remove(msgID)
		return 1

	def deleteAll(self):
		self.delete(self.messageIDs)

	def deleteOld(self, forum, maxAge):
		now = time.time()
		maxAge = maxAge * 24 * 60 * 60 # maxAge is in days
		delete = []
		for msgID in self.messageIDs:
			message = self.database["%s-%d" % (self.name, msgID)]
			if message['forum'] == forum and message['time'] + maxAge < now:
				#@log.debug("MsgMngr - deleting msg", self.name, forum, msgID)
				delete.append(msgID)
			elif message['forum'] == forum:
				break
		if not delete:
			return 0
		log.debug("MsgMngr - deleting %d messages (500 max) out of %d" % (len(delete), len(self.messageIDs)))
		t0 = time.time()
		maxMsg = 500
		count = min(len(delete), maxMsg)
		self.delete(delete[:maxMsg])
		t = time.time() - t0
		if t > 0.0:
			log.debug("MsgMngr - deleted %.3f msgs/sec" % (count / t))
		else:
			log.debug("MsgMngr - deleted NaN msgs/sec")
		return count

	def __getstate__(self):
		self.database = None
		return self.__dict__

	def upgrade(self):
		log.debug("Up-to-date")

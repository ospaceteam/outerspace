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

# Game manager
# Multiple instances can be created (one for each game)

from ige import *
import ige
from Database import Database
from Transaction import Transaction
from Index import Index
from Const import *
import os, os.path, time
import log
from IObject import IDataHolder

class GameMngr:

	def __init__(self, gameID, config, clientMngr, msgMngr, database):
		log.debug("Runtime mode", ige.igeRuntimeMode)
		self.status = GS_INIT
		self.gameID = gameID
		self.clientMngr = clientMngr
		self.msgMngr = msgMngr
		self.cmdPool = {}
		self.db = database
		self.config = config
		# register command objects
		# None here

	def init(self):
		pass

	def start(self):
		if self.status == GS_RUNNING:
			return
		# start timer
		self.status = GS_RUNNING

	def stop(self, checkpoint = 1):
		if self.status == GS_STOPPED:
			return
		# stop timer
		self.status = GS_STOPPED
		if checkpoint:
			self.db.checkpoint()
			self.msgMngr.checkpoint()
			self.clientMngr.checkpoint()

	def shutdown(self):
		if self.status == GS_SDOWN:
			return
		self.stop(checkpoint = 0)
		self.status = GS_SDOWN
		self.db.shutdown()

	def upgrade(self):
		oldStatus = self.status
		self.status = GS_MAINT
		tran = Transaction(self, OID_ADMIN)
		# used objects
		objIDs = {}
		for objID in self.db.keys():
			objIDs[objID] = None
		del objIDs[1]
		del objIDs[OID_ADMIN]
		del objIDs[OID_I_LOGIN2OID]
		del objIDs[OID_I_NAME2OID]
		# stats
		types = {}
		# upgrade all objects in database
		# and collect all not referenced objects
		for id in self.db.keys():
			try:
				obj = self.db[id]
			except:
				log.warning("Cannot upgrade object", id, "no such id in db")
			if not isinstance(obj, IDataHolder):
				#@log.debug('Upgrade - skiping', id)
				continue
			#@log.debug('Upgrade - upgrading', id, obj.type)
			types[obj.type] = types.get(obj.type, 0) + 1
			if self.cmdPool.has_key(obj.type):
				try:
					self.cmdPool[obj.type].upgrade(tran, obj)
				except Exception, e:
					log.warning("Cannot upgrade object", id)
			references = self.cmdPool[obj.type].getReferences(tran, obj)
			if references:
				for tmpID in references:
					if tmpID in objIDs:
						del objIDs[tmpID]
		# delete all not referenced objects
		for objID in objIDs:
			log.debug(objID, "is not referenced, deleting it")
			del tran.db[objID]
		# print stats
		log.debug("*****")
		for t in types:
			log.debug("Object type %d: %d occurences" % (t, types[t]))
		self.status = oldStatus

	def reset(self):
		# cleanup database
		self.db.clear()
		self.msgMngr.clear()
		# create indexes
		self.db.create(Index(), OID_I_LOGIN2OID)
		self.db.create(Index(), OID_I_NAME2OID)
		# create admin
		self.registerPlayer('admin', self.createAdmin(), OID_ADMIN)
		# create universe
		self.db.create(self.cmdPool[T_UNIVERSE].new(T_UNIVERSE), OID_UNIVERSE)
		self.createUniverse()
		# save all informations
		self.db.checkpoint()
		self.msgMngr.checkpoint()
		self.clientMngr.checkpoint()

	def processTurn(self, sid):
		session = self.clientMngr.getSession(sid)
		if session.login != ADMIN_LOGIN:
			raise SecurityException('You cannot issue this command.')
		log.message("--- TURN PROCESSING STARTED ---")
		# commit player's changes
		#if ige.igeRuntimeMode:
		#	self.db.checkpoint()
		# get turn phases
		turn, turnspec, data = self.getTurnData(sid)[0]
		log.debug('Processing turn %d' % turn)
		tran = Transaction(self, session.cid, session)
		counter = 0
		# phases
		for objIDs, phases in turnspec:
			# process all objects
			for objID in objIDs:
				# process all phases
				for phase in phases:
					todo = [objID]
					t0 = time.time()
					cnt0 = self.db.statCount
					log.debug('Processing turn %d phase %d.%s' % (turn, objID, phase))
					while todo:
						tmpID = todo.pop(0)
						#@log.debug('Processing obj', tmpID)
						try:
							counter += 1
							obj = self.db[tmpID]
							method = getattr(self.cmdPool[obj.type], 'process%sPhase' % phase,)
							result = method(tran, obj, data)
							if result:
								todo.extend(result)
							obj = None
						except:
							log.warning('Cannot execute %s on %d' % (phase, tmpID))
					log.debug('STATS -- time: %.3f sec, db accesses: %d' % (time.time() - t0, tran.db.statCount - cnt0))
		log.message('Processed commands:', counter)
		# turn processing has finished
		self.turnFinished(sid)
		log.message("--- TURN PROCESSING FINISHED ---")
		return 1, None

	def getTurnData(self, sid):
		# disable command execution during turn processing
		self.status = GS_TURNINPROG
		return 1, None

	def turnFinished(self, sid):
		# notify logged player's about finished turn
		for sessionID in self.clientMngr.sessions.keys():
			session = self.clientMngr.getSession(sessionID)
			session.messages[SMESSAGE_NEWTURN] = None
		# commit only in normal mode
		log.debug("Runtime mode", ige.igeRuntimeMode)
		if ige.igeRuntimeMode:
			self.db.checkpoint()
			self.msgMngr.checkpoint()
			self.clientMngr.checkpoint()
		# enable normal operations
		self.status = GS_RUNNING
		return 1, None

	def backup(self, sid, basename):
		session = self.clientMngr.getSession(sid)
		if session.login != ADMIN_LOGIN:
			raise SecurityException('You cannot issue this command.')
		self.db.backup(basename)
		self.clientMngr.backup(basename)
		self.msgMngr.backup(basename)
		return True, None

	def createAdmin(self):
		""" Return Player object which will act as administrator of the game."""
		raise NotImplementedError

	def createUniverse(self):
		""" Create gaming universe. """
		raise NotImplementedError

	def createPlayer(self, sid, *args, **kwargs):
		raise NotImplementedError

	def removePlayer(self, sid, *args, **kwargs):
		raise NotImplementedError

	def registerPlayer(self, login, playerObj, oid = None, force = 0):
		# preconditions
		log.debug("Checking LOGIN2OID")
		if self.db[OID_I_LOGIN2OID].has_key(login) and not force:
			raise CreatePlayerException('Account already exists.')
		log.debug("Checking NAME2OID")
		if self.db[OID_I_NAME2OID].has_key(playerObj.name) and not force:
			raise CreatePlayerException('Name already exists.')
		# action
		if not oid:
			log.debug("Creating object")
			oid = self.db.create(playerObj)
		else:
			self.db.create(playerObj, id = oid)
		log.debug("Fixing indexes")
		self.db[OID_I_LOGIN2OID][login] = oid
		self.db[OID_I_NAME2OID][playerObj.name] = oid
		playerObj.oid = oid
		playerObj.owner = oid
		return oid

	def unregisterPlayer(self, playerObj):
		log.debug('unregisterPlayer', playerObj.login, playerObj.name)
		# preconditions
		if not self.db[OID_I_LOGIN2OID].has_key(playerObj.login):
			#raise ServerException('Account does not exist.')
			log.debug("Account %s does not exist" % playerObj.login)
		if not self.db[OID_I_NAME2OID].has_key(playerObj.name):
			#raise ServerException('Name does not exist.')
			log.debug("Name %s does not exist" % playerObj.name)
		# try to remove it
		try:
			del self.db[OID_I_LOGIN2OID][playerObj.login]
		except:
			log.warning("Cannot remove '%s' from LOGIN2OID index" % playerObj.login)
		try:
			del self.db[OID_I_NAME2OID][playerObj.name]
		except:
			log.warning("Cannot remove '%s' from NAME2OID index" % playerObj.name)
		try:
			self.db.delete(playerObj.oid)
		except:
			log.warning("Cannot remove player %d from database" % playerObj.oid)

	def validateClient(self, session):
		raise NotImplementedError

	def registerObject(self, cls):
		cmdObj = cls(self)
		self.cmdPool[cmdObj.typeID] = cmdObj

	def sendMessage(self, tran, sourceID, msgID, locationID, turn, data):
		#@log.debug('Message', sourceID, msgID, locationID, turn, data)
		obj = self.db[sourceID]
		# notify owner
		if obj.owner == OID_NONE:
			log.warning('OID', sourceID, 'has no owner - no target for a message')
		else:
			owner = self.db[obj.owner]
			# new style messages
			message = {
				"sender": obj.name,
				"senderID": sourceID,
				"forum": "EVENTS",
				"data": (sourceID, msgID, locationID, turn, data),
				"topic": "EVENT",
			}
			self.cmdPool[owner.type].sendAdminMsg(tran, owner, message)
			session = self.clientMngr.getSessionByCID(obj.owner)
			if session:
				session.messages[SMESSAGE_NEWMESSAGE] = None
		# notify other players
		#for oid in obj.accRights.keys():
		#	if obj.accRights[oid] >= AL_FULLINFO:
		#		if self.db.has_key(oid):
		#			target = self.db[oid]
		#			# new style messages
		#			message = {
		#				"sender": obj.name,
		#				"senderID": sourceID,
		#				"forum": "EVENTS",
		#				"data": (sourceID, msgID, locationID, turn, data),
		#				"topic": "EVENT",
		#			}
		#			self.cmdPool[target.type].sendAdminMsg(tran, target, message)
		#			# TODO send event
		#			session = self.clientMngr.getSessionByCID(oid)
		#			if session:
		#				session.messages[SMESSAGE_NEWMESSAGE] = None

	# dispatch command
	def execute(self, sid, command, oid, *args):
		#@startTime = time.time()
		log.debug('execute', sid, oid, command, args)
		# check client id
		session = self.clientMngr.getSession(sid)
		if not session.cid:
			# check if real id exists
			try:
				cid = self.db[OID_I_LOGIN2OID].get(session.login, None)
			except AttributeError:
				raise SecurityException('Not logged in.')
			log.debug('Adding cid to session', cid)
			if not cid:
				# no real id
				#@log.debug('Raising exception NoAccountException')
				raise NoAccountException('No game account exists.')
			session.cid = cid
			# validate client
			if not self.validateClient(session):
				raise GameException('Wrong version of client.')
			# notify object, that player has logged in
			player = self.db[cid]
			self.cmdPool[player.type].loggedIn(Transaction(self), player)
		# check game status (admin is allowed anytime)
		if self.status != GS_RUNNING and session.cid != OID_ADMIN:
			raise ServerStatusException(self.status)
		# check existence of the commander
		if not self.db.has_key(session.cid):
			raise GameException('This player does not exist. He/she could lose.')
		# update client's liveness
		session.touch()
		# find correct object type
		try:
			obj = self.db[oid]
		except KeyError:
			raise NoSuchObjectException('Object %d does not exist.' % oid)
		cmdObj = getattr(self.cmdPool[obj.type], command)
		# TODO check access level
		if not hasattr(cmdObj, 'public') or not cmdObj.public:
			raise SecurityException('Access denied - method is not public.')
		# get acces level of the commander
		accLevel = AL_NONE
		if obj.owner == session.cid:
			accLevel = AL_OWNER
		if session.cid == OID_ADMIN:
			accLevel = AL_ADMIN
		# TODO delete
		#tmpAL = self.getAccRights(obj, session.cid)
		#if tmpAL > accLevel:
		#	accLevel = tmpAL
		#@log.debug('access rights', accLevel, cmdObj.accLevel)
		if cmdObj.accLevel > accLevel:
			raise SecurityException('Access denied - low access level.')
		# create transaction (TODO - cache it!)
		tran = Transaction(self, session.cid, session)
		# invoke command on it
		result = apply(cmdObj, (tran, obj) + args)
		# commit transaction
		tran.commit()
		#@log.debug('result', result)
		# session messages
		#@log.debug('Messages:', session.messages.items())
		messages = session.messages.items()
		session.messages.clear()
		#@log.debug("Execution time", time.time() - startTime)
		return result, messages

	# TODO
	#def getAccRights(self, obj, cid):
	#	return obj.accRights.get(cid, AL_NONE)

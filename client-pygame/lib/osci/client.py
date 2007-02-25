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

from igeclient import IClient, IClientDB
from ige.ospace import Rules
from ige.ospace.Const import *
from ige.IDataHolder import IDataHolder
import ige, gdata, osci, math, time
from ige import log

# module globals
cmdProxy = None
db = None
callbackObj = None
lastUpdate = -1
server = None
lastClientVersion = None
lastClientRevision = None
ignoreMsgs = {}
nonexistingObj = {}

def initialize(aServer, aCallbackObj):
	global callbackObj, server
	callbackObj = aCallbackObj
	server = aServer

def reinitialize():
	global cmdProxy
	cmdProxy = None
## Authentication

def login(gameid, login, password):
	global cmdProxy, server
	if not cmdProxy:
		callbackObj.onInitConnection()
		proxy = None
		if gdata.config.proxy.http != None:
			proxy = gdata.config.proxy.http
		cmdProxy = IClient.IClient(server, proxy, msgHandler, idleHandler, 'OSClient/%s' % osci.versionString)
		cmdProxy.connect(login)
		if gdata.config.client.keepAlive != None:
			cmdProxy.keepAliveTime = int(gdata.config.client.keepAlive)
		callbackObj.onConnInitialized()
	if cmdProxy.login(gameid, login, password):
		global lastClientVersion, lastClientRevision
		try:
			result = cmdProxy.getIntroInfo(OID_UNIVERSE)
			lastClientVersion = result.lastClientVersion
			lastClientRevision = result.lastClientRevision
		except ige.NoAccountException:
			callbackObj.createGameAccount()
			return 2
		return 1
	return 0

def createAccount(login, password, nick, email):
	global cmdProxy, server
	if not cmdProxy:
		callbackObj.onInitConnection()
		proxy = None
		if gdata.config.proxy.http != None:
			proxy = gdata.config.proxy.http
		cmdProxy = IClient.IClient(server, proxy, msgHandler, idleHandler, 'OSClient/%d.%d.%d%s' % osci.version)
		cmdProxy.connect(login)
		if gdata.config.client.keepAlive != None:
			cmdProxy.keepAliveTime = int(gdata.config.client.keepAlive)
		callbackObj.onConnInitialized()
	return cmdProxy.createAccount(login, password, nick, email)

def logout():
	if cmdProxy and cmdProxy.logged:
		cmdProxy.logout()
	if db:
		log.message('OSClient', 'Saving database')
		db.save()

## Message handler

def msgHandler(mid, data):
	if ignoreMsgs.has_key(mid):
		log.debug('OSClient', 'ignoring message', mid, data)
		return
	if mid == SMESSAGE_NEWTURN:
		updateDatabase()
	elif mid == SMESSAGE_NEWMESSAGE:
		getMessages()
	elif mid == IClient.MSG_CMD_BEGIN:
		callbackObj.onCmdBegin()
	elif mid == IClient.MSG_CMD_END:
		callbackObj.onCmdEnd()
	else:
		log.debug('OSClient', 'unhandled message', mid, data)

def messageIgnore(mid):
	global ignoreMsgs
	ignoreMsgs[mid] = None

def messageEnable(mid):
	global ignoreMsgs
	if ignoreMsgs.has_key(mid):
		del ignoreMsgs[mid]

## Idle handler
def idleHandler():
	callbackObj.onWaitingForResponse()

## Updater

def updateDatabase(clearDB = 0):
	try:
		return updateDatabaseUnsafe(clearDB)
	except:
		log.warning("Cannot update database")
	# again with clear
	callbackObj.onUpdateFinished()
	messageEnable(SMESSAGE_NEWTURN)
	messageEnable(SMESSAGE_NEWMESSAGE)
	return updateDatabaseUnsafe(clearDB = 1, force = 1)

def updateDatabaseUnsafe(clearDB = 0, force = 0):
	"""Update database by fetching data from the server."""
	global lastUpdate, nonexistingObj, db
	# get real turn
	result = cmdProxy.getIntroInfo(OID_UNIVERSE)
	if not db:
		db = IClientDB.IClientDB(result.cid, result.turn)
	if clearDB:
		db.clear()
	db.turn = result.turn
	#
	if db.turn <= lastUpdate and not force:
		return
	log.message('IClient', 'Updating...')
	lastUpdate = db.turn
	nonexistingObj.clear()
	# start updating...
	messageIgnore(SMESSAGE_NEWTURN)
	messageIgnore(SMESSAGE_NEWMESSAGE)
	callbackObj.onUpdateStarting()
	current = 0
	max = 1
	# compute total objects to be fetched
	max += 6 # clear map, get messages, ...
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Deleting obsolete data..."))
	# delete selected objects
	# reset combatCounters
	for objID in db.keys():
		obj = db[objID]
		if hasattr(obj, "combatCounter"):
			obj.combatCounter = 0
		if not hasattr(obj, 'type'):
			del db[objID]
		elif obj.type in (T_FLEET, T_ASTEROID):
			del db[objID]
		elif hasattr(obj, 'owner') and obj.owner == db.playerID \
			and objID != db.playerID:
			# delete player's objects
			del db[objID]
		else:
			if hasattr(obj, "scanPwr"): obj.scanPwr = 0
			if hasattr(obj, "scannerPwr"): obj.scannerPwr = 0
	# update player
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Downloading player data..."))
	db[db.playerID] = get(db.playerID)
	player = db[db.playerID]
	# update from scanner's map
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Updating scanner..."))
	map = cmdProxy.getScannerMap(db.playerID)
	for objID in map:
		db[objID] = map[objID]
	# update player's planets and fleets
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Downloading planets and fleets data..."))
	for obj in cmdProxy.multiGetInfo(1, player.planets[:] + player.fleets[:]):
		db[obj.oid] = obj
	#~ # compute system's positions
	#~ current += 1
	#~ callbackObj.onUpdateProgress(current, max, _("Updating astronomical coordinates..."))
	#~ systems = {}
	#~ for objID in db.keys():
		#~ obj = db[objID]
		#~ if obj.type == T_SYSTEM or obj.type == T_PLANET:
			#~ if obj.type == T_SYSTEM:
				#~ galaxy = get(obj.compOf)
				#~ system = obj
			#~ else:
				#~ if obj.compOf in systems:
					#~ system = systems[obj.compOf]
				#~ else:
					#~ system = get(obj.compOf, canBePublic = 0)
					#~ systems[obj.compOf] = system
				#~ if hasattr(system, "compOf"):
					#~ galaxy = get(system.compOf)
				#~ else:
					#~ continue
			#~ angle = system.sAngle / 1000.0 + (db.turn / Rules.rotationMod) * system.dAngle / 1000.0
			#~ obj.x = galaxy.x + system.dist * math.cos(angle) / 1000.0
			#~ obj.y = galaxy.y + system.dist * math.sin(angle) / 1000.0
	#~ del systems
	# TODO: try to load allies's info
	# get messages from server
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Downloading messages..."))
	getMessages()
	# clean maps on server
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Clearing data on the server..."))
	# TODO not needed - delete cmdProxy.clearScannerMap(db.playerID)
	# finished
	log.message('IClient', 'Update finished.')
	callbackObj.onUpdateFinished()
	messageEnable(SMESSAGE_NEWTURN)
	messageEnable(SMESSAGE_NEWMESSAGE)

## Basic functions

def keepAlive(force = False):
	if cmdProxy and db:
		try:
			if force or cmdProxy.doKeepAlive():
				getMessages()
		except ige.NoAccountException:
			pass

def get(objID, forceUpdate = 0, noUpdate = 0, canBePublic = 1, publicOnly = 0):
	global nonexistingObj
	if nonexistingObj.has_key(objID) and not forceUpdate:
		return None
	if noUpdate:
		return db.get(objID, None)
	if (db.needsUpdate(objID) or forceUpdate) and not publicOnly:
		try:
			db[objID] = cmdProxy.getInfo(objID)
		except ige.SecurityException:
			if canBePublic:
				db[objID] = cmdProxy.getPublicInfo(objID)
			else:
				return db.get(objID, None)
		except ige.NoSuchObjectException:
			if db.has_key(objID):
				del db[objID]
			nonexistingObj[objID] = None
			return None
	if (db.needsUpdate(objID) or forceUpdate) and publicOnly: #for when the data you need is never anything but public
		try:
			db[objID] = cmdProxy.getPublicInfo(objID)
		except ige.NoSuchObjectException:
			if db.has_key(objID):
				del db[objID]
			nonexistingObj[objID] = None
			return None
	return db[objID]

def updateIDs(objIDs):
	delete = objIDs[:]
	for obj in cmdProxy.multiGetInfo(1, objIDs):
		db[obj.oid] = obj
		delete.remove(obj.oid)
	for objID in delete:
		if db.has_key(objID):
			del db[objID]

def getRelationTo(objID):
	obj = getPlayer()
	if obj.oid == objID:
		return REL_UNITY
	if objID == OID_NONE:
		return REL_UNDEF
	dipl = obj.diplomacyRels.get(objID, None)
	if dipl:
		return dipl.relation
	else:
		return obj.defaultRelation

def getTurn():
	return db.turn

def getFullTechInfo(techID):
	player = db[db.playerID]
	return Rules.techs[techID]

def getTechInfo(techID):
	player = db[db.playerID]
	tech = Rules.techs[techID]
	# player possess this technology
	if player.techs.has_key(techID):
		return tech

	if tech.fullInfo:
		return tech

	# player can research this technology
	canResearch = 1
	if player.race not in tech.researchRaces:
		canResearch = 0
	for tmpTechID, improvement in tech.researchRequires:
		if not player.techs.has_key(tmpTechID) or player.techs[tmpTechID] < improvement:
			canResearch = 0
			break
	for stratRes in tech.researchReqSRes:
		if player.stratRes.get(stratRes, 0) < 1:
			canResearch = 0
			break
	for tmpTechID in player.techs:
		if techID in Rules.techs[tmpTechID].researchDisables:
			canResearch = 0
			break
	if tech.level > player.techLevel:
		canResearch = 0

	if canResearch:
		result = IDataHolder()
		result.partialData = None
		for attr in ['name', 'isDiscovery', 'isStructure',
			'isProject', 'isShipEquip', 'isShipHull', 'researchMod',
			'researchTurns', 'textPreRsrch', 'researchRequires', 'subtype',
			"researchReqSRes", "researchDisables", "level", "researchRaces"]:
			setattr(result, attr, getattr(tech, attr))
		return result
	# player should know only basic params about tech
	result = IDataHolder()
	result.partialData = None
	for attr in ["name", "researchRequires", "subtype", "level", "researchRaces"]:
		setattr(result, attr, getattr(tech, attr))
	return result

def getAllTechIDs():
	return Rules.techs.keys()

def getPlayerID():
	return db.playerID

def getPlayer():
	return db[db.playerID]

def getDiplomacyWith(contactID):
	obj = getPlayer()
	dipl = obj.diplomacyRels.get(contactID, None)
	if not dipl:
		# make default
		dipl = IDataHolder()
		dipl.type = T_DIPLREL
		dipl.pacts = {
			PACT_ALLOW_CIVILIAN_SHIPS: [PACT_ACTIVE, PACT_ALLOW_CIVILIAN_SHIPS]
		}
		dipl.relation = obj.defaultRelation
		dipl.relChng = 0
		dipl.lastContact = 0
		dipl.stats = None
		dipl.contactType = CONTACT_NONE
		obj.diplomacyRels[playerID] = dipl
	return dipl

def getMessages():
	# construct list of mailboxes
	mailboxes = []
	mailboxes.append((db.playerID, getMessagesLastID(db.playerID)))
	for galaxyID in getPlayer().galaxies:
		mailboxes.append((galaxyID, getMessagesLastID(galaxyID)))
	mailboxes.append((OID_UNIVERSE, getMessagesLastID(OID_UNIVERSE)))
	# get data
	data = cmdProxy.multiGetMsgs(OID_UNIVERSE, mailboxes)
	# process
	new = 0
	now = time.time()
	for objID, messages in data:
		obj = get(objID)
		# delete old messages TODO leave this to the user
		#for messageID in obj._messages.keys():
		#	message = obj._messages[messageID]
		#	if message["time"] + Rules.messageTimeout < now:
		#		del obj._messages[messageID]
		# add new
		for message in messages:
			#@log.debug("Got message ID", message["id"])
			if message["id"] not in obj._messages:
				if message["forum"] != "OUTBOX":
					message["readed"] = 0
					message["replied"] = 0
				else:
					message["readed"] = 1
					message["replied"] = 0
				obj._messagesLastID = max(message["id"], obj._messagesLastID)
				obj._messages[message["id"]] = message
				new += 1
			else:
				log.warning("Got duplicated message", message)
	if new > 0:
		callbackObj.onNewMessages(new)
	return new

def getMessagesLastID(objID):
	obj = get(objID)
	if not hasattr(obj, "_messages"):
		log.debug("Creating _messages")
		obj._messages = {}
		obj._messagesLastID = -1
	return obj._messagesLastID

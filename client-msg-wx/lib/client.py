from igeclient import IClient, IClientDB
from ige.ospace import Rules
from ige.ospace.Const import *
from ige.IDataHolder import IDataHolder
import gdata, ige, time
from ige import log
import version as Ver

# module globals
cmdProxy = None
db = None
callbackObj = None
lastUpdate = -1
server = None
lastClientVersion = None
lastClientBuild = None
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
		cmdProxy = IClient.IClient(server, proxy, msgHandler, idleHandler, 'OSClient/%s' % Ver.versionString)
		cmdProxy.connect(login)
		if gdata.config.client.keepAlive != None:
			cmdProxy.keepAliveTime = int(gdata.config.client.keepAlive)
		callbackObj.onConnInitialized()
	if cmdProxy.login(gameid, login, password):
		global lastClientVersion, lastClientBuild
		try:
			result = cmdProxy.getIntroInfo(OID_UNIVERSE)
			lastClientVersion = result.lastClientVersion
			lastClientBuild = result.lastClientRevision
		except ige.NoAccountException:
			callbackObj.createGameAccount()
			return 2
		return 1
	return 0

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
	# get messages from server
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Downloading messages..."))
	getMessages()
	# clean maps on server
	current += 1
	callbackObj.onUpdateProgress(current, max, _("Clearing data on the server..."))
	# finished
	log.message('IClient', 'Update finished.')
	callbackObj.onUpdateFinished()
	messageEnable(SMESSAGE_NEWTURN)
	messageEnable(SMESSAGE_NEWMESSAGE)

## Basic functions

def keepAlive():
	if cmdProxy and db:
		try:
			if cmdProxy.doKeepAlive():
				getMessages()
		except ige.NoAccountException:
			pass

def get(objID, forceUpdate = 0, noUpdate = 0, canBePublic = 1):
	global nonexistingObj
	if nonexistingObj.has_key(objID) and not forceUpdate:
		return None
	if noUpdate:
		return db.get(objID, None)
	if db.needsUpdate(objID) or forceUpdate:
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
	return db[objID]

def getTurn():
	return db.turn

def getTechInfo(techID):
	player = db[db.playerID]
	tech = Rules.techs[techID]
	# player possess this technology
	if player.techs.has_key(techID):
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
	for attr in ['name', 'researchRequires', 'subtype', "level"]:
		setattr(result, attr, getattr(tech, attr))
	return result

def getPlayerID():
	return db.playerID

def getPlayer():
	return db[db.playerID]

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

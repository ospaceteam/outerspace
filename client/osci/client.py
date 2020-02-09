#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import os.path

from igeclient import IClient, IClientDB
from ige.ospace import Rules
import ige.ospace.Const as Const
from ige.IDataHolder import IDataHolder
import ige, gdata, osci, math, time
from ige import log

# module globals
cmdProxy = None
db = None
callbackObj = None
lastUpdate = -1
server = None
serverVersion = None
ignoreMsgs = {}
nonexistingObj = {}
options = None
account = None

def initialize(aServer, aCallbackObj, anOptions):
    global callbackObj, server, options
    callbackObj = aCallbackObj
    server = aServer

    options = anOptions
    initCmdProxy(options.heartbeat)

def reinitialize():
    global cmdProxy
    cmdProxy = None
    initCmdProxy(options.heartbeat)

def initCmdProxy(keepAliveTime):
    global cmdProxy, server
    if not cmdProxy:
        callbackObj.onInitConnection()
        proxy = None
        if gdata.config.proxy.http != None:
            proxy = gdata.config.proxy.http
        cmdProxy = IClient.IClient(server, proxy, msgHandler, idleHandler, 'OSClient/%s' % ige.version.versionString, keepAliveTime)
        callbackObj.onConnInitialized()
        cmdProxy.connect()

## Authentication

def login(gameid, login, password):
    global account
    if gdata.config.client.keepAlive != None:
        cmdProxy.keepAliveTime = int(gdata.config.client.keepAlive)
    if cmdProxy.login(gameid, login, password):
        account = cmdProxy.getAccountData()
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
    global db, lastUpdate, account
    if cmdProxy and cmdProxy.logged:
        cmdProxy.logout()
    saveDB()
    db = None
    account = None
    lastUpdate = -1

def saveDB():
    if db:
        log.message('OSClient', 'Saving database')
        db.save()

    ## Message handler

def msgHandler(mid, data):
    if ignoreMsgs.has_key(mid):
        log.debug('OSClient', 'ignoring message', mid, data)
        return
    if mid == Const.SMESSAGE_NEWTURN:
        updateDatabase()
    elif mid == Const.SMESSAGE_NEWMESSAGE:
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
    messageEnable(Const.SMESSAGE_NEWTURN)
    messageEnable(Const.SMESSAGE_NEWMESSAGE)
    return updateDatabaseUnsafe(clearDB = 1, force = 1)

def updateDatabaseUnsafe(clearDB = 0, force = 0):
    """Update database by fetching data from the server."""
    global lastUpdate, nonexistingObj, db
    # get real turn
    result = cmdProxy.getIntroInfo(Const.OID_UNIVERSE)
    if not db:
        dbLocation = os.path.join(options.configDir, 'player_data')
        db = IClientDB.IClientDB(result.cid, result.turn, dbLocation, cmdProxy.gameID)
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
    messageIgnore(Const.SMESSAGE_NEWTURN)
    messageIgnore(Const.SMESSAGE_NEWMESSAGE)
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
        elif obj.type == Const.T_FLEET:
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
    # TODO: try to load allies's info
    # get messages from server
    current += 1
    callbackObj.onUpdateProgress(current, max, _("Downloading messages..."))
    getMessages()
    log.message('IClient', 'Update finished.')
    callbackObj.onUpdateFinished()
    messageEnable(Const.SMESSAGE_NEWTURN)
    messageEnable(Const.SMESSAGE_NEWMESSAGE)

## Basic functions

def keepAlive(force = False):
    if cmdProxy:
        try:
            if force or cmdProxy.doKeepAlive():
                if db:
                    # client is logged into the game
                    getMessages()
                else:
                    # client is in player selection / galaxy booking phase
                    cmdProxy.keepAlive()
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
        return Const.REL_UNITY
    if objID == Const.OID_NONE:
        return Const.REL_UNDEF
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
    if techID in player.techs or tech.fullInfo:
        return tech

    # player can research this technology
    canResearch = 1
    if player.race not in tech.researchRaces:
        canResearch = 0
    for tmpTechID, improvement in tech.researchRequires:
        if tmpTechID not in player.techs or player.techs[tmpTechID] < improvement:
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
        for attr in ["id", 'name', 'isDiscovery', 'isStructure',
            'isProject', 'isShipEquip', 'isShipHull', 'researchMod',
            'researchTurns', 'textPreRsrch', 'researchRequires', 'subtype',
            "researchReqSRes", "researchDisables", "level", "researchRaces"]:
            setattr(result, attr, getattr(tech, attr))
        return result
    # player should know only basic params about tech
    result = IDataHolder()
    result.partialData = None
    for attr in ["id", "name", "researchRequires", "subtype", "level", "researchRaces"]:
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
        dipl.type = Const.T_DIPLREL
        dipl.pacts = {
            Const.PACT_ALLOW_CIVILIAN_SHIPS: [Const.PACT_ACTIVE, Const.PACT_ALLOW_CIVILIAN_SHIPS]
        }
        dipl.relation = obj.defaultRelation
        dipl.relChng = 0
        dipl.lastContact = 0
        dipl.stats = None
        dipl.contactType = Const.CONTACT_NONE
        obj.diplomacyRels[playerID] = dipl
    return dipl

def getMessages():
    # construct list of mailboxes
    mailboxes = []
    mailboxes.append((db.playerID, getMessagesLastID(db.playerID)))
    galaxyID = getPlayer().galaxy
    if galaxyID:
        mailboxes.append((galaxyID, getMessagesLastID(galaxyID)))
    mailboxes.append((Const.OID_UNIVERSE, getMessagesLastID(Const.OID_UNIVERSE)))
    # get data
    data = cmdProxy.multiGetMsgs(Const.OID_UNIVERSE, mailboxes)
    # process
    new = 0
    now = time.time()
    for objID, messages in data:
        obj = get(objID)
        # delete old messages TODO leave this to the user
        #for messageID in obj._messages.keys():
        #    message = obj._messages[messageID]
        #    if message["time"] + Rules.messageTimeout < now:
        #        del obj._messages[messageID]
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
    obj = get(objID, publicOnly = 1)
    if not hasattr(obj, "_messages"):
        log.debug("Creating _messages")
        obj._messages = {}
        obj._messagesLastID = -1
    return obj._messagesLastID

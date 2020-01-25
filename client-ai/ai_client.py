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

from igeclient import IClient, IClientDB
from ige.ospace import Const
from ige.ospace import Rules
from ige.IDataHolder import IDataHolder
import ige, gdata, osci, math, time
from ige import log

# module globals
cmdProxy = None
db = None
lastUpdate = -1
server = None
nonexistingObj = {}
options = None

def initialize(aServer, anOptions):
    global server, options
    server = aServer
    options = anOptions
    initCmdProxy()

def initCmdProxy():
    global cmdProxy, server
    if not cmdProxy:
        proxy = None
        if gdata.config.proxy.http != None:
            proxy = gdata.config.proxy.http
        cmdProxy = IClient.IClient(server, proxy, None, None, 'OSClient/%s' % ige.version.versionString)

## Authentication

def login(gameid, login, password):
    cmdProxy.connect()
    if cmdProxy.login(gameid, login, password):
        return 1
    return 0

def logout():
    global db, lastUpdate
    if cmdProxy and cmdProxy.logged:
        cmdProxy.logout()
    saveDB()
    db = None
    lastUpdate = -1

def saveDB():
    if db:
        log.message('OSClient', 'Saving database')
        db.save()

## Updater

def updateDatabase(clearDB = 0):
    try:
        return updateDatabaseUnsafe(clearDB)
    except:
        log.warning("Cannot update database")
    return updateDatabaseUnsafe(clearDB = 1, force = 1)

def updateDatabaseUnsafe(clearDB = 0, force = 0):
    """Update database by fetching data from the server."""
    global lastUpdate, nonexistingObj, db
    # get real turn
    result = cmdProxy.getIntroInfo(Const.OID_UNIVERSE)
    if not db:
        db = IClientDB.IClientDB(result.cid, result.turn, options.configDir, cmdProxy.gameID)
    if clearDB:
        db.clear()
    db.turn = result.turn
    #
    if db.turn <= lastUpdate and not force:
        return
    log.message('IClient', 'Updating...')
    lastUpdate = db.turn
    nonexistingObj.clear()
    current = 0
    max = 1
    # compute total objects to be fetched
    max += 6 # clear map, get messages, ...
    current += 1
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
    db[db.playerID] = get(db.playerID)
    player = db[db.playerID]
    # update from scanner's map
    scannerMap = cmdProxy.getScannerMap(db.playerID)
    for objID in scannerMap:
        db[objID] = scannerMap[objID]
    # update player's planets and fleets
    for obj in cmdProxy.multiGetInfo(1, player.planets[:] + player.fleets[:]):
        db[obj.oid] = obj
    # finished
    log.message('IClient', 'Update finished.')

## Basic functions

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


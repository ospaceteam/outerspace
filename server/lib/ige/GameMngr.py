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

# Game manager
# Multiple instances can be created (one for each game)
import os
import os.path
import time
import random, hashlib # TODO: remove after 0.5.74 release

import ige
import log
import Const

from SQLiteDatabase import Database
from Index import Index
from IObject import IDataHolder
from Transaction import Transaction

class GameMngr:

    def __init__(self, gameID, config, clientMngr, msgMngr, database, configDir, gameName = None):
        log.debug("Runtime mode", ige.igeRuntimeMode)
        self.status = Const.GS_INIT
        self.gameID = gameID
        self.gameName = gameName or gameID
        self.clientMngr = clientMngr
        self.msgMngr = msgMngr
        self.cmdPool = {}
        self.db = database
        self.config = config
        self.configDir = configDir
        # register command objects
        # None here

    def init(self):
        pass

    def start(self):
        if self.status == Const.GS_RUNNING:
            return
        # start timer
        self.status = Const.GS_RUNNING

    def stop(self, checkpoint = 1):
        if self.status == Const.GS_STOPPED:
            return
        # stop timer
        self.status = Const.GS_STOPPED
        if checkpoint:
            self.db.checkpoint()
            self.msgMngr.checkpoint()
            self.clientMngr.checkpoint()

    def shutdown(self):
        if self.status == Const.GS_SDOWN:
            return
        self.stop(checkpoint = 0)
        self.status = Const.GS_SDOWN
        self.db.shutdown()

    def upgrade(self):
        oldStatus = self.status
        self.status = Const.GS_MAINT
        tran = Transaction(self, Const.OID_ADMIN)
        # used objects
        objIDs = {}
        for objID in self.db.keys():
            objIDs[objID] = None
        del objIDs[1]
        del objIDs[Const.OID_ADMIN]
        del objIDs[Const.OID_I_LOGIN2OID]
        # stats
        types = {}
        typesMin = {}
        typesMax = {}
        typesSum = {}
        # TODO: remove after 0.5.74
        # hash passwords in database
        for accountID in self.clientMngr.accounts.keys():
            account = self.clientMngr.accounts[accountID]
            if hasattr(account, 'passwdHashed'):
                continue
            if isinstance(account.passwd, unicode):
                account.passwd = account.passwd.encode('utf-8')
            elif not isinstance(account.passwd, str):
                # unexpected!
                raise TypeError
            # hash passwords of normal players
            if account.isAI or account.login == Const.ADMIN_LOGIN:
                account.passwdHashed = False
            else:
                account.passwdHashed = True
                account.setPassword = account.passwd
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
            size = self.db.getItemLength(id)
            typesMin[obj.type] = min(typesMin.get(obj.type, 1000000), size)
            typesMax[obj.type] = max(typesMax.get(obj.type, 0), size)
            typesSum[obj.type] = typesSum.get(obj.type, 0) + size
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
            log.debug("Object type %d:" % t)
            log.debug("  occurences    : %d" % types[t])
            log.debug("  size interval : %d - %d bytes" % (typesMin[t], typesMax[t]))
            log.debug("  total size    : %d (avg %d) bytes" % (typesSum[t], typesSum[t] / types[t]))
        self.status = oldStatus

    def reset(self):
        # cleanup database
        self.db.clear()
        self.msgMngr.clear()
        # create indexes
        self.db.create(Index(), Const.OID_I_LOGIN2OID)
        # create admin
        self.registerPlayer(Const.ADMIN_LOGIN, self.createAdmin(), Const.OID_ADMIN)
        # create universe
        self.createUniverse()
        # save all informations
        self.db.checkpoint()
        self.msgMngr.checkpoint()
        self.clientMngr.checkpoint()

    def processTurn(self, sid, turns = 1):
        session = self.clientMngr.getSession(sid)
        if session.login != Const.ADMIN_LOGIN:
            raise ige.SecurityException('You cannot issue this command.')
        for turn in xrange(turns):
            log.message("--- TURN PROCESSING STARTED ---")
            # commit player's changes
            #if ige.igeRuntimeMode:
            #    self.db.checkpoint()
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
        self.status = Const.GS_TURNINPROG
        return 1, None

    def turnFinished(self, sid):
        # notify logged player's about finished turn
        for sessionID in self.clientMngr.sessions.keys():
            session = self.clientMngr.getSession(sessionID)
            session.messages[Const.SMESSAGE_NEWTURN] = None
        # commit only in normal mode
        log.debug("Runtime mode", ige.igeRuntimeMode)
        if ige.igeRuntimeMode:
            self.db.checkpoint()
            self.msgMngr.checkpoint()
            self.clientMngr.checkpoint()
        # enable normal operations
        self.status = Const.GS_RUNNING
        return 1, None

    def backup(self, sid, basename):
        session = self.clientMngr.getSession(sid)
        if session.login != Const.ADMIN_LOGIN:
            raise ige.SecurityException('You cannot issue this command.')
        self.db.backup(basename)
        self.clientMngr.backup(basename)
        self.msgMngr.backup(basename)
        return True, None

    def commitDatabases(self, sid):
        session = self.clientMngr.getSession(sid)
        if session.login != Const.ADMIN_LOGIN:
            raise ige.SecurityException('You cannot issue this command.')
        self.db.checkpoint()
        self.clientMngr.checkpoint()
        self.msgMngr.checkpoint()
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

    def selectPlayer(self, sid, playerID):
        """ Selects which of the player objects of the account is going to be
        used for this particular session."""

        session = self.clientMngr.getSession(sid)
        if session.cid:
            raise ige.GameException('You already selected a player object.')
        try:
            accounts_player_objects = self.db[Const.OID_I_LOGIN2OID].get(session.login, [])
        except AttributeError:
            raise ige.SecurityException('Not logged in.')

        if playerID not in accounts_player_objects:
            raise ige.NoAccountException('Player object not on this account.')

        log.debug('Adding cid to session', playerID)
        session.cid = playerID
        # validate client
        if not self.validateClient(session):
            raise ige.GameException('Wrong version of client.')
        # notify object, that player has logged in
        player = self.db[playerID]
        self.cmdPool[player.type].loggedIn(Transaction(self), player)
        return True, None

    def registerPlayer(self, login, playerObj, oid = None, force = 0):
        raise NotImplementedError

    def unregisterPlayer(self, playerObj):
        log.debug('unregisterPlayer', playerObj.login, playerObj.name)
        # preconditions
        if not self.db[Const.OID_I_LOGIN2OID].has_key(playerObj.login):
            log.debug("Account %s does not exist" % playerObj.login)
        # try to remove it
        try:
            self.db[Const.OID_I_LOGIN2OID][playerObj.login].remove(playerObj.oid)
        except:
            log.warning("Cannot remove '%s' from LOGIN2OID index" % playerObj.login)
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
        if obj.owner == Const.OID_NONE:
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
                session.messages[Const.SMESSAGE_NEWMESSAGE] = None

    # dispatch command
    def execute(self, sid, command, oid, *args):
        #@startTime = time.time()
        log.debug('execute', sid, oid, command, args)
        # check client id
        session = self.clientMngr.getSession(sid)
        if not session.cid:
            raise ige.SecurityException('No player object selected.')
        if not self.validateClient(session):
            raise ige.GameException('Wrong version of client.')
        # check game status (admin is allowed anytime)
        if self.status != Const.GS_RUNNING and session.cid != Const.OID_ADMIN:
            raise ige.ServerStatusException(self.status)
        # check existence of the commander
        if not self.db.has_key(session.cid):
            raise ige.GameException('This player does not exist. He/she could lose.')
        # update client's liveness
        session.touch()
        # find correct object type
        try:
            obj = self.db[oid]
        except KeyError:
            raise ige.NoSuchObjectException('Object %d does not exist.' % oid)
        cmdObj = getattr(self.cmdPool[obj.type], command)
        if not hasattr(cmdObj, 'public') or not cmdObj.public:
            raise ige.SecurityException('Access denied - method is not public.')
        # get acces level of the commander
        accLevel = Const.AL_NONE
        if obj.owner == session.cid:
            accLevel = Const.AL_OWNER
        if session.cid == Const.OID_ADMIN:
            accLevel = Const.AL_ADMIN
        #@log.debug('access rights', accLevel, cmdObj.accLevel)
        if cmdObj.accLevel > accLevel:
            raise ige.SecurityException('Access denied - low access level.')
        # create transaction (TODO - cache it!)
        tran = Transaction(self, session.cid, session)
        # invoke command on it
        result = cmdObj(*(tran, obj) + args)
        # commit transaction
        tran.commit()
        #@log.debug('result', result)
        # session messages
        #@log.debug('Messages:', session.messages.items())
        messages = session.messages.items()
        session.messages.clear()
        #@log.debug("Execution time", time.time() - startTime)
        return result, messages


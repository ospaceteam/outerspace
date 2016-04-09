#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
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

import os
import hashlib
import random
import time
import log
from ige import SecurityException
from ige.Const import ADMIN_LOGIN
import Authentication

class Account:

    def __init__(self):
        # credentials
        self.login = None
        self.nick = None
        self.passwd = None
        # account options
        self.lastLogin = 0
        self.blockedUntil = -1 # -1 for not blocked, > 0 for blocked
        self.blocked = 0 # 1 for blocked account
        self.confToken = None # e-mail confirmation token, if None e-mail has been confirmed
        self.hostIDs = {} # hostids and times

    def addHostID(self, hostID):
        if hostID:
            self.hostIDs[hostID] = time.time()

class ClientMngr:

    def __init__(self, database, authMethod, configDir, metaserver = None):
        self.configDir = configDir
        self.authMethod = authMethod
        self.metaserver = metaserver
        if not self.authMethod:
            self.authMethod = Authentication.defaultMethod
        self._filename = os.path.join(self.configDir, 'accounts')
        self.sessions = {}
        #
        self.accounts = database
        # create nick to account mapping
        self.nick2login = database.get("**nick2login**", Mapping())
        # create special key
        if not self.accounts.has_key(ADMIN_LOGIN):
            log.message("No administator account found! (looking for '%s')" % ADMIN_LOGIN)
            log.message("Creating default account")
            self.createAccount(None, ADMIN_LOGIN, "tobechanged", "Administrator", "nospam@nospam.com")
        password = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()
        open(os.path.join(self.configDir, "token"), "w").write(password)
        self.accounts[ADMIN_LOGIN].passwd = password
        # tokens to provide player identification
        # to external parts of server (Galaxer)
        self.tokens = {}

    def shutdown(self):
        self.accounts.shutdown()

    def checkpoint(self):
        self.accounts.checkpoint()

    def backup(self, basename):
        self.accounts.backup(basename)

    def exists(self, login):
        return self.accounts.has_key(str(login))

    def getAccountByNick(self, nick, default = None):
        if not self.nick2login.has_key(nick):
            return default
        return self.accounts[self.nick2login[str(nick)]]

    def __getitem__(self, login):
        return self.accounts[str(login)]

    def createAccount(self, sid, login, passwd, nick, email):
        log.message('Creating account', login, nick, email)
        login = login.strip()
        passwd = passwd.strip()
        nick = nick.strip()
        # check requirement
        if len(login) < 4:
            raise SecurityException('Login is too short.')
        if len(passwd) < 4:
            raise SecurityException('Password is too short.')
        if len(nick) < 4:
            raise SecurityException('Nick is too short.')
        # check login, nick and uid
        for key in self.accounts.keys():
            account = self.accounts[key]
            if account.login == login:
                raise SecurityException('Login already used.')
            elif account.nick == nick:
                raise SecurityException('Nick already used.')
            elif account.email == email:
                raise SecurityException('E-mail already used.')
        # create account
        account = Account()
        # update
        account.login = login
        account.passwd = passwd
        account.nick = nick
        account.email = email
        account.confToken = hashlib.md5('%s%s%d' % (login, email, time.time())).hexdigest()
        self.accounts.create(account, id = str(account.login))
        self.nick2login[account.nick] = account.login
        log.message('Account created, confirmation token:', account.confToken)
        # TODO send confirmation token to the email address
        return 1, None

    def createAiAccount(self, sid, login, passwd, nick):
        self.accounts.delete(login)
        log.message('Creating AI account', login, nick)
        login = login.strip()
        passwd = passwd.strip()
        nick = nick.strip()
        # create account
        account = Account()
        # update
        account.login = login
        account.passwd = passwd
        account.nick = nick
        account.email = None
        account.confToken = None
        self.accounts.create(account, id = str(account.login))
        self.nick2login[account.nick] = account.login
        log.message('AI account created')
        return 1, None

    def removeAiAccount(self,login):
        self.accounts.delete(login)
        return 1, None

    def hello(self, sid, login, clientId):
        log.debug(clientId, 'connected. User', repr(login))
        login = str(login)
        # create sort of cookie
        while 1:
            sid = hashlib.sha256(str(random.random())).hexdigest()
            if not self.sessions.has_key(sid):
                break
        challenge = Authentication.getWelcomeString(self.authMethod)
        session = Session(sid)
        session.challenge = challenge
        session.clientIdent = clientId
        self.sessions[sid] = session
        account = self.accounts.get(login, None)
        return (sid, challenge), None

    def login(self, sid, login, cpasswd, hostID):
        login = login.strip()
        if not login:
            raise SecurityException("Specify login, please.")
        if login in ():
            raise SecurityException("Account blocked")
        log.debug(sid, 'login', repr(login), 'hostid', hostID)
        login = str(login)
        challenge = self.sessions[sid].challenge
        account = None
        # use metaserver login if metaserver is defined
        if self.metaserver:
            result = self.metaserver.verifyPassword(login, Authentication.processUserPassword(cpasswd, challenge))
            if result:
                account = Account()
                account.login = login
                account.nick = result["nick"]
                account.email = result["email"]
                log.debug("User", login, "has valid metaserver account")
            #else:
            #    raise SecurityException("Wrong login and/or password.")
        # local login
        # TBD: option to disable local login completely
        if not account:
            log.debug("Trying local login for user", login)
            if not self.accounts.has_key(login):
                raise SecurityException('Wrong login and/or password.')
            account = self.accounts[login]
            if not Authentication.verify(cpasswd, account.passwd, challenge):
                raise SecurityException('Wrong login and/or password.')
        # setup session
        self.sessions[sid].setAttrs(account.login, account.nick, account.email)
        account.lastLogin = time.time()
        account.addHostID(hostID)
        self.tokens[sid] = hashlib.md5(str(random.random())).hexdigest()
        return 1, None

    def getToken(self, sid):
        return self.tokens[sid], None

    def getSession(self, sid):
        session = self.sessions.get(sid, None)
        if not session:
            raise SecurityException('No such session id.')
        return session

    def getSessionByCID(self, cid):
        # TODO more effective - used by GameMngr.sendMessage
        for sid in self.sessions.keys():
            session = self.sessions[sid]
            if session.cid == cid:
                return session
        return None

    def getSessionByToken(self, sid, token):
        # check admin
        session = self.getSession(sid)
        if session.login != ADMIN_LOGIN:
            raise SecurityException('You cannot issue this command.')
        for sid in self.tokens:
            if self.tokens[sid] == token:
                return self.getSession(sid), None
        return 0, None

    def logout(self, sid):
        session = self.sessions.get(sid, None)
        if session:
            try:
                log.debug(sid, 'logout', self.sessions[sid].login)
            except AttributeError:
                pass
            del self.sessions[sid]
            del self.tokens[sid]
            return 1, None
        else:
            raise SecurityException('No such session id.')

    def changePassword(self, sid, old, new):
        session = self.sessions[sid]
        if session:
            if self.accounts[session.login].passwd == old:
                self.accounts[session.login].passwd = new
                return 1, None
            else:
                raise SecurityException('Wrong password.')
        else:
            raise SecurityException('No such session id.')

    def cleanupSessions(self, sid):
        session = self.sessions.get(sid, None)
        if session:
            log.debug('cleaning up sessions')
            now = time.time()
            deleted = 0
            for id in self.sessions.keys():
                if self.sessions[id].timeout < now:
                    log.debug("Deleting session", self.sessions[id].sid, getattr(self.sessions[id], "login", "<unknown>"))
                    del self.sessions[id]
                    deleted += 1
            log.debug('cleanup finished (%d active, %d deleted)' % (len(self.sessions), deleted))
            return None, None
        else:
            raise SecurityException('No such session id.')

    def exportAccounts(self, sid):
        # check admin
        session = self.getSession(sid)
        if session.login != ADMIN_LOGIN:
            raise SecurityException('You cannot issue this command.')
        # export accounts
        f = open(os.path.join(self.configDir,"accounts.txt"), "w")
        for account in self.accounts.keys():
            if account == "**nick2login**": continue
            account = self.accounts[account]
            print >>f, "%s\t%s\t%s\t%s" % (
                account.nick.encode("utf-8"),
                account.login.encode("utf-8"),
                account.passwd.encode("utf-8"),
                account.email.encode("utf-8")
            )
        f.close()
        return None, None

    def serverShutdown(self, sid):
        # check admin
        session = self.getSession(sid)
        if session.login != ADMIN_LOGIN:
            raise SecurityException('You cannot issue this command.')
        log.message('Shutting down server')
        import ige.RPCServer
        ige.RPCServer.running = 0
        return 1, None

    # new rpc interface wrappers
    def rpc_hello(self, login, clientId):
        return self.hello(None, login, clientId)[0]

    def rpc_login(self, sid, login, cpasswd, hostID):
        return self.login(sid, login, cpasswd, hostID)[0]

    def rpc_logout(self, sid):
        return self.logout(sid)[0]

    def rpc_createAccount(self, sid, login, passwd, nick, email):
        return self.createAccount(sid, login, passwd, nick, email)[0]

# Session class keeps various session data
class Session:

    def __init__(self, sid):
        self.cid = None
        self.sid = sid
        self.messages = {}
        self.touch()

    def setAttrs(self, login, nick, email):
        self.login = login
        self.nick = nick
        self.email = email

    def touch(self):
        # 10 minutes timeout of session
        self.timeout = time.time() + 10 * 60

class Mapping(dict):
    pass

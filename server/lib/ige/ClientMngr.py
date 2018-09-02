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

import os
import hashlib
import random
import time
import log
import ige
from ige import SecurityException
from ige.Const import ADMIN_LOGIN
import Authentication
from account import Account, AIAccount, AdminAccount, passwordGen
from ai_parser import AIList
from IDataHolder import IDataHolder

class ClientMngr:

    def __init__(self, database, authMethod, configDir):
        self.configDir = configDir
        self.authMethod = authMethod
        if not self.authMethod:
            self.authMethod = Authentication.defaultMethod
        if ige.igeRuntimeMode == 1:
            Authentication.init(self.authMethod, 2048)
        elif ige.igeRuntimeMode == 0:
            # it is minimum to cater for AI generated passwords
            Authentication.init(self.authMethod, 512)
        self._filename = os.path.join(self.configDir, 'accounts')
        self.sessions = {}
        #
        self.accounts = database
        self._initAdminAccount()
        self.generateAIList()

    def shutdown(self):
        self.accounts.shutdown()

    def checkpoint(self):
        self.accounts.checkpoint()

    def backup(self, basename):
        self.accounts.backup(basename)

    def exists(self, login):
        return self.accounts.has_key(str(login))

    def __getitem__(self, login):
        return self.accounts[str(login)]

    def _initAdminAccount(self):
        # create special key

        if self.accounts.has_key(ADMIN_LOGIN):
            self.accounts[ADMIN_LOGIN].passwdHashed = False # Needs plaintext login from token
            password = passwordGen()
            self.accounts[ADMIN_LOGIN].setPassword(password)
        else:
            log.message("No administator account found! (looking for '%s')" % ADMIN_LOGIN)
            log.message("Creating default account")
            # create account
            account = AdminAccount()
            # update
            password = account.passwd
            self.accounts.create(account, id = str(account.login))
        with open(os.path.join(self.configDir, "token"), "w") as tokenFile:
            tokenFile.write(password)

    def createAccount(self, sid, login, safePasswd, nick, email):
        log.message('Creating account', login, nick, email)
        session = self.getSession(sid)
        plainPassword = Authentication.unwrapUserPassword(safePasswd, session.challenge)
        login = login.strip()
        plainPassword = plainPassword.strip()
        nick = nick.strip()
        # check requirement
        if len(login) < ige.Const.ACCOUNT_LOGIN_MIN_LEN:
            raise SecurityException('Login is too short.')
        if len(plainPassword) < ige.Const.ACCOUNT_PASSWD_MIN_LEN:
            raise SecurityException('Password is too short.')
        if len(nick) < ige.Const.ACCOUNT_NICK_MIN_LEN:
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
        account = Account(login, nick, email, plainPassword)
        # update
        self.accounts.create(account, id = str(account.login))
        log.message('Account created, confirmation token:', account.confToken)
        # TODO send confirmation token to the email address
        return 1, None

    def createAIAccount(self, login, nick, aiType):
        if self.accounts.has_key(login):
            log.message('AI account already exists, no work needed.', login, nick)
            password = self.accounts[login].passwd
            return password, None

        log.message('Creating AI account', login, nick)
        login = login.strip()
        nick = nick.strip()
        # create account
        account = AIAccount(login, nick, aiType)
        # update
        self.accounts.create(account, id = str(account.login))
        log.message('AI account created')
        self.generateAIList()
        return 1, None

    def generateAIList(self):
        aiList = AIList(self.configDir)
        aiList.removeAll()
        for login in self.accounts.keys():
            account = self.accounts[login]
            if not account.isAI:
                continue
            aiList.add(login, account.passwd, account.aiType)
        aiList.save()
        log.message('AI list regenerated')

    def removeAIAccount(self, login):
        self.accounts.delete(login)
        self.generateAIList()
        return 1, None

    def resetAIAccounts(self):
        for login in self.accounts.keys():
            account = self.accounts[login]
            if account.isAI:
                self.accounts.delete(login)
        self.generateAIList()
        return 1, None

    def hello(self, sid, clientId):
        log.debug(clientId, 'connected. User', repr(clientId))
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
        return (sid, challenge), None

    def login(self, sid, login, safePassword, hostID):
        login = login.strip()
        if not login:
            raise SecurityException("Specify login, please.")
        if login in ():
            raise SecurityException("Account blocked")
        log.debug(sid, 'login', repr(login), 'hostid', hostID)
        login = str(login)
        challenge = self.sessions[sid].challenge
        log.debug("Trying local login for user", login)
        if not self.accounts.has_key(login):
            raise SecurityException('Wrong login and/or password.')
        account = self.accounts[login]
        plainPassword = Authentication.unwrapUserPassword(safePassword, challenge)
        if not account.verifyPassword(plainPassword):
            raise SecurityException('Wrong login and/or password.')
        # setup session
        self.sessions[sid].setAttrs(account.login, account.nick, account.email)
        account.lastLogin = time.time()
        account.addHostID(hostID)
        return 1, None

    def getAccountData(self, sid):
        session = self.getSession(sid)
        result = IDataHolder()
        result.login = session.login
        result.nick = session.nick
        result.email = session.email
        return result, None

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

    def logout(self, sid):
        session = self.sessions.get(sid, None)
        if session:
            try:
                log.debug(sid, 'logout', self.sessions[sid].login)
            except AttributeError:
                pass
            del self.sessions[sid]
            return 1, None
        else:
            raise SecurityException('No such session id.')

    def changePassword(self, sid, safeOld, safeNew):
        session = self.sessions[sid]
        if not session:
            raise SecurityException('No such session id.')
        challenge = session.challenge
        account = self.accounts[session.login]
        oldPassword = Authentication.unwrapUserPassword(safeOld, challenge)
        newPassword = Authentication.unwrapUserPassword(safeNew, challenge)
        if not account.verifyPassword(oldPassword):
            raise SecurityException('Wrong login and/or password.')
        if len(newPassword) < ige.Const.ACCOUNT_PASSWD_MIN_LEN:
            raise SecurityException('Password is too short.')
        account.setPassword(newPassword)
        log.debug('Password of account {0} successfully changed.'.format(session.login))
        return None, None

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

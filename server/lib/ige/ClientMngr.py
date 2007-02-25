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

import os
import md5
import random
import time
import log
from ige import SecurityException
from ige.Const import ADMIN_LOGIN
import sha

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

	def __init__(self, database):
		self._filename = os.path.join('var', 'accounts')
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
		password = sha.new(str(random.randrange(0, 1e10))).hexdigest()
		open(os.path.join("var", "token"), "w").write(password)
		self.accounts[ADMIN_LOGIN].passwd = password

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
		account.confToken = md5.new('%s%s%d' % (login, email, time.time())).hexdigest()
		self.accounts.create(account, id = str(account.login))
		self.nick2login[account.nick] = account.login
		log.message('Account created, confirmation token:', account.confToken)
		# TODO send confirmation token to the email address
		return 1, None

	def hello(self, sid, login, clientId):
		log.debug(clientId, 'connected. User', repr(login))
		login = str(login)
		# create sort of cookie
		while 1:
			sid = md5.new(str(time.time())).hexdigest()[:8]
			if not self.sessions.has_key(sid):
				break
		challenge = 'IGEServer@%f' % time.time()
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
		if not self.accounts.has_key(login):
			raise SecurityException('Wrong login and/or password.')

		account = self.accounts[login]
		challenge = self.sessions[sid].challenge
		if md5.new(account.passwd + challenge).hexdigest() != cpasswd:
			raise SecurityException('Wrong login and/or password.')
		self.sessions[sid].setAttrs(account.login, account.nick, account.email)
		account.lastLogin = time.time()
		account.addHostID(hostID)
		return 1, None

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
					del self.sessions[id]
					deleted += 1
			log.debug('cleanup finished (%d active, %d deleted)' % (len(self.sessions), deleted))
			return None, None
		else:
			raise SecurityException('No such session id.')

	def exportAccounts(self, sid):
		# check admin
		session = self.getSession(sid)
		if session.login != "admin":
			raise SecurityException('You cannot issue this command.')
		# export accounts
		f = open("var/accounts.txt", "w")
		for account in self.accounts.keys():
			if account == "**nick2login**": continue
			account = self.accounts[account]
			print >>f, "%s\t%s\t%s\t%s" % (
				account.nick,
				account.login,
				account.passwd,
				account.email
			)
		f.close()
		return None, None

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

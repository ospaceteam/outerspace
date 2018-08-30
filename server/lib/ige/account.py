#
#  Copyright 2001 - 2018 Ludek Smid [http://www.ospace.net/]
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

import hashlib
import random
import time

class Account(object):

    def __init__(self, login, nick, email, passwd, passwdHash = "sha256"):
        self._passwdSalt = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()
        # credentials
        self.login = login
        self.nick = nick
        self.email = email
        self.passwdHash = passwdHash
        self.passwd = self.hashPassword(passwd)
        # account options
        self.lastLogin = 0
        self.blockedUntil = -1 # -1 for not blocked, > 0 for blocked
        self.blocked = 0 # 1 for blocked account
        self.confToken = hashlib.md5('%s%s%d' % (login, email, time.time())).hexdigest() # when None, it's confirmed TODO make it work
        self.hostIDs = {} # hostids and times
        self.isAI = False

    def addHostID(self, hostID):
        if hostID:
            self.hostIDs[hostID] = time.time()

    def hashPassword(self, plainPassword):
        if self.passwdHash is None:
            return plainPassword
        elif self.passwdHash == "sha256":
            return hashlib.sha256(self._passwdSalt + plainPassword).hexdigest()

class AIAccount(Account):

    def __init__(self, login, nick, aiType):
        password = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()
        Account.__init__(self, login, nick, None, password, passwdHash = None)

        self.isAI = True
        self.aiType = aiType
        self.galaxyNames = []

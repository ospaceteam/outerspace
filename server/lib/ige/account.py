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
import os
import time

from passlib.context import CryptContext

import ige.Const as Const

CONTEXT = CryptContext(schemes=["pbkdf2_sha512"],
                       pbkdf2_sha512__default_rounds=50000,
                       pbkdf2_sha512__salt_size=64)

def passwordGen():
    return hashlib.sha1(os.urandom(160)).hexdigest()

class Account(object):

    def __init__(self, login, nick, email, passwd, passwdHashed = True):
        # credentials
        self.login = login
        self.nick = nick
        self.email = email
        self.passwdHashed = passwdHashed
        self.passwd = None
        self.setPassword(passwd)
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

    def setPassword(self, plainPassword):
        if self.passwdHashed:
            self.passwd = CONTEXT.hash(plainPassword)
        else:
            self.passwd = plainPassword

    def verifyPassword(self, password):
        if self.passwdHashed:
            return CONTEXT.verify(password, self.passwd)
        else:
            return password == self.passwd

class AIAccount(Account):

    def __init__(self, login, nick, aiType):
        password = passwordGen()
        Account.__init__(self, login, nick, None, password, passwdHashed = False)

        self.isAI = True
        self.aiType = aiType
        self.galaxyNames = []

class AdminAccount(Account):
    def __init__(self):
        password = passwordGen()
        Account.__init__(self, Const.ADMIN_LOGIN, Const.ADMIN_NICK, None, password, passwdHashed = False)

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

    def __init__(self):
        # credentials
        self.login = None
        self.nick = None
        self.passwd = None
        self.email = None
        # account options
        self.lastLogin = 0
        self.blockedUntil = -1 # -1 for not blocked, > 0 for blocked
        self.blocked = 0 # 1 for blocked account
        self.confToken = None # e-mail confirmation token, if None e-mail has been confirmed
        self.hostIDs = {} # hostids and times
        self.isAI = False

    def addHostID(self, hostID):
        if hostID:
            self.hostIDs[hostID] = time.time()

class AIAccount(Account):

    def __init__(self):
        Account.__init__(self)
        self.passwd = hashlib.sha1(str(random.randrange(0, 1e10))).hexdigest()

        self.isAI = True
        self.aiType = None
        self.galaxyNames = []

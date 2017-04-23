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

import cPickle as pickle
import os.path
from ige import log
class IClientDB:

    def __init__(self, cid, turn, dataDir = 'var', gameID = "UNDEFINED"):
        self.playerID = cid
        self.gameID = gameID
        self.turn = turn
        self.dataDir = dataDir
        self.load()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        if value != None:
            if self.data.has_key(key):
                self.data[key].__dict__.update(value.__dict__)
            else:
                self.data[key] = value
            self.timestamp[key] = self.turn

    def __delitem__(self, key):
        del self.data[key]
        del self.timestamp[key]

    def get(self, key, default = None):
        return self.data.get(key, default)

    def has_key(self, key):
        return self.data.has_key(key)

    def load(self):
        try:
            fh = open(os.path.join(self.dataDir, '%s_%d.data' % (self.gameID, self.playerID)), 'rb')
            self.data = pickle.load(fh)
            fh.close()
            fh = open(os.path.join(self.dataDir, '%s_%d.timestamp' % (self.gameID, self.playerID)), 'rb')
            self.timestamp = pickle.load(fh)
            fh.close()
        except:
            self.data = {}
            self.timestamp = {}

    def save(self):
        fh = open(os.path.join(self.dataDir, '%s_%d.data' % (self.gameID, self.playerID)), 'wb')
        pickle.dump(self.data, fh, 1)
        fh.close()
        fh = open(os.path.join(self.dataDir, '%s_%d.timestamp' % (self.gameID, self.playerID)), 'wb')
        pickle.dump(self.timestamp, fh, 1)
        fh.close()

    def needsUpdate(self, key, maxDelta = 0):
        return (not self.timestamp.has_key(key)) or self.timestamp[key] < self.turn - maxDelta

    def touch(self, key):
        self.timestamp[key] = self.turn

    def getLastUpdate(self):
        lastUpdate = -1
        for value in self.timestamp.values():
            lastUpdate = max(lastUpdate, value)
        return lastUpdate

    def clear(self):
        self.data = {}
        self.timestamp = {}

    def keys(self):
        return self.data.keys()

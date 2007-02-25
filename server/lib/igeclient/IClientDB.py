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

import cPickle as pickle
import os.path

class IClientDB:

	def __init__(self, cid, turn, dataDir = 'var'):
		self.playerID = cid
		self.turn = turn
		self.dataDir = dataDir
		self.load()

	def __getitem__(self, key):
		return self.data[key]

	def __setitem__(self, key, value):
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
			fh = open(os.path.join(self.dataDir, '%d.data' % self.playerID), 'rb')
			self.data = pickle.load(fh)
			fh.close()
			fh = open(os.path.join(self.dataDir, '%d.timestamp' % self.playerID), 'rb')
			self.timestamp = pickle.load(fh)
			fh.close()
		except:
			self.data = {}
			self.timestamp = {}

	def save(self):
		fh = open(os.path.join(self.dataDir, '%d.data' % self.playerID), 'wb')
		pickle.dump(self.data, fh, 1)
		fh.close()
		fh = open(os.path.join(self.dataDir, '%d.timestamp' % self.playerID), 'wb')
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

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

class Database:

	def __init__(self, gameName, dbName):
		self._filename = os.path.join('var', gameName, dbName + '.db')
		self.nextID = 10000
		try:
			self.load()
		except IOError:
			self._db = {}

	def __getitem__(self, key):
		return self._db[key]

	def __setitem__(self, key, value):
		value.oid = key
		self._db[key] = value

	def has_key(self, key):
		return self._db.has_key(key)

	def keys(self):
		return self._db.keys()

	def checkpoint(self):
		self.save()

	def load(self):
		fh = open(self._filename, 'rb')
		self._db = pickle.load(fh)
		fh.close()

	def save(self):
		fh = open(self._filename, 'wb')
		pickle.dump(self._db, fh, 1)
		fh.close()

	def shutdown(self):
		self.checkpoint()

	def clear(self):
		self._db.clear()

	def create(self, object):
		db = self._db
		id = self.nextID
		while db.has_key(id):
			id += 1
		self.nextID = id + 1
		object.oid = id
		db[id] = object
		return id

	def delete(self, key):
		del self._db[key]

	def __delitem__(self, key):
		del self._db[key]

	def get(self, key, default = None):
		return self._db.get(key, default)

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

import ige
import os.path, log, os, sys, time
from bsddb3 import db
import cPickle as pickle

IDX_PREV = 0
IDX_NEXT = 1

# active databases
dbOpened = 0

# db environment
dbEnv = None

class BSDDBDatabase:

	def __init__(self, directory, dbName, cache = 128,
			pagesize = None):
		global dbOpened, dbEnv
		log.message("Opening database", dbName)
		self.dbName = dbName
		self.nextID = 10000
		self.cacheSize = cache
		#
		try:
			os.makedirs(directory)
		except OSError:
			pass
		# create db env when needed
		if not dbEnv:
			log.debug("BSDSDB - creating environment")
			dbEnv = db.DBEnv()
			dbEnv.set_lg_max(16 * 1024 * 1024)
			dbEnv.set_cachesize(0, 10 * 1024 * 1024, 0)
			dbEnv.set_get_returns_none(0)
			dbEnv.open(directory, db.DB_CREATE | db.DB_INIT_MPOOL)
			log.debug("BSDSDB - environment created")
		self.db = db.DB(dbEnv)
		if not pagesize:
			self.db.set_pagesize(8192)
		else:
			self.db.set_pagesize(pagesize)
		# open
		self.db.open(dbName, dbtype = db.DB_BTREE, flags = db.DB_CREATE)
		dbOpened += 1
		# cache
		self.cache = {}
		self.cacheLinks = {
			"__first__": [None, "__last__"],
			"__last__": ["__first__", None],
		}
		# stats
		self.statCount = 0
		self.statHit = 0
		self.statSwap = 0
		self.statMiss = 0
		self.statCleanSwap = 0
		# ??
		#self.db.put("DUMMY", "DUMMY", txn = self.txn)
		#self.db.delete("DUMMY", txn = self.txn)

	def moveExistingCacheItem(self, key):
		#@log.debug("Cache MOVE ITEM", key, self.cacheLinks[key])
		# optimalization
		cacheLinks = self.cacheLinks
		# move item to the end of the chain
		prev, next = self.cacheLinks[key]
		cacheLinks[prev][IDX_NEXT] = next
		cacheLinks[next][IDX_PREV] = prev
		last = cacheLinks["__last__"]
		prev = last[IDX_PREV]
		cacheLinks[key] = [prev, "__last__"]
		cacheLinks[prev][IDX_NEXT] = key
		last[IDX_PREV] = key
		# print chain
		#idx = "__first__"
		#result = []
		#while idx != None:
		#	item = self.cacheLinks[idx]
		#	result.append("%s:%s" % (idx, item))
		#	idx = item[IDX_NEXT]
		#log.debug("Cache CHAIN", " ".join(result))

	def addNewCacheItem(self, key):
		#@log.debug("Cache ADD ITEM", key)
		# check cache size
		#@log.debug("Cache size", len(self.cache), self.cacheSize)
		if len(self.cache) > self.cacheSize:
			while len(self.cache) > self.cacheSize:
				# swap out oldest item
				current = self.cacheLinks["__first__"]
				oldKey = current[IDX_NEXT]
				if sys.getrefcount(self.cache[oldKey]) > 2:
					log.debug("CANNOT swap out", oldKey, "refs", sys.getrefcount(self.cache[oldKey]) - 2)
					if current == "__last__":
						# give up
						break
					else:
						# try next element
						self.moveExistingCacheItem(oldKey)
						#@log.debug("Trying to swap out", current[IDX_NEXT])
						continue
				else:
					#@log.debug("Swapping out", oldKey)
					self.statSwap += 1
					#TODOif not self.cache[oldKey]._v_modified:
					#TODO	self.statCleanSwap += 1
					prev, next = self.cacheLinks[oldKey]
					current[IDX_NEXT] = next
					self.cacheLinks[next][IDX_PREV] = prev
					self.db.put(oldKey, pickle.dumps(self.cache[oldKey], 1))
					del self.cacheLinks[oldKey]
					del self.cache[oldKey]
					# found space
					break
		# put item at the end of the chain
		last = self.cacheLinks["__last__"]
		prev = last[IDX_PREV]
		self.cacheLinks[prev][IDX_NEXT] = key
		self.cacheLinks[key] = [prev, "__last__"]
		last[IDX_PREV] = key
		# print chain
		#idx = "__first__"
		#result = []
		#while idx != None:
		#	item = self.cacheLinks[idx]
		#	result.append("%s:%s" % (idx, item))
		#	idx = item[IDX_NEXT]
		#log.debug("Cache CHAIN", " ".join(result))

	def updateCacheItem(self, key):
		if key in self.cache:
			return self.moveExistingCacheItem(key)
		return self.addNewCacheItem(key)

	def delCacheItem(self, key):
		#@log.debug("Cache DEL ITEM", key)
		prev, next = self.cacheLinks[key]
		self.cacheLinks[prev][IDX_NEXT] = next
		self.cacheLinks[next][IDX_PREV] = prev
		del self.cacheLinks[key]

	def __getitem__(self, key):
		key = str(key)
		self.statCount += 1
		if key in self.cache:
			self.statHit += 1
			self.moveExistingCacheItem(key)
			return self.cache[key]
		self.statMiss += 1
		item = pickle.loads(self.db.get(key))
		self.addNewCacheItem(key)
		self.cache[key] = item
		#TODOitem.setModified(0)
		return item

	def __setitem__(self, key, value):
		value.oid = key
		key = str(key)
		# set value
		self.updateCacheItem(key)
		self.cache[key] = value
		#value.setModified(0)
		# write through new objects
		if not self.db.has_key(key):
			self.db.put(key, pickle.dumps(value, 1))

	def __delitem__(self, key):
		key = str(key)
		if key in self.cache:
			self.delCacheItem(key)
			del self.cache[key]
		self.db.delete(str(key))

	def has_key(self, key):
		return self.db.has_key(str(key))

	def keys(self):
		return self.db.keys()

	def checkpoint(self, shutdown = 0):
		log.debug('DB Checkpoint', self.dbName)
		log.debug("Storing all objects")
		for key, value in self.cache.iteritems():
			self.db.put(key, pickle.dumps(value, 1))
		# checkpoint db (TODO can be moved into the separate process?)
		log.debug("BSDDB Checkpoint")
		self.db.sync()
		# TODO clear cache?
		# self.cache.clear()
		# stats
		if self.statCount > 0:
			log.debug("****** %s" % self.dbName)
			log.debug("Count: %10d" % self.statCount)
			log.debug("Hit  : %10d [%02d %%]" % (self.statHit, int(self.statHit * 100 / self.statCount)))
			log.debug("Miss : %10d [%02d %%]" % (self.statMiss, int(self.statMiss * 100 / self.statCount)))
			log.debug("Swap : %10d [%02d %%]" % (self.statSwap, int(self.statSwap * 100 / self.statCount)))
			log.debug("CSwap: %10d [%02d %%]" % (self.statCleanSwap, int(self.statCleanSwap * 100 / self.statCount)))
			log.debug("******")
		# more stats
		self.statCount = 0
		self.statHit = 0
		self.statMiss = 0
		self.statSwap = 0
		self.statCleanSwap = 0

	def shutdown(self):
		global dbOpened, dbEnv
		log.message('DB Shutting down', self.dbName)
		self.checkpoint()
		# close dabatase
		dbOpened -= 1
		# finish a transaction
		try:
			self.db.close()
		except db.DBError:
			log.warning("Error while closing database", self.dbName)
		# close environment (if last database has been closed)
		if not dbOpened:
			log.message("DB - checkpoint before closing env.")
			log.message("DB - closing environment")
			dbEnv.close()
			dbEnv = None

	def clear(self):
		log.message("Deleting database", self.dbName)
		for key in self.db.keys():
			self.db.delete(key)
		self.cache.clear()
		self.cacheLinks = {
			"__first__": [None, "__last__"],
			"__last__": ["__first__", None],
		}

	def create(self, object):
		id = self.nextID
		while self.db.has_key(str(id)):
			id += 1
		self.nextID = id + 1
		object.oid = id
		key = str(id)
		self.cache[key] = object
		self.addNewCacheItem(key)
		self.db.put(key, pickle.dumps(object, 1))
		return id

	def delete(self, key):
		del self[key]

	def get(self, key, default = None):
		key = str(key)
		if self.has_key(key):
			return self[key]
		else:
			return default

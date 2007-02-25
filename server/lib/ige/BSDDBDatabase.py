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
import os.path, log, os, sys, time, types, binascii
import cPickle as pickle

if sys.hexversion < 0x020300f0:
	# support for python 2.2 with bsddb3 module installed
	from bsddb3 import db
else:
	# support for python 2.3
	from bsddb import db


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
			log.debug("BSDDB - creating environment")
			dbEnv = db.DBEnv()
			dbEnv.set_lg_max(16 * 1024 * 1024)
			dbEnv.set_lg_bsize(4 * 1024 * 1024)
			dbEnv.set_cachesize(0, 16 * 1024 * 1024, 0)
			dbEnv.set_lk_max_locks(100000)
			dbEnv.set_lk_max_lockers(100000)
			dbEnv.set_lk_max_objects(100000)
			dbEnv.set_get_returns_none(0)
			envFlags = db.DB_INIT_MPOOL | db.DB_INIT_TXN
			try:
				dbEnv.open(directory, db.DB_CREATE | db.DB_RECOVER | envFlags)
			except db.DBRunRecoveryError:
				log.warning("BSDDB - creating env without DB_RECOVER")
				dbEnv.open(directory, db.DB_CREATE | envFlags)
			# this is potentially dangerous
			dbEnv.set_flags(db.DB_TXN_NOSYNC, 1)
			#dbEnv.set_flags(db.DB_TXN_WRITE_NOSYNC, 1)
		log.debug("BSDDB - opening db", dbName)
		self.db = db.DB(dbEnv)
		if not pagesize:
			self.db.set_pagesize(8192)
		else:
			self.db.set_pagesize(pagesize)
		# transtaction
		self.txn = dbEnv.txn_begin()
		# open
		self.db.open(dbName, dbtype = db.DB_BTREE,
			flags = db.DB_CREATE | db.DB_AUTO_COMMIT)
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
		cl = self.cacheLinks
		# move item to the end of the chain
		prev, next = cl[key]
		cl[prev][IDX_NEXT] = next
		cl[next][IDX_PREV] = prev
		last = cl["__last__"]
		prev = last[IDX_PREV]
		cl[key] = [prev, "__last__"]
		cl[prev][IDX_NEXT] = key
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
			tries = len(self.cache)
			while len(self.cache) > self.cacheSize:
				# swap out oldest item
				current = self.cacheLinks["__first__"]
				oldKey = current[IDX_NEXT]
				tries -= 1
				if tries == 0:
					# no room in the cache -> enlarge it
					log.debug("NO ROOM IN THE CACHE", self.dbName, len(self.cache))
					self.cacheSize += 100
					break
				if sys.getrefcount(self.cache[oldKey]) > 2:
					#@log.debug("CANNOT swap out", oldKey, "refs", sys.getrefcount(self.cache[oldKey]) - 2)
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
					self.db.put(oldKey, pickle.dumps(self.cache[oldKey], pickle.HIGHEST_PROTOCOL), txn = self.txn)
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
		try:
			item = pickle.loads(self.db.get(key, txn = self.txn))
		except db.DBNotFoundError:
			raise ige.NoSuchObjectException(key)
		self.addNewCacheItem(key)
		self.cache[key] = item
		#TODOitem.setModified(0)
		return item

	def __setitem__(self, key, value):
		if type(value) == types.InstanceType:
			value.oid = key
		key = str(key)
		# set value
		self.updateCacheItem(key)
		self.cache[key] = value
		#value.setModified(0)
		# write through new objects
		if self.db.get(key, None, self.txn) == None:
			self.db.put(key, pickle.dumps(value, pickle.HIGHEST_PROTOCOL), txn = self.txn)

	def __delitem__(self, key):
		key = str(key)
		if key in self.cache:
			self.delCacheItem(key)
			del self.cache[key]
		self.db.delete(str(key), txn = self.txn)

	def has_key(self, key):
		return self.db.get(str(key), None, self.txn) != None

	def keys(self):
		c = self.db.cursor(self.txn)
		keys = []
		try:
			while 1:
				key, dummy = c.next()
				keys.append(key)
		except db.DBNotFoundError:
			pass
		c.close()
		return keys
		# doesn't work return self.db.keys(self.txn)

	def checkpoint(self, shutdown = 0):
		log.debug('DB Checkpoint', self.dbName)
		log.debug("Storing all objects")
		for key, value in self.cache.iteritems():
			self.db.put(key, pickle.dumps(value, pickle.HIGHEST_PROTOCOL), txn = self.txn)
		# commit transaction
		log.debug("Commiting transtaction")
		self.txn.commit()
		# TODO clear cache?
		# self.cache.clear()
		# stats TODO: reenable
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
		# begin new transtaction
		if not shutdown:
			log.debug("Starting new transtaction")
			self.txn = dbEnv.txn_begin()

	def commit(self):
		self.txn.commit()
		self.txn = dbEnv.txn_begin()

	def checkpointDatabase(self):
		# checkpoint db (TODO can be moved into the separate process?)
		log.debug("BSDDB Checkpoint")
		dbEnv.txn_checkpoint(0, 0, 0)

	def shutdown(self):
		global dbOpened, dbEnv
		log.message('DB Shutting down', self.dbName)
		self.checkpoint(shutdown = 1)
		# close dabatase
		dbOpened -= 1
		try:
			self.db.close()
		except db.DBError:
			log.warning("Error while closing database", self.dbName)
		# close environment (if last database has been closed)
		if not dbOpened:
			log.message("DB - checkpoint before closing env.")
			dbEnv.txn_checkpoint(1024, 0, 0)
			log.message("DB - closing environment")
			dbEnv.close()
			dbEnv = None

	def clear(self):
		log.message("Deleting database", self.dbName)
		for key in self.db.keys(self.txn):
			self.db.delete(key, txn = self.txn)
		self.cache.clear()
		self.cacheLinks = {
			"__first__": [None, "__last__"],
			"__last__": ["__first__", None],
		}
		log.debug("Database empty")

	def create(self, object):
		id = self.nextID
		while self.db.get(str(id), None, self.txn) != None:
			id += 1
		self.nextID = id + 1
		object.oid = id
		key = str(id)
		self.cache[key] = object
		self.addNewCacheItem(key)
		self.db.put(key, pickle.dumps(object, pickle.HIGHEST_PROTOCOL), txn = self.txn)
		return id

	def delete(self, key):
		del self[key]

	def get(self, key, default = None):
		key = str(key)
		if self.has_key(key):
			return self[key]
		else:
			return default

	def loadBSDDBBackup(self, filename):
		log.message("Restoring database from file", filename)
		fh = file(filename, "r")
		for hLine in ("VERSION=3", "format=bytevalue", "type=btree", "keys=1",
			"HEADER=END"):
			line = fh.readline().strip()
			if line != hLine:
				raise ige.ServerException("Incorrect header: %s" % line)
		while True:
			key = fh.readline().strip()
			if key == "DATA=END":
				break
			data = fh.readline().strip()
			key = binascii.a2b_hex(key)
			data = binascii.a2b_hex(data)
			#@log.debug("Storing key", key)
			self.db.put(key, data, txn = self.txn)
		log.message("Database restored")

	def restore(self, filename):
		log.message("Restoring database from file", filename)
		fh = file(filename, "r")
		line = fh.readline().strip()
		if line != "IGE OUTER SPACE BACKUP VERSION 1":
			raise ige.ServerException("Incorrect header: %s" % line)
		while True:
			key = fh.readline().strip()
			if key == "END OF BACKUP":
				break
			data = fh.readline().strip()
			key = binascii.a2b_hex(key)
			data = binascii.a2b_hex(data)
			self.db.put(key, data, txn = self.txn)
		log.message("Database restored")

	def backup(self, basename):
		filename = "%s-%s.osbackup" % (basename, self.dbName)
		log.message("Creating backup", filename)
		fh = file(filename, "w") #bz2.BZ2File(filename, "w")
		fh.write("IGE OUTER SPACE BACKUP VERSION 1\n")
		for key in self.keys():
			fh.write(binascii.b2a_hex(str(key)))
			fh.write("\n")
			fh.write(binascii.b2a_hex(self.db.get(key, txn = self.txn)))
			fh.write("\n")
		fh.write("END OF BACKUP\n")
		fh.close()
		log.message("Backup completed")

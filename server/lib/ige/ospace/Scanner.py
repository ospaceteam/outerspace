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

import time, math
from ige.ospace import Rules
import ige
from ige import log

def recordScanLevel(distance, tObj, scannerPwr, owner, playerMaps):
	level = min(tObj.signature * scannerPwr / max(0.0001, distance), Rules.maxScanPwr)
	if level >= Rules.level1InfoScanPwr and owner > 0:
		if owner not in playerMaps:
			playerMaps[owner] = {}
		playerMaps[owner][tObj] = max(level, playerMaps[owner].get(tObj, 0))

def computeScanner(obj1, obj2, playerMaps):
	d = math.hypot(obj1.x - obj2.x, obj1.y - obj2.y)
	if hasattr(obj1, "scannerPwr"):
		recordScanLevel(d, obj2, obj1.scannerPwr, obj1.owner, playerMaps)
	elif hasattr(obj1, "scannerPwrs"):
		for owner, scannerPwr in obj1.scannerPwrs.iteritems():
			recordScanLevel(d, obj2, scannerPwr, owner, playerMaps)
	else:
		raise ige.ServerException("Unsupported object")

def computeMap(galaxyCmdObj, tran, galaxy):
	log.debug("SCAN2 Phase - starting")

	start0 = time.time()

	map = generateMap(galaxyCmdObj, tran, galaxy)
	sectors, surroundingSectors = generateSectors(map)
	playerMaps = {}

	start = time.time()

	while sectors:
		# get (and remove) random sector
		(sX, sY), sObjs = sectors.popitem()
		# build list of objects in surrounding sectors
		objs = []
		for dx in surroundingSectors:
			for dy in surroundingSectors:
				sIdx = (sX + dx, sY + dy)
				if sIdx not in sectors:
					continue
				objs.extend(sectors[sIdx])
		# check objects in current sector
		for obj1Idx in sObjs:
			obj1 = map[obj1Idx]
			# with objects in surrounding sectors
			for obj2Idx in objs:
				obj2 = map[obj2Idx]
				computeScanner(obj1, obj2, playerMaps)
				computeScanner(obj2, obj1, playerMaps)
			# with objects in current sector
			for obj2Idx in sObjs:
				# allow object scan on itself
				if obj1Idx > obj2Idx:
					continue
				obj2 = map[obj2Idx]
				computeScanner(obj1, obj2, playerMaps)
				computeScanner(obj2, obj1, playerMaps)
	stop = time.time()

	log.debug("Time    : %0.3f s" % (stop - start))
	log.debug("Time    : %0.3f s (including sector generation)" % (stop - start0))
	return playerMaps

def generateSectors(map):
	# generate sector map
	sectors = {}
	sectorSize = 5
	# can be optimized to not include corner sectors
	surroundingSectors = range(-10 / sectorSize, 10 / sectorSize + 1)

	for i in map:
		obj = map[i]
		sIdx = (int(obj.x / sectorSize), int(obj.y / sectorSize))
		if sIdx in sectors:
			sectors[sIdx].append(obj.oid)
		else:
			sectors[sIdx] = [obj.oid]

	return sectors, surroundingSectors

def generateMap(cmdObj, tran, galaxy):
	map = {}
	# all systems are part of the map
	for systemID in galaxy.systems:
		system = tran.db[systemID]
		map[systemID] = system
		# get mobile objects (fleet, ...)
		for objID in cmdObj.cmd(system).getObjectsInSpace(tran, system):
			map[objID] = tran.db[objID]
	return map

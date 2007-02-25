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

import Rules, ige
from ige.IDataHolder import IDataHolder
import random, string
from Const import *
from ige import log

def newStructure(tran, techID, playerID, status = STRUCT_STATUS_ON | STRUCT_STATUS_NEW):
	tech = Rules.techs[techID]
	s = IDataHolder()
	s = [techID, int(tech.maxHP * getTechEff(tran, techID, playerID)), status, 0]
	return s

def getTechEff(tran, techID, playerID):
	if playerID != OID_NONE:
		player = tran.db[playerID]
		techEff = Rules.techImprEff[player.techs.get(techID, Rules.techBaseImprovement)]
	else:
		techEff = Rules.techImprEff[Rules.techBaseImprovement]
	return techEff

def getTechRCost(player, techID, improvement = 0):
	tech = Rules.techs[techID]
	if tech.level > 9:
		return 1000000000
	if improvement == 0:
		improvement = player.techs.get(techID, Rules.techBaseImprovement - 1) + 1
	resCost = int((2 ** tech.level) * Rules.techImprCostMod[improvement] * tech.researchMod)
	return resCost

def rand(min, max):
	if min >= max:
		# TODO report problem
		return min
	return random.randrange(min, max)

def getPlanetName(systemName, nType, index):
	if nType == 1:
		suffix = ['Alpha', 'Beta', 'Gamma', 'Delta',
			'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa',
			'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho',
			'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega'][index]
	elif nType == 2:
		suffix = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
			'XI', 'XII'][index]
	elif nType == 3:
		suffix = ['Prime', 'Secundus', 'Tertius', 'Quartus', 'Quintus',
			'Sextus', 'Septimus', 'Octavus', 'Nonus', 'Decimus', 'Undecimus',
			'Duodecimus'][index]
	elif nType == 4:
		suffix = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'][index]
	elif nType == 5:
		suffix = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'][index]
	else:
		raise IndexError('No such numbering type [%d].' % nType)
	return '%s %s' % (systemName, suffix)

def getPlanetNamesType():
	return random.randrange(1, 6)

# fleet is idle, when there is no active command
def isIdleFleet(fleet):
	return fleet.actionIndex >= len(fleet.actions) or fleet.actionIndex < 0

# shortcut for send message
def sendMessage(tran, obj, msgID, whereID, data):
	when = tran.db[OID_UNIVERSE].turn
	tran.gameMngr.sendMessage(tran, obj.oid, msgID, whereID, when, data)

validChars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- .'

# check name
def isCorrectName(name):
	for letter in name:
		if letter not in validChars:
			return 0
	return len(name) <= 30

# compare planets by distance and population
def cmpPlanetsByDistAndPop(refPl, pl1, pl2):
	# special handling for reference planet (always smaller than other planets)
	if refPl == pl1:
		return -1
	elif refPl == pl2:
		return 1
	d1 = (refPl.x - pl1.x) ** 2 + (refPl.y - pl1.y) ** 2
	d2 = (refPl.x - pl2.x) ** 2 + (refPl.y - pl2.y) ** 2
	# primary key is distance (ascending)
	if d1 < d2: return -1
	elif d1 > d2:	return 1
	# secondary key is population (descending)
	if pl1.storPop > pl2.storPop: return -1
	elif pl1.storPop < pl2.storPop: return 1
	return 0

# speed boost?
def getSpeedBoost(tran, player, objs):
	speedBoost = 10000.0
	for obj in objs:
		if obj.type == T_PLANET:
			system = tran.db[obj.compOf]
		elif obj.type in (T_SYSTEM, T_WORMHOLE):
			system = obj
		else:
			raise ige.ServerException("Not a planet or system")
		#
		tmpBoost = 1.0
		for planetID in system.planets:
			planet = tran.db[planetID]
			if planet.owner == player.oid:
				tmpBoost = max(tmpBoost, planet.fleetSpeedBoost)
			elif tran.gameMngr.cmdPool[player.type].isPactActive(tran, player, planet.owner, PACT_ALLOW_TANKING):
				tmpBoost = max(tmpBoost, planet.fleetSpeedBoost)
		speedBoost = min(speedBoost, tmpBoost)
	#@log.debug("Speed boost", speedBoost)
	return speedBoost


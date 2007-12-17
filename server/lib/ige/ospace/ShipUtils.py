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

import Rules
from ige import GameException
from ige import log
from ige.IDataHolder import IDataHolder
from Const import *
import random


def makeShipMinSpec(player, name, hullID, eqIDs, improvements,
	raiseExs = True):
	ship = makeShipFullSpec(player, name, hullID, eqIDs, improvements, raiseExs)
	# make 'real' ship spec
	spec = IDataHolder()
	spec.type = T_SHIP
	spec.name = ship.name
	spec.hullID = ship.hullID
	spec.level = ship.level
	spec.eqIDs = ship.eqIDs
	spec.improvements = ship.improvements
	spec.combatClass = ship.combatClass
	spec.signature = ship.signature
	spec.scannerPwr = ship.scannerPwr
	spec.speed = ship.speed
	spec.maxHP = ship.maxHP
	spec.shieldHP = ship.shieldHP
	spec.combatAtt = ship.combatAtt
	spec.combatDef = ship.combatDef
	spec.missileDef = ship.missileDef
	spec.storEn = ship.storEn
	spec.operEn = ship.operEn
	spec.buildProd = ship.buildProd
	spec.buildSRes = ship.buildSRes
	spec.weaponIDs = ship.weaponIDs
	spec.deployStructs = ship.deployStructs
	spec.deployHandlers = ship.deployHandlers
	spec.built = 0
	spec.buildTurns = 1
	spec.upgradeTo = 0
	spec.isMilitary = ship.isMilitary
	spec.baseExp = ship.baseExp
	spec.combatPwr = ship.combatPwr
	spec.autoRepairFix = ship.autoRepairFix
	spec.autoRepairPerc = ship.autoRepairPerc
	spec.shieldRechargeFix = ship.shieldRechargeFix
	spec.shieldRechargePerc = ship.shieldRechargePerc
	spec.hardShield = ship.hardShield
	spec.combatAttMultiplier = ship.combatAttMultiplier
	spec.damageAbsorb = ship.damageAbsorb
	return spec

def makeShipFullSpec(player, name, hullID, eqIDs, improvements, raiseExs = True):
	if not hullID:
		raise GameException("Ship's hull must be specified.")
	hull = Rules.techs[hullID]
	if not hull.isShipHull:
		raise GameException("Ship's hull must be specified.")
	ship = IDataHolder()
	ship.type = T_SHIP
	# initial values
	techEff = Rules.techImprEff[player.techs.get(hullID, Rules.techBaseImprovement)]
	ship.name = name
	ship.hullID = hullID
	ship.eqIDs = eqIDs
	ship.level = hull.level
	ship.combatClass = hull.combatClass
	ship.improvements = improvements
	ship.buildProd = hull.buildProd
	ship.buildSRes = hull.buildSRes[:] # we need copy
	ship.operEn = hull.operEn
	ship.storEn = hull.storEn * techEff
	ship.weight = hull.weight
	ship.slots = 0
	ship.signature = hull.signature
	ship.negsignature = 0
	ship.minSignature = hull.minSignature
	ship.signatureCloak = 1.0                                                #NEW; 100% - this is the default rule
	ship.signatureDecloak = 1.0                                              #NEW; 100% - this is the default rule
	ship.combatAttBase = hull.combatAtt * techEff
	ship.combatAtt = 0
	ship.combatAttMultiplier = 1.0                                             #NEW; 100% - this is the default rule
	ship.combatDefBase = hull.combatDef * techEff
	ship.combatDef = 0
	ship.combatDefMultiplier = 1.0                                             #NEW; 100% - this is the default rule
	ship.missileDefBase = hull.missileDef * techEff
	ship.missileDef = 0
	ship.missileDefMultiplier = 1.0                                             #NEW; 100% - this is the default rule
	ship.scannerPwr = max(hull.scannerPwr * techEff, Rules.scannerMinPwr)
	ship.autoRepairFix = hull.autoRepairFix
	ship.autoRepairPerc = hull.autoRepairPerc
	ship.shieldRechargeFix = hull.shieldRechargeFix
	ship.shieldRechargePerc = hull.shieldRechargePerc
	ship.hardShield = 0.0
	ship.engPwr = 0
	ship.upgradeTo = 0
	ship.shieldHP = 0
	ship.maxHP = int(hull.maxHP * techEff)
	ship.weaponIDs = []
	ship.deployStructs = []
	ship.deployHandlers = []
	ship.isMilitary = 0
	ship.baseExp = 0
	ship.damageAbsorb = 0
	combatExtra = 0
	shieldPerc = 0.0
	unpactStruct = 0
	deployHandler = 0
	currentNegWeight = 0
	currentNegSlots = 0
	# add equipment
	#negslots = {}
	#negweight = {}
	counter = {}
	installations = {}
	equipCounter = {}
	for techID in eqIDs:
		tech = Rules.techs[techID]
		techEff = Rules.techImprEff[player.techs.get(techID, Rules.techBaseImprovement)]
		# prevent count < 0; allow count == 0 for placeholders.
		if eqIDs[techID] < 0 and raiseExs:
			raise GameException("Invalid equipment count (less than 0).")
		for i in xrange(0, eqIDs[techID]):
			counter[tech.subtype] = 1 + counter.get(tech.subtype, 0)
			installations[techID] = 1 + installations.get(techID, 0)
			# check min hull req
			if tech.minHull > ship.combatClass and raiseExs:
				log.warning("Cannot add tech", techID, tech.name)
				raise GameException("Minimum hull requirement not satisfied.")
			# check max hull req                                                                        #NEW
			if tech.maxHull < ship.combatClass and raiseExs:
				log.warning("Cannot add tech", techID, tech.name)
				raise GameException("Maximum hull requirement not satisfied.")
			# check maximum installations
			if tech.maxInstallations and installations[tech.id] > tech.maxInstallations \
				and raiseExs:
				raise GameException("Maximum number of equipment installations exceeded.")
			#check maximum type installations
			if tech.subtype == "seq_mod" and tech.equipType in Rules.maxEquipType and raiseExs::
				if tech.equipType in equipCounter:
					equipCounter[tech.equipType] += 1
				else:
					equipCounter[tech.equipType] = 1
				log.debug(equipCounter[tech.equipType])
				if equipCounter[tech.equipType] > Rules.maxEquipType[tech.equipType]:
					raise GameException("Maximum number of restricted type equipment installations exceeded: %s." % tech.equipType)
			# add values
			ship.level = max(ship.level, tech.level)
			ship.buildProd += tech.buildProd
			ship.buildSRes.extend(tech.buildSRes)
			ship.storEn += tech.storEn * techEff
			if (tech.weight > 0):
				ship.weight += tech.weight
			else:
				currentNegWeight += tech.weight
				#negweight[techID] = tech.weight + negweight.get(techID, 0) #this is complex for items with max installs...
			if (tech.slots > 0):
				ship.slots += tech.slots
			else:
				currentNegSlots += tech.slots
				#negslots[techID] = tech.slots + negslots.get(techID, 0) #this is complex for items with max installs...
			if tech.signature < 0 and tech.subtype == "seq_mod":
				ship.negsignature = min(tech.signature,ship.negsignature)
			else:
				ship.signature += tech.signature
			ship.minSignature = max(ship.minSignature, tech.minSignature)
			ship.signatureCloak = min(ship.signatureCloak, tech.signatureCloak)
			ship.signatureDecloak = min(ship.signatureDecloak, tech.signatureDecloak)
			if tech.subtype == "seq_mod": #not cumulative for equipment; pick best
				ship.combatAtt = max(ship.combatAtt, tech.combatAtt * techEff) 
				ship.combatDef = max(ship.combatDef, tech.combatDef * techEff)
				ship.missileDef = max(ship.missileDef, tech.missileDef * techEff)
			else :
				ship.combatDefBase += tech.combatDef * techEff
				ship.missileDefBase += tech.missileDef * techEff
				ship.combatAttBase += tech.combatAtt * techEff
			#not cumulative; pick best
			ship.combatAttMultiplier = max(ship.combatAttMultiplier, (tech.combatAttPerc-1.0) * techEff + 1.0)           #NEW
			ship.combatDefMultiplier = max(ship.combatDefMultiplier, (tech.combatDefPerc-1.0) * techEff + 1.0)           #NEW
			ship.missileDefMultiplier = max(ship.missileDefMultiplier, (tech.missileDefPerc-1.0) * techEff + 1.0)        #NEW
			
			ship.engPwr += tech.engPwr * techEff
			ship.maxHP += tech.maxHP * techEff
			shieldPerc = max(shieldPerc, tech.shieldPerc * techEff)
			ship.scannerPwr = max(ship.scannerPwr, tech.scannerPwr * techEff)
			ship.operEn += tech.operEn
			ship.autoRepairFix = max(ship.autoRepairFix, tech.autoRepairFix * techEff)
			ship.autoRepairPerc = max(ship.autoRepairPerc, tech.autoRepairPerc * techEff)
			ship.shieldRechargeFix = max(ship.shieldRechargeFix, tech.shieldRechargeFix * techEff)
			ship.shieldRechargePerc = max(ship.shieldRechargePerc, tech.shieldRechargePerc * techEff)
			ship.hardShield = max(ship.hardShield,tech.hardShield * techEff)
			ship.damageAbsorb = min(ship.damageAbsorb + tech.damageAbsorb,Rules.maxDamageAbsorb) #limit this by rule
			combatExtra += tech.addMP
			# if weapon - register only
			if tech.subtype == "seq_wpn":
				ship.weaponIDs.append(techID)
				ship.isMilitary = 1
				weapon = Rules.techs[techID]
				ship.baseExp += (weapon.weaponDmgMin + weapon.weaponDmgMax) / 2 * weapon.weaponROF
			# deployables
			if tech.unpackStruct != OID_NONE:
				ship.deployStructs.append(tech.unpackStruct)
				unpactStruct = 1
			if tech.deployHandlerID != OID_NONE: #this calls another tech at execute time, so only need the ID
				ship.deployHandlers.append(tech.deployHandlerID)
				deployHandler = 1
			
	#fix limiter based attibs; round when needed
	#currentNegWeight = 0
	#for negtech in negweight:
	#    currentNegWeight = min(currentNegWeight,negweight[negtech])
	#currentNegSlots = 0
	#for negtech in negslots:
	#    currentNegSlots = min(currentNegSlots,negslots[negtech])
	ship.weight = max(ship.weight+currentNegWeight,int(hull.weight/2))
	ship.slots = max(ship.slots+currentNegSlots,1)
	ship.combatAtt += ship.combatAttBase
	ship.combatDef = int((ship.combatDef + ship.combatDefBase) * ship.combatDefMultiplier)
	ship.missileDef = int((ship.missileDef + ship.missileDefBase) * ship.missileDefMultiplier)
	ship.hardShield = min(1.0,ship.hardShield) #don't allow this to be more than 100% blocking!!
	#add some MP for damage absorb:
	combatExtra += ship.damageAbsorb * 1500
	#calculate final signature
	ship.signature += ship.negsignature
	ship.signature *= ship.signatureCloak * ship.signatureDecloak
	# check various conditions
#	if unpactStruct and deployHandler and raiseExs: #we don't 'need' this, so I'm leaving it disabled for now; however, we might 'want' it to prevent abuse --RC
#                raise GameException("Cannot have both a deployable structure and a deployable project on the same ship") 
	if counter.get("seq_ctrl", 0) == 0 and raiseExs:
		raise GameException("No control module in the ship.")
	if counter.get("seq_ctrl", 0) > 1 and raiseExs:
		raise GameException("Only one control module in the ship allowed.")
	if ship.slots > hull.slots and raiseExs:
		raise GameException("Hull does not have enough slots to hold specified equipment.")
	if ship.weight > hull.maxWeight and raiseExs:
		raise GameException("Ship is too heavy.")
	# compute secondary paramaters
	ship.speed = float(ship.engPwr) / ship.weight
	ship.baseExp = int(ship.baseExp * Rules.shipBaseExpMod) + Rules.shipBaseExp[ship.combatClass]
	# compute base attack/defence
	ship.combatAtt += int(ship.speed)
	ship.combatDef += int(ship.speed)
	ship.missileDef += int(ship.speed / 2.0)
	# improvements
	if len(improvements) > Rules.shipMaxImprovements and raiseExs:
		raise GameException("Too many improvements.")
	for i in improvements:
		if i == SI_SPEED:
			ship.speed *= Rules.shipImprovementMod
		elif i == SI_TANKS:
			ship.storEn *= Rules.shipImprovementMod
		elif i == SI_ATT:
			ship.combatAtt *= Rules.shipImprovementMod
		elif i == SI_DEF:
			ship.combatDef *= Rules.shipImprovementMod
			ship.missileDef *= Rules.shipImprovementMod
		elif i == SI_HP:
			ship.maxHP *= Rules.shipImprovementMod
		elif i == SI_SHIELDS:
			ship.shieldHP *= Rules.shipImprovementMod
	# round values down
	ship.storEn = int(ship.storEn)
	ship.combatAtt = int(ship.combatAtt / (ship.combatClass + 1.0))
	ship.combatDef = int(ship.combatDef / (ship.combatClass + 1.0))
	ship.missileDef = int(ship.missileDef / (ship.combatClass + 1.0))
	ship.maxHP = int(ship.maxHP)
	ship.shieldHP = int(ship.maxHP * shieldPerc)
	ship.scannerPwr = int(ship.scannerPwr)
	ship.engPwr = int(ship.engPwr)
	ship.signature = int(ship.signature)
	ship.baseExp = int(ship.baseExp)
	# compute attack power
	attackPwr = 0.0
	refDefence = 10.0
	refAttack = 10.0
	refDmg = 10.0
	refSpeed = 5.0 #average speed of medium and large hulls
	for weaponID in ship.weaponIDs:
		weapon = Rules.techs[weaponID]
		dmg = (weapon.weaponDmgMin + weapon.weaponDmgMax) / 2 * weapon.weaponROF
		att = int((ship.combatAtt + weapon.weaponAtt) * ship.combatAttMultiplier) #added combat multiplier
#		attackPwr += (att / float(att + refDefence) * dmg)
		attackPwr += (att / float(att + refDefence) * dmg) / (max(1,weapon.weaponClass-1)) #9/11/06 - RC; reduce power of bombs and torps in calculation
	# defence
#	ship.combatPwr = int(attackPwr * (ship.maxHP + ship.shieldHP) / (refAttack / (refAttack + ship.combatDef) * refDmg)) 
	ship.combatPwr = int(attackPwr * (ship.maxHP + ship.shieldHP) / (refAttack / (refAttack + ship.combatDef) * refDmg) * min(1.33,max(0.5,(ship.speed / refSpeed))) + combatExtra)  #9/11/06 - RC; average speed ships get most weight)
	# fix signature
	ship.signature = max(hull.minSignature, ship.signature, ship.minSignature) #removed 1 as min signature; use hulls to control that from now on; change Fleet controls to make min signature for fleet rather than ship so that we can have human stealth craft! :)
	#
	return ship

# ROF tables
rofTable = {}
for i in xrange(0, 100):
	line = []
	level = i
	for j in xrange(0, 100):
		if level >= 100:
			line.append(1)
			level -= 100
		else:
			line.append(0)
		level += i
	# check
	sum = 0
	for e in line:
		sum += e
	#@log.debug("ROF %02d %2.2f" % (i, sum / 10.0), line)
	assert i == sum, "Bad ROF table sum for %d" % i
	rofTable[i] = line

def getRounds(rof, counter):
	rof = int(rof * 100)
	return rof / 100 + rofTable[rof % 100][counter % 100]

# damage
def computeDamage(wpnCls, trgtCls, dmgMin, dmgMax, weaponEff):
	"""Compute damage that causes weapon to the target with specified combat
	   class."""
	assert trgtCls >= wpnCls
	dmgMin = int(dmgMin*weaponEff)
	dmgMax = int(dmgMax*weaponEff)
	dmg = 1.0 * random.randint(dmgMin, dmgMax) * Rules.weaponDmgDegrade[trgtCls - wpnCls]
	intDmg = int(round(dmg,0))
	return intDmg

def sortShips(ships):
	# TODO: remove in 0.6
	origShips = ships[:]

	# split them
	types = {}
	for ship in ships:
		t = ship[SHIP_IDX_DESIGNID]
		if t not in types:
			types[t] = []
		types[t].append(ship)

	# sort them by HP, init counter
	incrs = {}
	counters = {}
	for t in types:
		# take shield into account
		types[t].sort(lambda a, b: cmp(a[SHIP_IDX_HP] + a[SHIP_IDX_SHIELDHP], b[SHIP_IDX_HP] + b[SHIP_IDX_SHIELDHP]))
		incrs[t] = 1.0 / (float(len(types[t])) / len(ships))
		counters[t] = incrs[t]

	# rearrange them
	ships = []

	while types:
		# find minimum
		minCounter = 1e100
		minType = None
		for t in counters:
			if minCounter > counters[t]:
				minType = t
				minCounter = counters[t]
		# pick ship, increase counter
		ships.append(types[minType].pop(0))
		counters[minType] += incrs[minType]
		if not types[minType]:
			del types[minType]
			del counters[minType]

	# check result
	# TODO: remove in 0.6
	for ship in ships:
		origShips.remove(ship)
	assert origShips == []

	return ships

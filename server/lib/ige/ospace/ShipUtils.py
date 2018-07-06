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

import copy
import random

import Const
import Rules
import Utils

from ige import GameException
from ige import log
from ige.IDataHolder import IDataHolder


def makeShipMinSpec(player, name, hullID, eqIDs, improvements,
    raiseExs = True):
    ship = makeShipFullSpec(player, name, hullID, eqIDs, improvements, raiseExs)
    # make 'real' ship spec
    spec = IDataHolder()
    spec.type = Const.T_SHIP
    spec.name = ship.name
    spec.hullID = ship.hullID
    spec.level = ship.level
    spec.eqIDs = ship.eqIDs
    spec.improvements = ship.improvements
    spec.combatClass = ship.combatClass
    spec.signature = ship.signature
    spec.scannerPwr = ship.scannerPwr
    spec.speed = ship.speed
    spec.battleSpeed = ship.battleSpeed
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

def _checkValidity(ship, tech, installations, equipCounter, raiseExs):
    if not raiseExs:
        return
    # check min hull req
    elif tech.minHull > ship.combatClass:
        log.warning("Cannot add tech", tech.id, tech.name)
        raise GameException("Minimum hull requirement not satisfied.")
    # check max hull req
    elif tech.maxHull < ship.combatClass:
        log.warning("Cannot add tech", tech.id, tech.name)
        raise GameException("Maximum hull requirement not satisfied.")
    # check maximum installations
    elif tech.maxInstallations and installations[tech.id] > tech.maxInstallations:
        raise GameException("Maximum number of equipment installations exceeded.")
    #check maximum type installations
    elif tech.subtype == "seq_mod" and tech.equipType in Rules.maxEquipType:
        try:
            equipCounter[tech.equipType] += 1
        except KeyError:
            equipCounter[tech.equipType] = 1
        if equipCounter[tech.equipType] > Rules.maxEquipType[tech.equipType]:
            raise GameException("Maximum number of restricted type equipment installations exceeded: %s." % tech.equipType)

def _checkValidityWhole(ship, hull, counter, raiseExs):
    if not raiseExs:
        return
    elif counter.get("seq_ctrl", 0) != 1:
        raise GameException("Exactly one control module needs to be in the ship.")
    elif ship.slots > hull.slots:
        raise GameException("Hull does not have enough slots to hold specified equipment.")
    elif ship.weight > hull.maxWeight:
        raise GameException("Ship is too heavy.")
    elif len(ship.improvements) > Rules.shipMaxImprovements:
        raise GameException("Too many improvements.")

def _moduleSignature(ship, tech):
    if tech.signature < 0 and not tech.subtype == "seq_eng":
        ship.negsignature = min(tech.signature, ship.negsignature)
    else:
        ship.signature += tech.signature
    ship.minSignature = max(ship.minSignature, tech.minSignature)
    ship.signatureCloak = min(ship.signatureCloak, tech.signatureCloak)
    ship.signatureDecloak = min(ship.signatureDecloak, tech.signatureDecloak)

def _finalizeSignature(ship, hull):
    ship.signature += ship.negsignature
    ship.signature *= ship.signatureCloak * ship.signatureDecloak
    ship.signature = int(ship.signature)
    ship.signature = max(hull.minSignature, ship.signature, ship.minSignature)

def _moduleCombat(ship, tech, techEff, combatExtra):
    combatExtra += tech.addMP
    if tech.subtype == "seq_mod": #not cumulative for equipment; pick best
        ship.combatAtt = max(ship.combatAtt, tech.combatAtt * techEff)
        ship.combatDef = max(ship.combatDef, tech.combatDef * techEff)
        ship.missileDef = max(ship.missileDef, tech.missileDef * techEff)
    else:
        ship.combatDefBase += tech.combatDef * techEff
        ship.missileDefBase += tech.missileDef * techEff
        ship.combatAttBase += tech.combatAtt * techEff
    #not cumulative; pick best
    ship.combatAttMultiplier = max(ship.combatAttMultiplier, (tech.combatAttPerc-1.0) * techEff + 1.0)
    ship.combatDefMultiplier = max(ship.combatDefMultiplier, (tech.combatDefPerc-1.0) * techEff + 1.0)
    ship.missileDefMultiplier = max(ship.missileDefMultiplier, (tech.missileDefPerc-1.0) * techEff + 1.0)
    # if weapon - register only
    if tech.subtype == "seq_wpn":
        ship.weaponIDs.append(tech.id)
        ship.isMilitary = 1
        weapon = Rules.techs[tech.id]
        ship.baseExp += (weapon.weaponDmgMin + weapon.weaponDmgMax) / 2 * weapon.weaponROF

def _finalizeCombat(ship):
    # compute base attack/defence
    ship.combatAtt += ship.combatAttBase
    ship.combatAtt += int(ship.battleSpeed)
    ship.combatDef = int((ship.combatDef + ship.combatDefBase) * ship.combatDefMultiplier)
    ship.missileDef = int((ship.missileDef + ship.missileDefBase) * ship.missileDefMultiplier)
    ship.combatDef += int(ship.battleSpeed)
    ship.missileDef += int(ship.battleSpeed / 2.0)
    for i in ship.improvements:
        if i == Const.SI_ATT:
            ship.combatAtt *= Rules.shipImprovementMod
        elif i == Const.SI_DEF:
            ship.combatDef *= Rules.shipImprovementMod
            ship.missileDef *= Rules.shipImprovementMod
    ship.combatAtt = int(ship.combatAtt / (ship.combatClass + 1.0))
    ship.combatDef = int(ship.combatDef / (ship.combatClass + 1.0))
    ship.missileDef = int(ship.missileDef / (ship.combatClass + 1.0))
    ship.baseExp = int(ship.baseExp * Rules.shipBaseExpMod) + Rules.shipBaseExp[ship.combatClass]

def _moduleSturdiness(ship, tech, techEff, shieldPerc):
    ship.maxHP += tech.maxHP * techEff
    shieldPerc = max(shieldPerc, tech.shieldPerc * techEff)
    ship.autoRepairFix = max(ship.autoRepairFix, tech.autoRepairFix * techEff)
    ship.autoRepairPerc = max(ship.autoRepairPerc, tech.autoRepairPerc * techEff)
    ship.shieldRechargeFix = max(ship.shieldRechargeFix, tech.shieldRechargeFix * techEff)
    ship.shieldRechargePerc = max(ship.shieldRechargePerc, tech.shieldRechargePerc * techEff)
    ship.hardShield = max(ship.hardShield,tech.hardShield * techEff)
    ship.damageAbsorb = min(ship.damageAbsorb + tech.damageAbsorb, Rules.maxDamageAbsorb)

def _finalizeSturdiness(ship, shieldPerc):
    # improvements
    for i in ship.improvements:
        if i == Const.SI_HP:
            ship.maxHP *= Rules.shipImprovementMod
        elif i == Const.SI_SHIELDS:
            ship.shieldHP *= Rules.shipImprovementMod
    # round values down
    ship.maxHP = int(ship.maxHP)
    ship.shieldHP = int(ship.maxHP * shieldPerc)
    ship.hardShield = min(1.0,ship.hardShield) #don't allow this to be more than 100% blocking!!

def _moduleDeployables(ship, tech):
    if tech.unpackStruct != Const.OID_NONE:
        ship.deployStructs.append(tech.unpackStruct)
    if tech.deployHandlerID != Const.OID_NONE:
        #this calls another tech at execute time, so only need the ID
        ship.deployHandlers.append(tech.deployHandlerID)

def _moduleBase(ship, tech, techEff):
    ship.level = max(ship.level, tech.level)
    ship.buildProd += tech.buildProd
    ship.buildSRes = Utils.dictAddition(ship.buildSRes, tech.buildSRes)
    ship.slots += tech.slots
    ship.weight += tech.weight
    ship.storEn += tech.storEn * techEff
    ship.operEn += tech.operEn
    ship.engPwr += tech.engPwr * techEff
    ship.engStlPwr += tech.engStlPwr * techEff
    ship.scannerPwr = max(ship.scannerPwr, tech.scannerPwr * techEff)

def _finalizeBase(ship, hull):
    ship.weight = max(ship.weight, int(hull.weight / 2.0))
    ship.slots = max(ship.slots, 1)
    ship.storEn = int(ship.storEn)
    ship.scannerPwr = int(ship.scannerPwr)
    ship.engPwr = int(ship.engPwr)
    ship.engStlPwr = int(ship.engStlPwr)
    ship.speed = float(ship.engPwr) / ship.weight
    ship.battleSpeed = float(ship.engPwr + ship.engStlPwr) / ship.weight
    # improvements
    for i in ship.improvements:
        if i == Const.SI_SPEED:
            ship.speed *= Rules.shipImprovementMod
            ship.battleSpeed *= Rules.shipImprovementMod
        elif i == Const.SI_TANKS:
            ship.storEn *= Rules.shipImprovementMod

def _setCombatPower(ship, combatExtra):
    attackPwr = 0.0
    refDefence = 10.0
    refAttack = 10.0
    refDmg = 10.0
    refSpeed = 5.0 #average speed of medium and large hulls
    for weaponID in ship.weaponIDs:
        weapon = Rules.techs[weaponID]
        dmg = (weapon.weaponDmgMin + weapon.weaponDmgMax) / 2 * weapon.weaponROF
        att = int((ship.combatAtt + weapon.weaponAtt) * ship.combatAttMultiplier)
        sizeCompensation = max(1, weapon.weaponClass - 1) # reduce torps and bombs
        attackPwr += (att / float(att + refDefence) * dmg) / sizeCompensation
    hpEffect = ship.maxHP + ship.shieldHP
    attDefEffect = refAttack / (refAttack + ship.combatDef) * refDmg
    speedEffect = min(1.33, max(0.5, (ship.battleSpeed / refSpeed)))
    combatExtra += ship.damageAbsorb * 1500
    ship.combatPwr = int(attackPwr * hpEffect / attDefEffect * speedEffect + combatExtra)

def makeShipFullSpec(player, name, hullID, eqIDs, improvements, raiseExs = True):
    if not hullID:
        raise GameException("Ship's hull must be specified.")
    hull = Rules.techs[hullID]
    if not hull.isShipHull:
        raise GameException("Ship's hull must be specified.")
    ship = IDataHolder()
    ship.type = Const.T_SHIP
    # initial values
    hullTechEff = Rules.techImprEff[player.techs.get(hullID, Rules.techBaseImprovement)]
    ship.name = name
    ship.hullID = hullID
    ship.eqIDs = eqIDs
    ship.level = hull.level
    ship.combatClass = hull.combatClass
    ship.improvements = improvements
    ship.buildProd = hull.buildProd
    ship.buildSRes = copy.copy(hull.buildSRes)
    # stats grouped as "Base"
    ship.operEn = hull.operEn
    ship.storEn = hull.storEn * hullTechEff
    ship.weight = hull.weight
    ship.slots = 0
    ship.scannerPwr = max(hull.scannerPwr * hullTechEff, Rules.scannerMinPwr)
    ship.engPwr = 0
    ship.engStlPwr = 0
    ship.speed = 0.0
    ship.battleSpeed = 0.0
    # stats grouped as "Signature"
    ship.signature = hull.signature
    ship.negsignature = 0
    ship.minSignature = hull.minSignature
    ship.signatureCloak = 1.0
    ship.signatureDecloak = 1.0
    # stats grouped as "Combat"
    ship.combatAttBase = hull.combatAtt * hullTechEff
    ship.combatAtt = 0
    ship.combatAttMultiplier = 1.0
    ship.combatDefBase = hull.combatDef * hullTechEff
    ship.combatDef = 0
    ship.combatDefMultiplier = 1.0
    ship.missileDefBase = hull.missileDef * hullTechEff
    ship.missileDef = 0
    ship.missileDefMultiplier = 1.0
    ship.weaponIDs = []
    ship.isMilitary = 0
    ship.baseExp = 0
    combatExtra = 0
    # stats grouped as "Sturdiness"
    ship.autoRepairFix = hull.autoRepairFix
    ship.autoRepairPerc = hull.autoRepairPerc
    ship.shieldRechargeFix = hull.shieldRechargeFix
    ship.shieldRechargePerc = hull.shieldRechargePerc
    ship.hardShield = 0.0
    ship.shieldHP = 0
    ship.maxHP = int(hull.maxHP * hullTechEff)
    ship.damageAbsorb = 0
    shieldPerc = 0.0
    # stats grouped as "Deployables"
    ship.deployStructs = []
    ship.deployHandlers = []

    ship.upgradeTo = 0
    counter = {}
    installations = {}
    equipCounter = {}
    for techID in eqIDs:
        tech = Rules.techs[techID]
        techEff = Rules.techImprEff[player.techs.get(techID, Rules.techBaseImprovement)]
        if eqIDs[techID] < 0 and raiseExs:
            raise GameException("Invalid equipment count (less than 0).")
        for i in xrange(0, eqIDs[techID]):
            counter[tech.subtype] = 1 + counter.get(tech.subtype, 0)
            installations[techID] = 1 + installations.get(techID, 0)
            _checkValidity(ship, tech, installations, equipCounter, raiseExs)
            # add values

            _moduleBase(ship, tech, techEff)
            _moduleSignature(ship, tech)
            _moduleCombat(ship, tech, techEff, combatExtra)
            _moduleSturdiness(ship, tech, techEff, shieldPerc)
            _moduleDeployables(ship, tech)

    _checkValidityWhole(ship, hull, counter, raiseExs)
    _finalizeBase(ship, hull)
    _finalizeSignature(ship, hull)
    _finalizeCombat(ship)
    _finalizeSturdiness(ship, shieldPerc)
    _setCombatPower(ship, combatExtra)
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
        t = ship[Const.SHIP_IDX_DESIGNID]
        if t not in types:
            types[t] = []
        types[t].append(ship)

    # sort them by HP, init counter
    incrs = {}
    counters = {}
    for t in types:
        # take shield into account
        types[t].sort(key=lambda a: a[Const.SHIP_IDX_HP] + a[Const.SHIP_IDX_SHIELDHP])
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

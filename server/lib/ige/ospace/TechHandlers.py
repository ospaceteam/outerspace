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

import Rules, Utils
from Const import *
import random
from ige import log

def spaceDocksTurn(tran, obj, tech):
    # skip unowned planets
    if obj.owner == OID_NONE:
        return
    maxRepaired, repairHP = tech.data.split(",")
    eff = Utils.getTechEff(tran, tech.id, obj.owner)
    maxRepaired = int(int(maxRepaired) * eff)
    repairHP = int(int(repairHP) * eff)
    repaired = 0
    # find damaged allied ship
    system = tran.db[obj.compOf]
    owner = tran.db[obj.owner]
    for relation in (REL_UNITY, REL_ALLY_LO):
        for fleetID in system.fleets:
            fleet = tran.db[fleetID]
            rel = tran.gameMngr.cmdPool[owner.type].getRelationTo(tran, owner, fleet.owner)
            if rel >= relation:
                # ok find ship to repair
                pl = tran.db[fleet.owner]
                index = 0
                for designID, hp, shield, exp in fleet.ships:
                    tech = pl.shipDesigns[designID]
                    if hp < tech.maxHP:
                        # repair damaged ship
                        fleet.ships[index][1] = min(tech.maxHP, hp + repairHP)
                        repaired += 1
                    index += 1
            if repaired >= maxRepaired:
                break
        if repaired >= maxRepaired:
            break

def finishStructOUTPOST(tran, source, target, tech):
    log.debug("Finishing OUTPOST", tech.id, "target", target.oid)
    # setup morale if colonizing noninhabited planet
    if target.storPop == 0:
        target.morale = Rules.maxMorale
    # try to change owner of planet
    tran.gameMngr.cmdPool[target.type].changeOwner(tran, target, source.owner)
    # increase population
    target.storPop += tech.unpackPop
    target.maxPop += tech.unpackPop

def finishStructSPORECOLONY(tran, source, target, tech):
    log.debug("Finishing SPORE COLONY", tech.id, "target", target.oid)
    # setup morale if colonizing noninhabited planet
    if target.storPop == 0:
        target.morale = Rules.maxMorale
    # try to change owner of planet
    tran.gameMngr.cmdPool[target.type].changeOwner(tran, target, source.owner)
    # increase population
    target.storPop += tech.unpackPop
    target.maxPop += tech.unpackPop

    if target.plSlots > 1:
        for i in range(len(target.slots),target.plSlots-1):
            target.slots.insert(0, Utils.newStructure(tran, 9013, source.owner))

def finishStructGOVCENTER(tran, source, target, tech):
    player = tran.db[source.owner]
    # delete old center
    planet = tran.db[player.planets[0]]
    slots = planet.slots[:] # copy
    slots.reverse()
    govStr = 0
    for slot in slots:
        tech = Rules.techs[slot[STRUCT_IDX_TECHID]]
        if tech.govPwr > 0 and planet.oid != target.oid:
            planet.slots.remove(slot)
            break
        elif tech.govPwr > 0:
            if govStr == 1:
                planet.slots.remove(slot)
                break
            else:
                govStr = 1
    # setup new one (move planet with new centre to the first position)
    player.planets.remove(target.oid)
    player.planets.insert(0, target.oid)
    # message
    Utils.sendMessage(tran, target, MSG_NEW_GOVCENTER, target.oid, None)

def validateTRUE(tran,source,target,tech):
    return 1;

## Ecosystem initiation
def validateProjectECOINIT3(tran, source, target, tech):
    return target.plBio == 0 and target.plType not in ('G', 'A', '-')

def finishProjectECOINIT3(tran, source, target, tech):
    target.plBio = Rules.projECOINIT3PlBio

## Habitable Surface Expansion
def validateProjectADDSLOT3(tran, source, target, tech):
    return target.plSlots < target.plMaxSlots and target.plType not in ('G', 'A', '-')

def finishProjectADDSLOT3(tran, source, target, tech):
    target.plSlots += 1

## Terraforming
def validateDeployTERRAFORM3(tran, source, target, tech):
    return validateProjectTERRAFORM3(tran, source, target, tech) and \
        target.owner==source.owner

def validateProjectTERRAFORM3(tran, source, target, tech):
    spec = Rules.planetSpec[target.plType]
    return spec.upgradeTo != None and \
        target.plEn >= spec.upgradeEnReqs[0] and \
        target.plEn <= spec.upgradeEnReqs[1] and \
        target.plBio >= spec.maxBio

def finishProjectTERRAFORM3(tran, source, target, tech):
    target.plType = Rules.planetSpec[target.plType].upgradeTo

## Uber Terraforming
def validateDeployTERRAFORMALIGNMENT6(tran, source, target, tech):
    return validateProjectTERRAFORMALIGNMENT6(tran, source, target, tech) and \
        target.owner==source.owner

def validateProjectTERRAFORMALIGNMENT6(tran, source, target, tech):
    log.debug('Validating TERRAFORM ALIGNMENT');
    spec = Rules.planetSpec[target.plType]
    return (target.plEnv < Rules.envMax or target.plBio < spec.upgradeEnReqs[0] or target.plBio > spec.upgradeEnReqs[1])

def finishProjectTERRAFORMALIGNMENT6(tran, source, target, tech):
    log.debug('Finishing TERRAFORM ALIGNMENT');
    spec = Rules.planetSpec[target.plType]
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    enAvg = int((spec.upgradeEnReqs[0] + spec.upgradeEnReqs[1]) / 2)
    delta = int(float(tech.data) * techEff)
    if target.plEn < enAvg:
        target.plEn = min(target.plEn+delta,enAvg)
    elif target.plEn > enAvg:
        target.plEn = max(target.plEn-delta,enAvg)
    target.plBio = min(target.plBio+int(delta/2),Rules.envMax)
    if validateProjectTERRAFORM3(tran, source, target, tech):
        target.plType = Rules.planetSpec[target.plType].upgradeTo

## Tech level advancement
def finishResTLAdvance(tran, player, tech):
    improvement = player.techs[tech.id]
    if improvement >= 3:
        player.techLevel = max(player.techLevel, tech.level + 1)
        player.race = tech.data

## Holidays
def finishProjectHOLIDAYS1(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    # no battle
    system = tran.db[source.compOf]
    if system.combatCounter == 0:
        source.morale = min(source.morale + int(tech.moraleTrgt * techEff), Rules.maxMorale)

## Produce resources
def finishProjectPRODRSRC(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    # raw resources
    target.storBio += int(tech.prodBio * techEff)
    target.storEn += int(tech.prodEn * techEff)
    # sci pts
    if target.owner != OID_NONE:
        owner = tran.db[target.owner]
        owner.sciPoints += int(tech.prodSci * techEff)

## Repair ships
def finishProjectREPAIRSHIPS2(tran, source, target, tech):
    spaceDocksTurn(tran, source, tech)

## Produce strategic resource
def finishProjectNF(tran, source, target, tech):
    if target.owner != OID_NONE:
        techEff = Utils.getTechEff(tran, tech.id, source.owner)
        # TODO success shall depend on the level of the technology
        owner = tran.db[target.owner]
        stratRes = int(tech.data)
        owner.stratRes[stratRes] = owner.stratRes.get(stratRes, 0) + 1
        Utils.sendMessage(tran, target, MSG_EXTRACTED_STRATRES, target.oid, stratRes)

## Antimatter transmutation
def finishProjectNF2(tran, source, target, tech):
    if target.owner != OID_NONE:
        techEff = Utils.getTechEff(tran, tech.id, source.owner)
        # TODO success shall depend on the level of the technology
        owner = tran.db[target.owner]
        stratRes = int(tech.data)
        owner.stratRes[stratRes] = owner.stratRes.get(stratRes, 0) + 4
        Utils.sendMessage(tran, target, MSG_EXTRACTED_ANTIMATTER_SYNTH, target.oid, stratRes)

## Upgrade ships
def finishProjectUPGRADESHIPS(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    # fleet upgrade pool
    if target.owner != OID_NONE:
        owner = tran.db[target.owner]
        owner.fleetUpgradePool += int(tech.prodProd * techEff)

## Deep scan
def finishProjectDEEPSPACESCAN(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    target.scannerPwr = int(float(tech.data) * techEff * target.scannerPwr)
    system = tran.db[target.compOf]
    system.scannerPwrs[target.owner] = max(system.scannerPwrs.get(target.owner, 0), target.scannerPwr)

## improve environment
def finishProjectIMPRENV(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    target.plEnv += int(float(tech.data) * techEff)

## QDev
def validateProjectCondPl(tran, source, target, tech):
    return target.plType == 'G'

def finishProjectCondPl(tran, source, target, tech):
    target.plType = 'R'
    target.plDiameter = target.plDiameter / 10
    target.plMaxSlots = target.plDiameter / 1000
    target.plSlots = target.plMaxSlots / 2

def validateProjectAssemblePl(tran, source, target, tech):
    return target.plType == 'A'

def finishProjectAssemblePl(tran, source, target, tech):
    target.plType = 'D'
    target.plDiameter = (random.randrange(1, 7) + random.randrange(1, 7) + 2) * 1000
    target.plMaxSlots = target.plDiameter / 1000
    target.plSlots = target.plMaxSlots / 2

def finishProjectAsteroidMining(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    minerals = min(int(float(tech.data) * techEff), target.plMin)
    target.plMin -= minerals
    source.plMin += minerals
    if source.plMin > 200:
        source.plMin = 200

def validateProjectBioEnrich(tran, source, target, tech):
    spec = Rules.planetSpec['E']
    return spec.upgradeTo != None and \
        target.plEn >= spec.upgradeEnReqs[0] and \
        target.plEn <= spec.upgradeEnReqs[1]

def finishProjectBioEnrich(tran, source, target, tech):
    target.plType = 'I'
    target.plBio = 200
    target.storPop = 1000

def validateProjectMinEnrich(tran, source, target, tech):
    return 1

def finishProjectMinEnrich(tran, source, target, tech):
    target.plMin = 200
    target.storPop = 1000

def validateProjectShiftPlDown(tran, source, target, tech):
    return target.plEn < 200

def finishProjectShiftPlDown(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    target.plEn = min(200, int(target.plEn + int(tech.data) * techEff))
    system = tran.db[target.compOf]
    tran.gameMngr.cmdPool[system.type].sortPlanets(tran, system, None)

def validateProjectShiftPlUp(tran, source, target, tech):
    return target.plEn > 0

def finishProjectShiftPlUp(tran, source, target, tech):
    techEff = Utils.getTechEff(tran, tech.id, source.owner)
    target.plEn = max(0, int(target.plEn - int(tech.data) * techEff))
    system = tran.db[target.compOf]
    tran.gameMngr.cmdPool[system.type].sortPlanets(tran, system, None)

## Pirate space docks
def getPirateFameMod(tran, player, system):
    mod = 1.0
    for planetID in system.planets:
        planet = tran.db[planetID]        
        if planet.owner == player.oid:
            # minimum reached, don't check rest
            return 0.0
        elif planet.plStratRes in (SR_TL3A, SR_TL3B, SR_TL3C):
            mod = min(mod, Rules.pirateTL3StratResColonyCostMod)
    return mod
    
def validateStructPIROUTPOST(tran, source, target, tech):
    player = tran.db[source.owner]
    if source.type == T_FLEET and target.owner != player.oid:
        mod = getPirateFameMod(tran, player, tran.db[target.compOf])
        return player.pirateFame >= int(mod * Rules.pirateColonyCostMod * len(player.planets))
    else:
        return True

def finishStructPIROUTPOST(tran, source, target, tech):
    log.debug("Finishing PIRATE OUTPOST", tech.id, "target", target.oid)
    player = tran.db[source.owner]
    famePenalty = 0
    if source.type == T_FLEET:
        mod = getPirateFameMod(tran, player, tran.db[target.compOf])
        log.debug(source.owner, "DEPLOYING MODULE -- BEFORE", player.pirateFame, mod)
        famePenalty = int(mod * Rules.pirateColonyCostMod * len(player.planets))
        log.debug(source.owner, "DEPLOYING MODULE -- AFTER", player.pirateFame - famePenalty, famePenalty)
    finishStructOUTPOST(tran, source, target, tech)
    player.pirateFame -= famePenalty

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
import random
import copy

from xml.dom.minidom import Node

import ige
import Const
import Rules
import Utils

from ige import log
from ige.IObject import IObject, public
from ige.IDataHolder import IDataHolder

class ISystem(IObject):

    typeID = Const.T_SYSTEM

    def init(self, obj):
        IObject.init(self, obj)
        #
        obj.x = 0.0
        obj.y = 0.0
        obj.planets = []
        obj.fleets = []
        obj.closeFleets = []
        obj.starClass = u'---' # Star clasification
        obj.signature = 100
        # renaming
        obj.lastNameChng = 0
        # combat
        obj.combatCounter = 0
        # system wide data
        obj.scannerPwrs = {}
        # mine field
        obj.minefield = {}  # for every owner (key) list of minefield (triplet) exists (mine_id, amount, last_deployed)

    def update(self, tran, obj):
        # check existence of all planets
        if 0:
            for planetID in obj.planets:
                if not tran.db.has_key(planetID):
                    log.debug("CONSISTENCY - planet %d from system %d does not exists" % (planetID, obj.oid))
                elif tran.db[planetID].type != Const.T_PLANET:
                    log.debug("CONSISTENCY - planet %d from system %d is not a Const.T_PLANET" % (planetID, obj.oid))
        # check that all .fleet are in .closeFleets
        for fleetID in obj.fleets:
            if fleetID not in obj.closeFleets:
                log.debug("CONSISTENCY - fleet %d is in .fleet but not in .closeFleets - adding" % fleetID)
                obj.closeFleets.append(fleetID)
        # check existence of all fleets
        for fleetID in obj.closeFleets:
            if not tran.db.has_key(fleetID):
                log.debug("CONSISTENCY - fleet %d from system %d does not exists" % (fleetID, obj.oid))
            elif tran.db[fleetID].type != Const.T_FLEET:
                log.debug("CONSISTENCY - fleet %d from system %d is not a Const.T_FLEET" % (fleetID, obj.oid))
        # delete nonexistent fleets
        index = 0
        while index < len(obj.closeFleets) and obj.closeFleets:
            fleet = tran.db.get(obj.closeFleets[index], None)
            if fleet == None:
                log.debug("CONSISTENCY - fleet %d does not exists" % obj.closeFleets[index])
                fleetID = obj.closeFleets[index]
                obj.closeFleets.remove(fleetID)
                obj.fleets.remove(fleetID)
            else:
                index += 1
        # check compOf
        if not tran.db.has_key(obj.compOf) or tran.db[obj.compOf].type != Const.T_GALAXY:
            log.debug("CONSISTENCY invalid compOf for system", obj.oid)
        # rebuild closeFleets attribute
        old = obj.closeFleets
        obj.closeFleets = []
        for fleetID in old:
            fleet = tran.db.get(fleetID, None)
            if fleet and fleet.closeSystem == obj.oid and fleetID not in obj.closeFleets:
                obj.closeFleets.append(fleetID)
        if old != obj.closeFleets:
            log.debug("System close fleets fixed", obj.oid, old, obj.closeFleets)

    def getReferences(self, tran, obj):
        return obj.planets

    def getScanInfos(self, tran, obj, scanPwr, player):
        result = IDataHolder()
        results = [result]
        if scanPwr >= Rules.level1InfoScanPwr:
            result._type = Const.T_SCAN
            result.scanPwr = scanPwr
            result.oid = obj.oid
            result.x = obj.x
            result.y = obj.y
            if hasattr(obj, 'destinationOid'):
                result.destinationOid = obj.destinationOid
            result.signature = obj.signature
            result.type = obj.type
            result.compOf = obj.compOf
            result.starClass = obj.starClass
        if scanPwr >= Rules.level2InfoScanPwr:
            result.name = obj.name
            result.combatCounter = obj.combatCounter
        if scanPwr >= Rules.level3InfoScanPwr:
            result.planets = obj.planets
            result.owner = obj.owner
            for planetID in obj.planets:
                planet = tran.db[planetID]
                if planet.owner == player: ####### This was player.owner, which made no sense. Hope this change doesn't break something
                    continue
                newPwr = scanPwr * planet.signature / obj.signature
                results.extend(self.cmd(planet).getScanInfos(tran, planet, newPwr, player))
        if scanPwr >= Rules.level4InfoScanPwr:
            result.fleets = obj.fleets
            for fleetID in obj.fleets:
                fleet = tran.db[fleetID]
                if fleet.owner == player:
                    continue
                newPwr = scanPwr * fleet.signature / obj.signature
                results.extend(self.cmd(fleet).getScanInfos(tran, fleet, newPwr, player))

            result.minefield = self.getMines(obj, player.oid)
            ownsMines = 1 if result.minefield else 0
            result.hasmines = min(2, len(self.getAllMines(obj))) - ownsMines
        return results

    @public(Const.AL_ADMIN)
    def processINITPhase(self, tran, obj, data):
        obj.scannerPwrs = {}

        return obj.planets

    @public(Const.AL_ADMIN)
    def processPRODPhase(self, tran, obj, data):
        # mine deployment
        owners = []
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner not in owners + [Const.OID_NONE]:
                owners.append(planet.owner)
        for owner_id in owners:
            self.deployMines(tran, obj, owner_id)
        return obj.planets

    @public(Const.AL_ADMIN)
    def processACTIONPhase(self, tran, obj, data):
        # distribute resources
        planets = {}
        # group planets by owner
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner != Const.OID_NONE:
                tmp = planets.get(planet.owner, [])
                tmp.append(planet)
                planets[planet.owner] = tmp
        # group planets if owners are allied
        # TODO
        # process each group
        for owner in planets.keys():
            # skip alone planets
            if len(planets[owner]) < 2:
                continue
            # process each resource
            for resName in ('Bio', 'En'):
                donors = []
                donees = []
                minRes = 'min%s' % resName
                maxRes = 'max%s' % resName
                storRes = 'stor%s' % resName
                donorsSum = 0
                doneesSum = 0
                # put planets into donors/donees
                for planet in planets[owner]:
                    if getattr(planet, storRes) > getattr(planet, minRes):
                        donors.append(planet)
                        donorsSum += getattr(planet, storRes) - getattr(planet, minRes)
                    elif getattr(planet, storRes) < getattr(planet, minRes):
                        donees.append(planet)
                        doneesSum += getattr(planet, minRes) - getattr(planet, storRes)
                #@log.debug('ISystem', obj.oid, 'Donors / donees for %s' % resName, donorsSum, doneesSum)
                # there are requests for donation and there is somebody able to donate
                if doneesSum > 0 and donorsSum > 0:
                    #@log.debug('ISystem', 'Redistributin %s for' % resName, owner)
                    # give
                    balance = 0
                    tmpRatio = min(float(doneesSum) / donorsSum, 1.0)
                    for planet in donees:
                        diff = getattr(planet, minRes) - getattr(planet, storRes)
                        amount = int(float(diff) / doneesSum * donorsSum * tmpRatio)
                        #@log.debug('ISystem', 'Give res', planet.oid, amount)
                        balance -= amount
                        setattr(planet, storRes, getattr(planet, storRes) + amount)
                    # take
                    assert donorsSum + balance >= 0
                    lastPlanet = None
                    tmpRatio = min(float(donorsSum) / doneesSum, 1.0)
                    for planet in donors:
                        diff = getattr(planet, storRes) - getattr(planet, minRes)
                        amount = int(float(diff) / donorsSum * doneesSum * tmpRatio)
                        balance += amount
                        #@log.debug('ISystem', 'Take res', planet.oid, amount)
                        setattr(planet, storRes, getattr(planet, storRes) - amount)
                        lastPlanet = planet
                    # fix rounding error
                    setattr(lastPlanet, storRes, getattr(lastPlanet, storRes) + balance)
                    #@log.debug('ISystem', 'Rounding error', balance)
                # try to move additional resources to the other planets
                for planet in planets[owner]:
                    if getattr(planet, storRes) > getattr(planet, maxRes):
                        excess = getattr(planet, storRes) - getattr(planet, maxRes)
                        #@log.debug('ISystem', 'Trying to move excess rsrcs from', planet.oid, excess)
                        for planet2 in planets[owner]:
                            if planet == planet2:
                                continue
                            if getattr(planet2, storRes) < getattr(planet2, maxRes):
                                space = getattr(planet2, maxRes) - getattr(planet2, storRes)
                                amount = min(space, excess)
                                #@log.debug('ISystem', 'Moved to', planet2.oid, amount)
                                setattr(planet2, storRes, getattr(planet2, storRes) + amount)
                                excess -= amount
                                if excess == 0:
                                    break
                        #@log.debug('ISystem', 'Cannot move excess rsrcs on', planet.oid, excess)
                        setattr(planet, storRes, getattr(planet, maxRes) + excess)
        # process planets and fleets
        #@log.debug("System close fleets", obj.oid, obj.closeFleets)
        return obj.planets[:] + obj.closeFleets[:]

    @public(Const.AL_ADMIN)
    def getObjectsInSpace(self, tran, obj):
        inSpace = obj.closeFleets[:]
        for fleetID in obj.fleets:
            try:
                inSpace.remove(fleetID)
            except ValueError:
                log.warning(obj.oid, "Cannot remove fleet from closeFleets", fleetID, obj.fleets, obj.closeFleets)
        return inSpace

    @public(Const.AL_ADMIN)
    def processBATTLEPhase(self, tran, obj, data):
        system = obj
        #@log.debug('ISystem', 'BATTLE - system', obj.oid)
        # we are processing fleets, planets, ...
        objects = obj.planets[:] + obj.fleets[:]
        # shuffle them to prevent predetermined one-sided battles (temporary hack)
        random.shuffle(objects)
        # store owners of objects
        # find enemies and allies
        attack = {}
        allies = {}
        owners = {}
        ownerIDs = {}
        systemAtt = {}
        systemDef = {}
        hasMine = {}
        isOwnedObject = 0
        for objID in objects:
            attack[objID] = []
            allies[objID] = []
            owner = tran.db[objID].owner
            owners[objID] = owner
            ownerIDs[owner] = owner
            if owner != Const.OID_NONE:
                isOwnedObject = 1
        for owner in ownerIDs:
            tempAtt, tempDef = self.getSystemCombatBonuses(tran, system, owner)
            systemAtt[owner] = tempAtt
            systemDef[owner] = tempDef
            hasMine[owner] = self.getSystemMineSource(tran, system, owner)
        if not isOwnedObject:
            #@log.debug('ISystem', 'No combat')
            # reset combat counters
            system.combatCounter = 0
            return
        # first - direct ones
        index = 1
        for obj1ID in objects:
            obj1 = tran.db[obj1ID]
            if obj1.owner == Const.OID_NONE:
                index += 1
                continue
            commander = tran.db[obj1.owner]
            # relationships
            #for obj2ID in objects[index:]:
            for obj2ID in objects:
                obj2 = tran.db[obj2ID]
                if obj2.owner == Const.OID_NONE or obj1 is obj2:
                    continue
                if obj1.owner == obj2.owner:
                    allies[obj1ID].append(obj2ID)
                    allies[obj2ID].append(obj1ID)
                    continue
                # planet and military object
                elif obj1.type == Const.T_PLANET and obj2.isMilitary and \
                    not self.cmd(commander).isPactActive(tran, commander, obj2.owner, Const.PACT_ALLOW_MILITARY_SHIPS):
                    #@log.debug("ISystem pl - mil", obj1ID, obj2ID)
                    if obj2ID not in attack[obj1ID]:
                        attack[obj1ID].append(obj2ID)
                    if obj1ID not in attack[obj2ID]:
                        attack[obj2ID].append(obj1ID)
                # planet and civilian object
                elif obj1.type == Const.T_PLANET and not obj2.isMilitary and \
                    not self.cmd(commander).isPactActive(tran, commander, obj2.owner, Const.PACT_ALLOW_CIVILIAN_SHIPS):
                    #@log.debug("ISystem pl - civ", obj1ID, obj2ID)
                    if obj2ID not in attack[obj1ID]:
                        attack[obj1ID].append(obj2ID)
                    if obj1ID not in attack[obj2ID]:
                        attack[obj2ID].append(obj1ID)
                # military and military object
                elif obj1.isMilitary and obj2.isMilitary and \
                    not self.cmd(commander).isPactActive(tran, commander, obj2.owner, Const.PACT_ALLOW_MILITARY_SHIPS):
                    #@log.debug("ISystem mil - mil", obj1ID, obj2ID)
                    if obj2ID not in attack[obj1ID]:
                        attack[obj1ID].append(obj2ID)
                    if obj1ID not in attack[obj2ID]:
                        attack[obj2ID].append(obj1ID)
                # military and civilian object
                elif obj1.isMilitary and not obj2.isMilitary and \
                    not self.cmd(commander).isPactActive(tran, commander, obj2.owner, Const.PACT_ALLOW_CIVILIAN_SHIPS):
                    #@log.debug("ISystem mil - civ", obj1ID, obj2ID)
                    if obj2ID not in attack[obj1ID]:
                        attack[obj1ID].append(obj2ID)
                    if obj1ID not in attack[obj2ID]:
                        attack[obj2ID].append(obj1ID)
                # planet and fleet
                #elif obj1.type == Const.T_PLANET and obj2.type == Const.T_FLEET and \
                #    self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_MUTUAL_DEFENCE):
                #    allies[obj1ID].append(obj2ID)
                #    allies[obj2ID].append(obj1ID)
                # fleet and fleet
                #elif obj1.type == Const.T_FLEET and obj2.type == Const.T_FLEET and \
                #    self.cmd(commander).isPactActive(tran, commander, obj2.owner, PACT_MUTUAL_OFFENCE):
                #    allies[obj1ID].append(obj2ID)
                #    allies[obj2ID].append(obj1ID)
            index += 1
        #@log.debug('ISystem', 'Targets:', targets)
        #@log.debug('ISystem', 'Allies:', allies)
        # find indirect a/e
        #for objID in objects:
        #    iTargets = []
        #    iAllies = []
        #    # find indirect a/e
        #    todo = allies[objID][:]
        #    while todo:
        #        id = todo.pop(0)
        #        iTargets.extend(targets[id])
        #        for tmpID in allies[id]:
        #            if tmpID not in iAllies:
        #                todo.append(tmpID)
        #                iAllies.append(tmpID)
        #    # remove allies from targets
        #    for id in iAllies:
        #        if id in iTargets:
        #            iTargets.remove(id)
        #    # IMPORTATNT preffer NOT to fire at possible allies
        #    # add my targets
        #    #for id in targets[objID]:
        #    #    if id not in iTargets:
        #    #        iTargets.append(id)
        #    # that's all folks
        #    for id in iTargets:
        #        if objID not in attack[id]:
        #            attack[id].append(objID)
        #        if id not in attack[objID]:
        #            attack[objID].append(id)
        # NOT VALID: objects with action ACTION_ATTACK will attack only their targets
        # check, if there are any targets
        isCombat = 0
        for objID in objects:
            if attack[objID]:
                isCombat = 1
                break #end loop
        if not isCombat:
            #@log.debug('ISystem', 'No combat')
            # reset combat counters
            system.combatCounter = 0
            for fleetID in system.fleets:
                tran.db[fleetID].combatCounter = 0
            return
        # increase combat counters
        system.combatCounter += 1
        for fleetID in system.fleets:
            tran.db[fleetID].combatCounter += 1
        # debug
        log.debug('ISystem', 'Final attacks in system %d:' % system.oid, attack)
        # mines detonate before battle
        shots = {}
        targets = {}
        firing = {}
        damageCaused = {}
        killsCaused = {}
        damageTaken = {}
        shipsLost = {}
        minesTriggered = {}
        fleetOwners = {}
        isCombat = False
        isMineCombat = False
        for owner in ownerIDs:
            if owner not in hasMine: # no planets
                continue
            if not hasMine[owner]: # no planet with control structure
                continue
            controlPlanetID = hasMine[owner][0]  # there is list returned, all planets have same effect
            if len(self.getMines(system, owner)) == 0:
                continue # no mines, something broke
            if len(attack[controlPlanetID]) == 0:
                continue # no targets
            isMineFired = True
            mineTargets = copy.copy(attack[controlPlanetID])
            while isMineFired:
                while len(mineTargets) > 0:
                    targetID = random.choice(mineTargets) # select random target
                    targetobj = tran.db.get(targetID, None)
                    try:
                        if targetobj.type == Const.T_FLEET:
                            fleetOwners[targetID] = targetobj.owner
                            break # target found
                        mineTargets.remove(targetID)  # remove an object type that a mine can't hit from the temporary targets list
                    except:
                        mineTargets.remove(targetID)  # remove a dead fleet from the temporary targets list

                if len(mineTargets) == 0:
                    break # no fleet targets for mines
                temp, temp, firing[targetID] = self.cmd(targetobj).getPreCombatData(tran, targetobj)  # fix firing for "surrender to" section
                damage, att, ignoreshield, mineID = self.cmd(obj).fireMine(system, owner)
                if not damage: # no more mines
                    isMineFired = False
                    break
                log.debug('ISystem', 'Mine Shooting (damage, att, ignore shield):', damage, att, ignoreshield)
                isMineCombat = True
                minesTriggered[mineID] = minesTriggered.get(mineID, 0) + 1
                # Process Combat
                # for now we assume only one ship can be destroyed by one mine
                dmg, destroyed = self.cmd(targetobj).applyMine(tran, targetobj, att, damage, ignoreshield)
                #log.debug('ISystem-Mines', 'Actual Damage Done:',dmg)
                if dmg > 0:
                    damageTaken[targetID] = damageTaken.get(targetID, 0) + dmg
                    shipsLost[targetID] = shipsLost.get(targetID, 0) + destroyed
                    killsCaused[mineID] = killsCaused.get(mineID, 0) + destroyed
                if dmg > 0:
                    damageCaused[mineID] = damageCaused.get(mineID, 0) + dmg
            # send messages about mine effects to the owner of the minefield
            # collect hit players
            players = {}
            for triggerID in firing.keys():
                players[owners[triggerID]] = None
            controllerPlanet = tran.db.get(controlPlanetID, None)
            damageCausedSum = 0
            killsCausedSum = 0
            for mineID in damageCaused.keys():
                damageCausedSum = damageCausedSum + damageCaused.get(mineID, 0)
                killsCausedSum = killsCausedSum + killsCaused.get(mineID, 0)
            Utils.sendMessage(tran, controllerPlanet, Const.MSG_MINES_OWNER_RESULTS, system.oid, (players.keys(),(damageCaused, killsCaused, minesTriggered),damageCausedSum,killsCausedSum))
        # send messages to the players whose fleets got hit by minefields
        for targetID in damageTaken.keys():
            targetFleet = tran.db.get(targetID, None)
            if targetFleet:
                Utils.sendMessage(tran, targetFleet, Const.MSG_MINES_FLEET_RESULTS, system.oid, (damageTaken[targetID], shipsLost[targetID]))
            else:
                targetFleet = IDataHolder()
                targetFleet.oid = fleetOwners[targetID]
                Utils.sendMessage(tran, targetFleet, Const.MSG_MINES_FLEET_RESULTS, system.oid, (damageTaken[targetID], shipsLost[targetID]))
                Utils.sendMessage(tran, targetFleet, Const.MSG_DESTROYED_FLEET, system.oid, ())
        damageCaused = {}
        killsCaused = {}
        damageTaken = {}
        shipsLost = {}
        # now to battle
        for objID in objects:
            obj = tran.db.get(objID, None)
            # get shots from object, should be sorted by weaponClass
            # shots = [ shot, ...], shot = (combatAtt, weaponID)
            # get target classes and numbers
            # (class1, class2, class3, class4)
            # cls0 == fighters, cls1 == midships, cls2 == capital ships, cls3 == planet installations
            #@log.debug(objID, obj.name, "getting pre combat data")
            if obj: # source already destroyed; ignore
                shots[objID], targets[objID], firing[objID] = self.cmd(obj).getPreCombatData(tran, obj)
                if firing[objID]:
                    isCombat = True
        if not isCombat and not isMineCombat:
            # no shots has been fired
            #@log.debug('ISystem', 'No combat')
            # reset combat counters
            system.combatCounter = 0
            for fleetID in system.fleets:
                tran.db[fleetID].combatCounter = 0
            return
        #@log.debug("Shots:", shots)
        #@log.debug("Targets", targets)
        if isCombat:
            for shotIdx in (3, 2, 1, 0):
                for objID in objects:
                    # obj CAN be deleted at this point
                    obj = tran.db.get(objID, None)
                    if obj == None:
                        continue # source already destroyed; move to next source
                    # if object is fleet, then it's signature is max
                    if obj and obj.type == Const.T_FLEET:
                        obj.signature = Rules.maxSignature
                    # target preselection
                    totalClass = [0, 0, 0, 0]
                    total = 0
                    for targetID in attack[objID]:
                        totalClass[0] += targets[targetID][0]
                        totalClass[1] += targets[targetID][1]
                        totalClass[2] += targets[targetID][2]
                        totalClass[3] += targets[targetID][3]
                    total = totalClass[0] + totalClass[1] + totalClass[2] + totalClass[3]
                    # process shots
                    for combatAtt, weaponID in shots[objID][shotIdx]:
                        weapon = Rules.techs[weaponID]
                        weaponClass = weapon.weaponClass
                        if total == 0:
                            # there are no targets
                            break
                        #@log.debug('ISystem', 'Processing shot', objID, weapon.name, weaponClass)
                        # process from weaponClass up
                        # never shoot on smaller ships than weaponClass
                        applied = 0
                        for tmpWpnClass in xrange(weaponClass, 4):
                            #@log.debug('ISystem', 'Trying target class', tmpWpnClass, totalClass[tmpWpnClass])
                            # select target
                            if totalClass[tmpWpnClass]:
                                target = Utils.rand(0, totalClass[tmpWpnClass])
                                #@log.debug('ISystem', 'Target rnd num', target, totalClass[tmpWpnClass])
                                for targetID in attack[objID]:
                                    if target < targets[targetID][tmpWpnClass]:
                                        #@log.debug(objID, 'attacks', targetID, tmpWpnClass)
                                        # targetID can be deleted at this point
                                        anObj = tran.db.get(targetID, None)
                                        if anObj:
                                            dmg, destroyed, destroyedClass = self.cmd(anObj).applyShot(tran, anObj, systemDef[owners[targetID]], combatAtt + systemAtt[owners[objID]], weaponID, tmpWpnClass, target)
                                            #@log.debug("ISystem result", dmg, destroyed, destroyedClass, tmpWpnClass)
                                            #@print objID, 'dmg, destroyed', dmg, destroyed
                                            damageTaken[targetID] = damageTaken.get(targetID, 0) + dmg
                                            if destroyed > 0:
                                                shipsLost[targetID] = shipsLost.get(targetID, 0) + destroyed
                                                total -= destroyed
                                                totalClass[destroyedClass] -= destroyed
                                            if dmg > 0 and obj:
                                                obj.combatExp += dmg
                                                damageCaused[objID] = damageCaused.get(objID, 0) + dmg
                                            applied = 1
                                        else:
                                            continue # target already destroyed, move to next target
                                        break
                                    else:
                                        #@log.debug('ISystem', 'Lovering target by', targets[targetID][tmpWpnClass])
                                        target -= targets[targetID][tmpWpnClass]
                            if applied:
                                break
        # send messages and modify diplomacy relations
        # distribute experience pts
        for objID in objects:
            obj = tran.db.get(objID, None)
            if obj:
                self.cmd(obj).distributeExp(tran, obj)
            if attack[objID]:
                source = obj or tran.db[owners[objID]]
                # collect players
                players = {}
                for attackerID in attack[objID]:
                    players[owners[attackerID]] = None
                d1 = damageTaken.get(objID,0)
                d2 = damageCaused.get(objID,0)
                l = shipsLost.get(objID, 0)
                if d1 or d2 or l:
                    # send only if damage is taken/caused
                    Utils.sendMessage(tran, source, Const.MSG_COMBAT_RESULTS, system.oid, (d1, d2, l, players.keys()))
                if not obj:
                    # report DESTROYED status
                    Utils.sendMessage(tran, source, Const.MSG_DESTROYED_FLEET, system.oid, ())
                # modify diplomacy relations
                objOwner = tran.db[owners[objID]]
                for attackerID in attack[objID]:
                    attOwner = tran.db.get(owners[attackerID], None)
                    # owner of the fleet
                    rel = self.cmd(objOwner).getDiplomacyWith(tran, objOwner, attOwner.oid)
                    rel.relChng = Rules.relLostWhenAttacked
                    # attacker
                    rel = self.cmd(attOwner).getDiplomacyWith(tran, attOwner, objOwner.oid)
                    rel.rechChng = Rules.relLostWhenAttacked
        # check if object surrenders
        for objID in objects:
            # object surrender IFF it and its allies had target and was not able
            # to fire at it, planet is not counted as ally in this case
            obj = tran.db.get(objID, None)
            if firing[objID] and obj:
                continue
            surrenderTo = []
            for attID in attack[objID]:
                if firing[attID] and tran.db.has_key(attID):
                    surrenderTo.append(tran.db[attID].owner)
            for allyID in allies[objID]:
                if not tran.db.has_key(allyID):
                    continue
                ally = tran.db[allyID]
                if firing[allyID] and ally.type != Const.T_PLANET:
                    surrenderTo = []
                    break
            if surrenderTo:
                index = Utils.rand(0, len(surrenderTo))
                if obj:
                    if self.cmd(obj).surrenderTo(tran, obj, surrenderTo[index]):
                        winner = tran.db[surrenderTo[index]]
                        source = tran.db.get(owners[objID], None)
                        log.debug('ISystem', 'BATTLE - surrender', objID, surrenderTo[index], surrenderTo)
                        if source:
                            Utils.sendMessage(tran, source, Const.MSG_COMBAT_LOST, system.oid, winner.oid)
                            Utils.sendMessage(tran, winner, Const.MSG_COMBAT_WON, system.oid, source.oid)
                        else:
                            Utils.sendMessage(tran, winner, Const.MSG_COMBAT_WON, system.oid, obj.oid)
                else:
                    winner = tran.db[surrenderTo[index]]
                    source = tran.db[owners[objID]]
                    log.debug('ISystem', 'BATTLE - surrender', objID, surrenderTo[index], surrenderTo)
                    Utils.sendMessage(tran, source, Const.MSG_COMBAT_LOST, system.oid, winner.oid)
                    Utils.sendMessage(tran, winner, Const.MSG_COMBAT_WON, system.oid, source.oid)
        return

    @public(Const.AL_ADMIN)
    def processFINALPhase(self, tran, obj, data):
        # TODO find new starting points
        # clean up mines if system ownership was lost
        owners = []
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner not in owners:
                owners.append(planet.owner)
        for ownerid in obj.minefield.keys():
            if ownerid not in owners:
                self.clearMines(obj, ownerid)
        return obj.planets[:] + obj.closeFleets[:]

    def sortPlanets(self, tran, obj, data):
        obj.planets.sort(key=lambda planetID: tran.db[planetID].plEn, reverse = True)
        orbit = 1
        for planetID in obj.planets:
            planet = tran.db[planetID]
            planet.orbit = orbit
            orbit += 1

    @public(Const.AL_NONE)
    def rename(self, tran, obj, newName, nType):
        newName = newName.strip()
        # you have to own all planets
        # TODO: Throw another cmdr exc AFTER you have no planet
        haveOne = 0
        anotherComm = 0
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner != tran.session.cid and planet.owner != Const.OID_NONE:
                anotherComm = 1
            if planet.owner == tran.session.cid:
                haveOne = 1
        if not haveOne:
            raise ige.GameException('You cannot change name of this system - you have no planet in this system.')
        if anotherComm:
            raise ige.GameException('You cannot change name of this system - another commander in system.')
        # check validity of name
        if not Utils.isCorrectName(newName):
            raise ige.GameException('Invalid name. Only characters, digits, space, dot and dash permitted, max. length is 30 characters.')
        # check if there is other system with this name
        galaxy = tran.db[obj.compOf]
        for systemID in galaxy.systems:
            if tran.db[systemID].name == newName and systemID != obj.oid:
                raise ige.GameException('This name is already used.')
        # TODO you have to own this system longer than previous owner
        # one change per 1 day allowed
        turn = tran.db[Const.OID_UNIVERSE].turn
        if obj.lastNameChng + Rules.turnsPerDay <= turn:
            # rename system
            obj.name = newName
            # rename planets
            newNames = [obj.name]
            for planetID in obj.planets:
                planet = tran.db[planetID]
                planet.name = Utils.getPlanetName(obj.name, nType, planet.orbit - 1)
                newNames.append(planet.name)
            obj.lastNameChng = turn
        else:
            raise ige.GameException('You cannot change name of this system - name has been changed recently (try it one day later).')
        return newNames

    def createPlanet(self, tran, obj):
        planet = self.new(Const.T_PLANET)
        planet.compOf = obj.oid
        oid = tran.db.create(planet)
        obj.planets.append(oid)
        return oid

    @public(Const.AL_ADMIN)
    def deployMines(self, tran, obj, owner_id):
        """ Go through all mine control structures and attempt to add mines.

        """
        for tech, struct in self.getSystemMineLauncher(tran, obj, owner_id):
            if not struct[Const.STRUCT_IDX_STATUS] & Const.STRUCT_STATUS_ON:
                # structure is offline, reset timer
                self.addMine(tran, obj, owner_id, tech.mineclass, 0)
                continue
            efficiency = struct[Const.STRUCT_IDX_HP] / float(tech.maxHP)
            minerate = int(tech.minerate / efficiency)
            minenum = int(tech.minenum * efficiency)
            if self.addMine(tran, obj, owner_id, tech.mineclass, minenum, minerate):
                log.debug('ISystem', 'Mine deployed for owner %d in system %d' % (owner_id, obj.oid))

    def _expandExistingMinefield(self, minefields, index, current_turn, max_amount, mine_rate):
        mine_id, amount, deploy_turn = minefields[index]
        if max_amount is not None and amount >= max_amount:
            # cannot add more, thus update deploy turn to current one
            # (so replenish starts after that amount of turns if needed)
            minefields[index] = (mine_id, amount, current_turn)
            return False
        if mine_rate and (current_turn - deploy_turn) < mine_rate:
            # need more time to deploy new mine
            return False
        minefields[index] = (mine_id, amount + 1, current_turn)
        return True

    @public(Const.AL_ADMIN)
    def addMine(self, tran, obj, owner_id, mine_tech_id, max_amount=None, mine_rate=None):
        """ Increment amount within particular minefield of particular player.
        Set current turn as a date of latest deployment.

        Returns True if mine was added.

        """
        current_turn = tran.db[obj.compOf].galaxyTurn
        if owner_id in obj.minefield:
            index = -1
            for mine_id, amount, deploy_turn in obj.minefield[owner_id]:
                index += 1
                if mine_id != mine_tech_id:
                    continue
                return self._expandExistingMinefield(obj.minefield[owner_id], index, current_turn, max_amount, mine_rate)
            # owner has some minefield, but not this type
            obj.minefield[owner_id].append((mine_tech_id, 1, current_turn))
            return True
        else:
            # this will be owner's first minefield in this system
            if mine_rate == 1 or mine_rate is None:
                obj.minefield[owner_id] = [(mine_tech_id, 1, current_turn)]
                return True
            else:
                obj.minefield[owner_id] = [(mine_tech_id, 0, current_turn - 1)]
                return False


    @public(Const.AL_ADMIN)
    def removeMine(self, obj, owner_id, mine_tech_id):
        """ Decrement amount within particular minefield of particular player.
        It's not possible to clean up records - it's expected to stay there till
        the end of game like that.

        """
        if owner_id in obj.minefield:
            index = -1
            for mine_id, amount, deploy_turn in obj.minefield[owner_id]:
                index += 1
                if mine_id != mine_tech_id or amount == 0:
                    continue
                amount -= 1
                obj.minefield[owner_id][index] = (mine_id, amount, deploy_turn)
                break

    def getMines(self, obj, owner_id):
        """ Return list of tuples representing each minefield.

        """
        try:
            return [mines for mines in obj.minefield[owner_id] if mines[Const.MINE_IDX_AMOUNT]]
        except KeyError:
            return []

    def getAllMines(self, obj):
        """ Return list of tuples representing each minefield.

        """
        minefields = {}
        for owner_id in obj.minefield:
            mines = self.getMines(obj, owner_id)
            if mines:
                minefields[owner_id] = mines
        return minefields

    def clearMines(self, obj, owner_id):
        """ Remove all minefields of given owner from the system.

        """
        if owner_id in obj.minefield:
            del obj.minefield[owner_id]

    @public(Const.AL_ADMIN)
    def fireMine(self, obj, owner_id): # shoot the mine
        if owner_id not in obj.minefield:
            return False, False, False, False

        mine_ids = []
        amounts = []
        for mine_id, amount, deploy_turn in obj.minefield[owner_id]:
            mine_ids.append(mine_id)
            amounts.append(amount)
        if not sum(amounts):
            return False, False, False, False
        mine = Utils.weightedRandom(mine_ids, amounts) # select random mine to detonate
        self.removeMine(obj, owner_id, mine)
        tech = Rules.techs[mine]
        damage = random.randrange(tech.weaponDmgMin, tech.weaponDmgMax)
        attack = tech.weaponAtt
        ignore_shield = tech.weaponIgnoreShield
        return damage, attack, ignore_shield, mine

    def getSystemMineLauncher(self, tran, obj, playerID):
        launchers = []
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner == playerID:
                for struct in planet.slots:
                    tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
                    if tech.mineclass:
                        launchtech = tech
                        launchers.append((launchtech, struct))
        return launchers

    def getSystemMineSource(self, tran, obj, playerID):
        sources = []
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner == playerID:
                for struct in planet.slots:
                    tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
                    if tech.mineclass:
                        sources.append(planetID)
        return sources

    def getSystemCombatBonuses(self, tran, obj, playerID):
        systemAtt = 0;
        systemDef = 0;
        for planetID in obj.planets:
            planet = tran.db[planetID]
            if planet.owner == playerID:
                for struct in planet.slots:
                    tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
                    techEff = Utils.getTechEff(tran, struct[Const.STRUCT_IDX_TECHID], planet.owner)
                    if tech.systemAtt > 0 or tech.systemDef > 0:
                        systemAtt = max(systemAtt, tech.systemAtt * techEff)
                        systemDef = max(systemDef, tech.systemDef * techEff)
        return (systemAtt, systemDef)

    def loadDOMNode(self, tran, obj, xoff, yoff, node):
        obj.x = float(node.getAttribute('x')) + xoff
        obj.y = float(node.getAttribute('y')) + yoff
        orbit = 1
        nType = Utils.getPlanetNamesType()
        for elem in node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                name = elem.tagName
                if name == 'properties':
                    self.loadDOMAttrs(obj, elem)
                elif name == 'planet':
                    # create planet
                    planet = tran.db[self.createPlanet(tran, obj)]
                    self.cmd(planet).loadDOMNode(tran, planet, obj.x, obj.y, orbit, elem)
                    # planet.name = u'%s %s' % (obj.name, '-ABCDEFGHIJKLMNOPQRSTUVWXYZ'[orbit])
                    planet.name = Utils.getPlanetName(obj.name, nType, orbit - 1)
                    orbit += 1
                else:
                    raise ige.GameException('Unknown element %s' % name)
        return Const.SUCC

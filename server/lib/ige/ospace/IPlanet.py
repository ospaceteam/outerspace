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
import math
import random

from xml.dom.minidom import Node

import ige
import Const
import Rules
import Utils
import ShipUtils

from ige import log
from ige.IObject import IObject, public
from ige.IDataHolder import IDataHolder

class IPlanet(IObject):

    typeID = Const.T_PLANET

    def init(self, obj):
        IObject.init(self, obj)
        #
        obj.x = 0.0
        obj.y = 0.0
        obj.plDiameter = 0
        obj.plType = u'-'
        obj.plMin = 0
        obj.plBio = 0
        obj.plEn = 0
        obj.plEnv = 0
        obj.plSlots = 0
        obj.plMaxSlots = 0
        obj.plStratRes = 0
        obj.plDisease = 0
        obj.plStarting = 0
        obj.orbit = 0
        obj.storPop = 0
        obj.slots = []
        obj.lastPirCapture = 0
        # storage
        obj.storBio = 0
        obj.storEn = 0
        obj.minBio = Rules.colonyMinBio
        obj.minEn = Rules.colonyMinEn
        obj.maxBio = 0
        obj.maxEn = 0
        # changes/prod
        obj.prodQueue = []
        obj.globalQueue = 0
        obj.changeBio = 0
        obj.changeEn = 0
        obj.changePop = 0
        obj.changeEnv = 0
        obj.prodProd = 0
        obj.effProdProd = 0
        obj.prodSci = 0
        obj.effProdSci = 0
        obj.unemployedPop = 0
        # eating / housing
        obj.popEatBio = 10
        obj.popEatEn = 0
        obj.maxPop = 0
        # extra goodies
        obj.solarmod = 0
        obj.scannerPwr = 0
        obj.signature = 75
        obj.autoMinStor = 1
        obj.morale = Rules.maxMorale
        obj.changeMorale = 0.0
        obj.moraleTrgt = 0.0
        # moraleModifiers [ base morale by distance from homeworld, from buildings, from population, from unemployment, summary 1+2+3+4 ]
        obj.moraleModifiers = [0.0, 0.0, 0.0, 0.0, 0.0]
        obj.revoltLen = 0
        obj.combatExp = 0
        obj.isMilitary = 0
        obj.refuelMax = 0
        obj.refuelInc = 0
        obj.repairShip = 0.0
        obj.upgradeShip = 0.0
        obj.trainShipInc = 0
        obj.trainShipMax = 0
        obj.fleetSpeedBoost = 1.0
        obj.ownerSince = 0
        obj.shield = 0          #current planetary shield level
        obj.maxShield = 0       #structural max sheild (best structure method)
        obj.prevShield = 0      #previous turn's shield level (for client growth calculation)

    @public(Const.AL_FULL)
    def startConstruction(self, tran, obj, techID, quantity, targetID, isShip, reportFinished,
        demolishStruct):
        if len(obj.prodQueue) > Rules.maxProdQueueLen:
            raise ige.GameException('Queue is full.')
        if quantity < 1:
            raise ige.GameException("Quantity must be greater than 0")
        player = tran.db[obj.owner]
        if not player.techs.has_key(techID) and isShip == 0:
            raise ige.GameException('You do not own this kind of technology.')
        if not player.shipDesigns.has_key(techID) and isShip == 1:
            raise ige.GameException('You do not own this ship design.')
        if targetID not in tran.db[obj.compOf].planets:
            raise ige.GameException('You can build only in the same system.')
        if isShip:
            tech = player.shipDesigns[techID]
            if tech.upgradeTo:
                raise ige.GameException("You cannot build obsolete ship design.")
        else:
            tech = Rules.techs[techID]
            if not (tech.isStructure or tech.isProject):
                raise ige.GameException('You cannot construct this technology.')
            if not tech.validateConstrHandler(tran, obj, tran.db[targetID], tech):
                raise ige.GameException('Conditions for construction are not satisfied.')
        neededSR = {}
        for sr in tech.buildSRes:
            nSR = neededSR.get(sr, 0) + quantity * tech.buildSRes[sr]
            if player.stratRes.get(sr, 0) < nSR:
                raise ige.GameException("You do not own enough of required strategic resource(s)")
            neededSR[sr] = nSR
        # consume strategic resources
        for sr in neededSR:
            player.stratRes[sr] -= neededSR[sr]
        # start construction
        item = IDataHolder()
        item.techID = techID
        item.currProd = 0
        item.currTurn = 0
        item.quantity = int(quantity)
        item.targetID = targetID
        item.changePerc = 0
        item.isShip = bool(isShip)
        item.reportFin = bool(reportFinished)
        item.demolishStruct = demolishStruct
        item.type = Const.T_TASK
        obj.prodQueue.append(item)
        return obj.prodQueue, player.stratRes

    @public(Const.AL_FULL)
    def changeConstruction(self, tran, obj, index, quantity):
        if index < 0 or index >= len(obj.prodQueue):
            raise ige.GameException("No such item in the construction queue.")

        if quantity < 1:
            raise ige.GameException("Quantity must be greater than 0")

        player = tran.db[obj.owner]
        item = obj.prodQueue[index]
        if item.isShip:
            tech = player.shipDesigns[item.techID]
        else:
            tech = Rules.techs[item.techID]

        quantityChange = quantity - obj.prodQueue[index].quantity

        neededSR = {}
        for sr in tech.buildSRes:
            nSR = neededSR.get(sr, 0) + quantityChange * tech.buildSRes[sr]
            if player.stratRes.get(sr, 0) < nSR:
                raise ige.GameException("You do not own enough of required strategic resource(s)")
            neededSR[sr] = nSR
        # consume strategic resources
        for sr in neededSR:
            player.stratRes[sr] -= neededSR[sr]

        obj.prodQueue[index].quantity = quantity
        return obj.prodQueue, player.stratRes

    @public(Const.AL_FULL)
    def abortConstruction(self, tran, obj, index):
        if index >= len(obj.prodQueue):
            raise ige.GameException('No such item in the construction queue.')
        # Free strategic resources
        player = tran.db[obj.owner]
        item = obj.prodQueue[index]
        if item.isShip:
            tech = player.shipDesigns[item.techID]
        else:
            tech = Rules.techs[item.techID]
        for sr in tech.buildSRes:
            player.stratRes[sr] = player.stratRes.get(sr, 0) + item.quantity * tech.buildSRes[sr]
        # delete task
        del obj.prodQueue[index]
        return obj.prodQueue, player.stratRes

    @public(Const.AL_FULL)
    def moveConstrItem(self, tran, obj, index, rel):
        if index >= len(obj.prodQueue):
            raise ige.GameException('No such item in the construction queue.')
        if index + rel < 0 or index + rel >= len(obj.prodQueue):
            raise ige.GameException('Cannot move.')
        item = obj.prodQueue[index]
        del obj.prodQueue[index]
        obj.prodQueue.insert(index + rel, item)
        return obj.prodQueue

    @public(Const.AL_ADMIN)
    def changeOwner(self, tran, obj, ownerID, force = 0):
        oldOwnerID = obj.owner
        if obj.owner == ownerID:
            # the owner is the same
            return
        elif obj.owner != Const.OID_NONE and force == 0:
            # this planet is already owned!
            # TODO resolve conflict (based on player relations)
            raise ige.GameException('Planet is already owned by another commander.')
        elif obj.owner != Const.OID_NONE and force == 1:
            # remove planet from old owner
            try:
                oldOwner = tran.db[obj.owner]
                oldOwner.planets.remove(obj.oid)
                if tran.db.has_key(obj.owner):
                    Utils.sendMessage(tran, obj, Const.MSG_LOST_PLANET, obj.oid, None)
            except Exception:
                log.warning("Cannot remove planet from owner", obj.oid, obj.owner)
                oldOwnerID = Const.OID_NONE
        # reset timer
        obj.ownerSince = tran.db[Const.OID_UNIVERSE].turn
        # add planet to new owner's empire
        if ownerID != Const.OID_NONE:
            newOwner = tran.db[ownerID]
            newOwner.planets.append(obj.oid)
        # reset some attributes
        obj.owner = ownerID
        obj.revoltLen = 0 # no revolt
        obj.prodQueue = [] # clear production queue
        obj.globalQueue = 0 # default global queue
        obj.autoMinStor = 1 # storage is set to auto
        if ownerID != Const.OID_NONE:
            # notify player
            Utils.sendMessage(tran, obj, Const.MSG_GAINED_PLANET, obj.oid, None)

    @public(Const.AL_FULL)
    def setStructOn(self, tran, obj, slotIdx, on):
        if slotIdx >= len(obj.slots) or slotIdx < 0:
            raise ige.GameException('No such structure.')
        if on:
            obj.slots[slotIdx][Const.STRUCT_IDX_STATUS] |= Const.STRUCT_STATUS_ON
        else:
            obj.slots[slotIdx][Const.STRUCT_IDX_STATUS] &= ~Const.STRUCT_STATUS_ON
        return obj.slots[slotIdx]

    @public(Const.AL_FULL)
    def demolishStruct(self, tran, obj, slotIdx):
        # TODO implement special button for demolishing structures when
        # planet surrenders
        #isCombat = tran.db[obj.compOf].combatCounter > 0
        #if isCombat and len(obj.slots) < obj.plSlots:
        #    raise ige.GameException("You cannot destroy this structure under fire - at least one slot is free.")
        if slotIdx >= len(obj.slots) or slotIdx < 0:
            raise ige.GameException('No such structure.')
        del obj.slots[slotIdx]
        return obj.slots

    @public(Const.AL_FULL)
    def moveStruct(self, tran, obj, slotIdx, rel):
        if slotIdx >= len(obj.slots) or slotIdx < 0:
            raise ige.GameException('No such structure.')
        if slotIdx + rel < 0 or slotIdx + rel >= len(obj.slots):
            raise ige.GameException('Cannot move.')
        struct = obj.slots[slotIdx]
        del obj.slots[slotIdx]
        obj.slots.insert(slotIdx + rel, struct)
        return obj.slots

    @public(Const.AL_ADMIN)
    def processINITPhase(self, tran, obj, data):
        # get rid of the NEW states
        for struct in obj.slots:
            struct[Const.STRUCT_IDX_STATUS] &= Const.STRUCT_STATUS_RESETFLGS

    def _getStructProdMod(self, obj, techProdMod):
        b, m, e, d = techProdMod
        return (b * obj.plBio + m * obj.plMin + e * obj.plEn + d * 100) / 100

    def _getOpStatus(self, obj, techProdMod, techOper, techProd, stor):
        prodMod = self._getStructProdMod(obj, techProdMod)
        slope = techProd * prodMod - techOper
        if slope >= 0:
            # structure is self-sufficient in this aspect
            return 1.0
        else:
            return min(stor / - slope, 1.0)

    def _getStructStatus(self, obj, struct, tech, maxHP):
        # find most limitating condition
        if not struct[Const.STRUCT_IDX_STATUS] & Const.STRUCT_STATUS_ON:
            return 0.0, 0.0
        try:
            opStatusHP = min(1.0, float(struct[Const.STRUCT_IDX_HP]) / maxHP)
        except:
            opStatusHP = 0.0
            log.warning('Invalid max HP of structure', Const.STRUCT_IDX_TECHID)
        opStatusBio = self._getOpStatus(obj, tech.prodBioMod, tech.operBio, tech.prodBio, obj.storBio)
        opStatusEn = self._getOpStatus(obj, tech.prodEnMod, tech.operEn, tech.prodEn, obj.storEn)
        opStatusPop = min(1.0, float(obj.unemployedPop) / tech.operWorkers)
        opStatus = min(opStatusHP, opStatusBio, opStatusEn, opStatusPop)
        if opStatus < 1.0:
            if opStatusBio == opStatus:
                struct[Const.STRUCT_IDX_STATUS] |= Const.STRUCT_STATUS_NOBIO
            if opStatusEn == opStatus:
                struct[Const.STRUCT_IDX_STATUS] |= Const.STRUCT_STATUS_NOEN
            if opStatusPop == opStatus:
                struct[Const.STRUCT_IDX_STATUS] |= Const.STRUCT_STATUS_NOPOP
        struct[Const.STRUCT_IDX_OPSTATUS] = int(100 * opStatus)
        return opStatusHP, min(opStatusBio, opStatusEn, opStatusPop)

    def _updateStructHP(self, obj, struct, tech, opStatuses, maxHP):
        # auto repair/damage
        # also damage structures on not owned planets
        opStatusHP, opStatusOther = opStatuses
        properHP = opStatusOther * maxHP
        if struct[Const.STRUCT_IDX_HP] < properHP:
            repairDiff = min(properHP - struct[Const.STRUCT_IDX_HP], Rules.repairRatioFunc(tech.buildProd) * maxHP)
            struct[Const.STRUCT_IDX_HP] += repairDiff
            struct[Const.STRUCT_IDX_STATUS] |= Const.STRUCT_STATUS_REPAIRING
        elif struct[Const.STRUCT_IDX_HP] > properHP:
            decayDiff = min(struct[Const.STRUCT_IDX_HP] - properHP, Rules.decayRatioFunc(tech.buildProd) * maxHP)
            struct[Const.STRUCT_IDX_STATUS] |= Const.STRUCT_STATUS_DETER
            # damage it a bit
            struct[Const.STRUCT_IDX_HP] -= decayDiff
            if obj.storPop > 0:
                # do not fall below 1 HP for populated planets so it won't destroy buildings
                struct[Const.STRUCT_IDX_HP] = max(struct[Const.STRUCT_IDX_HP], 1)
        if struct[Const.STRUCT_IDX_HP] <= 0:
            obj.slots.remove(struct)

    def _processStructs(self, tran, obj):
        for struct in obj.slots[:]:
            # skip structure if it was built this turn
            if struct[Const.STRUCT_IDX_STATUS] & Const.STRUCT_STATUS_NEW:
                continue
            tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
            # compute struct effectivity
            techEff = Utils.getTechEff(tran, struct[Const.STRUCT_IDX_TECHID], obj.owner)
            # morale does not affect hit points of structures
            maxHP = int(tech.maxHP * techEff)
            # auto regulation of min resources
            if obj.autoMinStor:
                obj.minBio += tech.operBio * Rules.autoMinStorTurns
                obj.minEn += tech.operEn * Rules.autoMinStorTurns
            # produce/consume resources
            opStatuses = self._getStructStatus(obj, struct, tech, maxHP)
            self._updateStructHP(obj, struct, tech, opStatuses, maxHP)
            opStatus = min(opStatuses)
            # solarmod effects ENV change and terraforming only if benificial
            if tech.solarMod * opStatus > 0:
                obj.solarmod = max(obj.solarmod, tech.solarMod * techEff * opStatus)
            elif tech.solarMod * opStatus < 0:
                obj.solarmod = min(obj.solarmod, tech.solarMod * techEff * opStatus)
            # bio
            prodMod = self._getStructProdMod(obj, tech.prodBioMod)
            obj.storBio += int(tech.prodBio * prodMod * techEff * opStatus) - int(tech.operBio * opStatus)
            # en
            prodMod = self._getStructProdMod(obj, tech.prodEnMod)
            obj.storEn += int(tech.prodEn * prodMod * techEff * opStatus) - int(tech.operEn * opStatus)

            obj.unemployedPop -= min(obj.unemployedPop, int(tech.operWorkers * opStatus))
            obj.storPop += int(tech.prodPop * techEff * opStatus)
            obj.scannerPwr = max(int(tech.scannerPwr * techEff * opStatus), obj.scannerPwr)
            obj.scannerPwr = min(obj.scannerPwr, Rules.scannerMaxPwr)
            # rebellion and combat has common penalty
            prodMod = self._getStructProdMod(obj, tech.prodProdMod)
            obj.prodProd += int(tech.prodProd * prodMod * techEff * opStatus)
            # science
            prodMod = self._getStructProdMod(obj, tech.prodSciMod)
            obj.prodSci += int(tech.prodSci * prodMod * techEff * opStatus)
            # refuelling & repairing
            obj.refuelMax = max(obj.refuelMax, int(tech.refuelMax * techEff * opStatus))
            # refuelling
            obj.refuelInc = max(obj.refuelInc, int(tech.refuelInc * techEff * opStatus))
            # repair
            obj.repairShip += tech.repairShip * techEff * opStatus
            obj.upgradeShip += tech.upgradeShip * techEff * opStatus
            # train
            obj.trainShipMax = max(obj.trainShipMax, tech.trainShipMax)
            obj.trainShipInc = max(obj.trainShipInc, tech.trainShipInc * techEff * opStatus)
            # shielding
            obj.maxShield = max(tech.planetShield * techEff * opStatus, obj.maxShield)
            # stargates
            obj.fleetSpeedBoost = max(obj.fleetSpeedBoost, tech.fleetSpeedBoost * techEff * opStatus)
            # storage
            obj.maxBio += int(tech.storBio * techEff)
            obj.maxEn += int(tech.storEn * techEff)
            # each structure accomodate it's workers
            obj.maxPop += tech.operWorkers
            obj.maxPop += int(tech.storPop * techEff)
            obj.plEnv += int(tech.prodEnv * techEff * opStatus)
            # morale modifier of the building
            obj.moraleModifiers[1] += tech.moraleTrgt * techEff * opStatus

    def _processPopulation(self, obj, owner):
        if not obj.storPop:
            return
        # population reserve
        obj.maxPop += obj.plSlots * getattr(owner, "techLevel", 1) * Rules.tlPopReserve
        # max pop
        maxPop = obj.maxPop
        if obj.popEatBio: maxPop = min(maxPop,  1000.0 * obj.storBio / obj.popEatBio)
        if obj.popEatEn: maxPop = min(maxPop, 1000.0 * obj.storEn / obj.popEatEn)
        maxPop = int(maxPop)
        # eat
        pop = obj.storPop / 1000.0
        wantBio = int(math.ceil(pop * obj.popEatBio))
        wantEn = int(math.ceil(pop * obj.popEatEn))
        # auto regulation of min resources
        if obj.autoMinStor:
            obj.minBio += wantBio * Rules.autoMinStorTurns
            obj.minEn += wantEn * Rules.autoMinStorTurns
        # consume resources
        obj.storBio -= min(obj.storBio, wantBio)
        obj.storEn -= min(obj.storEn, wantEn)
        # modify pop
        if obj.storPop > maxPop:
            # die
            obj.storPop -= max(int((obj.storPop - maxPop) * Rules.popDieRate), Rules.popMinDieRate)
            #if obj.storPop < maxPop: obj.storPop = maxPop
            # do not generate this message when construction has been destroyed
            # and do not lower morale too
            if obj.storPop < obj.maxPop:
                obj.morale = max(obj.morale - Rules.moraleLostNoFood,0)
        elif obj.storPop < maxPop:
            # born
            obj.storPop += max(min(int(obj.storPop * Rules.popGrowthRate), maxPop - obj.storPop), Rules.popMinGrowthRate)

    def _buildShip(self, tran, obj, item, owner):
        system = tran.db[obj.compOf]
        # find commander's fleet
        fleet = None
        # check if current system has any redirection
        hasRedirection = obj.compOf in owner.shipRedirections
        for fleetID in system.fleets:
            tmpFleet = tran.db[fleetID]
            if tmpFleet.owner == obj.owner and Utils.isIdleFleet(tmpFleet):
                fleet = tmpFleet
                break
        if not fleet or hasRedirection:
            fleet = self.new(Const.T_FLEET)
            tran.db.create(fleet)
            self.cmd(fleet).create(tran, fleet, system, obj.owner)
            self.cmd(fleet).addAction(tran, fleet, 0, Const.FLACTION_REDIRECT, Const.OID_NONE, None)
        # add ships to the fleet
        self.cmd(fleet).addNewShip(tran, fleet, item.techID)
        if item.reportFin and item.quantity == 1:
            Utils.sendMessage(tran, obj, Const.MSG_COMPLETED_SHIP, obj.oid, item.techID)

    def _buildStructure(self, tran, obj, item, tech, target):
        # if there is struct to demolish, find it, determine its CP value, and remove it
        validStructs = [struct for struct in target.slots if struct[Const.STRUCT_IDX_TECHID] == item.demolishStruct]
        if len(validStructs):
            assert item.demolishStruct != Const.OID_NONE
            oldStruct = validStructs[0]
            target.slots.remove(oldStruct)
            # replacement of structure means new struct will start in slightly more complete state
            oldStructTech = Rules.techs[item.demolishStruct]
            try:
                oldStructImpr = tran.db[obj.owner].techs[item.demolishStruct]
            except KeyError:
                oldStructImpr = 1
            maxHP = oldStructTech.maxHP * Rules.techImprEff[oldStructImpr]
            structValue = oldStructTech.buildProd * float(oldStruct[Const.STRUCT_IDX_HP]) / maxHP
            newStruct = Rules.techs[item.techID]
            buildHPRatio = min(Rules.structTransferMaxRatio,
                               Rules.structTransferWaste * structValue / newStruct.buildProd)
        else:
            buildHPRatio = Rules.structDefaultHpRatio
        if len(target.slots) < target.plSlots:
            target.slots.append(Utils.newStructure(tran, item.techID, obj.owner, hpRatio = buildHPRatio))
            try:
                tech.finishConstrHandler(tran, obj, target, tech)
            except Exception:
                log.warning("Cannot execute finish constr handler")
            if item.reportFin and item.quantity == 1:
                Utils.sendMessage(tran, obj, Const.MSG_COMPLETED_STRUCTURE, target.oid, item.techID)
        else:
            # no free slot!
            Utils.sendMessage(tran, obj, Const.MSG_CANNOTBUILD_NOSLOT, target.oid, None)

    def _processProduction(self, tran, obj, owner):
        # produce items in construction queue
        if owner:
            moraleBonus = Rules.moraleProdBonus[int(obj.morale / Rules.moraleProdStep)]
            prod  = obj.effProdProd = max(0, int(obj.prodProd * (owner.prodEff + moraleBonus)))
            if (obj.morale > 15 and prod == 0 and obj.prodProd > 0 and owner.prodEff > 0): #added for super-low moral bonus issues
                prod  = obj.effProdProd = 1
        else:
            prod = obj.prodProd
        explicitIdleProd = 0.0
        # empty queue should be filled by global queue
        if len(obj.prodQueue) == 0 and prod:
            task = self.cmd(obj).popGlobalQueue(tran, obj)
            if task:
                obj.prodQueue.append(task)
        index = 0
        while prod > 0 and index < len(obj.prodQueue):
            item = obj.prodQueue[index]
            # check if owner has this tech
            if not item.isShip and item.techID not in owner.techs:
                # bad tech
                del obj.prodQueue[index]
                # TODO send message
            # set target
            target = tran.db[item.targetID]
            # set tech and build conditions
            if item.isShip:
                tech = tran.db[obj.owner].shipDesigns[item.techID]
                mod = Rules.buildOnSamePlanetMod
            else:
                tech = Rules.techs[item.techID]
                # check validity of the project
                if not tech.validateConstrHandler(tran, obj, target, tech):
                    index += 1
                    # message to player
                    Utils.sendMessage(tran, obj, Const.MSG_INVALID_TASK, obj.oid, item.techID)
                    continue
                # building on other planet is more expensive
                if item.targetID == obj.oid:
                    mod = Rules.buildOnSamePlanetMod
                else:
                    mod = Rules.buildOnAnotherPlanetMod
            # compute needs (do not consume resources under minimal storage)
            wantProd = min(int(tech.buildProd * mod / tech.buildTurns - item.currProd), prod)
            # production
            item.changePerc = wantProd * 10000 / (tech.buildProd * mod)
            # consume / produce
            if item.techID == Rules.Tech.IDLETASK and item.isShip == 0:
                explicitIdleProd += wantProd
            prod -= wantProd
            item.currProd += wantProd
            # check, if production is complete
            if item.currProd >= tech.buildProd * mod:
                # item is complete
                if item.isShip:
                    self._buildShip(tran, obj, item, owner)
                elif tech.isStructure:
                    self._buildStructure(tran, obj, item, tech, target)
                elif tech.isProject:
                    tech.finishConstrHandler(tran, obj, target, tech)
                    if item.reportFin and item.quantity == 1:
                        Utils.sendMessage(tran, obj, Const.MSG_COMPLETED_PROJECT, target.oid, item.techID)
                else:
                    raise ige.GameException('Unsupported type of technology %d ' % item.techID)
                # remove item from prod queue
                item.quantity -= 1
                if item.quantity == 0:
                    # remove item from the queue
                    del obj.prodQueue[index]
                    # was it last item in the queue? pop the global one!
                    if index == len(obj.prodQueue):
                        task = self.cmd(obj).popGlobalQueue(tran, obj)
                        if task:
                            obj.prodQueue.append(task)

                else:
                    # try to produce another item
                    item.currProd = 0
            else:
                # item is not complete stop production
                index += 1
                break
        # decay items not currently produced
        while index < len(obj.prodQueue):
            item = obj.prodQueue[index]
            item.currProd -= int(item.currProd * Rules.decayProdQueue)
            index += 1
        # use excess raw CP to increase production elsewhere
        prod += explicitIdleProd
        if prod > 0.0:
            owner.prodIncreasePool += prod

    def _processEnvironmentChange(self, tran, obj, owner):
        downgradeTo = Rules.planetSpec[obj.plType].downgradeTo
        solarminus = min(0, obj.solarmod)
        solarplus = max(0, obj.solarmod)
        if downgradeTo is not None:
            if (Rules.planetSpec[downgradeTo].upgradeEnReqs[0] > obj.plEn + solarplus) or (Rules.planetSpec[downgradeTo].upgradeEnReqs[1] < obj.plEn + solarminus):
                # auto damage on plEn outside downgrade's upgrade range
                obj.plEnv -= Rules.envAutoMod
        if obj.plBio > Rules.planetSpec[obj.plType].maxBio:
            # auto damage on plBio > maxBio of class
            dEnv = int((obj.plBio - Rules.planetSpec[obj.plType].maxBio) * Rules.envAutoMod)
            if obj.plEnv > 0:
                obj.plEnv -= min(obj.plEnv, dEnv)
            else:
                obj.plEnv -= dEnv
            # small chance of self-upgrading
            spec = Rules.planetSpec[obj.plType]
            race = owner.race if owner else "H"
            chance = int((obj.plBio - spec.maxBio) * Rules.envSelfUpgradeChance[race])
            if Utils.rand(0, 10001) < chance and spec.upgradeTo and \
                    obj.plEn + solarplus >= spec.upgradeEnReqs[0] and \
                    obj.plEn + solarminus <= spec.upgradeEnReqs[1]:
                log.debug('IPlanet', obj.oid, 'Upgraded to', spec.upgradeTo)
                obj.plType = spec.upgradeTo
                Utils.sendMessage(tran, obj, Const.MSG_UPGRADED_PLANET_ECO, obj.oid, spec.upgradeTo)
        while obj.plEnv >= Rules.envInterval:
            #@log.debug('IPlanet', obj.oid, 'Env improved')
            obj.plEnv -= Rules.envInterval
            obj.changeEnv += Rules.envInterval
            if obj.plBio < 200: obj.plBio += 1
        while obj.plEnv < 0:
            if obj.plBio > 0:
                obj.plBio -= 1
                obj.plEnv += Rules.envInterval
                obj.changeEnv -= Rules.envInterval
            else:
                obj.changeEnv += obj.plEnv
                obj.plEnv = 0
        # downgrade planet if necessary
        if obj.plBio < Rules.planetSpec[obj.plType].minBio:
            downgradeTo = Rules.planetSpec[obj.plType].downgradeTo
            if downgradeTo:
                log.debug('IPlanet', obj.oid, 'Downgraded to', downgradeTo)
                obj.plType = downgradeTo
                Utils.sendMessage(tran, obj, Const.MSG_DOWNGRADED_PLANET_ECO, obj.oid, downgradeTo)
        # record changes
        obj.changeBio += obj.storBio
        obj.changeEn += obj.storEn
        obj.changePop += obj.storPop
        obj.changeEnv += obj.plEnv

    @public(Const.AL_ADMIN)
    def processPRODPhase(self, tran, obj, data):
        # max storage
        obj.maxPop = obj.plSlots * Rules.popPerSlot + Rules.popBaseStor
        obj.maxBio = obj.plSlots * Rules.bioPerSlot + Rules.bioBaseStor
        obj.maxEn = obj.plSlots * Rules.enPerSlot + Rules.enBaseStor
        # refuel & repair
        obj.refuelMax = 0
        obj.refuelInc = 0
        obj.repairShip = 0.0
        obj.upgradeShip = 0.0
        # train
        obj.trainShipInc = 0
        obj.trainShipMax = 0
        obj.fleetSpeedBoost = 1.0
        #
        if obj.storPop <= 0 and not obj.slots and obj.owner == Const.OID_NONE:
            # do not process this planet
            return
        obj.scannerPwr = Rules.scannerMinPwr
        obj.prodProd = Rules.basePlanetProdProd
        obj.prodSci = 0
        obj.changeBio = - obj.storBio
        obj.changeEn = - obj.storEn
        obj.changePop = - obj.storPop
        obj.changeEnv = - obj.plEnv
        obj.changeMorale = - obj.morale
        # parent objects
        system = tran.db[obj.compOf]
        galaxy = tran.db[system.compOf]
        # collect strategic resources
        owner = tran.db.get(obj.owner, None)
        if owner and obj.plStratRes != Const.SR_NONE:
            turn = tran.db[Const.OID_UNIVERSE].turn
            if turn % Rules.stratResRate == 0:
                owner.stratRes[obj.plStratRes] = owner.stratRes.get(obj.plStratRes, 0) + Rules.stratResAmountBig
                Utils.sendMessage(tran, obj, Const.MSG_EXTRACTED_STRATRES, obj.oid, obj.plStratRes)
        # compute base morale
        if owner:
            homePlanet = tran.db[owner.planets[0]]
            dist = int(math.sqrt((homePlanet.x - obj.x) ** 2 + (homePlanet.y - obj.y) ** 2))
            moraleTrgt = -37.5 * dist / owner.govPwrCtrlRange + 107.5
            obj.moraleModifiers[0] = max(Rules.minMoraleTrgt, min(moraleTrgt, Rules.maxMorale))
            #@log.debug(obj.oid, "Morale target", obj.moraleTrgt, "dist", dist, owner.govPwrCtrlRange)
        # auto regulation of min resources
        if obj.autoMinStor:
            obj.minBio = obj.minEn = 0
        # combat?
        isCombat = system.combatCounter > 0
        obj.unemployedPop = obj.storPop
        # ok, reset max pop
        obj.maxPop = 0
        # process all structures
        obj.maxShield = 0
        obj.solarmod = 0
        #@log.debug("Morale bonus/penalty for planet", obj.oid, moraleBonus)
        # reset of "morale modifier by buildings" value
        obj.moraleModifiers[1] = 0
        self._processStructs(tran, obj)
        if obj.revoltLen > 0 or isCombat:
            # no services available if distressed
            obj.refuelInc = obj.repairShip = obj.upgradeShip = obj.trainShipMax = obj.trainShipInc = 0
        # do shield self generation
        obj.prevShield = obj.shield #for planet display of shield growth
        if obj.maxShield < obj.shield:
            obj.shield = obj.maxShield
        if obj.maxShield > obj.shield and not isCombat:
            regenTemp = max(1, Rules.plShieldRegen* obj.maxShield) #always regen at at least 1
            obj.shield = min(obj.shield + regenTemp, obj.maxShield) #don't let it regen over shieldMax
        # pass scanner/... to the system
        obj.scannerPwr = min(obj.scannerPwr * (2.0 - galaxy.emrLevel), Rules.scannerMaxPwr)
        system.scannerPwrs[obj.owner] = max(obj.scannerPwr, system.scannerPwrs.get(obj.owner, 0))

        self._processPopulation(obj, owner)
        self._processProduction(tran, obj, owner)
        self._processEnvironmentChange(tran, obj, owner)
        # auto regulation of min resources
        if obj.autoMinStor:
            obj.minBio = min(obj.minBio, obj.maxBio / 2)
            obj.minEn = min(obj.minEn, obj.maxEn / 2)
        # science
        if owner:
            moraleBonus = Rules.moraleProdBonus[int(obj.morale / Rules.moraleProdStep)]
            obj.effProdSci = max(0, int(obj.prodSci * (owner.sciEff + moraleBonus)))
            owner.sciPoints += obj.effProdSci
        # planet with no population cannot have an owner
        # and planet with no owner cannot have population
        if (obj.storPop <= 0 and obj.owner != Const.OID_NONE) or obj.owner == Const.OID_NONE:
            self.cmd(obj).changeOwner(tran, obj, Const.OID_NONE, force = 1)
            obj.storPop = 0

    @public(Const.AL_ADMIN)
    def processACTIONPhase(self, tran, obj, data):
        return

    @public(Const.AL_ADMIN)
    def processFINALPhase(self, tran, obj, data):
        if obj.storPop <= 0 and not obj.slots and obj.owner == Const.OID_NONE:
            # do not process this planet
            return
        # reset of "morale modifier by population" value
        obj.moraleModifiers[2] = 0
        system = tran.db[obj.compOf]
        galaxy = tran.db[system.compOf]
        if galaxy.timeEnabled:
            owner = tran.db.get(obj.owner, None)
            # too much population affects morale (if there is more than base population)
            if obj.storPop > Rules.moraleBasePop:
                obj.moraleModifiers[2] -= Rules.moraleHighPopPenalty * obj.storPop / Rules.moraleBasePop
            elif obj.storPop <= Rules.moraleLowPop:
                obj.moraleModifiers[2] += Rules.moraleLowPopBonus
            else:
                # gradually removing LowPop bonus as we approach BasePop - big jumps are awful game
                # mechanic
                moraleBonusRange = Rules.moraleBasePop - Rules.moraleLowPop
                moraleBonus = float(obj.storPop - Rules.moraleLowPop) / moraleBonusRange
                obj.moraleModifiers[2] += int(Rules.moraleLowPopBonus * (1 - moraleBonus) )
            # there is effect of unemployed population
            # if there is none, there is a hit, if there is what's necessary, there is a bonus
            # effect between the two is linear
            idealUnemployedPop =  obj.plSlots * getattr(owner, "techLevel", 1) * Rules.tlPopReserve
            moraleBonusRange = Rules.unemployedMoraleHigh - Rules.unemployedMoraleLow
            unemployedRatio = min(1.0, float(obj.unemployedPop) / idealUnemployedPop)
            obj.moraleModifiers[3] = Rules.unemployedMoraleLow + int(moraleBonusRange * unemployedRatio)
            # count final morale values
            obj.moraleModifiers[4] = obj.moraleModifiers[0] +obj.moraleModifiers[1] + obj.moraleModifiers[2] + obj.moraleModifiers[3]
            obj.moraleTrgt = obj.moraleModifiers[4]
            obj.moraleTrgt = max(0.0, min(obj.moraleTrgt, Rules.maxMorale))
            if obj.morale > int(obj.moraleTrgt):
                obj.morale -= max(1.0, (obj.morale - obj.moraleTrgt) * Rules.moraleChngPerc)
            elif obj.morale < int(obj.moraleTrgt) and system.combatCounter == 0:
                obj.morale += max(1.0, (obj.moraleTrgt - obj.morale) * Rules.moraleChngPerc)
            #@log.debug('IPlanet', 'Mor Mor trgt/reb thr', obj.morale, obj.moraleTrgt)
            # revolt?
            if obj.revoltLen > 0:
                obj.revoltLen += 1
            if obj.morale < Rules.revoltThr and obj.owner != Const.OID_NONE and obj.revoltLen == 0:
                chance = (Rules.revoltThr - obj.morale) * Rules.moralePerPointChance
                #@log.debug('IPlanet', 'Start revolt? mor, mor trgt, reb thr, chance', obj.morale, obj.moraleTrgt, chance)
                if  Utils.rand(0, 101) <= chance:
                    # rebelion starts
                    #@log.debug('IPlanet', 'Revolt on', obj.oid)
                    obj.revoltLen = 1
                    Utils.sendMessage(tran, obj, Const.MSG_REVOLT_STARTED, obj.oid, None)
            elif obj.revoltLen > 0 and obj.morale > Rules.revoltThr:
                chance = (obj.morale - Rules.revoltThr) * Rules.moralePerPointChance
                #@log.debug('IPlanet', 'Stop revolt? mor, mor trgt, reb thr, chance', obj.morale, obj.moraleTrgt, chance)
                if Utils.rand(0, 101) <= chance:
                    # revolt ends
                    obj.revoltLen = 0
                    Utils.sendMessage(tran, obj, Const.MSG_REVOLT_ENDED, obj.oid, None)
            obj.morale = max(0.0, min(Rules.maxMorale, obj.morale))
            obj.changeMorale += obj.morale
            # when rebelling destroy some resources
            if obj.revoltLen > 0:
                obj.storBio -= int(obj.storBio * Rules.revoltDestrBio)
                obj.storEn -= int(obj.storEn * Rules.revoltDestrEn)
            # storage
            obj.storBio = min(obj.storBio, obj.maxBio)
            obj.storEn = min(obj.storEn, obj.maxEn)
        # collect stats
        if obj.owner != Const.OID_NONE:
            player = tran.db[obj.owner]
            player.stats.storPop += obj.storPop
            player.stats.prodProd += obj.prodProd
            player.stats.effProdProd += obj.effProdProd
            player.stats.prodSci += obj.prodSci
            player.stats.effProdSci += obj.effProdSci
            player.stats.structs += len(obj.slots)
            player.stats.slots += obj.plSlots
            # morale computation
            homePlanet = tran.db[player.planets[0]]
            dist = int(math.sqrt((homePlanet.x - obj.x) ** 2 + (homePlanet.y - obj.y) ** 2))
            player.tmpPopDistr[dist] = player.tmpPopDistr.get(dist, 0) + obj.storPop

    def getScanInfos(self, tran, obj, scanPwr, player):
        if scanPwr >= Rules.level1InfoScanPwr:
            result = IDataHolder()
            result._type = Const.T_SCAN
            result.scanPwr = scanPwr
            result.oid = obj.oid
            result.signature = obj.signature
            result.type = obj.type
            result.orbit = obj.orbit
            result.compOf = obj.compOf
            result.x = obj.x
            result.y = obj.y
            result.plType = obj.plType
        if scanPwr >= Rules.level2InfoScanPwr:
            result.plDiameter = obj.plDiameter
            if getattr(obj, "plType", 'X') != 'G':
                result.plMin = obj.plMin
            result.plBio = obj.plBio
            result.plEn = obj.plEn
            result.plSlots = obj.plSlots
            result.plStratRes = obj.plStratRes
            result.plMaxSlots = obj.plMaxSlots
        if scanPwr >= Rules.level3InfoScanPwr:
            result.name = obj.name
            result.storPop = obj.storPop
            result.owner = obj.owner
        if scanPwr >= Rules.level4InfoScanPwr:
            # TODO provide less information
            result.hasRefuel = (obj.refuelInc > 0) #simple detect if docks exist for problems dialog
            result.slots = obj.slots
            result.shield = obj.shield
            result.prevShield = -1
            result.maxShield = -1
        if scanPwr >= Rules.partnerScanPwr:
            result.maxShield = obj.maxShield
            result.prevShield = obj.prevShield
            result.refuelMax = obj.refuelMax
            result.refuelInc = obj.refuelInc
            result.scannerPwr = obj.scannerPwr
            result.trainShipInc = obj.trainShipInc
            result.trainShipMax = obj.trainShipMax
            result.upgradeShip = obj.upgradeShip
            result.repairShip = obj.repairShip
            result.fleetSpeedBoost = obj.fleetSpeedBoost
        return [result]

    def loadDOMNode(self, tran, obj, xoff, yoff, orbit, node):
        obj.x = xoff
        obj.y = yoff
        obj.orbit = orbit
        for elem in node.childNodes:
            if elem.nodeType == Node.ELEMENT_NODE:
                name = elem.tagName
                if name == 'properties':
                    self.loadDOMAttrs(obj, elem)
                elif name == 'startingpoint':
                    galaxy = tran.db[tran.db[obj.compOf].compOf]
                    galaxy.startingPos.append(obj.oid)
                    galaxy.numOfStartPos += 1
                else:
                    raise ige.GameException('Unknown element %s' % name)
        return Const.SUCC

    def update(self, tran, obj):
        # clean up negative build queues and fix missing demolishStruct keys
        loopAgain = True

        while loopAgain:
            deletedKey = False
            for key in range(0,len(obj.prodQueue)):
                item = obj.prodQueue[key]
                if not hasattr(item, "demolishStruct"):
                    item.demolishStruct = Const.OID_NONE
                if item.quantity < 0:
                    log.warning("Deleting negative item queue on", obj.oid,"for player",obj.owner)
                    if item.isShip:
                        tech = player.shipDesigns[item.techID]
                    else:
                        tech = Rules.techs[item.techID]
                    player = tran.db[obj.owner]
                    for sr in tech.buildSRes:
                        player.stratRes[sr] = player.stratRes.get(sr, 0) + item.quantity #quantity negative, so subtracting strat resources
                    # del the bad item. Since this changes indicies, start the check over again on remaining items
                    deletedKey = True
                    del obj.prodQueue[key]
                    break
            # no more bad entries found; break the while loop
            if not deletedKey:
                loopAgain = False

        # change owner to Const.OID_NONE when owner is invalid
        if obj.owner != Const.OID_NONE:
            player = tran.db.get(obj.owner, None)
            if not player or player.type not in Const.PLAYER_TYPES or obj.oid not in player.planets:
                # TODO this can be a probem - this planet cannot be attacked!
                log.warning("Changing owner to Const.OID_NONE - invalid owner", obj)
                self.cmd(obj).changeOwner(tran, obj, Const.OID_NONE, force = 1)
                # kill all population
                obj.storPop = 0
                return
        # check compOf
        if not tran.db.has_key(obj.compOf) or tran.db[obj.compOf].type != Const.T_SYSTEM:
            log.debug("CONSISTENCY invalid compOf for planet", obj.oid)
        # fix signature
        obj.signature = 75

    @public(Const.AL_FULL)
    def changePlanetsGlobalQueue(self, tran, obj, newQueue):
        player = tran.db[obj.owner]
        if newQueue < 0 or newQueue >= len(player.prodQueues):
            raise ige.GameException("Invalid queue")
        obj.globalQueue = newQueue
        return obj.globalQueue

    def popGlobalQueue(self, tran, obj):
        player = tran.db[obj.owner]
        queue = obj.globalQueue
        task = None
        if len(player.prodQueues[queue]):
            task = copy.copy(player.prodQueues[queue][0])
            if task.quantity > 1:
                player.prodQueues[queue][0].quantity -= 1
            else:
                if task.reportFin:
                    Utils.sendMessage(tran, obj, Const.MSG_QUEUE_TASK_ALLOTED, Const.OID_NONE, (queue, task.techID))
                del player.prodQueues[queue][0]
            # add other demanded values, report finalization was used to report allot (to prevent reporting every unit)
            task.reportFin = 0
            task.quantity = 1
            task.isShip = task.techID < 1000
            task.targetID = obj.oid
            task.currProd = 0
            task.demolishStruct = Const.OID_NONE
        return task

    def deleteDesign(self, tran, obj, designID, keepWIP = 0):
        # TODO: handle stategic resources
        for task in obj.prodQueue[:]:
            if task.isShip and task.techID == designID:
                if task.currProd > 0 and keepWIP:
                    self.cmd(obj).changeConstruction(tran, obj, obj.procQueue.index(task), 1)
                else:
                    self.cmd(obj).abortConstruction(tran, obj, obj.prodQueue.index(task))

    def changeShipDesign(self, tran, obj, oldDesignID, newDesignID):
        # TODO: handle strategic resources
        for task in obj.prodQueue[:]:
            if task.isShip and task.techID == oldDesignID:
                task.techID = newDesignID
                task.currProd = int(task.currProd / Rules.shipUpgradeMod)

    ##
    ## Combat related functions
    ##

    def getPreCombatData(self, tran, obj):
        # scan buildings and fire their weapons
        shots = {0: [], 1: [], 2: [], 3: []}
        if obj.owner == Const.OID_NONE:
            return shots, [0, 0, 0, 8], False
        player = tran.db[obj.owner]
        system = tran.db[obj.compOf]
        desCount = {}
        firing = False
        systemAtt = 0;
        systemDef = 0;
        for struct in obj.slots:
            structTechID = struct[Const.STRUCT_IDX_TECHID]
            opStatus = struct[Const.STRUCT_IDX_OPSTATUS] / 100.0
            tech = Rules.techs[structTechID]
            desCount[structTechID] = desCount.get(structTechID, 0) + 1
            wpnCount = {}
            if not tech.structWeapons:
                continue
            firing = True
            for cClass in range(0, 4):
                weaponID = player.planetWeapons[cClass]
                if weaponID is None:
                    continue
                weapon = Rules.techs[weaponID]
                maxWeaponCount = int(tech.structWeapons[cClass] * opStatus)
                for weaponIdx in range(0, maxWeaponCount):
                    #@log.debug(obj.oid, "FIRING PLANET WEAPON", weapon.name)
                    wpnCount[weaponID] = wpnCount.get(weaponID, 0) + 1
                    #
                    weaponEff = Rules.techImprEff[player.techs.get(weaponID, Rules.techBaseImprovement)]
                    # base attack
                    attack = tech.combatAtt + int(weapon.weaponAtt * weaponEff)
                    # because ALL counters starts at 1, subtract 3
                    count = system.combatCounter + desCount[structTechID] + wpnCount[weaponID] - 2
                    # add to attacks
                    #@log.debug('IPlanet', obj.oid, structTechID, "Count", count, 'Shots', weapon.name, ShipUtils.getRounds(weapon.weaponROF, count))
                    for round in xrange(0, ShipUtils.getRounds(weapon.weaponROF, count)):
                        shots[weapon.weaponClass].append((attack, weaponID))
        # hit limit
        obj.maxHits = len(obj.slots)
        obj.hitCounter = 0
        obj.lastHitClass = 3
        obj.hitMod = 1.0
        log.debug(obj.oid, "Combat settings", obj.maxHits)
        # +1 means population only hit
        return shots, [0, 0, 0, 8], firing

    def applyShot(self, tran, obj, defense, attack, weaponID, cClass, count):
        #@log.debug('IPlanet', 'Apply shot', weaponID, attack, cClass, count)
        # compute chance to hit
        weapon = Rules.techs[weaponID]
        #system defense bonus is dropped for planets...structures can't move; just calculate defense off structure defense
        defense = Rules.combatStructDefense
        destroyed = 0
        dmg = 0
        # limit number of shots
        if weapon.weaponClass < obj.lastHitClass:
            #@log.debug(obj.oid, "Different class", obj.lastHitClass, weapon.weaponClass, obj.maxHits)
            obj.maxHits = int(Rules.combatHitXferMod * obj.maxHits * (obj.lastHitClass - weapon.weaponClass))
            obj.hitCounter = int(Rules.combatHitXferMod * obj.hitCounter * (obj.lastHitClass - weapon.weaponClass))
            obj.lastHitClass = weapon.weaponClass
        if weapon.weaponROF > 1:
            #@log.debug(obj.oid, "Increasing counter PL", 1.0 / weapon.weaponROF)
            obj.hitCounter += 1.0 / weapon.weaponROF
        else:
            #@log.debug(obj.oid, "Increasing counter PL", 1)
            obj.hitCounter += 1
        if obj.hitCounter > obj.maxHits:
            obj.hitCounter = 0
            obj.hitMod *= Rules.combatStructureHitMod
            #@log.debug(obj.oid, "Increasing hit penalty", obj.hitMod, obj.maxHits)
        attackChance = obj.hitMod * attack / (attack + defense)
        #@log.debug(obj.oid, "Chance to attack", attackChance, obj.hitMod, obj.hitCounter, obj.maxHits,
        #@    "without penalty:", float(attack) / (attack + defense))
        #@log.debug('IPlanet', obj.oid, 'HIT?', attack + defense + 1, defense)
        absorb = 0 #for when it doesn't hit
        if random.random() <= attackChance:
            # hit
            player = tran.db[obj.owner]
            weaponEff = Rules.techImprEff[player.techs.get(weaponID, Rules.techBaseImprovement)]
            dmg = ShipUtils.computeDamage(weapon.weaponClass, 3, weapon.weaponDmgMin, weapon.weaponDmgMax, weaponEff)
            #@log.debug(obj.oid, 'HIT! att=%d vs def=%d, dmg=%d '% (attack, defense, dmg))
            #shield strike
            if obj.shield > 0:
                absorb = min(dmg,obj.shield)
                obj.shield -= absorb
                dmg -= absorb
            if dmg == 0:
                return 0+absorb, 0, 3
            # select slot
            if count == 7 or not obj.slots:
                #@log.debug('IPlanet', 'Population hit')
                # population hit
                if obj.storPop == 0:
                    dmg = 0
                else:
                    # free slot hit -> dmg population
                    # OLD dmgPop = int(Rules.popPerSlot * float(dmg) / Rules.popSlotHP * Rules.popKillMod)
                    dmgPop = int(dmg * Rules.popSlotKillMod)
                    obj.storPop = max(obj.storPop - dmgPop, 0)
                    obj.changePop -= dmgPop
                    if obj.storPop > 0:
                        obj.morale -= Rules.moraleModPlHit * float(dmgPop) / float(obj.storPop)
                    #@log.debug('IPlanet', obj.oid, 'Morale penalty', dmg, maxHP, Rules.moraleModPlHit * float(dmg) / float(maxHP))
            elif count < 0:
                # TODO can be count negative?
                log.warning('IPlanet', 'applyShot: count is negative')
            else:
                if count == 6:
                    # random structure hit
                    #@log.debug('IPlanet', 'Random structure hit')
                    struct = obj.slots[Utils.rand(0, len(obj.slots))]
                else:
                    # most damaged structure hit
                    #@log.debug('IPlanet', 'Most damaged structure hit')
                    struct = obj.slots[-1]
                    for tmpStruct in obj.slots:
                        if tmpStruct[Const.STRUCT_IDX_HP] <= struct[Const.STRUCT_IDX_HP]:
                            struct = tmpStruct
                # compute sum hp of all buildings
                sumHP = 0
                for tmpStruct in obj.slots:
                    sumHP += tmpStruct[Const.STRUCT_IDX_HP]
                # damage building
                struct[Const.STRUCT_IDX_HP] -= dmg
                # "damage" population
                tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
                # compute struct effectivity
                techEff = Utils.getTechEff(tran, struct[Const.STRUCT_IDX_TECHID], obj.owner)
                maxHP = int(tech.maxHP * techEff)
                dmgPop = int(tech.operWorkers * float(dmg) / maxHP * Rules.popKillMod)
                obj.storPop = max(obj.storPop - dmgPop, 0)
                obj.changePop -= dmgPop
                # destroy building
                if struct[Const.STRUCT_IDX_HP] <= 0:
                    destroyed = 1
                    dmg += struct[Const.STRUCT_IDX_HP]
                    obj.slots.remove(struct)
                # compute morale penalty
                if dmg:
                    obj.morale -= Rules.moraleModPlHit * float(dmg) / float(sumHP)
                    #@log.debug('IPlanet', obj.oid, 'Morale penalty', dmg, sumHP, Rules.moraleModPlHit * float(dmg) / float(sumHP))
        #@log.debug('IPlanet', 'Shot applied', dmg, destroyed)
        # when destroyed, only class 3 (structure) i valid
        return dmg+absorb, destroyed, 3

    def distributeExp(self, tran, obj):
        # TODO - will buildings have exp? Answ: NO
        if hasattr(obj, "maxHits"):
            del obj.maxHits
            del obj.hitCounter
            del obj.lastHitClass
            del obj.hitMod

    def surrenderTo(self, tran, obj, newOwnerID):
        # morale is lost when this is called
        obj.morale -= Rules.moraleLostWhenSurrender
        if obj.morale >= Rules.revoltThr:
            #@log.debug('IPlanet', 'Surrender - revolt thr not reached', obj.morale)
            return 0
        chance = (Rules.revoltThr - obj.morale) * Rules.moralePerPointChance
        #@log.debug('IPlanet', 'Surrender? mor, mor trgt, reb thr, chance', obj.morale, obj.moraleTrgt, chance)
        if Utils.rand(0, 101) > chance:
            # do not surrender!
            #@log.debug('IPlanet', 'Surrender - pure luck', obj.morale, obj.revoltLen)
            return 0
        # we've lost the battle - we have a new owner
        #@log.debug('IPlanet', 'Surrender - surrending to', newOwnerID)
        newOwner = tran.db[newOwnerID]
        if newOwner.type == Const.T_PIRPLAYER or newOwner.type == Const.T_AIPIRPLAYER:
            # special handling for pirates
            currentTurn = tran.db[Const.OID_UNIVERSE].turn
            # prevent abuse - require 8 turns between capturing the same planet and require the owner to control the planet at least 2 turns if you want to gain fame & tech (two turns prevents orbiting pirate fleet from immediately bombing)
            if (currentTurn - obj.lastPirCapture) > 8 and (currentTurn - obj.ownerSince) > 2:
                # gain/lose fame
                self.cmd(newOwner).capturePlanet(tran, newOwner, obj)
                # steal ship techs
                self.cmd(newOwner).stealTechs(tran, newOwner, obj.owner, obj.oid)
            else:
                log.debug(obj.oid, "Pirate captured planet too soon after previous capture or colonization to gain bonuses", obj.oid)
            obj.storPop = 0
            obj.lastPirCapture = currentTurn
            self.cmd(obj).changeOwner(tran, obj, Const.OID_NONE, force = 1)
        else:
            # change owner
            self.cmd(obj).changeOwner(tran, obj, newOwnerID, force = 1)
        # blow up all military buildings
        for struct in obj.slots[:]:
            tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
            if tech.isMilitary:
                obj.slots.remove(struct)
        return 1

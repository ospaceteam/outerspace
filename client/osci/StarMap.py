# -*- coding: utf-8 -*-
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

from pygameui import Fonts
import ige.ospace.Const as Const
from ige.ospace import Rules, Utils
import pygame, pygame.draw, pygame.key, pygame.image
import gdata, client, res, math, string
from ige import log

buoyColors = [(0xff, 0xff, 0x00), (0x00, 0xff, 0xff), (0xff, 0x00, 0xff), (0xb0, 0xb0, 0xff)]
MAX_BOUY_DISPLAY_LEN = 30
CONTROLRANGE = 5
MAXCONTROLRANGE = 30 #square of CONTROLRANGE + small amount

class StarMap(object):
    MAP_SCANNER1 = 1
    MAP_SYSTEMS = 3
    MAP_PLANETS = 4
    MAP_FLEETS = 5
    MAP_FORDERS = 6
    MAP_OTHERS = 7
    MAP_FREDIRECTS = 8
    MAP_GATESYSTEMS = 10
    MAP_CONTROLAREA = 11

    def __init__(self, modes):
        self.rect = None # will be set later - rect during init phase is not precise
        # map
        self._map = {
            self.MAP_SCANNER1: [],
            self.MAP_SYSTEMS: [],
            self.MAP_PLANETS: [],
            self.MAP_FLEETS: [],
            self.MAP_FORDERS: [],
            self.MAP_OTHERS: [],
            self.MAP_FREDIRECTS: [],
            self.MAP_GATESYSTEMS: [],
            self.MAP_CONTROLAREA: {}
        }
        self._popupInfo = {}
        self._fleetRanges = {}
        self._fleetTarget = {}
        self._fordersTarget = {}
        self._actAreas = {}
        self._actBuoyAreas = {}
        self.currX = 0.0
        self.currY = 0.0
        self.scale = 50.0
        self.textSize = 'normal'
        #modes
        self.control_modes = modes
        # overlay system
        self.overlayMode = gdata.OVERLAY_OWNER
        self._overlayZone = False

    def chronicle_draw(self):
        galaxy_id = client.getPlayer().galaxy
        galaxy = client.get(galaxy_id, noUpdate = 1)
        saved_x, saved_y = self.currX, self.currY
        self.currX, self.currY = galaxy.x, galaxy.y
        surface_side = (galaxy.radius + 2) * 2 * self.scale
        new_surf, empty, empty = self.draw(pygame.Surface((surface_side, surface_side)))
        self.currX, self.currY = saved_x, saved_y
        return new_surf


    def precompute(self):
        player_highlight = -1
        if gdata.config.game.highlight != None:
            player_highlight = gdata.config.game.highlight
        self._map = {
            self.MAP_SCANNER1: [],
            self.MAP_SYSTEMS: [],
            self.MAP_PLANETS: [],
            self.MAP_FLEETS: [],
            self.MAP_FORDERS: [],
            self.MAP_OTHERS: [],
            self.MAP_FREDIRECTS: [],
            self.MAP_GATESYSTEMS: [],
            self.MAP_CONTROLAREA: {}
        }
        self._popupInfo = {}
        self._fleetRanges = {}
        # find all pirate planets
        pirate_systems = self.precomputePirateSystems()
        # process objects
        self.fleetOrbit = {}
        anyX = 0.0
        anyY = 0.0
        player = client.getPlayer()
        for objID in client.db.keys():
            if objID < Const.OID_FREESTART:
                continue
            obj = client.get(objID, noUpdate = 1)
            if not hasattr(obj, "type"):
                continue
            if obj.type == Const.T_PLAYER:
                continue
            try:
                if hasattr(obj, "x"):
                    anyX = obj.x
                if hasattr(obj, "y"):
                    anyY = obj.y
            except AttributeError, e:
                log.warning('StarMap', 'Cannot render objID = %d' % objID)
                continue
            if obj.type == Const.T_SYSTEM:
                self.precomputeSystems(obj, player, pirate_systems)
            elif obj.type == Const.T_WORMHOLE:
                self.precomputeWormholes(obj, player, pirate_systems)
            elif obj.type == Const.T_PLANET:
                self.precomputePlanets(obj, player, pirate_systems)
            elif obj.type == Const.T_FLEET:
                self.precomputeFleet(obj)
            elif obj.type in (Const.T_GALAXY, Const.T_AIPLAYER, Const.T_AIRENPLAYER, Const.T_AIMUTPLAYER, Const.T_AIPIRPLAYER, Const.T_AIEDENPLAYER, Const.T_PIRPLAYER):
                pass
            elif obj.type == Const.T_UNKNOWN:
                # pop up info
                info = []
                info.append(_('Unknown object [ID: %d]') % obj.oid)
                if hasattr(obj, 'scanPwr'):
                    info.append(_('Scan pwr: %d') % obj.scanPwr)
                self._popupInfo[obj.oid] = info
            else:
                log.warning('StarMap', 'Unknown object type %d' % obj.type)
        # redirections
        self.precomputeRedirections()
        # set position (typically on first show)
        if self.currX == 0.0 and self.currY == 0.0:
            self.currX = anyX
            self.currY = anyY


    def precomputePirateSystems(self):
        pirate_systems = {}
        log.debug("Checking pirate planets and wormholes")
        for objID in client.db.keys():
            if objID < Const.OID_FREESTART:
                continue
            obj = client.get(objID, noUpdate = 1)
            if not hasattr(obj, "type"):
                continue
            if obj.type == Const.T_WORMHOLE and not hasattr(obj, 'destinationOid'):
                obj = client.get(objID, forceUpdate = 1, publicOnly = 1)
            if obj.type == Const.T_PLANET and hasattr(obj, "x"):
                ownerID = getattr(obj, 'owner', Const.OID_NONE)
                if ownerID == Const.OID_NONE:
                    continue
                owner = client.get(ownerID, publicOnly = 1)
                if hasattr(owner, "type") and (owner.type == Const.T_PIRPLAYER or\
                                                owner.type == Const.T_AIPIRPLAYER):
                    pirate_systems[obj.x, obj.y] = None
        return pirate_systems

    def precomputeSystems(self, obj, player, pirate_systems):
        img = res.getSmallStarImg(obj.starClass[1]) # TODO correct me
        icons = []
        name = getattr(obj, 'name', None)
        # TODO compute real relationship
        #rel = Const.REL_UNDEF
        refuelMax = 0
        refuelInc = 0
        hasRefuel = False
        upgradeShip = 0
        repairShip = 0
        speedBoost = 0
        moraleCount = 0
        morale = 200
        constPoints = 0
        sciPoints = 0
        minerals = -1
        bio = -1
        slots = 0
        numPlanets = 0
        stratRes = Const.SR_NONE
        isGovCentral = False
        #owner2 = 0
        ownerID = Const.OID_NONE
        explored = False
        if hasattr(obj, 'planets'):
            hasPirate = False
            for planetID in obj.planets:
                planet = client.get(planetID, noUpdate = 1)
                owner = getattr(planet, 'owner', Const.OID_NONE)
                if hasattr(planet, "plType") and planet.plType not in ("A", "G"):
                    numPlanets += 1
                if hasattr(planet, "plMin"):
                    minerals = max(minerals,planet.plMin)
                if hasattr(planet, "plBio"):
                    bio = max(bio,planet.plBio)
                if hasattr(planet, "plSlots"):
                    slots += planet.plSlots
                if hasattr(planet, "plStratRes") and planet.plStratRes != Const.SR_NONE:
                    stratRes = planet.plStratRes
                    stratRes = planet.plStratRes
                    icons.append(res.icons["sr_%d" % planet.plStratRes])
                if owner:
                    ownerID = owner
                    if hasattr(planet, "morale"):
                        morale = min(morale,planet.morale)
                    if hasattr(planet, "refuelMax"):
                        refuelMax = max(refuelMax, planet.refuelMax)
                        refuelInc = max(refuelInc, planet.refuelInc)
                    if hasattr(planet, "repairShip"):
                        upgradeShip += planet.upgradeShip
                        repairShip = max(repairShip, planet.repairShip)
                    hasRefuel = hasRefuel or getattr(planet, 'hasRefuel', False)
                    if hasattr(planet, "fleetSpeedBoost"):
                        speedBoost = max(speedBoost, planet.fleetSpeedBoost)
                    if hasattr(planet, "effProdProd"):
                        constPoints += planet.effProdProd
                    if hasattr(planet, "effProdSci"):
                        sciPoints += planet.effProdSci
                    if hasattr(planet, "slots"):
                        for struct in planet.slots:
                            tech = Rules.techs[struct[Const.STRUCT_IDX_TECHID]]
                            if not tech.govPwr == 0:
                                isGovCentral = True
                            if not hasattr(planet, "morale"): # ugly way to say "planets of other players"
                                # operational status and tech effectivity
                                maxTechHP = tech.maxHP
                                opStatus = struct[Const.STRUCT_IDX_OPSTATUS]/100.0
                                if opStatus != 0:
                                    currHP = struct[Const.STRUCT_IDX_HP]
                                    techEff = (currHP / opStatus) / maxTechHP
                                else:
                                    techEff = 0
                                # production
                                b, m, e, d = tech.prodProdMod
                                prodMod = (b * planet.plBio + m * planet.plMin + e * planet.plEn + d * 100) / 100
                                constPoints += int(tech.prodProd * prodMod * techEff * opStatus)
                                # science
                                b, m, e, d = tech.prodSciMod
                                prodMod = (b * planet.plBio + m * planet.plMin + e * planet.plEn + d * 100) / 100
                                sciPoints += int(tech.prodSci * prodMod * techEff * opStatus)
                # uncharted system
                if hasattr(planet, 'plBio') and hasattr(planet, 'plEn'):
                    explored = True
        if not explored and name != None:
            name = "[%s]" % (name)
        #if moraleCount > 0:
        #    morale = morale/moraleCount
        if morale==200:
            morale = -1
        pirProb = self.precomputePiratesProbability(obj, pirate_systems, icons)
        if (player.type == Const.T_PIRPLAYER or\
                player.type == Const.T_AIPIRPLAYER):
            pirateFameCost = self.getPirateFameCost(player.oid,obj.oid,len(player.planets),pirate_systems)
        # refuelling
        if refuelMax > 0:
            if refuelMax >= 87:
                icons.append(res.icons["fuel_99"])
            elif refuelMax >= 62:
                icons.append(res.icons["fuel_75"])
            elif refuelMax >= 37:
                icons.append(res.icons["fuel_50"])
            elif refuelMax >= 12:
                icons.append(res.icons["fuel_25"])
        elif hasRefuel:
            icons.append(res.icons["fuel_-"])
        # repair and upgrade
        if upgradeShip > 10 and repairShip > 0.02:
            icons.append(res.icons["rep_10"])
        elif upgradeShip > 0 and repairShip > 0:
            icons.append(res.icons["rep_1"])

        self.precomputeCombat(obj, icons)
        self.precomputeMines(obj, icons)
        self.precomputeBuoys(obj, player, icons)
        # star gates
        if speedBoost > 1.0:
            icons.append(res.icons["sg_%02d" % round(speedBoost)])
            self._map[self.MAP_GATESYSTEMS].append((obj.x, obj.y, speedBoost))
        #if owner2 != 0:
        #   color = gdata.playerHighlightColor
        #else:
        #   color = res.getFFColorCode(rel)
        if (player.type == Const.T_PIRPLAYER or\
                player.type == Const.T_AIPIRPLAYER):
            colors = res.getStarmapWidgetSystemColor(ownerID,bio,minerals,slots,numPlanets,speedBoost, refuelInc, upgradeShip, pirProb*100, stratRes, morale, pirateFameCost)
        else:
            colors = res.getStarmapWidgetSystemColor(ownerID,bio,minerals,slots,numPlanets,speedBoost, refuelInc, upgradeShip, pirProb*100, stratRes, morale)
        namecolor = res.getPlayerColor(ownerID)
        controlcolor = res.getControlColor(ownerID)
        if controlcolor:
            groupCenterX = int(obj.x)
            groupCenterY = int(obj.y)
            for rX in range(-CONTROLRANGE,CONTROLRANGE):
                for rY in range(-CONTROLRANGE,CONTROLRANGE):
                    if rX*rX+rY*rY < MAXCONTROLRANGE:
                        ctrlid = "%d:%d" % (groupCenterX+rX,groupCenterY+rY)
                        dist = pow(obj.x-(groupCenterX+rX+0.5),2) + pow(obj.y-(groupCenterY+rY+0.5),2)
                        if ctrlid in self._map[self.MAP_CONTROLAREA]:
                            oldCtrl = self._map[self.MAP_CONTROLAREA][ctrlid]
                            if dist > oldCtrl[1]:
                                continue
                        self._map[self.MAP_CONTROLAREA][ctrlid] = (controlcolor,dist)
        self._map[self.MAP_SYSTEMS].append((obj.oid, obj.x, obj.y, name, img, colors, namecolor, False, icons, constPoints, sciPoints, isGovCentral))
        # pop up info
        info = []
        info.append(_('System: %s [ID: %d]') % (name or res.getUnknownName(), obj.oid))
        info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
        info.append(_('Scan pwr: %d') % obj.scanPwr)
        info.append(_('Star Class: %s') % obj.starClass[1:])
        info.append(_('Star Type: %s') % _(gdata.starTypes[obj.starClass[0]]))
        if (player.type == Const.T_PIRPLAYER or\
                player.type == Const.T_AIPIRPLAYER):
            info.append(_('Fame to Colonize: %d') % pirateFameCost)
        if refuelMax > 0:
            info.append(_("Refuel: %d %%/turn [%d %% max]") % (refuelInc, refuelMax))
        if repairShip > 0:
            info.append(_("Repair ratio: %d %%/turn") % (repairShip * 100))
        if upgradeShip > 0:
            info.append(_("Upgrade points: %d/turn") % upgradeShip)
        if speedBoost > 0:
            info.append(_("Fleet speed: +%d %%") % (speedBoost * 100))
        if pirProb > 0.0:
            info.append(_("Pirate get fame chance: %d %%") % (pirProb * 100))
        self._popupInfo[obj.oid] = info

    def precomputeWormholes(self, obj, player, pirate_systems):
        log.debug("Displaying wormhole",obj.oid)
        img = res.getSmallStarImg(obj.starClass[1])
        icons = []
        name = getattr(obj, 'name', None)
        pirProb = self.precomputePiratesProbability(obj, pirate_systems, icons)
        self.precomputeCombat(obj, icons)
        self.precomputeMines(obj, icons)
        self.precomputeBuoys(obj, player, icons)
        color = res.getPlayerColor(Const.OID_NONE)
        namecolor = res.getPlayerColor(Const.OID_NONE)
        constPoints = 0
        sciPoints = 0
        isGovCentral = False
        self._map[self.MAP_SYSTEMS].append((obj.oid, obj.x, obj.y, name, img, color, namecolor, True, icons, constPoints, sciPoints, isGovCentral))
        # pop up info
        info = []
        info.append(_('Worm hole: %s [ID: %d]') % (name or res.getUnknownName(), obj.oid))
        info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
        try:
            log.debug("Attempting to get wormhole destination (",obj.destinationOid,") from client.")
            whDestObj = client.get(obj.destinationOid, noUpdate = 1) #except if the client doesn't have this in their DB
            whDestName = getattr(whDestObj, 'name', None)
            info.append(_('Destination: %s [ID: %d]') % (whDestName or res.getUnknownName(), obj.oid))
            info.append(_('Dest. Coords: [%.2f, %.2f]') % (whDestObj.x, whDestObj.y))
        except:
            log.debug("Failed getting wormhole destination from client.")
            info.append(_('Destination: ? [ID: ?]'))
            info.append(_('Dest. Coords: [?, ?]'))
        if pirProb > 0.0:
            info.append(_("Pirate get fame chance: %d %%") % (pirProb * 100))
        self._popupInfo[obj.oid] = info

    def precomputePlanets(self, obj, player, pirate_systems):
        owner = getattr(obj, 'owner', Const.OID_NONE)
        # set up color reference data
        biodata = -1
        mindata = -1
        slotdata = 0
        stargatedata = 0
        dockrefueldata = 0
        dockupgradedata = 0
        stratresdata = Const.SR_NONE
        moraledata = -1
        pirProb = self.precomputePiratesProbability(obj, pirate_systems, False)
        famedata = pirProb*100
        biodata = getattr(obj, 'plBio', -1)
        mindata = getattr(obj, 'plMin', -1)
        slotdata = getattr(obj, 'plSlots', 0)
        dockrefueldata = getattr(obj, 'refuelInc', 0)
        dockupgradedata = getattr(obj, 'upgradeShip', 0)
        stargatedata = getattr(obj, 'fleetSpeedBoost', 0)
        stratresdata = getattr(obj, 'plStratRes', Const.SR_NONE)
        moraledata = getattr(obj, 'morale', -1)
        if (player.type == Const.T_PIRPLAYER or\
                player.type == Const.T_AIPIRPLAYER):
            pirateFameCost = self.getPirateFameCost(player.oid,obj.compOf,len(player.planets),pirate_systems)
        # build system
        name = getattr(obj, 'name', None) or res.getUnknownName()
        singlet = True
        if hasattr(obj, "plType") and obj.plType in ("A", "G"):
            colors = gdata.sevColors[gdata.DISABLED]
        else:
            singlet = False
            if (player.type == Const.T_PIRPLAYER or\
                    player.type == Const.T_AIPIRPLAYER):
                colors = res.getStarmapWidgetPlanetColor(owner,biodata,mindata,slotdata,stargatedata, dockrefueldata, dockupgradedata, famedata, stratresdata, moraledata, pirateFameCost)
            else:
                colors = res.getStarmapWidgetPlanetColor(owner,biodata,mindata,slotdata,stargatedata, dockrefueldata, dockupgradedata, famedata, stratresdata, moraledata)
        self._map[self.MAP_PLANETS].append((obj.oid, obj.x, obj.y, obj.orbit, colors, singlet))
        scannerPwr = getattr(obj, 'scannerPwr', 0)
        if scannerPwr:
            self._map[self.MAP_SCANNER1].append((obj.x, obj.y, scannerPwr))
        # pop up info
        info = []
        info.append(_('Planet: %s [ID: %d]') % (name, obj.oid))
        if hasattr(obj, 'scanPwr'): info.append(_('Scan pwr: %d') % obj.scanPwr)
        elif hasattr(obj, 'scannerPwr'): info.append(_('Scanner pwr: %d') % obj.scannerPwr)
        plType = gdata.planetTypes[getattr(obj, 'plType', None)]
        info.append(_('Type: %s') % _(plType))
        if (player.type == Const.T_PIRPLAYER or\
                player.type == Const.T_AIPIRPLAYER):
            info.append(_('Fame to Colonize: %d') % pirateFameCost)
        if hasattr(obj, 'plBio'): info.append(_('Environment: %d') % obj.plBio)
        if hasattr(obj, 'plMin'): info.append(_('Minerals: %d') % obj.plMin)
        if hasattr(obj, 'plEn'): info.append(_('Energy: %d') % obj.plEn)
        if hasattr(obj, 'plSlots'): info.append(_('Slots: %d') % obj.plSlots)
        if hasattr(obj, "plStratRes") and obj.plStratRes != Const.SR_NONE:
            info.append(_("Strat. resource: %s") % _(gdata.stratRes[obj.plStratRes]))
        if owner:
            ownerobj = client.get(owner, publicOnly = 1)
            info.append(_('Owner: %s [ID: %s]') % (
                getattr(ownerobj, 'name', res.getUnknownName()),
                getattr(ownerobj, 'oid', '?')
            ))
        self._popupInfo[obj.oid] = info

    def getPirateFameCost(self, playerID, systemID, numPiratePlanets, pirate_systems):
        mod = 1
        system = client.get(systemID, noUpdate = 1)
        if hasattr(system,'planets') and system.planets:
            for planetID in system.planets:
                planet = client.get(planetID, noUpdate = 1)
                if getattr(planet, 'owner', Const.OID_NONE) == playerID:
                    # minimum reached, don't check rest
                    return 0.0
                elif getattr(planet, 'plStratRes', None) in (Const.SR_TL3A, Const.SR_TL3B, Const.SR_TL3C):
                    mod = min(mod, Rules.pirateTL3StratResColonyCostMod)
        dist = 10000
        for pirX, pirY in pirate_systems:
            dist = min(dist, math.hypot(system.x - pirX, system.y - pirY))
        if Rules.pirateGainFamePropability(dist) > 0:
            mod = Rules.pirateColonyFameZoneCost(dist)
        else:
            mod = Rules.pirateColonyPlayerZoneCost(dist)
        return mod * numPiratePlanets * Rules.pirateColonyCostMod

    def precomputeRedirections(self,repaint=False): #also called from Mass Redirector
        player = client.getPlayer()
        for sourceID in player.shipRedirections:
            targetID = player.shipRedirections[sourceID]
            source = client.get(sourceID, noUpdate = 1)
            target = client.get(targetID, noUpdate = 1)
            if hasattr(source, "x") and hasattr(target, "y"):
                self._map[self.MAP_FREDIRECTS].append((source.x, source.y, target.x, target.y))

    def precomputeFleet(self,obj):

        owner = getattr(obj, 'owner', Const.OID_NONE)
        if hasattr(obj,'customname') and obj.customname:
            name = obj.customname
        else:
            name = getattr(obj, 'name', res.getUnknownName())
        color = res.getPlayerColor(owner)
        # fleet scanner setup
        scannerPwr = getattr(obj, 'scannerPwr', 0)
        if hasattr(obj, "scannerOn") and not obj.scannerOn:
            scannerPwr = 0
        if scannerPwr:
            self._map[self.MAP_SCANNER1].append((obj.x, obj.y, scannerPwr))
        #  get orbital position
        orbit = -1
        if obj.orbiting != Const.OID_NONE:
            orbit = self.fleetOrbit.get(obj.orbiting, 0)
            self.fleetOrbit[obj.orbiting] = orbit + 1
        # set path and times
        eta = getattr(obj, 'eta', 0)
        self._map[self.MAP_FLEETS].append((obj.oid, obj.x, obj.y, obj.oldX, obj.oldY, orbit, res.formatTime(eta), color,
            obj.signature / 25, getattr(obj, "isMilitary", 1)))
        # pop up info
        info = []
        info.append(_('Fleet: %s [ID: %d]') % (name, obj.oid))
        if hasattr(obj, 'scanPwr'):    info.append(_('Scan pwr: %d') % obj.scanPwr)
        if hasattr(obj, 'scannerPwr'): info.append(_('Scanner pwr: %d') % obj.scannerPwr)
        info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
        info.append(_('Signature: %d') % obj.signature)
        if hasattr(obj, 'speed'): info.append(_(u'Speed: %3.2f') % obj.speed)
        elif eta:
            info.append(_(u'Speed: %3.2f') % (24*((obj.y-obj.oldY)**2+(obj.x-obj.oldX)**2)**.5))
        if eta:
            info.append(_('ETA: %s') % res.formatTime(eta))
        if owner:
            ownerobj = client.get(owner, publicOnly = 1)
            info.append(_('Owner: %s [ID: %s]') % (
                getattr(ownerobj, 'name', res.getUnknownName()),
                getattr(ownerobj, 'oid', '?')
            ))
        if hasattr(obj, 'storEn'):
            if obj.maxEn > 0: full = 100 * obj.storEn / obj.maxEn
            else: full = 0
            info.append(_('Tanks: %d / %d [%d %%]') % (obj.storEn, obj.maxEn, full))
            info.append(_('Support (fuel): %d/turn') % (obj.operEn))
            info.append(_('Support (const. pts): %d/turn') % (obj.operProd))
        if hasattr(obj, 'combatPwr'):
            info.append(_('Military power: %d') % obj.combatPwr)
        # ranges
        if hasattr(obj, 'storEn') and hasattr(obj, 'operEn'):
            turns = 100000
            if obj.operEn > 0: turns = obj.storEn / obj.operEn
            range = turns * obj.speed / Rules.turnsPerDay
            self._fleetRanges[obj.oid] = (obj.x, obj.y, range, range  / 2., range / 3., obj.speed * 6 / Rules.turnsPerDay, turns)
            info.append(_("Operational time: %s") % res.formatTime(turns))
        if hasattr(obj, 'target') and obj.target != Const.OID_NONE:
            target = client.get(obj.target, noUpdate=1)
            if hasattr(target, "x"):
                self._fleetTarget[obj.oid] = (obj.x, obj.y, target.x, target.y)
            info.append(_('Target: %s') % getattr(target, "name", res.getUnknownName()))
        # pop up info (continued)
        if hasattr(obj, 'ships'):
            info.append(_('Ships:'))
            number = {}
            for designID, hp, shield, exp in obj.ships:
                tech = client.get(owner).shipDesigns[designID]
                level = Rules.shipExpToLevel.get(int(exp / tech.baseExp), Rules.shipDefLevel)
                if designID not in number:
                    number[designID] = [0, 0, 0, 0, 0]
                number[designID][level - 1] += 1
            order = number.keys()
            order.sort()
            for designID in order:
                tech = client.get(owner).shipDesigns[designID]
                levels = number[designID]
                info.append(_('  %d x %s   [%d, %d, %d, %d, %d]') % (
                        levels[0] + levels[1] + levels[2] + levels[3] + levels[4],
                        tech.name,
                        levels[0], levels[1], levels[2], levels[3], levels[4],
                    )
                )
        elif hasattr(obj, 'shipScan'):
            info.append(_('Ships:'))
            for name, shipClass, isMilitary in obj.shipScan:
                if isMilitary:
                    sType = _("military")
                else:
                    sType = _("civilian")
                info.append(_("  %d x %s [%s %s ship]") % (
                    obj.shipScan[name, shipClass, isMilitary],
                    name,
                    _(gdata.shipClasses[shipClass]),
                    sType
                ))
        if hasattr(obj, 'actionIndex') and not Utils.isIdleFleet(obj):
            action, target, data = obj.actions[obj.actionIndex]
            if target != Const.OID_NONE:
                targetName = getattr(client.get(target, noUpdate = 1), 'name', res.getUnknownName())
            else:
                targetName = ""
            info.append(_("Command: %s %s") % (
                gdata.fleetActions[action],
                targetName,
            ))
        self._popupInfo[obj.oid] = info
        # orders
        if hasattr(obj, 'actions'):
            oldX = obj.x
            oldY = obj.y
            self._fordersTarget[obj.oid]=[]
            for action, target, aData in obj.actions[obj.actionIndex:]:
                if target:
                    # TODO add action colors
                    if action == Const.FLACTION_REFUEL: color = (0x00, 0x90, 0x00)
                    elif action == Const.FLACTION_DEPLOY: color = (0x90, 0x90, 0x00)
                    elif action == Const.FLACTION_REDIRECT: color = (0x20, 0x20, 0x80)
                    else: color = (0x90, 0x90, 0x90)
                    trgt = client.get(target, noUpdate = 1)
                    if hasattr(trgt, 'x'):
                        self._map[self.MAP_FORDERS].append((oldX, oldY, trgt.x, trgt.y, color, getattr(obj, "isMilitary", 0)))
                        self._fordersTarget[obj.oid].append((oldX, oldY, trgt.x, trgt.y, color))
                        oldX, oldY = trgt.x, trgt.y

    def precomputePiratesProbability(self, system, pirate_systems, icons = False):
        dist = 10000
        for pirX, pirY in pirate_systems:
            dist = min(dist, math.hypot(system.x - pirX, system.y - pirY))
        pirProb = Rules.pirateGainFamePropability(dist)
        if icons != False:
            if pirProb >= 1.0:
                icons.append(res.icons["pir_99"])
            elif pirProb > 0.0:
                icons.append(res.icons["pir_00"])
        return pirProb

    def precomputeMines(self, system, icons):
        if getattr(system, "minefield", False):
            # ok, system has our mines - as minefield is identified
            icons.append(res.icons["mines_ours"])
            if getattr(system, "hasmines", 0) == 2:
                # there are also unknown mines!
                icons.append(res.icons["mines_unknown"])
        elif getattr(system, "hasmines", 0):
            # there are only unknown mines
            icons.append(res.icons["mines_unknown"])



    def precomputeCombat(self, system, icons):
        if hasattr(system, "combatCounter") and system.combatCounter > 0:
            icons.append(res.icons["combat"])

    def precomputeBuoys(self, system, player, icons):
        if hasattr(player, "buoys") and system.oid in player.buoys:
            icons.append(res.icons["buoy_%d" % player.buoys[system.oid][1]])
        if hasattr(player, "alliedBuoys") and system.oid in player.alliedBuoys and len(player.alliedBuoys[system.oid]) > 0:
            buoyName = "buoy_%d" % player.alliedBuoys[system.oid][0][1]
            if len(player.alliedBuoys[system.oid]) > 1:
                buoyName = "%s_plus" % buoyName
            icons.append(res.icons[buoyName])


    def draw(self, mapSurf):
        self._actAreas = {}
        # clear active areas for buoy texts
        self._actBuoyAreas = {}
        mapSurf.fill((0x00, 0x00, 0x00))
        ## scanners
        # scanner ranges and control areas
        if self.control_modes['scanners'] or self.control_modes['control_areas']:
            if self.control_modes['control_areas']:
                self.drawControlAreas(mapSurf)
            else:
                self.drawScanners(mapSurf)
        # pirate area
        if self.control_modes['pirate_areas']:
            pass # TODO
        # grid
        if self.control_modes['map_grid']:
            self.drawGrid(mapSurf)
        # redirections
        if self.control_modes['redirects']:
            self.drawRedirects(mapSurf)
        # gate systems
        if self.control_modes['gate_systems']:
            self.drawGateSystems(mapSurf)
        # stars
        if self.control_modes['systems']:
            self.drawSystems(mapSurf)
        # planets
        if self.control_modes['planets']:
            self.drawPlanets(mapSurf)
        # fleets
        if self.control_modes['fleets']:
            self.drawFleets(mapSurf)
        self.drawOverlayEffects(mapSurf)
        return mapSurf, self._actAreas, self._actBuoyAreas

    def drawScanners(self, mapSurf):
        # default scanner ranges (inner and outer circles)
        scanner1range = 1.0/10
        scanner2range = 1.0/16
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxX = mapSurf.get_rect().width
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        scannerCalced = []
        # draw
        for x, y, scan_range in self._map[self.MAP_SCANNER1]:
            sx = int((x - currX) * scale) + centerX
            sy = maxY - (int((y - currY) * scale) + centerY)
            currRange = int(scan_range * scale * scanner1range + 2)
            range1 = int(scan_range * scale * scanner1range)
            range2 = int(scan_range * scale * scanner2range)
            if sx+currRange > 0 and sx-currRange < maxX and sy+currRange > 0 and sy-currRange < maxY:
                pygame.draw.circle(mapSurf, (0x00, 0x00, 0x60), (sx, sy), currRange, 2)
                scannerCalced.append((sx,sy,range1,range2))
        for sx, sy, range1, range2 in scannerCalced:
            pygame.draw.circle(mapSurf, (0x00, 0x00, 0x30), (sx, sy), range1, 0)
        for sx, sy, range1, range2 in scannerCalced:
            pygame.draw.circle(mapSurf, (0x00, 0x00, 0x40), (sx, sy), range2, 0)
#        log.debug("Total scanner circles:",len(self._map[self.MAP_SCANNER1]))
#        log.debug("Drawn scanner circles:",len(scannerCalced))

    def drawControlAreas(self, mapSurf):
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        first = True
        for xy in self._map[self.MAP_CONTROLAREA].keys():
            x,y = xy.split(':',2)
            sx = int((int(x) - currX) * scale) + centerX + 1
            sy = maxY - (int((int(y) + 1 - currY) * scale) + centerY) # use y+1 because we have to draw from top down rather than bottom up
            if sy > centerY: sy += 1 #fix a bug with the draw system
            dx = scale
            dy = scale
            mapSurf.fill(self._map[self.MAP_CONTROLAREA][xy][0], pygame.Rect(sx, sy, dx, dy), 0)

    def drawRedirects(self, mapSurf):
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        for sx, sy, tx, ty in self._map[self.MAP_FREDIRECTS]:
            sx = int((sx - currX) * scale) + centerX
            sy = maxY - (int((sy - currY) * scale) + centerY)
            tx = int((tx - currX) * scale) + centerX
            ty = maxY - (int((ty - currY) * scale) + centerY)
            # TODO: change do polygon (triangle), but needs to start
            # perpendicular to the redirect
            #pygame.draw.polygon(mapSurf, (0x20, 0x20, 0x80), [(sx+2, sy), (sx-2, sy), (tx, ty)])
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx, sy), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx, sy + 1), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx, sy - 1), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy + 1), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy - 1), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy + 1), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy - 1), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx + 2, sy), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx - 2, sy), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx, sy + 2), (tx, ty), 1)
            pygame.draw.line(mapSurf, (0x20, 0x20, 0x80), (sx, sy - 2), (tx, ty), 1)

    def drawSystems(self, mapSurf):
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        namecolor = res.getPlayerColor(Const.OID_NONE)
        if scale >= 30:
            for objID, x, y, name, img, color, namecolor, singlet, icons, constPoints, sciPoints, isGovCentral in self._map[self.MAP_SYSTEMS]:
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                w, h = img.get_size()
                x = sx - w / 2
                y = sy - h / 2
                mapSurf.blit(img, (x, y))
                # images are now smaller - TODO fix images of stars
                w = 22
                h = 22
                if name:
                    if self.overlayMode != gdata.OVERLAY_OWNER:
                        namecolor = res.fadeColor(namecolor)
                    img = Fonts.renderText(self.textSize, name, 1, namecolor)
                    mapSurf.blit(img, (sx - img.get_width() / 2, sy + h / 2))
                buoy = self.getBuoy(objID)
                if buoy != None and not self.control_modes['alternative_mode']:
                    if not name: #if name not set and there is a bouy, set "?" as the name
                        if self.overlayMode != gdata.OVERLAY_OWNER:
                            namecolor = res.fadeColor(namecolor)
                        img = Fonts.renderText(self.textSize, '[ ? ]', 1, namecolor)
                        mapSurf.blit(img, (sx - img.get_width() / 2, sy + h / 2))
                        nSy = sy + h / 2 + img.get_height()
                    nSy = sy + h / 2 + img.get_height()
                    lines = buoy[0].split("\n")
                    maxW = 0
                    hh = 0
                    for line in lines:
                        if len(line) == 0:
                            break
                        if len(line) > MAX_BOUY_DISPLAY_LEN:
                            line = u"%s..." % line[:MAX_BOUY_DISPLAY_LEN]
                        if self.overlayMode == gdata.OVERLAY_OWNER:
                            bouycolor = buoyColors[buoy[1] - 1]
                        else:
                            bouycolor = res.fadeColor(buoyColors[buoy[1] - 1])
                        img = Fonts.renderText(self.textSize, line, 1, bouycolor)
                        maxW = max(img.get_width(), maxW)
                        mapSurf.blit(img, (sx - img.get_width() / 2, nSy + hh))
                        hh += img.get_height()
                    if maxW > 0:
                        actRect = pygame.Rect(sx - maxW / 2, nSy, maxW, hh)
                        actRect.move_ip(self.rect.left, self.rect.top)
                        self._actBuoyAreas[objID] = actRect
                elif self.control_modes['alternative_mode']:
                    alternative = name
                    nSy = sy + h / 2 + img.get_height()
                    if constPoints != 0 or sciPoints != 0:
                        img = Fonts.renderText(self.textSize, u"CP: %d RP: %d" % (constPoints, sciPoints), 1, namecolor)
                        mapSurf.blit(img, (sx - img.get_width() / 2, nSy))
                    if isGovCentral:
                        img = Fonts.renderText(self.textSize, u"Central system", 1, (255, 255, 255))
                        mapSurf.blit(img, (sx - img.get_width() / 2, nSy + img.get_height()))
                for icon in icons:
                    mapSurf.blit(icon, (x, y))
                    x += icon.get_width() + 1
                # active rectangle
                actRect = pygame.Rect(sx - w / 2, sy - h / 2, w, h)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect
        else:
            for objID, x, y, name, img, color, namecolor, singlet, icons, constPoints, sciPoints, isGovCentral in self._map[self.MAP_SYSTEMS]:
                if not singlet:
                    color = color[self.overlayMode]
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                pygame.draw.circle(mapSurf, color, (sx, sy), 5, 1)
                pygame.draw.circle(mapSurf, color, (sx, sy), 4, 0)
                if name and scale > 15:
                    if self.overlayMode != gdata.OVERLAY_OWNER:
                        namecolor = res.fadeColor(namecolor)
                    img = Fonts.renderText(self.textSize, name, 1, namecolor)
                    mapSurf.blit(img, (sx - img.get_width() / 2, sy + 6 / 2))
                    buoy = self.getBuoy(objID)
                    if buoy != None:
                        lines = buoy[0].split("\n")
                        nSy = sy + 6 / 2 + img.get_height()
                        maxW = 0
                        hh = 0
                        for line in lines:
                            if len(line) == 0:
                                break
                            img = Fonts.renderText(self.textSize, line, 1, buoyColors[buoy[1] - 1])
                            maxW = max(img.get_width(), maxW)
                            mapSurf.blit(img, (sx - img.get_width() / 2, nSy + hh))
                            hh += img.get_height()
                        if maxW > 0:
                            actRect = pygame.Rect(sx - maxW / 2, nSy, maxW, hh)
                            actRect.move_ip(self.rect.left, self.rect.top)
                            self._actBuoyAreas[objID] = actRect
                # active rectangle
                actRect = pygame.Rect(sx - 6 / 2, sy - 6 / 2, 6, 6)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect

    def drawGateSystems(self, mapSurf):
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        minRadius = 8
        radiusMult = 3
        if scale < 30:
            for x, y, speed in self._map[self.MAP_GATESYSTEMS]:
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                for curSpeed in range(1,int(speed+1)):
                    radius = (curSpeed-1)* radiusMult + minRadius
                    color = res.getStargateColorCode(curSpeed)
                    pygame.draw.circle(mapSurf, color, (sx, sy), radius, 1)

    def drawPlanets(self, mapSurf):
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        if scale >= 30:
            rectSize = max(int(gdata.config.defaults.minplanetsymbolsize), math.floor(scale/6))
            if not int(gdata.config.defaults.maxplanetsymbolsize) == 0:
                rectSize = min(int(gdata.config.defaults.maxplanetsymbolsize), rectSize)
            rectSpace = rectSize + math.floor(rectSize/5)
            for objID, x, y, orbit, color, singlet in self._map[self.MAP_PLANETS]:
                if not singlet:
                    color = color[self.overlayMode]
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                orbit -= 1
                actRect = pygame.Rect(sx + (orbit % 8) * rectSpace + 13, sy + 6 * (orbit / 8) - rectSize , rectSize, rectSize)

                mapSurf.fill(color, actRect)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect
        elif scale > 20:
            for objID, x, y, orbit, color, singlet in self._map[self.MAP_PLANETS]:
                if not singlet:
                    color = color[self.overlayMode]
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                orbit -= 1
                actRect = pygame.Rect(sx + (orbit % 8) * 3 + 7, sy - 3 * (orbit / 8) - 1, 2, 2)
                mapSurf.fill(color, actRect)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect

    def drawFleets(self, mapSurf):
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        minSize = int(gdata.config.defaults.minfleetsymbolsize)
        rectSize = max(minSize, math.floor(scale / 7) - math.floor(scale / 7) % 2)
        if not int(gdata.config.defaults.maxfleetsymbolsize) == 0:
            rectSize = min(int(gdata.config.defaults.maxfleetsymbolsize), rectSize)
        rectSpace = rectSize + math.floor(rectSize/5)
        # draw orders lines
        if self.control_modes['fleet_lines']:
            for x1, y1, x2, y2, color, military in self._map[self.MAP_FORDERS]:
                if not self.control_modes['civilian_fleets'] and not military:
                    continue
                sx1 = int((x1 - currX) * scale) + centerX
                sy1 = maxY - (int((y1 - currY) * scale) + centerY)
                sx2 = int((x2 - currX) * scale) + centerX
                sy2 = maxY - (int((y2 - currY) * scale) + centerY)
                pygame.draw.line(mapSurf, color, (sx1, sy1), (sx2, sy2), 1)
        # draw fleet symbol
        for objID, x, y, oldX, oldY, orbit, eta, color, size, military in self._map[self.MAP_FLEETS]:
            if not self.control_modes['civilian_fleets'] and not military:
                continue
            if self.overlayMode != gdata.OVERLAY_OWNER:
                color = res.fadeColor(color)
            sx = int((x - currX) * scale) + centerX
            sy = maxY - (int((y - currY) * scale) + centerY)
            if orbit >= 0 and scale >= 30:
                actRect = pygame.Rect(sx + (orbit % 7) * rectSpace + 13 + 2 * (orbit % 7), sy + scale/6 * (orbit / 7) + 6, rectSize, rectSize)
                # TODO this is a workaround - fix it when pygame gets fixed
                # pygame.draw.polygon(mapSurf, color,
                #    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 1)
                pygame.draw.polygon(mapSurf, color,
                    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 0)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect
            elif orbit < 0:
                rectSizeFlying = rectSize+2
                sox = int((oldX - currX) * scale) + centerX
                soy = maxY - (int((oldY - currY) * scale) + centerY)
                actRect = pygame.Rect(sx - rectSizeFlying / 2, sy - rectSizeFlying / 2, rectSizeFlying , rectSizeFlying)
                if military:
                    mColor = color
                else:
                    mColor = (0xff, 0xff, 0xff)
                pygame.draw.line(mapSurf, mColor, (sx, sy), (sox, soy), size + 1)
                # TODO rotate triangle
                pygame.draw.polygon(mapSurf, color,
                    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 1)
                pygame.draw.polygon(mapSurf, color,
                    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 0)
                if eta and scale > 15:
                    img = Fonts.renderText(self.textSize, eta, 1, color)
                    mapSurf.blit(img, actRect.topright)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect

    def drawOverlayEffects(self, mapSurf):
        # coordinates
        centerX, centerY = mapSurf.get_rect().center
        maxY = mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        # draw overlay specific features, coloring itself is applied in drawPlanets etc.
        if self.overlayMode == gdata.OVERLAY_MORALE:
            player = client.getPlayer()
            if hasattr(player, "planets"):
                centralPlanet = client.get(player.planets[0])
                govPCR = player.govPwrCtrlRange
                player.stats.storPop, player.govPwr
                maxMorale = int(Rules.maxMorale)
                minAchievedMorale = int(max(Rules.minMoraleTrgt - 1, 107.5 - 37.5 * player.stats.storPop / player.govPwr))
                for step in xrange(maxMorale, minAchievedMorale - 1 , -10):
                    moraleColor = res.getMoraleColors(step)
                    centralX = int((centralPlanet.x - currX) * scale) + centerX
                    centralY = maxY - (int((centralPlanet.y - currY) * scale) + centerY)
                    radius = int((107.5 - step) * govPCR / 37.5 * scale)
                    pygame.draw.circle(mapSurf, moraleColor, (centralX, centralY), radius, 1)
                    text = Fonts.renderText(self.textSize, step, 1, moraleColor)
                    #maxW = max(text.get_width(), maxW)
                    mapSurf.blit(text, (centralX + radius, centralY))





    def drawGrid(self, mapSurf):
        rect = mapSurf.get_rect()
        centerX, centerY = rect.center
        maxY = rect.height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        left = int((int(currX) - currX) * scale) + centerX - int(rect.width / scale / 2) * scale
        x = left
        while x < left + rect.width + scale:
            value =  math.floor((x - centerX) / scale + currX)
            if value % 5 == 0:
                pygame.draw.line(mapSurf, (0x00, 0x00, 0x90),
                    (x, rect.top), (x, rect.bottom), 1)
                if self.control_modes['map_grid_coords']:
                    textSrfc = Fonts.renderText(self.textSize, int(value), 1, (0x70, 0x70, 0x80))
                    mapSurf.blit(textSrfc, (x + 2, rect.height - textSrfc.get_height()))
            else:
                pygame.draw.line(mapSurf, (0x33, 0x33, 0x66),
                    (x, rect.top), (x, rect.bottom), 1)
            x += scale
        top = int((int(currY) - currY) * scale) + centerY - int(rect.height / scale / 2) * scale
        y = top
        while y < top + rect.height + scale:
            yScrn = maxY - y
            value =  math.floor(((maxY - yScrn) - centerY) / scale + currY)
            if value % 5 == 0:
                pygame.draw.line(mapSurf, (0x00, 0x00, 0x90),
                    (rect.left, yScrn), (rect.right, yScrn), 1)
                textSrfc = Fonts.renderText(self.textSize, int(value), 1, (0x70, 0x70, 0x80))
                mapSurf.blit(textSrfc, (0, yScrn))
            else:
                pygame.draw.line(mapSurf, (0x33, 0x33, 0x66),
                    (rect.left, yScrn), (rect.right, yScrn), 1)
            y += scale


    def getBuoy(self, objID):
        player = client.getPlayer()
        if hasattr(player, "buoys") and objID in player.buoys:
            lines = player.buoys[objID][0].split("\n")
            if len(lines) > 2:
                return (u"%s\n%s" % (lines[0], lines[1]), player.buoys[objID][1])
            else:
                return player.buoys[objID]
        else:
            if hasattr(player, "alliedBuoys") and objID in player.alliedBuoys:
                if len(player.alliedBuoys[objID]) > 0:
                    lines = player.alliedBuoys[objID][0][0].split("\n")
                    if len(lines) > 2:
                        return (u"%s\n%s" % (lines[0], lines[1]), player.alliedBuoys[objID][0][1])
                    else:
                        return player.alliedBuoys[objID][0]
                else:
                    return None
            else:
                return None


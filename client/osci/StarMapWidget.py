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

from pygameui.Widget import Widget, registerWidget
import pygameui as ui
from pygameui.Fonts import *
from ige.ospace.Const import *
from ige.ospace import Rules, Utils
import pygame, pygame.draw, pygame.key, pygame.image
from pygame.locals import *
from dialog.ShowBuoyDlg import ShowBuoyDlg
from dialog.MapOverlayDlg import MapOverlayDlg
from dialog.KeyModHelp import KeyModHelp
import gdata, client, res, math, string
from ige import log
from osci.dialog.SearchDlg import SearchDlg
from osci.MiniMap import MiniMap

buoyColors = [(0xff, 0xff, 0x00), (0x00, 0xff, 0xff), (0xff, 0x00, 0xff), (0xb0, 0xb0, 0xff)]
MAX_BOUY_DISPLAY_LEN = 30
CONTROLRANGE = 5
MAXCONTROLRANGE = 30 #square of CONTROLRANGE + small amount

class StarMapWidget(Widget):

    MAP_SCANNER1 = 1
    MAP_SYSTEMS = 3
    MAP_PLANETS = 4
    MAP_FLEETS = 5
    MAP_FORDERS = 6
    MAP_OTHERS = 7
    MAP_FREDIRECTS = 8
    MAP_GATESYSTEMS = 10
    MAP_CONTROLAREA = 11

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent)
        self.searchDlg = SearchDlg(self.app)
        self.searchDlg.mapWidget = self
        self.showOverlayDlg = MapOverlayDlg(self.app)
        self.showOverlayDlg.mapWidget = self
        # data
        self.action = None
        self.callEventHandler = None
        # map
        self._mapSurf = None
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
        self.activeObjID = OID_NONE
        self.activeObjIDs = []
        self.pressedObjIDs = []
        self._newCurrXY = 0
        self.activePos = (0, 0)
        self.lockObj = None # source object in fleet move
        self.repaintMap = 1
        self.repaintHotbuttons = 1
        self.setPosition = 1
        #modes
        self.updateConfigModes()
        self.showSystems = 1
        self.showPlanets = 1
        self.showFleets = 1
        self.showCivilianFleets = 1
        self.showOverlaySelector = 1
        self.showHotButtons = 1
        self.showPirateAreas = True
        self.highlightPos = None
        self.alwaysShowRangeFor = None
        #setup
        self.pirateDlgs = False
        self.showBuoyDlg = ShowBuoyDlg(self.app)
        self.KeyModHelp = KeyModHelp(self.app)
        self._miniMapRect = Rect(0, 20, 175, 175)
        self._overlayRect = Rect(0, 0, 175, 24)
        self._detectOverlayZone = Rect(0,0,0,0)
        self._hotbuttonsZone = Rect(0,0,0,0)
        self.initHotbuttons()
        self.miniMap = MiniMap(self._miniMapRect.width, self._miniMapRect.height)
        # flags
        self.processKWArguments(kwargs)
        parent.registerWidget(self)
        # popup menu
        self.popup = ui.Menu(self.app, title = _("Select object"))
        self.popup.subscribeAction("*", self)
        # overlay system
        self.overlayMode = gdata.OVERLAY_OWNER
        self._overlayZone = False
        # key setting system
        self.selectobject = False
        self.setKey = False
        # commands
        self.keyPress = False

    def updateConfigModes(self):
        if gdata.config.defaults.showredirects == 'no':
            self.showRedirects = 0
        else:
            self.showRedirects = 1
        if gdata.config.defaults.showcoords == 'no':
            self.showCoords = 0
        else:
            self.showCoords = 1
        if gdata.config.defaults.showmapgrid == 'no':
            self.showGrid = 0
        else:
            self.showGrid = 1
        if gdata.config.defaults.showmapscanners == 'no':
            self.showScanners = 0
        else:
            self.showScanners = 1
        if gdata.config.defaults.showfleetlines == 'no':
            self.showFleetLines = 0
        else:
            self.showFleetLines = 1
        if gdata.config.defaults.showgatesystems == 'no':
            self.showGateSystems = 0
        else:
            self.showGateSystems = 1
        if gdata.config.defaults.alternateviewmode == 'no':
            self.alternativeViewMode = 0
        else:
            self.alternativeViewMode = 1
        if gdata.config.defaults.showplayerzones == 'yes': #default off
            self.toggleControlAreas = 1
        else:
            self.toggleControlAreas = 0
        if gdata.config.defaults.showminimap == 'yes':
            self.showMiniMap = 1
        else:
            self.showMiniMap = 0

    def requestRepaint(self):
        self.repaintMap = 1

    def save(self,append=''):
        name = ("starmap_%s.bmp" % append)
        pygame.image.save(self._mapSurf,name)
        return name

    def precompute(self):
        # clear active areas for buoy texts
        self._actBuoyAreas = {}
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
        pirates = {}
        log.debug("Checking pirate planets and wormholes")
        for objID in client.db.keys():
            if objID < OID_FREESTART:
                continue
            obj = client.get(objID, noUpdate = 1)
            if not hasattr(obj, "type"):
                continue
            if obj.type == T_WORMHOLE and not hasattr(obj, 'destinationOid'):
                obj = client.get(objID, forceUpdate = 1, publicOnly = 1)
            if obj.type == T_PLANET and hasattr(obj, "x"):
                ownerID = getattr(obj, 'owner', OID_NONE)
                if ownerID == OID_NONE:
                    continue
                owner = client.get(ownerID, publicOnly = 1)
                if hasattr(owner, "type") and (owner.type == T_PIRPLAYER or\
                                                owner.type == T_AIPIRPLAYER):
                    pirates[obj.x, obj.y] = None
        # process objects
        self.fleetOrbit = {}
        anyX = 0.0
        anyY = 0.0
        player = client.getPlayer()
        if (player.type == T_PIRPLAYER or\
            player.type == T_AIPIRPLAYER) and not self.pirateDlgs:
            self.pirateDlgs = True
            if self.showHotButtons:
                self.initHotbuttons() #reinit to add the pirate button
        for objID in client.db.keys():
            if objID < OID_FREESTART:
                continue
            obj = client.get(objID, noUpdate = 1)
            if not hasattr(obj, "type"):
                continue
            try:
                if obj.type == T_PLAYER:
                    continue
                if hasattr(obj, "x"):
                    anyX = obj.x
                if hasattr(obj, "y"):
                    anyY = obj.y
            except AttributeError, e:
                log.warning('StarMapWidget', 'Cannot render objID = %d' % objID)
                continue
            if obj.type == T_SYSTEM:
                img = res.getSmallStarImg(obj.starClass[1]) # TODO correct me
                icons = []
                name = getattr(obj, 'name', None)
                # TODO compute real relationship
                #rel = REL_UNDEF
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
                stratRes = SR_NONE
                isGovCentral = False
                #owner2 = 0
                ownerID = OID_NONE
                explored = False
                if hasattr(obj, 'planets'):
                    hasPirate = False
                    for planetID in obj.planets:
                        planet = client.get(planetID, noUpdate = 1)
                        owner = getattr(planet, 'owner', OID_NONE)
                        if hasattr(planet, "plType") and planet.plType not in ("A", "G"):
                            numPlanets += 1
                        if hasattr(planet, "plMin"):
                            minerals = max(minerals,planet.plMin)
                        if hasattr(planet, "plBio"):
                            bio = max(bio,planet.plBio)
                        if hasattr(planet, "plSlots"):
                            slots += planet.plSlots
                        if hasattr(planet, "plStratRes") and planet.plStratRes != SR_NONE:
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
                                    tech = Rules.techs[struct[STRUCT_IDX_TECHID]]
                                    if not tech.govPwr == 0:
                                        isGovCentral = True
                                    if not hasattr(planet, "morale"): # ugly way to say "planets of other players"
                                        # operational status and tech effectivity
                                        maxTechHP = tech.maxHP
                                        opStatus = struct[STRUCT_IDX_OPSTATUS]/100.0
                                        if opStatus != 0:
                                            currHP = struct[STRUCT_IDX_HP]
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
                pirProb = self.precomputePirates(obj, pirates, icons)
                if (player.type == T_PIRPLAYER or\
                        player.type == T_AIPIRPLAYER):
                    pirateFameCost = self.getPirateFameCost(player.oid,obj.oid,len(player.planets),pirates)
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
                self.precomputeBuoys(obj, player, icons)
                # star gates
                if speedBoost > 1.0:
                    icons.append(res.icons["sg_%02d" % round(speedBoost)])
                    self._map[self.MAP_GATESYSTEMS].append((obj.x, obj.y, speedBoost))
                #if owner2 != 0:
                #   color = gdata.playerHighlightColor
                #else:
                #   color = res.getFFColorCode(rel)
                if (player.type == T_PIRPLAYER or\
                        player.type == T_AIPIRPLAYER):
                    colors = res.getStarmapWidgetSystemColor(ownerID,bio,minerals,slots,numPlanets,speedBoost, refuelInc, upgradeShip, pirProb*100, stratRes, morale, pirateFameCost)
                else:
                    colors = res.getStarmapWidgetSystemColor(ownerID,bio,minerals,slots,numPlanets,speedBoost, refuelInc, upgradeShip, pirProb*100, stratRes, morale)
                namecolor = res.getPlayerColor(ownerID)
                controlcolor = res.getControlColor(ownerID)
                if controlcolor:
                    groupCenterX = int(anyX)
                    groupCenterY = int(anyY)
                    for rX in range(-CONTROLRANGE,CONTROLRANGE):
                        for rY in range(-CONTROLRANGE,CONTROLRANGE):
                            if rX*rX+rY*rY < MAXCONTROLRANGE:
                                ctrlid = "%d:%d" % (groupCenterX+rX,groupCenterY+rY)
                                dist = pow(anyX-(groupCenterX+rX+0.5),2) + pow(anyY-(groupCenterY+rY+0.5),2)
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
                if (player.type == T_PIRPLAYER or\
                        player.type == T_AIPIRPLAYER):
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
            elif obj.type == T_WORMHOLE:
                log.debug("Displaying wormhole",obj.oid)
                img = res.getSmallStarImg(obj.starClass[1])
                icons = []
                name = getattr(obj, 'name', None)
                pirProb = self.precomputePirates(obj, pirates, icons)
                self.precomputeCombat(obj, icons)
                self.precomputeBuoys(obj, player, icons)
                color = res.getPlayerColor(OID_NONE)
                namecolor = res.getPlayerColor(OID_NONE)
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
            elif obj.type == T_PLANET:
                owner = getattr(obj, 'owner', OID_NONE)
                # set up color reference data
                biodata = -1
                mindata = -1
                slotdata = 0
                stargatedata = 0
                dockrefueldata = 0
                dockupgradedata = 0
                stratresdata = SR_NONE
                moraledata = -1
                pirProb = self.precomputePirates(obj, pirates, False)
                famedata = pirProb*100
                biodata = getattr(obj, 'plBio', -1)
                mindata = getattr(obj, 'plMin', -1)
                slotdata = getattr(obj, 'plSlots', 0)
                dockrefueldata = getattr(obj, 'refuelInc', 0)
                dockupgradedata = getattr(obj, 'upgradeShip', 0)
                stargatedata = getattr(obj, 'fleetSpeedBoost', 0)
                stratresdata = getattr(obj, 'plStratRes', SR_NONE)
                moraledata = getattr(obj, 'morale', -1)
                if (player.type == T_PIRPLAYER or\
                        player.type == T_AIPIRPLAYER):
                    pirateFameCost = self.getPirateFameCost(player.oid,obj.compOf,len(player.planets),pirates)
                # build system
                name = getattr(obj, 'name', None) or res.getUnknownName()
                singlet = True
                if hasattr(obj, "plType") and obj.plType in ("A", "G"):
                    colors = gdata.sevColors[gdata.DISABLED]
                else:
                    singlet = False
                    if (player.type == T_PIRPLAYER or\
                            player.type == T_AIPIRPLAYER):
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
                if (player.type == T_PIRPLAYER or\
                        player.type == T_AIPIRPLAYER):
                    info.append(_('Fame to Colonize: %d') % pirateFameCost)
                if hasattr(obj, 'plBio'): info.append(_('Environment: %d') % obj.plBio)
                if hasattr(obj, 'plMin'): info.append(_('Minerals: %d') % obj.plMin)
                if hasattr(obj, 'plEn'): info.append(_('Energy: %d') % obj.plEn)
                if hasattr(obj, 'plSlots'): info.append(_('Slots: %d') % obj.plSlots)
                if hasattr(obj, "plStratRes") and obj.plStratRes != SR_NONE:
                    info.append(_("Strat. resource: %s") % _(gdata.stratRes[obj.plStratRes]))
                if owner:
                    ownerobj = client.get(owner, publicOnly = 1)
                    info.append(_('Owner: %s [ID: %s]') % (
                        getattr(ownerobj, 'name', res.getUnknownName()),
                        getattr(ownerobj, 'oid', '?')
                    ))
                self._popupInfo[obj.oid] = info
            elif obj.type == T_FLEET:
                self.precomputeFleet(obj)
            elif obj.type == T_ASTEROID:
                owner = getattr(obj, 'owner', OID_NONE)
                name = getattr(obj, 'name', None) or res.getUnknownName()
                color = (0xff, 0xff, 0xff)
                scannerPwr = getattr(obj, 'scannerPwr', 0)
                orbit = -1
                if obj.orbiting != OID_NONE:
                    orbit = self.fleetOrbit.get(obj.orbiting, 0)
                    self.fleetOrbit[obj.orbiting] = orbit + 1
                eta = getattr(obj, 'eta', 0)
                self._map[self.MAP_FLEETS].append((obj.oid, obj.x, obj.y, obj.oldX, obj.oldY, orbit, res.formatTime(eta), color,
                    obj.signature / 25, 0))
                # pop up info
                info = []
                info.append(_('Asteroid: %s [ID: %d]') % (name, obj.oid))
                if hasattr(obj, 'scanPwr'): info.append(_('Scan pwr: %d') % obj.scanPwr)
                info.append(_('Coordinates: [%.2f, %.2f]') % (obj.x, obj.y))
                info.append(_('Signature: %d') % obj.signature)
                if hasattr(obj, 'asDiameter'): info.append(_('Diameter: %d') % obj.asDiameter)
                if hasattr(obj, 'asHP'): info.append(_('HP: %d') % obj.asHP)
                if hasattr(obj, 'speed'): info.append(_('Speed: %.2f') % obj.speed)
                if eta:
                    info.append(_('ETA: %s') % res.formatTime(eta))
                if owner:
                    ownerobj = client.get(owner, publicOnly = 1)
                    info.append(_('Owner: %s [ID: %s]') % (
                        getattr(ownerobj, 'name', res.getUnknownName()),
                        getattr(ownerobj, 'oid', '?')
                    ))
                self._popupInfo[obj.oid] = info
            elif obj.type in (T_GALAXY, T_AIPLAYER, T_AIRENPLAYER, T_AIMUTPLAYER, T_AIPIRPLAYER, T_AIEDENPLAYER, T_PIRPLAYER):
                pass
            elif obj.type == T_UNKNOWN:
                # pop up info
                info = []
                info.append(_('Unknown object [ID: %d]') % obj.oid)
                if hasattr(obj, 'scanPwr'):
                    info.append(_('Scan pwr: %d') % obj.scanPwr)
                self._popupInfo[obj.oid] = info
            else:
                log.warning('StarMapWidget', 'Unknown object type %d' % obj.type)
        # redirections
        self.precomputeRedirections()
        # set position (typically on first show)
        if self.setPosition:
            self.setPosition = 0
            self.currX = anyX
            self.currY = anyY

        self.miniMap.precompute()
        # self dirty flag
        self.repaintMap = 1

    def getPirateFameCost(self, playerID, systemID, numPiratePlanets, pirates):
        mod = 1
        system = client.get(systemID, noUpdate = 1)
        if hasattr(system,'planets') and system.planets:
            for planetID in system.planets:
                planet = client.get(planetID, noUpdate = 1)
                if getattr(planet, 'owner', OID_NONE) == playerID:
                    # minimum reached, don't check rest
                    return 0.0
                elif getattr(planet, 'plStratRes', None) in (SR_TL3A, SR_TL3B, SR_TL3C):
                    mod = min(mod, Rules.pirateTL3StratResColonyCostMod)
        dist = 10000
        for pirX, pirY in pirates:
            dist = min(dist, math.hypot(system.x - pirX, system.y - pirY))
        if Rules.pirateGainFamePropability(dist) > 0:
            mod = Rules.pirateColonyFameZoneCost(dist)
        else:
            mod = Rules.pirateColonyPlayerZoneCost(dist)
        return mod * numPiratePlanets * Rules.pirateColonyCostMod

    def OLDgetPirateFameCost(self, playerID, systemID,numPiratePlanets):
        mod = 1.0
        system = client.get(systemID, noUpdate = 1)
        for planetID in system.planets:
            planet = client.get(planetID, noUpdate = 1)
            if getattr(planet, 'owner', OID_NONE) == playerID:
                # minimum reached, don't check rest
                return 0.0
            elif getattr(planet, 'plStratRes', None) in (SR_TL3A, SR_TL3B, SR_TL3C):
                mod = min(mod, Rules.pirateTL3StratResColonyCostMod)
        famePenalty = int(mod * Rules.pirateColonyCostMod * numPiratePlanets)
        return famePenalty

    def precomputeRedirections(self,repaint=False): #also called from Mass Redirector
        if repaint:
            self._map[self.MAP_FREDIRECTS] = []
        player = client.getPlayer()
        for sourceID in player.shipRedirections:
            targetID = player.shipRedirections[sourceID]
            source = client.get(sourceID, noUpdate = 1)
            target = client.get(targetID, noUpdate = 1)
            if hasattr(source, "x") and hasattr(target, "y"):
                self._map[self.MAP_FREDIRECTS].append((source.x, source.y, target.x, target.y))
        if repaint:
            self.repaintMap = 1

    def precomputeFleet(self,obj):

        owner = getattr(obj, 'owner', OID_NONE)
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
        if obj.orbiting != OID_NONE:
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
        if hasattr(obj, 'target') and obj.target != OID_NONE:
            target = client.get(obj.target, noUpdate=1)
            if hasattr(target, "x"):
                self._fleetTarget[obj.oid] = (obj.x, obj.y, target.x, target.y)
            info.append(_('Target: %s') % getattr(target, "name", res.getUnknownName()))
        # pop up info (continued)
        if hasattr(obj, 'ships'):
            info.append(_('Ships:'))
            number = {}
            for designID, hp, shield, exp in obj.ships:
                tech = client.getPlayer().shipDesigns[designID]
                level = Rules.shipExpToLevel.get(int(exp / tech.baseExp), Rules.shipDefLevel)
                if designID not in number:
                    number[designID] = [0, 0, 0, 0, 0]
                number[designID][level - 1] += 1
            order = number.keys()
            order.sort()
            for designID in order:
                tech = client.getPlayer().shipDesigns[designID]
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
            if target != OID_NONE:
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
                    if action == FLACTION_REFUEL: color = (0x00, 0x90, 0x00)
                    elif action == FLACTION_DEPLOY: color = (0x90, 0x90, 0x00)
                    elif action == FLACTION_REDIRECT: color = (0x20, 0x20, 0x80)
                    else: color = (0x90, 0x90, 0x90)
                    trgt = client.get(target, noUpdate = 1)
                    if hasattr(trgt, 'x'):
                        self._map[self.MAP_FORDERS].append((oldX, oldY, trgt.x, trgt.y, color, getattr(obj, "isMilitary", 0)))
                        self._fordersTarget[obj.oid].append((oldX, oldY, trgt.x, trgt.y, color))
                        oldX, oldY = trgt.x, trgt.y

    def precomputePirates(self, system, pirates, icons = False):
        dist = 10000
        for pirX, pirY in pirates:
            dist = min(dist, math.hypot(system.x - pirX, system.y - pirY))
        pirProb = Rules.pirateGainFamePropability(dist)
        if icons != False:
            if pirProb >= 1.0:
                icons.append(res.icons["pir_99"])
            elif pirProb > 0.0:
                icons.append(res.icons["pir_00"])
        return pirProb

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

    def drawScanners(self):
        # default scanner ranges (inner and outer circles)
        scanner1range = 1.0/10
        scanner2range = 1.0/16
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxX = self._mapSurf.get_rect().width
        maxY = self._mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        scannerCalced = []
        # draw
        for x, y, range in self._map[self.MAP_SCANNER1]:
            sx = int((x - currX) * scale) + centerX
            sy = maxY - (int((y - currY) * scale) + centerY)
            currRange = int(range * scale * scanner1range + 2)
            range1 = int(range * scale * scanner1range)
            range2 = int(range * scale * scanner2range)
            if sx+currRange > 0 and sx-currRange < maxX and sy+currRange > 0 and sy-currRange < maxY:
                pygame.draw.circle(self._mapSurf, (0x00, 0x00, 0x60), (sx, sy), currRange, 2)
                scannerCalced.append((sx,sy,range1,range2))
        for sx, sy, range1, range2 in scannerCalced:
            pygame.draw.circle(self._mapSurf, (0x00, 0x00, 0x30), (sx, sy), range1, 0)
        for sx, sy, range1, range2 in scannerCalced:
            pygame.draw.circle(self._mapSurf, (0x00, 0x00, 0x40), (sx, sy), range2, 0)
#        log.debug("Total scanner circles:",len(self._map[self.MAP_SCANNER1]))
#        log.debug("Drawn scanner circles:",len(scannerCalced))

    def drawControlAreas(self):
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
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
            self._mapSurf.fill(self._map[self.MAP_CONTROLAREA][xy][0], pygame.Rect(sx, sy, dx, dy), 0)

    def drawRedirects(self):
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        for sx, sy, tx, ty in self._map[self.MAP_FREDIRECTS]:
            sx = int((sx - currX) * scale) + centerX
            sy = maxY - (int((sy - currY) * scale) + centerY)
            tx = int((tx - currX) * scale) + centerX
            ty = maxY - (int((ty - currY) * scale) + centerY)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy + 1), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy - 1), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy + 1), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx + 1, sy - 1), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy + 1), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx - 1, sy - 1), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx + 2, sy), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx - 2, sy), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy + 2), (tx, ty), 1)
            pygame.draw.line(self._mapSurf, (0x20, 0x20, 0x80), (sx, sy - 2), (tx, ty), 1)
            # pygame.draw.line(self._mapSurf, (0x00, 0x00, 0x80), (sx, sy), ((sx + tx) / 2, (sy + ty) / 2), 3)

    def drawSystems(self):
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        namecolor = res.getPlayerColor(OID_NONE)
        if scale >= 30:
            for objID, x, y, name, img, color, namecolor, singlet, icons, constPoints, sciPoints, isGovCentral in self._map[self.MAP_SYSTEMS]:
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                w, h = img.get_size()
                x = sx - w / 2
                y = sy - h / 2
                self._mapSurf.blit(img, (x, y))
                # images are now smaller - TODO fix images of stars
                w = 22
                h = 22
                if name:
                    if self.overlayMode != gdata.OVERLAY_OWNER:
                        namecolor = res.fadeColor(namecolor)
                    img = renderText(self.textSize, name, 1, namecolor)
                    self._mapSurf.blit(img, (sx - img.get_width() / 2, sy + h / 2))
                buoy = self.getBuoy(objID)
                if buoy != None and not self.alternativeViewMode:
                    if not name: #if name not set and there is a bouy, set "?" as the name
                        if self.overlayMode != gdata.OVERLAY_OWNER:
                            namecolor = res.fadeColor(namecolor)
                        img = renderText(self.textSize, '[ ? ]', 1, namecolor)
                        self._mapSurf.blit(img, (sx - img.get_width() / 2, sy + h / 2))
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
                        img = renderText(self.textSize, line, 1, bouycolor)
                        maxW = max(img.get_width(), maxW)
                        self._mapSurf.blit(img, (sx - img.get_width() / 2, nSy + hh))
                        hh += img.get_height()
                    if maxW > 0:
                        actRect = Rect(sx - maxW / 2, nSy, maxW, hh)
                        actRect.move_ip(self.rect.left, self.rect.top)
                        self._actBuoyAreas[objID] = actRect
                elif self.alternativeViewMode:
                    alternative = name
                    nSy = sy + h / 2 + img.get_height()
                    if constPoints != 0 or sciPoints != 0:
                        img = renderText(self.textSize, u"CP: %d RP: %d" % (constPoints, sciPoints), 1, namecolor)
                        self._mapSurf.blit(img, (sx - img.get_width() / 2, nSy))
                    if isGovCentral:
                        img = renderText(self.textSize, u"Central system", 1, (255, 255, 255))
                        self._mapSurf.blit(img, (sx - img.get_width() / 2, nSy + img.get_height()))
                for icon in icons:
                    self._mapSurf.blit(icon, (x, y))
                    x += icon.get_width() + 1
                # active rectangle
                actRect = Rect(sx - w / 2, sy - h / 2, w, h)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect
        else:
            for objID, x, y, name, img, color, namecolor, singlet, icons, constPoints, sciPoints, isGovCentral in self._map[self.MAP_SYSTEMS]:
                if not singlet:
                    color = color[self.overlayMode]
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                pygame.draw.circle(self._mapSurf, color, (sx, sy), 5, 1)
                pygame.draw.circle(self._mapSurf, color, (sx, sy), 4, 0)
                if name and scale > 15:
                    if self.overlayMode != gdata.OVERLAY_OWNER:
                        namecolor = res.fadeColor(namecolor)
                    img = renderText(self.textSize, name, 1, namecolor)
                    self._mapSurf.blit(img, (sx - img.get_width() / 2, sy + 6 / 2))
                    buoy = self.getBuoy(objID)
                    if buoy != None:
                        lines = buoy[0].split("\n")
                        nSy = sy + 6 / 2 + img.get_height()
                        maxW = 0
                        hh = 0
                        for line in lines:
                            if len(line) == 0:
                                break
                            img = renderText(self.textSize, line, 1, buoyColors[buoy[1] - 1])
                            maxW = max(img.get_width(), maxW)
                            self._mapSurf.blit(img, (sx - img.get_width() / 2, nSy + hh))
                            hh += img.get_height()
                        if maxW > 0:
                            actRect = Rect(sx - maxW / 2, nSy, maxW, hh)
                            actRect.move_ip(self.rect.left, self.rect.top)
                            self._actBuoyAreas[objID] = actRect
                # active rectangle
                actRect = Rect(sx - 6 / 2, sy - 6 / 2, 6, 6)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect

    def drawGateSystems(self):
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
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
                    pygame.draw.circle(self._mapSurf, color, (sx, sy), radius, 1)

    def drawPlanets(self):
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
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
                actRect = Rect(sx + (orbit % 8) * rectSpace + 13, sy + 6 * (orbit / 8) - rectSize , rectSize, rectSize)

                self._mapSurf.fill(color, actRect)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect
        elif scale > 20:
            for objID, x, y, orbit, color, singlet in self._map[self.MAP_PLANETS]:
                if not singlet:
                    color = color[self.overlayMode]
                sx = int((x - currX) * scale) + centerX
                sy = maxY - (int((y - currY) * scale) + centerY)
                orbit -= 1
                actRect = Rect(sx + (orbit % 8) * 3 + 7, sy - 3 * (orbit / 8) - 1, 2, 2)
                self._mapSurf.fill(color, actRect)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect

    def drawFleets(self):
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
        currX = self.currX
        currY = self.currY
        scale = self.scale
        minSize = int(gdata.config.defaults.minfleetsymbolsize)
        rectSize = max(minSize, math.floor(scale / 7) - math.floor(scale / 7) % 2)
        if not int(gdata.config.defaults.maxfleetsymbolsize) == 0:
            rectSize = min(int(gdata.config.defaults.maxfleetsymbolsize), rectSize)
        rectSpace = rectSize + math.floor(rectSize/5)
        # draw orders lines
        if self.showFleetLines:
            for x1, y1, x2, y2, color, military in self._map[self.MAP_FORDERS]:
                if not self.showCivilianFleets and not military:
                    continue
                sx1 = int((x1 - currX) * scale) + centerX
                sy1 = maxY - (int((y1 - currY) * scale) + centerY)
                sx2 = int((x2 - currX) * scale) + centerX
                sy2 = maxY - (int((y2 - currY) * scale) + centerY)
                pygame.draw.line(self._mapSurf, color, (sx1, sy1), (sx2, sy2), 1)
        # draw fleet symbol
        for objID, x, y, oldX, oldY, orbit, eta, color, size, military in self._map[self.MAP_FLEETS]:
            if not self.showCivilianFleets and not military:
                continue
            if self.overlayMode != gdata.OVERLAY_OWNER:
                color = res.fadeColor(color)
            sx = int((x - currX) * scale) + centerX
            sy = maxY - (int((y - currY) * scale) + centerY)
            if orbit >= 0 and scale >= 30:
                actRect = Rect(sx + (orbit % 7) * rectSpace + 13 + 2 * (orbit % 7), sy + scale/6 * (orbit / 7) + 6, rectSize, rectSize)
                # TODO this is a workaround - fix it when pygame gets fixed
                # pygame.draw.polygon(self._mapSurf, color,
                #    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 1)
                pygame.draw.polygon(self._mapSurf, color,
                    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 0)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect
            elif orbit < 0:
                rectSizeFlying = rectSize+2
                sox = int((oldX - currX) * scale) + centerX
                soy = maxY - (int((oldY - currY) * scale) + centerY)
                actRect = Rect(sx - rectSizeFlying / 2, sy - rectSizeFlying / 2, rectSizeFlying , rectSizeFlying)
                if military:
                    mColor = color
                else:
                    mColor = (0xff, 0xff, 0xff)
                pygame.draw.line(self._mapSurf, mColor, (sx, sy), (sox, soy), size + 1)
                # TODO rotate triangle
                pygame.draw.polygon(self._mapSurf, color,
                    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 1)
                pygame.draw.polygon(self._mapSurf, color,
                    (actRect.midleft, actRect.midtop, actRect.midright, actRect.midbottom), 0)
                if eta and scale > 15:
                    img = renderText(self.textSize, eta, 1, color)
                    self._mapSurf.blit(img, actRect.topright)
                actRect.move_ip(self.rect.left, self.rect.top)
                self._actAreas[objID] = actRect

    def drawOverlayEffects(self):
        # coordinates
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
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
                for step in xrange(100, max(Rules.minMoraleTrgt-1, int(107.5-37.5*player.stats.storPop/player.govPwr) - 1) , -10):
                    moraleColor = res.getMoraleColors(step)
                    centralX = int((centralPlanet.x - currX) * scale) + centerX
                    centralY = maxY - (int((centralPlanet.y - currY) * scale) + centerY)
                    radius = int((107.5 - step) * govPCR / 37.5 * scale)
                    pygame.draw.circle(self._mapSurf, moraleColor, (centralX, centralY), radius, 1)
                    text = renderText(self.textSize, step, 1, moraleColor)
                    #maxW = max(text.get_width(), maxW)
                    self._mapSurf.blit(text, (centralX + radius, centralY))



    def draw(self, surface):
        if not self._mapSurf:
            self._mapSurf = pygame.Surface(self.rect.size, SWSURFACE, surface)
            # workaround for FILLED CIRCLE CLIP BUG - TODO remove
            clip = self._mapSurf.get_clip()
            clip.left += 1
            clip.top += 1
            clip.width -= 2
            clip.height -= 2
            self._mapSurf.set_clip(clip)
            #
            self._miniMapRect.left = self.rect.width - self._miniMapRect.width
            self._miniMapRect.top = self.rect.top
            #self._overlayRect.left = self.rect.width - self._overlayRect.width
            self._overlayRect.top = 0 #self.rect.top
            #log.debug("Overlay Rect aligned to top:",self.rect.top)
            self.repaintMap = 1
        if self.repaintMap:
            self._actAreas = {}
            mapSurface = self._mapSurf
            # redraw map
            mapSurface.fill((0x00, 0x00, 0x00))
            # coordinates
            centerX, centerY = mapSurface.get_rect().center
            maxY = mapSurface.get_rect().height
            currX = self.currX
            currY = self.currY
            scale = self.scale
            # clipping (TODO better one)
            clip = mapSurface.get_clip()
            # scanners
            # scanner ranges and control areas
            if self.showScanners or self.toggleControlAreas:
                if self.toggleControlAreas:
                    self.drawControlAreas()
                else:
                    self.drawScanners()
            # pirate area
            if self.showPirateAreas:
                pass # TODO
            # grid
            if self.showGrid:
                self.drawGrid()
            # redirections
            if self.showRedirects:
                self.drawRedirects()
            # gate systems
            if self.showGateSystems:
                self.drawGateSystems()
            # stars
            if self.showSystems:
                self.drawSystems()
            # planets
            if self.showPlanets:
                self.drawPlanets()
            # fleets
            if self.showFleets:
                self.drawFleets()
            self.drawOverlayEffects()
            # clean up flag
            self.repaintHotbuttons = 1
            self.repaintMap = 0
        if self.repaintHotbuttons and self.showHotButtons:
            # overlay selector
            #if self.showOverlaySelector:
            #    self.drawOverlaySelector(surface)
            self.drawHotbuttons()
            # clean up flag
            self.repaintHotbuttons = 0
        # blit cached map
        surface.blit(self._mapSurf, self.rect)
        # additional informations
        oldClip = surface.get_clip()
        surface.set_clip(self.rect)
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
        if self.highlightPos:
            sx = int((self.highlightPos[0] - self.currX) * self.scale) + centerX + self.rect.left
            sy = maxY - (int((self.highlightPos[1] - self.currY) * self.scale) + centerY) + self.rect.top
            pygame.draw.circle(surface, (0xff, 0xff, 0xff), (sx, sy), 13, 2)
        if self.alwaysShowRangeFor and self._fleetRanges.has_key(self.alwaysShowRangeFor):
            x, y, maxRange, operRange, halfRange, speed, turns = self._fleetRanges[self.alwaysShowRangeFor]
            sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
            sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
            rng = max(maxRange * self.scale, 0.2 * self.scale)
            if rng > 1:
                pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), int(rng), 1)
            rng = operRange * self.scale
            if rng > 1:
                pygame.draw.circle(surface, (0x20, 0x80, 0x20), (sx, sy), int(rng), 1)
            rng = halfRange * self.scale
            if rng > 1:
                pygame.draw.circle(surface, (0x20, 0x20, 0x80), (sx, sy), int(rng), 1)
        # draw ranges
        for activeObjID in self.activeObjIDs:
            if activeObjID and activeObjID in self._fleetTarget:
                x, y, x1, y1 = self._fleetTarget[activeObjID]
                sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
                sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
                dx = int((x1 - self.currX) * self.scale) + centerX + self.rect.left
                dy = maxY - (int((y1 - self.currY) * self.scale) + centerY) + self.rect.top
                pygame.draw.line(surface, (0xff, 0xff, 0x00), (sx, sy), (dx, dy), 2)
            if activeObjID and activeObjID in self._fordersTarget:
                for x, y, x1, y1, color in self._fordersTarget[activeObjID]:
                    sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
                    sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
                    dx = int((x1 - self.currX) * self.scale) + centerX + self.rect.left
                    dy = maxY - (int((y1 - self.currY) * self.scale) + centerY) + self.rect.top
                    pygame.draw.line(surface, color, (sx, sy), (dx, dy), 2)
            if activeObjID and activeObjID in self._fleetRanges:
                x, y, maxRange, operRange, halfRange, speed, turns = self._fleetRanges[activeObjID]
                sx = int((x - self.currX) * self.scale) + centerX + self.rect.left
                sy = maxY - (int((y - self.currY) * self.scale) + centerY) + self.rect.top
                if pygame.key.get_mods() & KMOD_SHIFT:
                    for i in xrange(1, turns / 6):
                        rng = int(i * speed * self.scale)
                        if rng > 1:
                            pygame.draw.circle(surface, (0x70, 0x70, 0x80), (sx, sy), rng, 1)
                            textSrfc = renderText(self.textSize, res.formatTime(i * 6), 1, (0x70, 0x70, 0x80), (0x00, 0x00, 0x00))
                            surface.blit(textSrfc, (sx - rng, sy - textSrfc.get_height() / 2))
                            surface.blit(textSrfc, (sx + rng, sy - textSrfc.get_height() / 2))
                            surface.blit(textSrfc, (sx - textSrfc.get_width() / 2, sy - rng))
                            surface.blit(textSrfc, (sx - textSrfc.get_width() / 2, sy + rng - textSrfc.get_height()))
                    rng = int(max(maxRange * self.scale, 0.2 * self.scale))
                    if rng > 1:
                        pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), rng, 1)
                else:
                    rng = int(max(maxRange * self.scale, 0.2 * self.scale))
                    if rng > 1:
                        pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), rng, 1)
                    rng = int(operRange * self.scale)
                    if rng > 1:
                        pygame.draw.circle(surface, (0x20, 0x80, 0x20), (sx, sy), rng, 1)
                    rng = int(halfRange * self.scale)
                    if rng > 1:
                        pygame.draw.circle(surface, (0x20, 0x20, 0x80), (sx, sy), rng, 1)

        if self.showMiniMap:
            self.miniMap.draw(surface, self._miniMapRect.left, self._miniMapRect.top)
            if self.miniMap.needRect():
                self.processMiniMapRect()
                self.miniMap.draw(surface, self._miniMapRect.left, self._miniMapRect.top)
        # draw popups
        moreIDs = len(self.activeObjIDs) > 1
        if not moreIDs:
            x, y = self.activePos
            x += 20
        else:
            x = self.rect.left + 2
            y = self.rect.top
        if not pygame.key.get_mods() & KMOD_SHIFT:
            for activeObjID in self.activeObjIDs:
                index = 0
                if self._popupInfo.has_key(activeObjID):
                    # put pop up info on the screen
                    info = self._popupInfo[activeObjID]
                    # x1, y1 = self._actAreas[self.activeObjID].center
                    fg = self.theme.themeForeground #(0x30, 0xe0, 0x30, 0xff)
                    bg = self.theme.themeBackground #(0x20, 0x40, 0x20, 0x99)
                    width = 0
                    height = 0
                    # pygame.draw.line(surface, fg, (x1, y1), (x, y), 1)
                    for item in info:
                        w, h = getTextSize('normal', item)
                        width = max(width, w)
                        height += h
                    if not moreIDs:
                        if x + width >= self.rect.width:
                            x -= width + 40
                        if y + 1 + height >= self.rect.height:
                            y -= height
                    surface.fill(bg, (x, y, width + 2, height + 2))
                    x += 1
                    tmpY = y + 1
                    for item in info:
                        textSrfc = renderText('normal', item, 1, fg)
                        surface.blit(textSrfc, (x, tmpY))
                        tmpY += textSrfc.get_height()
                    x += width + 2

        # restore clipping
        surface.set_clip(oldClip)
        #
        return self.rect

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

    def drawOverlaySelector(self,surface):

        #guess we have to make this a popup! :(
        #log.debug('Overlay Size:',self._overlayRect.width,self._overlayRect.height)
        if not self._overlayZone:
            self._overlayZone = pygame.Surface((self._overlayRect.width,self._overlayRect.height),SWSURFACE | SRCALPHA, surface)

        self._detectOverlayZone.top = self._overlayRect.top + self.rect.top
        self._detectOverlayZone.left = self._overlayRect.left
        self._detectOverlayZone.width = self._overlayRect.width
        self._detectOverlayZone.height = self._overlayRect.height

        self._overlayZone.fill((0x00,0x00,0x00))

        pygame.draw.rect(self._overlayZone,(0x00, 0x00, 0x90),Rect(0,0,self._overlayRect.width,self._overlayRect.height),1)




        #pygame.draw.rect(self.overlayZone,(0x00, 0x00, 0x00),self._overlayRect,0) #this picks up mouse button position
        #pygame.draw.rect(self._mapSurf,(0x00, 0x00, 0x00),self._overlayRect,0)
        #pygame.draw.rect(self.overlayZone,(0x00, 0x00, 0x90),self._overlayRect,1)


        mode = _("Overlay Mode: ")
        if self.overlayMode == gdata.OVERLAY_OWNER:
            mode = mode + _("Normal")
        if self.overlayMode == gdata.OVERLAY_DIPLO:
            mode = mode + _("Diplomatic")
        if self.overlayMode == gdata.OVERLAY_BIO:
            mode = mode + _("Environment")
        if self.overlayMode == gdata.OVERLAY_FAME:
            mode = mode + _("Pirate Fame")
        if self.overlayMode == gdata.OVERLAY_MIN:
            mode = mode + _("Minerals")
        if self.overlayMode == gdata.OVERLAY_SLOT:
            mode = mode + _("Slots")
        if self.overlayMode == gdata.OVERLAY_STARGATE:
            mode = mode + _("Fleet Acceleration")
        if self.overlayMode == gdata.OVERLAY_DOCK:
            mode = mode + _("Refuel and Repair")
        if self.overlayMode == gdata.OVERLAY_MORALE:
            mode = mode + _("Morale")

        textSrfc = renderText(self.textSize, mode, 1, (0x70, 0x70, 0x80))
        self._overlayZone.blit(textSrfc, (
            6,
            4 )
        )

        self._mapSurf.blit(self._overlayZone, self._overlayRect)
#        surface.blit(self._overlayZone, self._overlayRect)




    def drawGrid(self):
        rect = self._mapSurf.get_rect()
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
                pygame.draw.line(self._mapSurf, (0x00, 0x00, 0x90),
                    (x, rect.top), (x, rect.bottom), 1)
                if self.showCoords:
                    textSrfc = renderText(self.textSize, int(value), 1, (0x70, 0x70, 0x80))
                    self._mapSurf.blit(textSrfc, (x + 2, rect.height - textSrfc.get_height()))
            else:
                pygame.draw.line(self._mapSurf, (0x33, 0x33, 0x66),
                    (x, rect.top), (x, rect.bottom), 1)
            x += scale
        top = int((int(currY) - currY) * scale) + centerY - int(rect.height / scale / 2) * scale
        y = top
        while y < top + rect.height + scale:
            yScrn = maxY - y
            value =  math.floor(((maxY - yScrn) - centerY) / scale + currY)
            if value % 5 == 0:
                pygame.draw.line(self._mapSurf, (0x00, 0x00, 0x90),
                    (rect.left, yScrn), (rect.right, yScrn), 1)
                textSrfc = renderText(self.textSize, int(value), 1, (0x70, 0x70, 0x80))
                self._mapSurf.blit(textSrfc, (0, yScrn))
            else:
                pygame.draw.line(self._mapSurf, (0x33, 0x33, 0x66),
                    (rect.left, yScrn), (rect.right, yScrn), 1)
            y += scale

    def drawHotbuttons(self):
        rect = self._mapSurf.get_rect()
        bottom = rect.bottom
        right = rect.right
        dx = 137
        dy = 46
        top = bottom - dy - 1
        left = right - dx - 1
        self._hotbuttonsZone.top = top + self.rect.top
        self._hotbuttonsZone.left = left
        self._hotbuttonsZone.width = dx
        self._hotbuttonsZone.height = dy

        pygame.draw.rect(self._mapSurf,(0x00, 0x00, 0x90),(left-1,top-1,dx+2,dy+2))
        pygame.draw.rect(self._mapSurf,(0x33, 0x33, 0x66),(left,top,dx,dy))

        for buttonkey in self._hotbuttons:
            button = self._hotbuttons[buttonkey]
            self._hotbuttonRects[button[0]] = [button[0],Rect(button[2]+self._hotbuttonsZone.left,button[3]+self._hotbuttonsZone.top+15,button[4],button[5])]
            img = res.getButton(button[0],button[1])
            if (button[1] and not (self._tempOverlayHotbutton and self._tempOverlayHotbutton == button[0])) or (not button[1] and self._tempOverlayHotbutton and self._tempOverlayHotbutton == button[0]):
                pygame.draw.rect(self._mapSurf,(0x90, 0x90, 0x90),(left+button[2]-1,top+15+button[3]-1,button[4]+2,button[5]+2),1)
            self._mapSurf.blit(img,(left+button[2],top+15+button[3]))
        if self._tempOverlayHotbutton:
            text = self._hotbuttons[self._tempOverlayHotbutton][7]
            textSrfc = renderText(self.textSize, text, 1, (0xEF, 0xEF, 0xEF))
            self._mapSurf.blit(textSrfc, (left+2,top+1))

    def initHotbuttons(self):
        # key : [ key , state , x , y , dx, dy, value, tooltip ]
        # 'value' is "active state' gdata value or true
        self._hotbuttons = {
            'pzone': ['pzone',self.toggleControlAreas,2,2,17,13, 1,_('Player Zones (CTRL-P)')],
            'civ': ['civ',self.showCivilianFleets,21,2,18,13, 1,_('Civilian Ships (CTRL-H)')],
            'lines': ['lines',self.showFleetLines,41,2,18,13, 1,_('Fleet Lines (CTRL-L)')],
            'redir': ['redir',self.showRedirects,61,2,18,13, 1,_('Redirect Arrows (CTRL-R)')],
            'scanner': ['scanner',self.showScanners,81,2,17,13, 1,_('Scanners (CTRL-S)')],
            'grid': ['grid',self.showGrid,100,2,17,13, 1,_('Grid (CTRL-G)')],
            'alternate': ['alternate',self.alternativeViewMode,119,2,17,13, 2,_('Alternate View (CTRL-A)')],
            'ov_diplo': ['ov_diplo',False,2,17,13,13, gdata.OVERLAY_DIPLO,_('Overlay: Diplomacy')],
            'ov_min': ['ov_min',False,17,17,13,13, gdata.OVERLAY_MIN,_('Overlay: Minerals')],
            'ov_env': ['ov_env',False,32,17,13,13, gdata.OVERLAY_BIO,_('Overlay: Environment')],
            'ov_slot': ['ov_slot',False,47,17,13,13, gdata.OVERLAY_SLOT,_('Overlay: Slots')],
            'ov_morale': ['ov_morale',False,62,17,13,13, gdata.OVERLAY_MORALE,_('Overlay: Morale')],
            'ov_fuel': ['ov_fuel',False,77,17,13,13, gdata.OVERLAY_DOCK,_('Overlay: Fuel and Repair')],
            'ov_gate': ['ov_gate',False,92,17,13,13, gdata.OVERLAY_STARGATE,_('Overlay: Star Gate Speed')],
            'ov_pirate': ['ov_pirate',False,107,17,13,13, gdata.OVERLAY_FAME,_('Overlay: Pirate Fame')],
        }
        if self.pirateDlgs:
            self._hotbuttons['ov_piratecolony'] = ['ov_piratecolony',False,122,17,13,13, gdata.OVERLAY_PIRATECOLONYCOST,'Overlay: Pirate Colony Cost']
        self._oldOverlayHotbutton = False;
        self._tempOverlayHotbutton = False;
        self._hotbuttonRects = {}

    def toggleHotbuttons(self,button):
        self.toggleTempButton(False)
        if (button[:3] == 'ov_'): #overlay
            if self._oldOverlayHotbutton == button:
                self.overlayMode = gdata.OVERLAY_OWNER
                self._hotbuttons[button][1] = False
                self._oldOverlayHotbutton = False
            else:
                if self._oldOverlayHotbutton:
                    self._hotbuttons[self._oldOverlayHotbutton][1] = False
                self._hotbuttons[button][1] = True
                self.overlayMode = self._hotbuttons[button][6]
                self._oldOverlayHotbutton = button
        else: #normal toggle
            if self._hotbuttons[button][1]:
                self._hotbuttons[button][1] = 0
            else:
                self._hotbuttons[button][1] = self._hotbuttons[button][6] # set standard value
            if button == 'pzone':
                self.toggleControlAreas = self._hotbuttons[button][1]
            elif button == 'civ':
                self.showCivilianFleets = self._hotbuttons[button][1]
            elif button == 'lines':
                self.showFleetLines = self._hotbuttons[button][1]
            elif button == 'redir':
                self.showRedirects = self._hotbuttons[button][1]
            elif button == 'scanner':
                self.showScanners = self._hotbuttons[button][1]
            elif button == 'grid':
                self.showGrid = self._hotbuttons[button][1]
            elif button == 'alternate':
                self.alternativeViewMode = self._hotbuttons[button][1]
        self.repaintHotbuttons = 1
        self.repaintMap = 1

    def toggleTempButton(self,pos=False):
        if pos: # true unless we are no longer in the box, in which case we are resetting
            currentButton = self.detectButtonOverpass(pos)
            if currentButton == self._tempOverlayHotbutton: return
            if self._tempOverlayHotbutton:
                self._hotbuttons[self._tempOverlayHotbutton][1] = not self._hotbuttons[self._tempOverlayHotbutton][1]
            if not currentButton:
                self.repaintHotbuttons = 1
                self._tempOverlayHotbutton = False
                return
            self._hotbuttons[currentButton][1] = not self._hotbuttons[currentButton][1]
            self._tempOverlayHotbutton = currentButton
        elif self._tempOverlayHotbutton:
            self._hotbuttons[self._tempOverlayHotbutton][1] = not self._hotbuttons[self._tempOverlayHotbutton][1]
            self._tempOverlayHotbutton = False
        self.repaintHotbuttons = 1

    def detectButtonOverpass(self,pos):
        for buttonkey in self._hotbuttonRects:
            #log.debug(self._hotbuttonRects[buttonkey][1],pos)
            if self._hotbuttonRects[buttonkey][1].collidepoint(pos): return buttonkey
        return False

    def processMB1Down(self, evt):
        # handle SHIFT click as MB3
        mods = pygame.key.get_mods()
        if mods & KMOD_SHIFT:
            return self.processMB3Down(evt)
        pos = evt.pos
        # show current position for debugging
        # log.debug(pos)
        if self.showMiniMap:
            if self._miniMapRect.collidepoint(pos):
                return ui.NoEvent
        if self._detectOverlayZone.collidepoint(pos):
            return ui.NoEvent
        if self.showHotButtons and self._hotbuttonsZone.collidepoint(pos):
            return ui.NoEvent
        self.pressedObjIDs = []
        for objID in self._actAreas.keys():
            rect = self._actAreas[objID]
            if rect.collidepoint(pos):
                self.pressedObjIDs.append(objID)

        self.pressedBuoyObjIDs = []
        for objID in self._actBuoyAreas.keys():
            rect = self._actBuoyAreas[objID]
            if rect.collidepoint(pos):
                self.pressedBuoyObjIDs.append(objID)

        if self.pressedObjIDs or self.pressedBuoyObjIDs:
            return ui.NoEvent
        else:
            self.activeObjID = OID_NONE
            return ui.NoEvent

    def processMB1Up(self, evt):
        # handle SHIFT click as MB3
        mods = pygame.key.get_mods()
        if mods & KMOD_SHIFT:
            return self.processMB3Up(evt)
        pos = evt.pos
        if self.showMiniMap:
            if self._miniMapRect.collidepoint(pos):
                self.currX, self.currY = self.miniMap.processMB1Up((pos[0] - self._miniMapRect.left, self._miniMapRect.height - pos[1] + self._miniMapRect.top))
                self.processMiniMapRect()
                self.repaintMap = 1
                return ui.NoEvent
        if self._detectOverlayZone.collidepoint(pos):
            self.showOverlayDlg.display()
            return ui.NoEvent
        if self.showHotButtons and self._hotbuttonsZone.collidepoint(pos):
            button = self.detectButtonOverpass(pos)
            if button:
                self.toggleHotbuttons(button)
            return ui.NoEvent
        objIDs = []
        for objID in self._actAreas.keys():
            rect = self._actAreas[objID]
            if rect.collidepoint(pos):
                objIDs.append(objID)

        bObjIDs = []
        for objID in self._actBuoyAreas.keys():
            rect = self._actBuoyAreas[objID]
            if rect.collidepoint(pos):
                bObjIDs.append(objID)

        if (objIDs or bObjIDs) and (self.pressedObjIDs == objIDs or self.pressedBuoyObjIDs == bObjIDs) and self.action:
            if self.selectobject:
                self.setKeyObject(objIDs,bObjIDs)
                return ui.NoEvent
            self.gotoObject(objIDs,bObjIDs)
            return ui.NoEvent
        else:
            self.activeObjID = OID_NONE
            return ui.NoEvent

    def gotoObject(self,objIDs,bObjIDs):
        if len(objIDs) + len(bObjIDs) == 1:
            if len(objIDs) == 1:
                if self.selectobject:
                    return objIDs[0]
                self.processAction(self.action, objIDs[0])
                self.pressedObjIDs = []
            else:
                if self.selectobject:
                    return OID_NONE
                self.showBuoyDlg.display(bObjIDs[0])
                self.pressedBuoyObjIDs = []
        else:
            # multiple objects -> post pop-up menu
            items = []
            for objID in objIDs:
                obj = client.get(objID)
                if obj.type == T_SYSTEM:
                    name = getattr(obj, "name", None)
                    name = _("System: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == T_WORMHOLE:
                    name = getattr(obj, "name", None)
                    name = _("Worm hole: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == T_PLANET:
                    name = getattr(obj, "name", None)
                    name = _("Planet: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == T_FLEET:
                    if hasattr(obj,'customname') and obj.customname:
                        name = obj.customname
                    else:
                        name = getattr(obj, "name", None)
                    name = _("Fleet: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == T_ASTEROID:
                    name = getattr(obj, "name", None)
                    name = _("Asteroid: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                else:
                    name = _("Unknown object [ID: %d]") % obj.oid
                item = ui.Item(name, action = "onObjectSelected", data = objID)
                items.append(item)
            for objID in bObjIDs:
                obj = client.get(objID)
                if obj.type == T_SYSTEM:
                    name = getattr(obj, "name", None)
                    name = _("Buoy on system: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == T_WORMHOLE:
                    name = getattr(obj, "name", None)
                    name = _("Buoy on worm hole: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                else:
                    name = _("Buoy on unknown object [ID: %d]") % obj.oid
                item = ui.Item(name, action = "onBuoySelected", data = objID)
                items.append(item)
            self.popup.items = items
            self.popup.show()
        if self.selectobject:
            return OID_NONE

    def onObjectSelected(self, widget, action, data):
        self.processAction(self.action, data)

    def onBuoySelected(self, widget, action, data):
        self.showBuoyDlg.display(data)

    def processMB3Down(self, evt):
        if self.showMiniMap:
            if self._miniMapRect.collidepoint(evt.pos):
                return ui.NoEvent
        self._newCurrXY = 1
        return ui.NoEvent

    def processMB3Up(self, evt):
        if self._newCurrXY:
            x, y = evt.pos
            centerX, centerY = self._mapSurf.get_rect().center
            self.currX -= float(centerX - x) / self.scale
            self.currY += float(centerY - y) / self.scale
            self.processMiniMapRect()
            self.repaintMap = 1
            self._newCurrXY = 0
        return ui.NoEvent

    def processMiniMapRect(self):
        if self.showMiniMap:
            rect = self._mapSurf.get_rect()
            self.miniMap.moveRect(self.currX, self.currY, rect.width / self.scale, rect.height / self.scale)

    def processMWUp(self, evt):
        if self.scale < 80:
            x, y = evt.pos
            centerX, centerY = self._mapSurf.get_rect().center
            self.currX -= float(centerX - x) * (1/ self.scale - 1 / (self.scale+5))
            self.currY += float(centerY - y) * (1/ self.scale - 1 / (self.scale+5))
            self.scale += 5
            if self.scale > 60:
                self.textSize = 'large'
            elif self.scale > 40:
                self.textSize = 'normal'
            else:
                self.textSize = 'small'
            self.repaintMap = 1
            self.processMiniMapRect()
        return ui.NoEvent

    def processMWDown(self, evt):
        if self.scale > 10:
            x, y = evt.pos
            centerX, centerY = self._mapSurf.get_rect().center
            self.currX += float(centerX - x) * (1/ self.scale - 1 / (self.scale+5))
            self.currY -= float(centerY - y) * (1/ self.scale - 1 / (self.scale+5))
            self.scale -= 5
            if self.scale > 60:
                self.textSize = 'large'
            elif self.scale > 40:
                self.textSize = 'normal'
            else:
                self.textSize = 'small'
            self.repaintMap = 1
            self.processMiniMapRect()
        return ui.NoEvent

    def processMMotion(self, evt):
        pos = evt.pos
        if self.showMiniMap:
            if self._miniMapRect.collidepoint(pos):
                #log.debug('Minimap Rect Position');
                return ui.NoEvent
        if self._detectOverlayZone.collidepoint(pos):
            #log.debug('Overlay Rect Position');
            return ui.NoEvent
        if self.showHotButtons and self._hotbuttonsZone.collidepoint(pos):
            #should give hotkey tooltips for this eventually
            self.toggleTempButton(pos)
            return ui.NoEvent
        elif self._tempOverlayHotbutton: # cleanup if cursor not in zone
            self.toggleTempButton(False)
        self.activeObjID = OID_NONE
        self.activeObjIDs = []
        for objID in self._actAreas.keys():
            rect = self._actAreas[objID]
            if rect.collidepoint(pos):
                self.activeObjID = objID
                self.activeObjIDs.append(objID)
                self.activePos = pos
        return ui.NoEvent

    # put actually processing of key in "processKeyUp" using key pressed during "processKeyDown" to prevent erroneous double press detection when holding down CTRL, SHIFT, or ALT keys
    def processKeyDown(self, evt):
        self.keyPress = evt
        if self.callEventHandler:
            self.callEventHandler.processKeyDown(evt)
        return ui.NoEvent

    def processKeyUp(self,evt2):
        if self.callEventHandler:
            self.callEventHandler.processKeyUp(evt2)
        evt = self.keyPress
        if not self.keyPress: return ui.NoEvent
        self.keyPress = False
        # ==== Object Hotkeys ====
        #I have not found unicode escape characters for Ctrl-0 through Ctrl-9, so using direct key reference (less preferred due to international keyboards)
        if evt.key in [49,50,51,52,53,54,55,56,57,48]:
            if pygame.key.get_mods() & KMOD_CTRL:
                log.debug('Set Key:',evt.key)
                if gdata.config.defaults.displayhelp != 'no':
                    self.KeyModHelp.show()
                self.selectobject = True
                self.setKey = evt.key
                self.app.setStatus(_("Select object to hotkey. ESC to cancel."))
            elif pygame.key.get_mods() & KMOD_SHIFT:
                log.debug('Focus Key:',evt.key)
                self.focusOnKeyObject(evt.key)
            else:
                log.debug('Goto Key:',evt.key)
                self.gotoKeyObject(evt.key)
            return ui.NoEvent
        # ==== Map and Dialog Hotkeys ====
        elif evt.key == K_ESCAPE and self.selectobject:
            log.debug('Canceled Key')
            if self.selectobject:
                self.app.setStatus(_("Ready."))
                self.selectobject = False
            return ui.NoEvent
        if not evt.unicode:
            # force update
            self.scale += 1
            self.scale -= 1
            return ui.NoEvent
        if evt.unicode in u'+=':
            self.scale += 5
            self.repaintMap = 1
        elif evt.unicode == u'-':
            if self.scale > 10:
                self.scale -= 5
                self.repaintMap = 1
        # Space Bar - Recenter
        elif evt.unicode == u' ':
            x, y = pygame.mouse.get_pos()
            centerX, centerY = self._mapSurf.get_rect().center
            self.currX -= float(centerX - x) / self.scale
            self.currY += float(centerY - y) / self.scale
            self.repaintMap = 1
            self._newCurrXY = 0
        # ==== Standard Hotkeys ====
        # Ctrl+A - Alternative system info [production instead of buoys]
        elif evt.unicode == u'\x01':
            self.toggleHotbuttons('alternate')
        # Reserve CTRL-C for copy (future editor support)
        # Ctrl+F
        elif evt.unicode == u'\x06' and pygame.key.get_mods() & KMOD_CTRL:
            self.searchDlg.display()
        # Ctrl+G - Toggle grid
        elif evt.unicode == u'\x07' and pygame.key.get_mods() & KMOD_CTRL:
            self.toggleHotbuttons('grid')
        # Ctrl-H - Toggle visibility of civilian ships
        elif evt.unicode == u'\x08' and pygame.key.get_mods() & KMOD_CTRL:
            self.toggleHotbuttons('civ')
        # Ctrl+L - Toggle drawing fleet lines
        elif evt.unicode == u'\x0C' and pygame.key.get_mods() & KMOD_CTRL:
            self.toggleHotbuttons('lines')
        # Ctrl+M
        elif evt.unicode == u'\x0D' and pygame.key.get_mods() & KMOD_CTRL:
            self.showOverlayDlg.display()
        # Ctrl+P - Toggle viewing of control areas (turns off scanner circles)
        elif evt.unicode == u'\x10' and pygame.key.get_mods() & KMOD_CTRL:
            self.toggleHotbuttons('pzone')
        # Ctrl+R - Toggle drawing redirects
        elif evt.unicode == u'\x12' and pygame.key.get_mods() & KMOD_CTRL:
            self.toggleHotbuttons('redir')
        # Ctrl+S - Toggle drawing scanners
        elif evt.unicode == u'\x13' and pygame.key.get_mods() & KMOD_CTRL:
            self.toggleHotbuttons('scanner')
        # Reserve CTRL-V,X,and Z for paste, cut, and undo (future editor support)
        # ==== Else ====
        else:
            # force update
            self.scale += 1
            self.scale -= 1
        return ui.NoEvent

    def setKeyObject(self,objIDs,bObjIDs):
        objID = self.gotoObject(objIDs,bObjIDs)
        log.debug('Setting Key Object To:',objID)
        self.app.setStatus(_("Ready."))
        self.selectobject = False
        if (objID == OID_NONE):
            return
        obj = client.get(objID)
        if obj.type in (T_SYSTEM, T_PLANET, T_FLEET):
            gdata.objectFocus[self.setKey]=objID

    def gotoKeyObject(self,evtkey):
        if evtkey in gdata.objectFocus:
            objID = gdata.objectFocus[evtkey]
            self.processAction(self.action, objID)
            self.pressedObjIDs = []

    def focusOnKeyObject(self,evtkey):
        if evtkey in gdata.objectFocus:
            objID = gdata.objectFocus[evtkey]
            obj = client.get(objID, noUpdate = 1)
            if hasattr(obj, "x"):
                gdata.mainGameDlg.win.vStarMap.highlightPos = (obj.x, obj.y)
                gdata.mainGameDlg.win.vStarMap.setPos(obj.x, obj.y)

    def onMouseOver(self):
        self.mouseOver = 1
        try:
            self.parent.parent.setFocus(self)
        except:
            log.debug('Cannot refocus on starmap')

    def setPos(self, x, y):
        self.currX = x
        self.currY = y
        self.repaintMap = 1
        self.processMiniMapRect()
        # disable auto position setting
        self.setPosition = 0

registerWidget(StarMapWidget, 'starmapwidget')

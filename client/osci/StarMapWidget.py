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
import bisect

from pygameui.Widget import Widget, registerWidget
import pygameui as ui
from pygameui import Fonts
import ige.ospace.Const as Const
import pygame, pygame.draw, pygame.key, pygame.image
from dialog.ShowBuoyDlg import ShowBuoyDlg
from dialog.KeyModHelp import KeyModHelp
import gdata, client, res
from ige import log
from osci.dialog.SearchDlg import SearchDlg
from osci.MiniMap import MiniMap
from osci.StarMap import StarMap


class StarMapWidget(Widget):

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent)
        self.searchDlg = SearchDlg(self.app)
        self.searchDlg.mapWidget = self
        # data
        self.control_modes = {}  # mutable, thus updating here will update StarMap
        self.updateConfigModes()
        self.control_modes['systems'] = 1
        self.control_modes['planets'] = 1
        self.control_modes['fleets'] = 1
        self.control_modes['civilian_fleets'] = 1
        self.control_modes['pirate_areas'] = 1
        self.control_modes['hotbuttons'] = 1
        self.control_modes['minimap'] = 1
        self.control_modes['redirects'] = 1
        self.control_modes['map_grid_coords'] = 1
        self.control_modes['map_grid'] = 1
        self.control_modes['scanners'] = 1
        self.control_modes['fleet_lines'] = 1
        self.control_modes['gate_systems'] = 1
        self.control_modes['alternative_view'] = 1
        self.control_modes['control_areas'] = 0
        self.control_modes['pirate_dialogs'] = 0  # only for pirate, obv.
        # more data
        self.highlightPos = None
        self.alwaysShowRangeFor = None
        self.activeObjID = Const.OID_NONE
        self.activeObjIDs = []
        self.pressedObjIDs = []
        self._newCurrXY = 0
        self.activePos = (0, 0)

        # the map itself!
        self.star_map = StarMap(self.control_modes)
        self.action = None
        self.callEventHandler = None
        self.showBuoyDlg = ShowBuoyDlg(self.app)
        self.KeyModHelp = KeyModHelp(self.app)
        self._miniMapRect = pygame.Rect(0, 20, 175, 175)
        self._hotbuttonsZone = pygame.Rect(0,0,0,0)
        self.initHotbuttons()
        self.miniMap = MiniMap(self._miniMapRect.width, self._miniMapRect.height)
        # flags
        self.processKWArguments(kwargs)
        parent.registerWidget(self)
        # popup menu
        self.popup = ui.Menu(self.app, title = _("Select object"))
        self.popup.subscribeAction("*", self)
        # overlay system
        self._overlayZone = False
        # key setting system
        self.selectobject = False
        self.setKey = False
        # commands
        self.keyPress = False
        # map - produced by StarMap draw method
        self._mapSurf = None
        self._actAreas = {}
        self._actBuoyAreas = {}
        # dirty flag
        self.repaint_map = True


    def updateConfigModes(self):
        self.control_modes['redirects'] = gdata.config.defaults.showredirects is not 'no'
        self.control_modes['coords'] = gdata.config.defaults.showcoords is not 'no'
        self.control_modes['map_grid'] = gdata.config.defaults.showmapgrid is not 'no'
        self.control_modes['scanners'] = gdata.config.defaults.showmapscanners is not 'no'
        self.control_modes['fleet_lines'] = gdata.config.defaults.showfleetlines is not 'no'
        self.control_modes['gate_systems'] = gdata.config.defaults.showgatesystems is not 'no'
        self.control_modes['alternative_mode'] = gdata.config.defaults.alternateviewmode is not 'no'
        self.control_modes['control_areas'] = gdata.config.defaults.showplayerzones is not 'no'
        self.control_modes['minimap'] = gdata.config.defaults.showminimap is not 'yes'

    def precompute(self):
        self.star_map.rect = self.rect
        self.star_map.precompute()
        player = client.getPlayer()
        if (player.type == Const.T_PIRPLAYER or\
            player.type == Const.T_AIPIRPLAYER) and not self.control_modes['pirate_dialogs']:
            self.control_modes['pirate_dialogs'] = True
            if self.control_modes['hotbuttons']:
                self.initHotbuttons() #reinit to add the pirate button
        self.miniMap.precompute()
        # self dirty flag
        self.repaint_map = 1

    def save(self, append='', chronicle_shot=False):
        name = ("%s.png" % append)
        if chronicle_shot:
            # print whole galaxy, centered over black hole
            # star_map has much more information about the galaxy, thus handling this request
            new_surf = self.star_map.chronicle_draw()
            pygame.image.save(new_surf, name)
        else:
            # print current player view
            new_surf, empty, empty = self.star_map.draw(pygame.Surface((self.star_map.rect.width,
                                                                        self.star_map.rect.height)))
            pygame.image.save(new_surf, name)
        return name


    def draw(self, surface):
        self._miniMapRect.left = self.rect.width - self._miniMapRect.width
        self._miniMapRect.top = self.rect.top
        if not self._mapSurf:
            mapSurf = pygame.Surface(self.rect.size, pygame.SWSURFACE, surface)
        else:
            mapSurf = self._mapSurf

        if self.repaint_map:
            mapSurf, self._actAreas, self._actBuoyAreas  = self.star_map.draw(mapSurf)
            # For some reason, this is not just optimization, it's mandatory for proper
            # function. BUG?!
            self.repaint_map = 0
            self.repaintHotbuttons = 1
        if self.repaintHotbuttons and self.control_modes['hotbuttons']:
            self.drawHotbuttons(mapSurf)
            self.repaintHotbuttons = 0
        # blit cached map
        surface.blit(mapSurf, self.rect)
        self._mapSurf = mapSurf

        if self.control_modes['minimap']:
            self.miniMap.draw(surface, self._miniMapRect.left, self._miniMapRect.top)
            if self.miniMap.needRect():
                self.processMiniMapRect()
                self.miniMap.draw(surface, self._miniMapRect.left, self._miniMapRect.top)
        # additional information (ranges, fleet lines, selected system sign)
        self.drawAdditions(surface)

        self.drawPopups(surface)
        return self.rect

    def drawHotbuttons(self, mapSurf):
        rect = mapSurf.get_rect()
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

        pygame.draw.rect(mapSurf,(0x00, 0x00, 0x90),(left-1,top-1,dx+2,dy+2))
        pygame.draw.rect(mapSurf,(0x33, 0x33, 0x66),(left,top,dx,dy))

        for buttonkey in self._hotbuttons:
            button = self._hotbuttons[buttonkey]
            self._hotbuttonRects[button[0]] = [button[0],pygame.Rect(button[2]+self._hotbuttonsZone.left,button[3]+self._hotbuttonsZone.top+15,button[4],button[5])]
            img = res.getButton(button[0],button[1])
            if (button[1] and not (self._tempOverlayHotbutton and self._tempOverlayHotbutton == button[0])) or (not button[1] and self._tempOverlayHotbutton and self._tempOverlayHotbutton == button[0]):
                pygame.draw.rect(mapSurf,(0x90, 0x90, 0x90),(left+button[2]-1,top+15+button[3]-1,button[4]+2,button[5]+2),1)
            mapSurf.blit(img,(left+button[2],top+15+button[3]))
        if self._tempOverlayHotbutton:
            text = self._hotbuttons[self._tempOverlayHotbutton][7]
            textSrfc = Fonts.renderText(self.star_map.textSize, text, 1, (0xEF, 0xEF, 0xEF))
            mapSurf.blit(textSrfc, (left+2,top+1))

    def drawPopups(self, surface):
        # draw popups
        moreIDs = len(self.activeObjIDs) > 1
        if not moreIDs:
            x, y = self.activePos
            x += 20
        else:
            x = self.rect.left + 2
            y = self.rect.top
        if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
            for activeObjID in self.activeObjIDs:
                index = 0
                if self.star_map._popupInfo.has_key(activeObjID):
                    # put pop up info on the screen
                    info = self.star_map._popupInfo[activeObjID]
                    # x1, y1 = self._actAreas[self.activeObjID].center
                    fg = self.theme.themeForeground #(0x30, 0xe0, 0x30, 0xff)
                    bg = self.theme.themeBackground #(0x20, 0x40, 0x20, 0x99)
                    width = 0
                    height = 0
                    # pygame.draw.line(surface, fg, (x1, y1), (x, y), 1)
                    for item in info:
                        w, h = Fonts.getTextSize('normal', item)
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
                        textSrfc = Fonts.renderText('normal', item, 1, fg)
                        surface.blit(textSrfc, (x, tmpY))
                        tmpY += textSrfc.get_height()
                    x += width + 2

    def _drawApproachingFleetLine(self, surface, activeObjID):
        maxY = self._mapSurf.get_rect().height
        centerX, centerY = self._mapSurf.get_rect().center
        x, y, x1, y1 = self.star_map._fleetTarget[activeObjID]
        sx = int((x - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
        sy = maxY - (int((y - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top
        dx = int((x1 - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
        dy = maxY - (int((y1 - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top
        pygame.draw.line(surface, (0xff, 0xff, 0x00), (sx, sy), (dx, dy), 2)

    def _drawThickeningFleetOrderLines(self, surface, activeObjID):
        maxY = self._mapSurf.get_rect().height
        centerX, centerY = self._mapSurf.get_rect().center
        for x, y, x1, y1, color in self.star_map._fordersTarget[activeObjID]:
            sx = int((x - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
            sy = maxY - (int((y - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top
            dx = int((x1 - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
            dy = maxY - (int((y1 - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top
            pygame.draw.line(surface, color, (sx, sy), (dx, dy), 2)

    def _drawFleetRangesTime(self, surface, activeObjID):
        maxY = self._mapSurf.get_rect().height
        centerX, centerY = self._mapSurf.get_rect().center
        x, y, maxRange, operRange, halfRange, speed, turns = self.star_map._fleetRanges[activeObjID]
        sx = int((x - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
        sy = maxY - (int((y - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top

        for i in xrange(1, turns / 6):
            rng = int(i * speed * self.star_map.scale)
            if rng > 1:
                pygame.draw.circle(surface, (0x70, 0x70, 0x80), (sx, sy), rng, 1)
                textSrfc = Fonts.renderText(self.star_map.textSize, res.formatTime(i * 6), 1, (0x70, 0x70, 0x80), (0x00, 0x00, 0x00))
                surface.blit(textSrfc, (sx - rng, sy - textSrfc.get_height() / 2))
                surface.blit(textSrfc, (sx + rng, sy - textSrfc.get_height() / 2))
                surface.blit(textSrfc, (sx - textSrfc.get_width() / 2, sy - rng))
                surface.blit(textSrfc, (sx - textSrfc.get_width() / 2, sy + rng - textSrfc.get_height()))
        rng = int(max(maxRange * self.star_map.scale, 0.2 * self.star_map.scale))
        if rng > 1:
            pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), rng, 1)

    def _drawFleetRangesFuel(self, surface, activeObjID):
        maxY = self._mapSurf.get_rect().height
        centerX, centerY = self._mapSurf.get_rect().center
        x, y, maxRange, operRange, halfRange, speed, turns = self.star_map._fleetRanges[activeObjID]
        sx = int((x - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
        sy = maxY - (int((y - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top

        # fleet range based on fuel
        rng = int(max(maxRange * self.star_map.scale, 0.2 * self.star_map.scale))
        if rng > 1:
            pygame.draw.circle(surface, (0xc0, 0x20, 0x20), (sx, sy), rng, 1)
        rng = int(operRange * self.star_map.scale)
        if rng > 1:
            pygame.draw.circle(surface, (0x20, 0x80, 0x20), (sx, sy), rng, 1)
        rng = int(halfRange * self.star_map.scale)
        if rng > 1:
            pygame.draw.circle(surface, (0x20, 0x20, 0x80), (sx, sy), rng, 1)

    def _drawFleetRanges(self, surface, activeObjID):
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self._drawFleetRangesTime(surface, activeObjID)
        else:
            self._drawFleetRangesFuel(surface, activeObjID)

    def drawAdditions(self, surface):
        oldClip = surface.get_clip()
        surface.set_clip(self.rect)
        centerX, centerY = self._mapSurf.get_rect().center
        maxY = self._mapSurf.get_rect().height
        # highlight position circle
        if self.highlightPos:
            sx = int((self.highlightPos[0] - self.star_map.currX) * self.star_map.scale) + centerX + self.rect.left
            sy = maxY - (int((self.highlightPos[1] - self.star_map.currY) * self.star_map.scale) + centerY) + self.rect.top
            pygame.draw.circle(surface, (0xff, 0xff, 0xff), (sx, sy), 13, 2)
        # fleet range in case of selecting fleet orders
        if self.alwaysShowRangeFor and self.star_map._fleetRanges.has_key(self.alwaysShowRangeFor):
            self._drawFleetRangesFuel(surface, self.alwaysShowRangeFor)
        for activeObjID in self.activeObjIDs:
            if activeObjID and activeObjID in self.star_map._fleetTarget:
                self._drawApproachingFleetLine(surface, activeObjID)
            if activeObjID and activeObjID in self.star_map._fordersTarget:
                self._drawThickeningFleetOrderLines(surface, activeObjID)
            if activeObjID and activeObjID in self.star_map._fleetRanges:
                self._drawFleetRanges(surface, activeObjID)
        # restore clipping
        surface.set_clip(oldClip)

    def initHotbuttons(self):
        # key : [ key , state , x , y , dx, dy, value, tooltip ]
        # 'value' is "active state' gdata value or true
        self._hotbuttons = {
            'pzone': ['pzone',self.control_modes['control_areas'],2,2,17,13, 1,_('Player Zones (CTRL-P)')],
            'civ': ['civ',self.control_modes['civilian_fleets'],21,2,18,13, 1,_('Civilian Ships (CTRL-H)')],
            'lines': ['lines',self.control_modes['fleet_lines'],41,2,18,13, 1,_('Fleet Lines (CTRL-L)')],
            'redir': ['redir',self.control_modes['redirects'],61,2,18,13, 1,_('Redirect Arrows (CTRL-R)')],
            'scanner': ['scanner',self.control_modes['scanners'],81,2,17,13, 1,_('Scanners (CTRL-S)')],
            'grid': ['grid',self.control_modes['map_grid'],100,2,17,13, 1,_('Grid (CTRL-G)')],
            'alternate': ['alternate',self.control_modes['alternative_mode'],119,2,17,13, 2,_('Alternate View (CTRL-A)')],
            'ov_diplo': ['ov_diplo',False,2,17,13,13, gdata.OVERLAY_DIPLO,_('Overlay: Diplomacy')],
            'ov_min': ['ov_min',False,17,17,13,13, gdata.OVERLAY_MIN,_('Overlay: Minerals')],
            'ov_env': ['ov_env',False,32,17,13,13, gdata.OVERLAY_BIO,_('Overlay: Environment')],
            'ov_slot': ['ov_slot',False,47,17,13,13, gdata.OVERLAY_SLOT,_('Overlay: Slots')],
            'ov_morale': ['ov_morale',False,62,17,13,13, gdata.OVERLAY_MORALE,_('Overlay: Morale')],
            'ov_fuel': ['ov_fuel',False,77,17,13,13, gdata.OVERLAY_DOCK,_('Overlay: Fuel and Repair')],
            'ov_gate': ['ov_gate',False,92,17,13,13, gdata.OVERLAY_STARGATE,_('Overlay: Star Gate Speed')],
            'ov_pirate': ['ov_pirate',False,107,17,13,13, gdata.OVERLAY_FAME,_('Overlay: Pirate Fame')],
        }
        if self.control_modes['pirate_dialogs']:
            self._hotbuttons['ov_piratecolony'] = ['ov_piratecolony',False,122,17,13,13, gdata.OVERLAY_PIRATECOLONYCOST,'Overlay: Pirate Colony Cost']
        self._oldOverlayHotbutton = False;
        self._tempOverlayHotbutton = False;
        self._hotbuttonRects = {}

    def toggleHotButtons(self, button):
        self.toggleTempButton(False)
        if (button[:3] == 'ov_'): #overlay
            if self._oldOverlayHotbutton == button:
                self.star_map.overlayMode = gdata.OVERLAY_OWNER
                self._hotbuttons[button][1] = False
                self._oldOverlayHotbutton = False
            else:
                if self._oldOverlayHotbutton:
                    self._hotbuttons[self._oldOverlayHotbutton][1] = False
                self._hotbuttons[button][1] = True
                self.star_map.overlayMode = self._hotbuttons[button][6]
                self._oldOverlayHotbutton = button
        else: #normal toggle
            if self._hotbuttons[button][1]:
                self._hotbuttons[button][1] = 0
            else:
                self._hotbuttons[button][1] = self._hotbuttons[button][6] # set standard value
            translation = {'pzone': 'control_areas',
                           'civ': 'civilian_fleets',
                           'lines': 'fleet_lines',
                           'redir': 'redirects',
                           'scanner': 'scanners',
                           'grid': 'map_grid',
                           'alternate': 'alternative_mode'}
            if button in translation:
                self.control_modes[translation[button]] = self._hotbuttons[button][1]
        self.repaintHotbuttons = 1
        self.repaint_map = 1

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
        if mods & pygame.KMOD_SHIFT:
            return self.processMB3Down(evt)
        pos = evt.pos
        # show current position for debugging
        # log.debug(pos)
        if self.control_modes['minimap']:
            if self._miniMapRect.collidepoint(pos):
                return ui.NoEvent
        if self.control_modes['hotbuttons'] and self._hotbuttonsZone.collidepoint(pos):
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
            self.activeObjID = Const.OID_NONE
            return ui.NoEvent

    def processMB1Up(self, evt):
        # handle SHIFT click as MB3
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_SHIFT:
            return self.processMB3Up(evt)
        pos = evt.pos
        if self.control_modes['minimap']:
            if self._miniMapRect.collidepoint(pos):
                self.star_map.currX, self.star_map.currY = self.miniMap.processMB1Up((pos[0] - self._miniMapRect.left, self._miniMapRect.height - pos[1] + self._miniMapRect.top))
                self.processMiniMapRect()
                self.repaint_map = 1
                return ui.NoEvent
        if self.control_modes['hotbuttons'] and self._hotbuttonsZone.collidepoint(pos):
            button = self.detectButtonOverpass(pos)
            if button:
                self.toggleHotButtons(button)
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
            self.activeObjID = Const.OID_NONE
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
                    return Const.OID_NONE
                self.showBuoyDlg.display(bObjIDs[0])
                self.pressedBuoyObjIDs = []
        else:
            # multiple objects -> post pop-up menu
            items = []
            for objID in objIDs:
                obj = client.get(objID)
                if obj.type == Const.T_SYSTEM:
                    name = getattr(obj, "name", None)
                    name = _("System: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == Const.T_WORMHOLE:
                    name = getattr(obj, "name", None)
                    name = _("Worm hole: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == Const.T_PLANET:
                    name = getattr(obj, "name", None)
                    name = _("Planet: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == Const.T_FLEET:
                    if hasattr(obj,'customname') and obj.customname:
                        name = obj.customname
                    else:
                        name = getattr(obj, "name", None)
                    name = _("Fleet: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                else:
                    name = _("Unknown object [ID: %d]") % obj.oid
                item = ui.Item(name, action = "onObjectSelected", data = objID)
                items.append(item)
            for objID in bObjIDs:
                obj = client.get(objID)
                if obj.type == Const.T_SYSTEM:
                    name = getattr(obj, "name", None)
                    name = _("Buoy on system: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                elif obj.type == Const.T_WORMHOLE:
                    name = getattr(obj, "name", None)
                    name = _("Buoy on worm hole: %s [ID: %d]") % (name or res.getUnknownName(), obj.oid)
                else:
                    name = _("Buoy on unknown object [ID: %d]") % obj.oid
                item = ui.Item(name, action = "onBuoySelected", data = objID)
                items.append(item)
            self.popup.items = items
            self.popup.show()
        if self.selectobject:
            return Const.OID_NONE

    def onObjectSelected(self, widget, action, data):
        self.processAction(self.action, data)

    def onBuoySelected(self, widget, action, data):
        self.showBuoyDlg.display(data)

    def processMB3Down(self, evt):
        if self.control_modes['minimap']:
            if self._miniMapRect.collidepoint(evt.pos):
                return ui.NoEvent
        self._newCurrXY = 1
        return ui.NoEvent

    def processMB3Up(self, evt):
        if self._newCurrXY:
            x, y = evt.pos
            centerX, centerY = self._mapSurf.get_rect().center
            self.star_map.currX -= float(centerX - x) / self.star_map.scale
            self.star_map.currY += float(centerY - y) / self.star_map.scale
            self.processMiniMapRect()
            self.repaint_map = 1
            self._newCurrXY = 0
        return ui.NoEvent

    def processMiniMapRect(self):
        if self.control_modes['minimap']:
            rect = self._mapSurf.get_rect()
            self.miniMap.moveRect(self.star_map.currX, self.star_map.currY, rect.width / self.star_map.scale, rect.height / self.star_map.scale)

    def _rescaleMap(self, evt, delta):
        if not 10 < self.star_map.scale + delta < 80:
            return ui.NoEvent
        try:
            x, y = evt.pos
        except AttributeError:
            # keyboard rescale
            x, y = pygame.mouse.get_pos()
        centerX, centerY = self._mapSurf.get_rect().center
        sign = cmp(delta, 0)
        self.star_map.currX -= sign * float(centerX - x) * (1 / self.star_map.scale - 1 / (self.star_map.scale + delta))
        self.star_map.currY += sign * float(centerY - y) * (1 / self.star_map.scale - 1 / (self.star_map.scale + delta))
        self.star_map.scale += delta
        self.star_map.textSize = ['small', 'normal', 'large'][bisect.bisect([40, 60], self.star_map.scale)]
        self.repaint_map = 1
        self.processMiniMapRect()

    def processMWUp(self, evt):
        return self._rescaleMap(evt, 5)

    def processMWDown(self, evt):
        return self._rescaleMap(evt, -5)

    def processMMotion(self, evt):
        pos = evt.pos
        if self.control_modes['minimap']:
            if self._miniMapRect.collidepoint(pos):
                #log.debug('Minimap Rect Position');
                return ui.NoEvent
        if self.control_modes['hotbuttons'] and self._hotbuttonsZone.collidepoint(pos):
            #should give hotkey tooltips for this eventually
            self.toggleTempButton(pos)
            return ui.NoEvent
        elif self._tempOverlayHotbutton: # cleanup if cursor not in zone
            self.toggleTempButton(False)
        self.activeObjID = Const.OID_NONE
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

    def _processObjectHotkeys(self, evt):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            log.debug('Set Key:', evt.key)
            if gdata.config.defaults.displayhelp != 'no':
                self.KeyModHelp.show()
            self.selectobject = True
            self.setKey = evt.key
            self.app.setStatus(_("Select object to hotkey. ESC to cancel."))
        elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
            log.debug('Focus Key:', evt.key)
            self.focusOnKeyObject(evt.key)
        else:
            log.debug('Goto Key:', evt.key)
            self.gotoKeyObject(evt.key)
        return ui.NoEvent

    def processKeyUp(self, evt2):
        if self.callEventHandler:
            self.callEventHandler.processKeyUp(evt2)
        evt = self.keyPress
        if not self.keyPress: return ui.NoEvent
        self.keyPress = False
        # ==== Object Hotkeys ====
        #I have not found unicode escape characters for Ctrl-0 through Ctrl-9, so using direct key reference (less preferred due to international keyboards)
        if evt.key in [49,50,51,52,53,54,55,56,57,48]:
            self._processObjectHotkeys(evt)
        # ==== Map and Dialog Hotkeys ====
        elif evt.key == pygame.K_ESCAPE and self.selectobject:
            log.debug('Canceled Key')
            if self.selectobject:
                self.app.setStatus(_("Ready."))
                self.selectobject = False
            return ui.NoEvent
        if not evt.unicode:
            # force update
            self.star_map.scale += 1
            self.star_map.scale -= 1
            return ui.NoEvent
        if evt.unicode in u'+=':
            self._rescaleMap(evt, 5)
        elif evt.unicode == u'-':
            self._rescaleMap(evt, -5)
        # Space Bar - Recenter
        elif evt.unicode == u' ':
            x, y = pygame.mouse.get_pos()
            centerX, centerY = self._mapSurf.get_rect().center
            self.star_map.currX -= float(centerX - x) / self.star_map.scale
            self.star_map.currY += float(centerY - y) / self.star_map.scale
            self.repaint_map = 1
            self._newCurrXY = 0
        # ==== Standard Hotkeys ====
        # Reserve CTRL-C for copy (future editor support)
        # Ctrl+F
        toggleMapping = {u'\x01': 'alternate',  # Alternative system info
                         u'\x07': 'grid',       # Grid
                         u'\x08': 'civ',        # Civilian ships
                         u'\x0C': 'lines',      # Fleet lines
                         u'\x10': 'pzone',      # Control areas
                         u'\x12': 'redir',      # Redirections
                         u'\x13': 'scanner'}    # Scanner circles
        if evt.unicode in toggleMapping and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.toggleHotButtons(toggleMapping[evt.unicode])
        # Ctrl+F to open the search (find) dialog
        elif evt.unicode == u'\x06' and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.searchDlg.display()
        # Reserve CTRL-V,X,and Z for paste, cut, and undo (future editor support)
        # ==== Else ====
        else:
            # force update
            self.star_map.scale += 1
            self.star_map.scale -= 1
        return ui.NoEvent

    def setKeyObject(self,objIDs,bObjIDs):
        objID = self.gotoObject(objIDs,bObjIDs)
        log.debug('Setting Key Object To:',objID)
        self.app.setStatus(_("Ready."))
        self.selectobject = False
        if (objID == Const.OID_NONE):
            return
        obj = client.get(objID)
        if obj.type in (Const.T_SYSTEM, Const.T_PLANET, Const.T_FLEET):
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
        self.star_map.currX = x
        self.star_map.currY = y
        self.repaint_map = 1
        self.processMiniMapRect()


registerWidget(StarMapWidget, 'starmapwidget')

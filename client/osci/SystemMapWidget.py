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
from pygameui import Fonts
import ige.ospace.Const as Const
import pygame, pygame.draw
import gdata, res, client
from ige import log

# number of planet's images
typeImgs = {'A': 2, 'C': 1, 'D': 5, 'E': 2, 'G': 5, 'H': 2, 'M': 1, 'R': 4, 'X': 1, 'I': 2}

buoyColors = [(0xff, 0xff, 0x00), (0x00, 0xff, 0xff), (0xff, 0x00, 0xff), (0xb0, 0xb0, 0xff)]
MAX_BOUY_DISPLAY_LEN = 30
MAX_BOUY_DISPLAY_ROWS = 3

class SystemMapWidget(Widget):

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent)
        # data
        self.action = None
        self.hoverAction = None
        # map
        self.pressedObjID = Const.OID_NONE
        self._actAreas = {}
        self._starImg = None
        self._planetImgs = []
        self.ObjID = Const.OID_NONE
        self.activeObjID = Const.OID_NONE
        self.selectedObjID = Const.OID_NONE
        self.systemID = Const.OID_NONE
        self.unknown_mines = 0
        self.my_mines = 0
        self.buoytext = None
        # flags
        self.processKWArguments(kwargs)
        parent.registerWidget(self)

    def precompute(self):
        system = client.get(self.systemID, noUpdate = 1)
        self.unknown_mines = 0
        self.my_mines = 0
        if hasattr(system, 'hasmines'):
            if getattr(system, 'minefield', []):
                if len(system.minefield) > 0:
                    self.my_mines = 1
                if system.hasmines == 2:
                    self.unknown_mines = 1
            elif system.hasmines > 0:
                self.unknown_mines = 1
        self.computeBuoy()
        self._starImg = None
        if hasattr(system, 'starClass'):
            self._starImg = res.getBigStarImg(system.starClass[1])
        self._planetImgs = []
        if hasattr(system, 'planets'):
            for planetID in system.planets:
                planet = client.get(planetID, noUpdate = 1)
                if not planet:
                    continue
                # image
                plType = getattr(planet, 'plType', 'X')
                img = res.getPlanetImg(plType, planet.oid + system.oid)
                #if plType != 'G':
                #    ratio = planet.plDiameter / 19000.0
                #else:
                #    ratio = planet.plDiameter / 180000.0
                #img2 = pygame.transform.scale(img, (int(ratio * img.get_width()), int(ratio * img.get_height())))
                name = getattr(planet, 'name', res.getUnknownName()).split(' ')[-1]
                #rel = Const.REL_UNDEF
                if hasattr(planet, 'owner'):
                    ownerID = planet.owner
                else:
                    ownerID = Const.OID_NONE
                self._planetImgs.append((planetID, img, name, res.getPlayerColor(ownerID)))

    def computeBuoy(self):
        player = client.getPlayer()
        if hasattr(player, "buoys") and self.systemID in player.buoys:
            self.buoytext = player.buoys[self.systemID]
        else:
            self.buoytext = None

    def draw(self, surface):
        player = client.getPlayer()
        self._actAreas = {}
        # background
        surface.fill((0x00, 0x00, 0x00), self.rect)
        # common positions
        y = self.rect.centery
        x = self.rect.left
        r = self.rect.right
        height = self.rect.height
        if self._starImg:
            x += self._starImg.get_width()
        # mines
        if self.my_mines:
            if self.unknown_mines:
                textSrfc = Fonts.renderText('small', 'Minefield', 1, res.getFFColorCode(1250))
                surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()))
                textSrfc = Fonts.renderText('small', 'Unknown Minefield Detected', 1, res.getFFColorCode(0))
                surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()*2 + 5))
            else:
                textSrfc = Fonts.renderText('small', 'Minefield', 1, res.getFFColorCode(1250))
                surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()))
        elif self.unknown_mines:
            textSrfc = Fonts.renderText('small', 'Unknown Minefield Detected', 1, res.getFFColorCode(0))
            surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()))
        # buoy
        if self.buoytext:
            lines = self.buoytext[0].split("\n")
            maxW = 0
            hh = 0
            i = 1
            textSrfcs = []
            bouycolor = buoyColors[self.buoytext[1] - 1]
            for line in lines:
                if len(line) == 0:
                    break
                if len(line) > MAX_BOUY_DISPLAY_LEN:
                    line = u"%s..." % line[:MAX_BOUY_DISPLAY_LEN]
                elif i == MAX_BOUY_DISPLAY_ROWS:
                    line = u"%s..." % line
                textSrfc = Fonts.renderText('small', line, 1, bouycolor)
                textSrfcs.append(textSrfc)
                maxW = max(textSrfc.get_width(), maxW)
                i += 1
                if i > MAX_BOUY_DISPLAY_ROWS: break
            for textSrfc in textSrfcs:
                hh += textSrfc.get_height()
                surface.blit(textSrfc, (r - maxW - 20, 5 + hh))
        # star
        if self._starImg:
            surface.blit(self._starImg, self.rect.topleft)
            self._actAreas[self.systemID] = pygame.Rect(self.rect.topleft, self._starImg.get_size())
        # planets
        for planetID, img, name, ffColor in self._planetImgs:
            planet = client.get(planetID, noUpdate = 1)
            py = y - img.get_height() / 2
            surface.blit(img, (x, py))
            self._actAreas[planetID] = pygame.Rect((x, py), img.get_size())
            text = pygame.transform.rotate(Fonts.renderText('small', ' %s' % name, 1, ffColor), 90)
            py = height - text.get_height()
            px = x + img.get_width() / 2 - text.get_width() / 2
            nameWidth = text.get_width()
            surface.blit(text, (px, py))
            if getattr(planet, 'owner', Const.OID_NONE) == player.oid:
                text = pygame.transform.rotate(Fonts.renderText('small', ' (%d)' % self.getFreeSlots(planetID), 1, ffColor), 90)
                py = height - text.get_height()
                px = x + img.get_width() / 2 - text.get_width() / 2 + nameWidth
                surface.blit(text, (px, py))
            if planetID in [self.activeObjID, self.selectedObjID]:
                if planetID == self.selectedObjID: style = 0
                elif planetID == self.activeObjID: style = 2
                gx, gy = self.theme.getGridParams()
                gx = gx / 2
                gy = gy / 2
                rect = pygame.Rect((x + img.get_width() / 2 - gx / 2, y + img.get_height() / 2), (gx, gy))
                pygame.draw.polygon(surface, self.theme.themeForeground,
                    (rect.bottomleft, rect.midtop, rect.bottomright), style)
                rect = pygame.Rect((x + img.get_width() / 2 - gx / 2, y - img.get_height() / 2 - gy), (gx, gy))
                pygame.draw.polygon(surface, self.theme.themeForeground,
                    (rect.topleft, rect.midbottom, rect.topright), style)
            x += int(img.get_width() * 1.25) + 10

    def getFreeSlots(self, planetID):
        planet = client.get(planetID, noUpdate = 1)
        system = client.get(self.systemID, noUpdate = 1)
        player = client.getPlayer()
        owner = getattr(planet, 'owner', Const.OID_NONE)
        freeSlots = 0
        if owner == player.oid and hasattr(planet, 'slots') and hasattr(planet, 'plSlots'):
            freeSlots = planet.plSlots - len(planet.slots)
        if hasattr(system, 'planets'):
            for sPlanetID in system.planets:
                sPlanet = client.get(sPlanetID, noUpdate = 1)
                if hasattr(sPlanet, 'prodQueue'):
                    for task in sPlanet.prodQueue:
                        # Target Slot does not changes number of free slots
                        if not task.isShip and hasattr(task, "demolishStruct") and task.demolishStruct == 0 and task.targetID == planetID:
                            tech = client.getFullTechInfo(task.techID)
                            # constructing Habitable Surface Expansion increases planet slots
                            if tech.isProject and tech.id == 3802:
                                freeSlots += task.quantity
                            elif tech.isStructure:
                                freeSlots -= task.quantity

        return freeSlots

    def onMouseOut(self):
        # this is used when cursor moves directly from sun field out of widget
        if self.selectedObjID:
            self.processAction(self.action, self.selectedObjID)
        return Widget.onMouseOut(self)

    def processMMotion(self, evt):
        pos = evt.pos
        for objID in self._actAreas.keys():
            rect = self._actAreas[objID]
            if rect.collidepoint(pos) and self.action:
                self.processAction(self.hoverAction, objID)
                return ui.NoEvent
        if self.selectedObjID:
            self.processAction(self.action, self.selectedObjID)
        return ui.NoEvent

    def processMB1Down(self, evt):
        pos = evt.pos
        for objID in self._actAreas.keys():
            rect = self._actAreas[objID]
            if rect.collidepoint(pos):
                self.pressedObjID = objID
                return ui.NoEvent
        return ui.NoEvent

    def processMB1Up(self, evt):
        pos = evt.pos
        for objID in self._actAreas.keys():
            rect = self._actAreas[objID]
            if rect.collidepoint(pos):
                if self.pressedObjID == objID and self.action:
                    self.pressedObjID = Const.OID_NONE
                    self.processAction(self.action, objID)
                return ui.NoEvent
        if self.selectedObjID:
            self.processAction(self.action, self.selectedObjID)
        return ui.NoEvent

registerWidget(SystemMapWidget, 'systemmapwidget')

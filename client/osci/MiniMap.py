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
import ige.ospace.Const as Const
import pygame, pygame.draw
from ige import log
import res, client

borderColor = (0x00, 0x00, 0x90)
rectColor = (29, 118, 229)
#rect2Color = (0xFF, 0xFF, 0xFF)
rect2Color = (0x00, 0x00, 0x00)

class MiniMap:
    def __init__(self, width, height):
        self._map = []
        self._repaintMap = True
        self._repaintRect = False
        self._mapSurf = None
        self._mapSurfCache = None
        self._scaleX = 0.0
        self._scaleY = 0.0
        self._minX = 0
        self._minY = 0
        self._shiftX = 0
        self._shiftY = 0
        self._width = width
        self._height = height
        self._rectRect = (0, 0, 0, 0)
        self._rectRect2 = (0, 0, 0, 0)
        self._rectRect3 = (0, 0, 0, 0)
        self._noRect = True

    def precompute(self):
        galaxy_id = client.getPlayer().galaxy
        galaxy = client.get(galaxy_id, noUpdate = 1)
        minX, maxX = galaxy.x - galaxy.radius, galaxy.x + galaxy.radius
        minY, maxY = galaxy.y - galaxy.radius, galaxy.y + galaxy.radius
        for objID in client.db.keys():
            if objID < Const.OID_FREESTART:
                continue
            obj = client.get(objID, noUpdate = 1)
            if not (hasattr(obj, "type")):
                continue
            if obj.type in (Const.T_SYSTEM,Const.T_WORMHOLE):
                ownerID = Const.OID_NONE
                if hasattr(obj, 'planets'):
                    for planetID in obj.planets:
                        planet = client.get(planetID, noUpdate = 1)
                        owner = getattr(planet, 'owner', Const.OID_NONE)
                        if int(owner) != 0:
                            ownerID = owner
                            break
                color = res.getPlayerColor(ownerID)
                self._map.append((obj.oid, obj.x, obj.y, color))

        self._minX = minX
        self._minY = minY
        zoomFactor = 0.05 #percent
        self._shiftX = int(self._width * zoomFactor)
        self._shiftY = int(self._height * zoomFactor)
        if ((maxX - minX) == 0) :
            self._scaleX = 1
        else :
            self._scaleX = float(self._width - 2 * self._shiftX) / float(maxX - minX)
        if ((maxY - minY) == 0) :
            self._scaleY = 1
        else :
            self._scaleY = float(self._height - 2 * self._shiftX) / float(maxY - minY)

        self._repaintMap = True

    def preDraw(self, surface):
        if not self._mapSurf:
            self._mapSurf = pygame.Surface((self._width, self._height), pygame.SWSURFACE | pygame.SRCALPHA, surface)
            self._repaintMap = 1
        # redraw map
        self._mapSurf.fill((0x00, 0x00, 0x00))
        maxY = self._mapSurf.get_rect().height
        #reset drawn map
        for systemID, x, y, color in self._map:
            sx = int((x - self._minX) * self._scaleX) + self._shiftX
            sy = maxY - int((y - self._minY) * self._scaleY) - self._shiftY
            #save drawn map for rectangle moves when recompute of positions isn't needed
            pygame.draw.circle(self._mapSurf, color, (sx, sy), 2)
        maxY = self._mapSurf.get_rect().height
        pygame.draw.rect(self._mapSurf, borderColor, (0, 0, self._width, self._height), 1)
        #cache for rectRect movement
        self._mapSurfCache = self._mapSurf.copy()

    def draw(self, surface, startX, startY):
        if self._repaintMap: #repaint whole map
            self.preDraw(surface)
        elif self._repaintRect: #when not repainting whole map, pull cached version
            self._mapSurf = self._mapSurfCache.copy()
        # draw view area
        if (self._rectRect[3] != 0):
            self._noRect = False
        pygame.draw.rect(self._mapSurf, rectColor, self._rectRect, 1)
        pygame.draw.rect(self._mapSurf, rect2Color, self._rectRect2, 1)
        pygame.draw.rect(self._mapSurf, rect2Color, self._rectRect3, 1)
        # clean up flags
        self._repaintMap = False
        self._repaintRect = False
        # blit map
        rect = pygame.Rect(startX, startY, self._width, self._height)
        surface.blit(self._mapSurf, rect)
        return rect

    def needRect(self):
        return self._noRect

    def moveRect(self, centerX, centerY, width, height):
        maxX, maxY = self._mapSurf.get_rect().size
        sx = int((centerX - self._minX) * self._scaleX) + self._shiftX
        sy = maxY - int((centerY - self._minY) * self._scaleY) - self._shiftY
        w = max(int(width * self._scaleX),2)
        h = max(int(height * self._scaleY),2)
        self._rectRect = (sx - w / 2, sy - h / 2, w, h)
        self._rectRect2 = (sx - w / 2 - 1, sy - h / 2 - 1, w+2, h+2)
        self._rectRect3 = (sx - w / 2 + 1, sy - h / 2 + 1, w-2, h-2)
        self._repaintRect = True

    def processMB1Up(self, pos):
        return (((pos[0] - self._shiftX) / self._scaleX) + self._minX, ((pos[1] - self._shiftY) / self._scaleY) + self._minY)

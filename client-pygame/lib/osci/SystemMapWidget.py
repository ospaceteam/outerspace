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

from pygameui.Widget import Widget, registerWidget
import pygameui as ui
from pygameui.Fonts import *
from ige.ospace.Const import *
import pygame, pygame.draw
from pygame.locals import *
import gdata, res, client
from ige import log

# number of planet's images
typeImgs = {'A': 2, 'C': 1, 'D': 5, 'E': 2, 'G': 5, 'H': 2, 'M': 1, 'R': 4, 'X': 1, 'I': 2}

class SystemMapWidget(Widget):

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		# data
		self.action = None
		# map
		self.pressedObjID = OID_NONE
		self._actAreas = {}
		self._starImg = None
		self._planetImgs = []
		self.selectedObjID = OID_NONE
		self.systemID = OID_NONE
		self.unknown_mines = 0
		self.my_mines = 0
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)

	def precompute(self):
		system = client.get(self.systemID, noUpdate = 1)
		self.unknown_mines = 0
		self.my_mines = 0
		if hasattr(system, 'hasmines'):
			if hasattr(system, 'minefield'):
				if len(system.minefield) > 0:
					self.my_mines = 1
				if system.hasmines == 2:
					self.unknown_mines = 1
			elif system.hasmines > 0:
				self.unknown_mines = 1
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
				#	ratio = planet.plDiameter / 19000.0
				#else:
				#	ratio = planet.plDiameter / 180000.0
				#img2 = pygame.transform.scale(img, (int(ratio * img.get_width()), int(ratio * img.get_height())))
				name = getattr(planet, 'name', res.getUnknownName()).split(' ')[-1]
				#rel = REL_UNDEF
				if hasattr(planet, 'owner'):
					ownerID = planet.owner
				else:
					ownerID = OID_NONE
				self._planetImgs.append((planetID, img, name, res.getPlayerColor(ownerID)))

	def draw(self, surface):
		player = client.getPlayer()
		self._actAreas = {}
		# background
		surface.fill((0x00, 0x00, 0x00), self.rect)
		# common positions
		y = self.rect.centery
		x = self.rect.left
		height = self.rect.height
		if self._starImg:
			x += self._starImg.get_width()
		# mines
		if self.my_mines:
			if self.unknown_mines:
				textSrfc = renderText('small', 'Minefield', 1, res.getFFColorCode(1250))
				surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()))
				textSrfc = renderText('small', 'Unknown Minefield Detected', 1, res.getFFColorCode(0))
				surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()*2 + 5))
			else:
				textSrfc = renderText('small', 'Minefield', 1, res.getFFColorCode(1250))
				surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()))
		elif self.unknown_mines:
			textSrfc = renderText('small', 'Unknown Minefield Detected', 1, res.getFFColorCode(0))
			surface.blit(textSrfc, (x, self.rect.top + textSrfc.get_height()))
		# star
		if self._starImg:
			surface.blit(self._starImg, self.rect.topleft)
			self._actAreas[self.systemID] = Rect(self.rect.topleft, self._starImg.get_size())
		# planets
		for planetID, img, name, ffColor in self._planetImgs:
			planet = client.get(planetID, noUpdate = 1)
			py = y - img.get_height() / 2
			surface.blit(img, (x, py))
			self._actAreas[planetID] = Rect((x, py), img.get_size())
			text = pygame.transform.rotate(renderText('small', ' %s' % name, 1, ffColor), 90)
			py = height - text.get_height()
			px = x + img.get_width() / 2 - text.get_width() / 2
			nameWidth = text.get_width()
			surface.blit(text, (px, py))
			if getattr(planet, 'owner', OID_NONE) == player.oid:
				text = pygame.transform.rotate(renderText('small', ' (%d)' % self.getFreeSlots(planetID), 1, ffColor), 90)
				py = height - text.get_height()
				px = x + img.get_width() / 2 - text.get_width() / 2 + nameWidth
				surface.blit(text, (px, py))
			if planetID == self.selectedObjID:
				gx, gy = self.theme.getGridParams()
				gx = gx / 2
				gy = gy / 2
				rect = Rect((x + img.get_width() / 2 - gx / 2, y + img.get_height() / 2), (gx, gy))
				pygame.draw.polygon(surface, self.theme.themeForeground,
					(rect.bottomleft, rect.midtop, rect.bottomright), 0)
				rect = Rect((x + img.get_width() / 2 - gx / 2, y - img.get_height() / 2 - gy), (gx, gy))
				pygame.draw.polygon(surface, self.theme.themeForeground,
					(rect.topleft, rect.midbottom, rect.topright), 0)
			x += int(img.get_width() * 1.25) + 10

	def getFreeSlots(self, planetID):
		planet = client.get(planetID, noUpdate = 1)
		system = client.get(self.systemID, noUpdate = 1)
		player = client.getPlayer()
		owner = getattr(planet, 'owner', OID_NONE)
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

	def processMB1Down(self, evt):
		pos = evt.pos
		for objID in self._actAreas.keys():
			rect = self._actAreas[objID]
			if rect.collidepoint(pos):
				self.pressedObjID = objID
				return ui.NoEvent
		self.activeObjID = OID_NONE
		return ui.NoEvent

	def processMB1Up(self, evt):
		pos = evt.pos
		for objID in self._actAreas.keys():
			rect = self._actAreas[objID]
			if rect.collidepoint(pos):
				if self.pressedObjID == objID and self.action:
					self.processAction(self.action, objID)
				self.pressedObjID = OID_NONE
				self.selectedObjID = objID
				return ui.NoEvent
		self.activeObjID = OID_NONE
		return ui.NoEvent

registerWidget(SystemMapWidget, 'systemmapwidget')

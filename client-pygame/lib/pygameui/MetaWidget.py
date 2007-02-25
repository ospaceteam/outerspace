#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Pygame.UI.
#
#  Pygame.UI is free software; you can redistribute it and/or modify
#  it under the terms of the Lesser GNU General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
#  Pygame.UI is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  Lesser GNU General Public License for more details.
#
#  You should have received a copy of the Lesser GNU General Public License
#  along with Pygame.UI; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygame.event
from pygame.locals import *
from Const import *
from Widget import Widget

class MetaWidget(Widget):

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		self.__dict__['metaType'] = TYPE_METAWIDGET
		self.__dict__['_widgetArea'] = None
		self.__dict__['_widgetSurface'] = None
		self.__dict__['redrawMyself'] = 1
		self.__dict__['redrawWidgets'] = {}
		self.__dict__['_oldWidgetArea'] = Rect(0, 0, 0, 0)
		self.__dict__['widgets'] = []
		self.__dict__['widgetMap'] = {}
		self.__dict__['layoutManager'] = None
		self.__dict__['statusBar'] = None
		self.__dict__['statusBarText'] = None
		self.processKWArguments(kwargs)

	def registerWidget(self, widget):
		if widget not in self.widgets:
			self.widgets.append(widget)
		if widget.id:
			self.widgetMap[widget.id] = widget

	def setTagAttr(self, tagName, attrName, value):
		for widget in self.widgets:
			if tagName in widget.tags:
				setattr(widget, attrName, value)

	def getWidgetsByTag(self, tagName):
		result = []
		for widget in self.widgets:
			if tagName in widget.tags:
				result.append(widget)
		return result

	def setStatus(self, text):
		self.statusBarText = text
		if self.statusBar:
			self.statusBar.text = text
			self.app.update()
		else:
			self.parent.setStatus(text)

	def setTempStatus(self, text):
		if self.statusBar:
			if text:
				self.statusBar.text = text
			else:
				self.statusBar.text = self.statusBarText
		else:
			self.parent.setTempStatus(text)

	def __getattr__(self, name):
		# no __*__ methods
		if name[:2] == '__':
			raise AttributeError(name)
		# access widgets
		value = self.__dict__['widgetMap'].get(name, NoValue)
		if value != NoValue:
			return value
		else:
			raise AttributeError(name)

	def layoutWidgets(self):
		if self.layoutManager:
			self.layoutManager.metaWidget = self
			self.layoutManager.layoutWidgets()

	def redraw(self, widget, redrawParent = 0):
		if widget.visible:
			self.redrawWidgets[widget] = None
		elif self.redrawWidgets.has_key(widget):
			del self.redrawWidgets[widget]
		if not self._changeReported:
			self.parent.redraw(self)
			self.__dict__['_changeReported'] = 1
		if redrawParent:
			self.__dict__['redrawMyself'] = 1

	def drawMetaWidget(self, surface):
		return Rect(self.rect)

	def draw(self, surface):
		changed = None
		if self.visible and self.redrawMyself or not self._widgetArea:
			self._widgetArea = self.drawMetaWidget(surface)
			self._widgetArea = self._widgetArea.clip((0,0), surface.get_size())
			if self._widgetArea.width == 0:
				# area is invisible
				return
			self._widgetSurface = pygame.Surface(self._widgetArea.size)
			self._widgetSurface.blit(surface, (0,0), self._widgetArea)
			# force to redraw all widgets
			#@print self.__class__, 'FORCE REDRAW'
			for widget in self.widgets:
				if widget.visible:
					self.redrawWidgets[widget] = None
					if widget.metaType == TYPE_METAWIDGET:
						widget.__dict__['redrawMyself'] = 1
			self.__dict__['redrawMyself'] = 0
			changed = Rect(self._widgetSurface.get_rect())
		if self._widgetArea and self._widgetArea.size != self._oldWidgetArea.size:
			#@print self.__class__, 'LAYING OUT WIDGETS'
			self.layoutWidgets()
			self._oldWidgetArea = Rect(self._widgetArea)
		if self._widgetSurface and self.visible and self.redrawWidgets:
			for widget in self.redrawWidgets:
				assert widget.visible == 1
				#@print 'Draw', widget,
				rect = widget.draw(self._widgetSurface)
				#@print "X", rect
				if changed and rect: changed.union_ip(rect)
				elif rect : changed = Rect(rect)
				widget.__dict__['_changeReported'] = 0
			self.__dict__['redrawWidgets'] = {}
			if changed:
				surface.blit(self._widgetSurface, changed.move(self._widgetArea.topleft), changed)
				changed.move_ip(self._widgetArea.topleft)
			#@print "Changed", changed
			return changed

	def transpose(self, pos):
		if not self._widgetArea:
			# TODO fix this, should be assert self._widgetArea
			return (-1, -1)
		return (pos[0] - self._widgetArea.left,
				pos[1] - self._widgetArea.top)

	def processMB1Down(self, evt):
		evt = pygame.event.Event(MOUSEBUTTONDOWN, pos = self.transpose(evt.pos), button = evt.button)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				if widget.metaType == TYPE_WIDGET:
					self.app.setFocus(widget)
				return widget.processMB1Down(evt)
		self.app.setFocus(None)
		return NoEvent

	def processMB1Up(self, evt):
		evt = pygame.event.Event(MOUSEBUTTONUP, pos = self.transpose(evt.pos), button = evt.button)
		widget = self.app.focusedWidget
		if widget and widget.enabled and widget.visible:
			widget.processMB1UpMissed(evt)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				return widget.processMB1Up(evt)
		return NoEvent

	def processMB3Down(self, evt):
		evt = pygame.event.Event(MOUSEBUTTONDOWN, pos = self.transpose(evt.pos), button = evt.button)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				if widget.metaType == TYPE_WIDGET:
					self.app.setFocus(widget)
				return widget.processMB3Down(evt)
		self.app.setFocus(None)
		return NoEvent

	def processMB3Up(self, evt):
		evt = pygame.event.Event(MOUSEBUTTONUP, pos = self.transpose(evt.pos), button = evt.button)
		widget = self.app.focusedWidget
		if widget and widget.enabled and widget.visible:
			widget.processMB3UpMissed(evt)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				return widget.processMB3Up(evt)
		return NoEvent

	def processMMotion(self, evt):
		evt = pygame.event.Event(MOUSEMOTION, pos = self.transpose(evt.pos), rel = evt.rel, buttons = evt.buttons)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				if widget.metaType == TYPE_WIDGET:
					self.app.setMouseOver(widget)
				return widget.processMMotion(evt)
		self.app.setMouseOver(None)
		return NoEvent

	def processMWUp(self, evt):
		evt = pygame.event.Event(MOUSEBUTTONDOWN, pos = self.transpose(evt.pos), button = evt.button)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				return widget.processMWUp(evt)
		self.app.setFocus(None)
		return NoEvent

	def processMWDown(self, evt):
		evt = pygame.event.Event(MOUSEBUTTONDOWN, pos = self.transpose(evt.pos), button = evt.button)
		for widget in self.widgets:
			if widget.rect.collidepoint(evt.pos) and widget.enabled and widget.visible:
				return widget.processMWDown(evt)
		self.app.setFocus(None)
		return NoEvent

	def onMouseOver(self):
		pass

	def onMouseOut(self):
		pass

	def __setattr__(self, name, value):
		#@name = intern(name)
		dict = self.__dict__
		if value == dict.get(name, NoValue):
			return
		dict[name] = value
		if name == 'visible' and self.parent:
			#@print 'set', self, name , value
			self.parent.redraw(self, 1)
			dict['_changeReported'] = 1
		elif name[0] != '_':
			#@print 'set', self, name , value
			self.__dict__['redrawMyself'] = 1
			if self.parent and not self._changeReported:
				self.parent.redraw(self)
				dict['_changeReported'] = 1

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

import types
from pygame.locals import *
from Const import *
from Widget import widgets, registerWidget
from MetaWidget import MetaWidget
from Button import Button

class Window(MetaWidget):

	def __init__(self, parent, **kwargs):
		MetaWidget.__init__(self, parent)
		self.surface = None
		self.visible = 0
		# data
		self.title = None
		self.closeButton = 1
		# flags
		self.looseFocusClose = 0
		self.alwaysInBackground = 0
		self.alwaysOnTop = 0
		self.modal = 0
		self.rightButtonClose = 0
		self.escKeyClose = 0
		self.decorated = 1
		self.titleOnly = 0
		self.movable = 1
		self.acceptButton = None
		self._dragging = 0
		self._fullUpdate = True
		self.tabChange = False
		self.callEventHandler = False
		# register
		self.app.registerWindow(self)
		self.processKWArguments(kwargs)

	def show(self):
		self.visible = 1
		self.toFront()
		if self.widgets:
			for widget in self.widgets:
				if widget.focusable:
					self.app.setFocus(widget)
					break

	def hide(self):
		self.visible = 0
		self.app.hideWindow(self)

	def destroy(self):
		if self.visible:
			self.hide()
		self.app.unregisterWindow(self)

	def toFront(self):
		if not self.alwaysInBackground:
			self._fullUpdate = True
			self.app.moveWindowToFront(self)
		else:
			self.app.focusWindow(self)

	def drawMetaWidget(self, surface):
		if self.decorated:
			return self.theme.drawDecoratedWindow(surface, self)
		else:
			return self.theme.drawPlainWindow(surface, self)

	def draw(self, surface):
		if not self.surface or self.surface.get_size() != self.rect.size:
			self.surface = pygame.Surface(self.rect.size, self.app.windowSurfaceFlags)
		changed = MetaWidget.draw(self, self.surface)
		if self._fullUpdate:
			changed = self.surface.get_rect()
			self._fullUpdate = False
		if surface and changed:
			surface.blit(self.surface, self.rect.topleft)
			changed.move_ip(self.rect.topleft)
		return changed

	def transpose(self, pos):
		if self._widgetArea == None:
			# TODO fix this, should be assert self._widgetArea
			return (0, 0)
		return (pos[0] - self._widgetArea.left - self.rect.left,
				pos[1] - self._widgetArea.top - self.rect.top)

	def processMB1Down(self, evt):
		pos = (
			evt.pos[0] - self.rect.left,
			evt.pos[1] - self.rect.top
		)
		if self._widgetArea and not self._widgetArea.collidepoint(pos) and self.movable:
			self._dragging = 1
			return NoEvent
		else:
			return MetaWidget.processMB1Down(self, evt)

	def processMB1Up(self, evt):
		self._dragging = 0
		return MetaWidget.processMB1Up(self, evt)

	def processMB1UpMissed(self, evt):
		self._dragging = 0
		return MetaWidget.processMB1UpMissed(self, evt)

	def processMB3Down(self, evt):
		if self.rightButtonClose:
			self.hide()
			return NoEvent
		return MetaWidget.processMB3Down(self, evt)

	def processMMotion(self, evt):
		if self._dragging and evt.buttons[0]:
			self.rect.left += evt.rel[0]
			self.rect.top += evt.rel[1]
			self._fullUpdate = True
			self.parent.redrawWidgets[self] = None
			return NoEvent
		elif self._dragging and not evt.buttons[0]:
			self._dragging = 0
			return NoEvent
		else:
			return MetaWidget.processMMotion(self, evt)

	def processKeyUp(self, evt):
		if self.escKeyClose and evt.key == K_ESCAPE:
			self.hide()
			return NoEvent
		elif self.tabChange and evt.key == K_TAB and self.widgets:
			self.focusNext()
		elif self.acceptButton != None and evt.key == K_RETURN:
			if isinstance(self.acceptButton, Button) and self.acceptButton.action != None:
				self.processAction(self.acceptButton.action)
		if self.callEventHandler:
			self.callEventHandler.processKeyUp(evt)
		return evt

	def processKeyDown(self, evt):
		if self.callEventHandler:
			self.callEventHandler.processKeyDown(evt)

	def focusNext(self):
		for widget in self.widgets:
			# We need set lastFocus even when nothing is focused, exception on line 175 without this
			lastFocus = widget.orderNo
			if widget.focused:
				# keep the focued orderNo
				break

		nextFocus = None
		minWidget = None

		for widget in self.widgets:
			if widget.orderNo == 0:
				continue

			if minWidget == None:
				minWidget = widget
			elif widget.orderNo < minWidget.orderNo:
				minWidget = widget

			if nextFocus == None:
				if widget.orderNo > lastFocus:
					nextFocus = widget
			elif widget.orderNo > lastFocus and widget.orderNo < nextFocus.orderNo:
				nextFocus = widget

		if nextFocus:
			self.app.setFocus(nextFocus)
		elif minWidget:
			self.app.setFocus(minWidget)


registerWidget(Window, 'window')

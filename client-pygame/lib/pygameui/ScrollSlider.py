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

from pygame.locals import *
from Const import *
from Widget import Widget, registerWidget

class ScrollSlider(Widget):

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		# data
		self.action = None
		self.min = 0.0
		self.max = 100.0
		self.position = 0.0
		self.shown = 10
		self.dragging = 0
		self._handler = None
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)

	def draw(self, surface):
		self._handler = self.theme.drawScrollSlider(surface, self)
		return self.rect

	def processMB1Down(self, evt):
		if self._handler and self._handler.collidepoint(evt.pos):
			self.dragging = 1
		return NoEvent

	def processMB1Up(self, evt):
		self.dragging = 0
		return NoEvent

	def processMB1UpMissed(self, evt):
		self.dragging = 0
		return NoEvent

	def processMMotion(self, evt):
		if self.dragging and evt.buttons[0] == 1:
			if self.rect.width > self.rect.height:
				ratio = float(self.max - self.min) / (self.rect.width - self._handler.width)
				self.position += evt.rel[0] * ratio
			else:
				ratio = float(self.max - self.min) / (self.rect.height - self._handler.height)
				self.position += evt.rel[1] * ratio
		elif self.dragging:
			self.dragging = 0

		if self.position < self.min:
			self.position = self.min
		if self.position + self.shown > self.max:
			self.position = self.max - self.shown
		# if shown is greater then max, then position is negative
		if self.position < self.min:
			self.position = self.min

		if self.dragging and evt.buttons[0] == 1:
			self.processAction(self.action)

		return NoEvent

	def processMWUp(self, evt):
		self.position -= 1
		if self.position < self.min:
			self.position = self.min

		self.processAction(self.action)
		return NoEvent

	def processMWDown(self, evt):
		self.position += 1
		if self.position + self.shown > self.max:
			self.position = self.max - self.shown
		# if shown is greater then max, then position is negative
		if self.position < self.min:
			self.position = self.min

		self.processAction(self.action)
		return NoEvent

registerWidget(ScrollSlider, 'scrollslider')

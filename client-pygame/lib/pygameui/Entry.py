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

# keys mapping
mapping = {
	K_KP0: '0', K_KP1: '1', K_KP2: '2', K_KP3: '3', K_KP4: '4',
	K_KP5: '5', K_KP6: '6', K_KP7: '7', K_KP8: '8', K_KP9: '9',
}

class Entry(Widget):

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		# data
		self.__dict__['text'] = u''
		self.__dict__['cursorPos'] = 0
		self.__dict__['action'] = None
		self.__dict__['showChar'] = None
		self.__dict__['reportValueChanged'] = False
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)

	def draw(self, surface):
		self.theme.drawEntry(surface, self)
		return self.rect

	def onCursorChanged(self):
		# force redraw
		self.cursorPos += 1
		self.cursorPos -= 1
		# super
		Widget.onCursorChanged(self)

	def processKeyDown(self, evt):
		if evt.key == K_BACKSPACE:
			if self.cursorPos > 0:
				self.text = '%s%s' % (self.text[:self.cursorPos - 1], self.text[self.cursorPos:])
				self.cursorPos -= 1
		elif evt.key == K_DELETE:
			if self.cursorPos < len(self.text):
				self.text = '%s%s' % (self.text[:self.cursorPos], self.text[self.cursorPos + 1:])
		elif evt.key == K_RETURN:
			self.app.setFocus(None)
		elif evt.key == K_ESCAPE:
			self.app.setFocus(None)
		elif evt.key == K_HOME:
			self.cursorPos = 0
		elif evt.key == K_END:
			self.cursorPos = len(self.text)
		elif evt.key == K_LEFT:
			if self.cursorPos > 0: self.cursorPos -= 1
		elif evt.key == K_RIGHT:
			if self.cursorPos < len(self.text): self.cursorPos += 1
		elif evt.key == K_TAB:
			pass
		elif hasattr(evt, 'unicode') and evt.unicode:
			# TODO this is ugly windows only hack
			char = unicode(chr(ord(evt.unicode)), 'cp1250')
			if self.text:
				self.text = u'%s%c%s' % (
					self.text[:self.cursorPos], char, self.text[self.cursorPos:]
				)
			else:
				self.text = char
			self.cursorPos += 1
		elif mapping.has_key(evt.key):
			self.text = u'%s%c%s' % (
				self.text[:self.cursorPos], mapping[evt.key], self.text[self.cursorPos:]
			)
			self.cursorPos += 1
		if (self.reportValueChanged):
			self.processAction("onValueChanged")
		return Widget.processKeyDown(self, NoEvent)

	def onFocusGained(self):
		Widget.onFocusGained(self)
		self.cursorPos = len(self.text)

	def onFocusLost(self):
		Widget.onFocusLost(self)
		self.processAction(self.action)

registerWidget(Entry, 'entry')

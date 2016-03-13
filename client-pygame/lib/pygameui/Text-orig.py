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
from WordUtils import *
from Widget import Widget, registerWidget
import pygame.key

# keys mapping
mapping = {
	K_KP0: '0', K_KP1: '1', K_KP2: '2', K_KP3: '3', K_KP4: '4',
	K_KP5: '5', K_KP6: '6', K_KP7: '7', K_KP8: '8', K_KP9: '9',
}

class Text(Widget):
	"""Text edit widget."""

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		# data
		self.__dict__['text'] = [""]
		self.__dict__['offsetRow'] = 0
		self.__dict__['cursorRow'] = 0
		self.__dict__['cursorColumn'] = 0
		self.__dict__['action'] = None
		self.__dict__['editable'] = 1
		self.__dict__['vertScrollbar'] = None
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)

	def draw(self, surface):
		self.theme.drawText(surface, self)

	def attachVScrollbar(self, scrollbar):
		self.vertScrollbar = scrollbar
		scrollbar.subscribeAction("*", self)
		scrollbar.action = "onScroll"
		scrollbar.slider.min = 0
		scrollbar.slider.max = len(self.text) + 100
		scrollbar.slider.position = self.offsetRow
		scrollbar.slider.shown = 1

	def onScroll(self, widget, action, data):
		self.offsetRow = self.vertScrollbar.slider.position

	def onCursorChanged(self):
		# force redraw
		self.cursorColumn += 1
		self.cursorColumn -= 1
		# super
		Widget.onCursorChanged(self)

	def processKeyDown(self, evt):
		if not self.editable:
			return Widget.processKeyDown(self, evt)
		# process keys
		if evt.key == K_BACKSPACE:
			if self.cursorColumn > 0:
				self.text[self.cursorRow] = u'%s%s' % (self.text[self.cursorRow][:self.cursorColumn - 1], self.text[self.cursorRow][self.cursorColumn:])
				self.cursorColumn -= 1
			else:
				if self.cursorRow > 0:
					self.cursorColumn = len(self.text[self.cursorRow -1])
					self.text[self.cursorRow - 1] = u'%s%s' % (self.text[self.cursorRow - 1], self.text[self.cursorRow])
					del self.text[self.cursorRow]
					self.cursorRow -= 1
		elif evt.key == K_DELETE:
			if self.cursorColumn < len(self.text[self.cursorRow]):
				self.text[self.cursorRow] = u'%s%s' % (self.text[self.cursorRow][:self.cursorColumn], self.text[self.cursorRow][self.cursorColumn + 1:])
			elif self.cursorRow < len(self.text) - 1:
				self.text[self.cursorRow] = u'%s%s' % (self.text[self.cursorRow], self.text[self.cursorRow + 1])
				del self.text[self.cursorRow + 1]
		elif evt.key == K_RETURN:
			text1 = self.text[self.cursorRow][self.cursorColumn:]
			text2 = self.text[self.cursorRow][:self.cursorColumn]
			self.text[self.cursorRow] = text1
			self.text.insert(self.cursorRow, text2)
			self.cursorRow += 1
			self.cursorColumn = 0
		elif evt.key == K_ESCAPE:
			self.app.setFocus(None)
		elif evt.key == K_LEFT:
			if evt.mod & KMOD_CTRL:
				# move one word left
				# take words on line
				words = splitter(self.text[self.cursorRow])
				if len(words) == 0:
					#move to previous line
					if self.cursorRow > 0:
						self.cursorRow -= 1
						words2 = splitter(self.text[self.cursorRow])
						if len(words2) > 0:
							#move cursor to begining of last word
							self.cursorColumn = words2[-1][1]
						else:
							#no words on line, so move cursor to the end of line
							self.cursorColumn = len(self.text[self.cursorRow])
					else:
						#we are on first line, so move cursor to begining of line
						self.cursorColumn = 0
				idxs = getIdxFromColumn(words, self.cursorColumn)
				if idxs != (-1, -1):
					if idxs[0] == -1:
						#cursor is before first word, jump to beginig of last word on previous line
						if self.cursorRow > 0:
							self.cursorRow -= 1
							words2 = splitter(self.text[self.cursorRow])
							if len(words2) > 0:
								#move cursor to begining of last word
								self.cursorColumn = words2[-1][1]
							else:
								#no words on line, so move cursor to the end of line
								self.cursorColumn = len(self.text[self.cursorRow])
						else:
							#we are on first line, so move cursor to begining of line
							self.cursorColumn = 0
					elif idxs[0] == idxs[1]:
						#we are inside word, so move cursor to begining of word
						self.cursorColumn = words[idxs[0]][1]
					elif idxs[1] == -1:
						#cursor is after last word, we must jump to begining of last word
						self.cursorColumn = words[idxs[0]][1]
					else:
						#cursor is between words, we must jump to begining of left word
						self.cursorColumn = words[idxs[0]][1]
			elif self.cursorColumn > 0: self.cursorColumn -= 1
			elif self.cursorRow > 0:
				self.cursorRow -= 1
				self.cursorColumn = len(self.text[self.cursorRow])
		elif evt.key == K_RIGHT:
			if evt.mod & KMOD_CTRL:
				# move one word right
				# take words on line
				words = splitter(self.text[self.cursorRow])
				if len(words) == 0:
					#move to next line
					if self.cursorRow < len(self.text) - 1:
						self.cursorRow += 1
						words2 = splitter(self.text[self.cursorRow])
						if len(words2) > 0:
							self.cursorColumn = words2[0][1]
						else:
							#on next line are only separators (or is empty), so move to column 0
							self.cursorColumn = 0
					else:
						#we are on last line, so move cursor to end of line
						self.cursorColumn = len(self.text[self.cursorRow])
				idxs = getIdxFromColumn(words, self.cursorColumn)
				if idxs != (-1, -1):
					if idxs[0] == idxs[1] or self.cursorColumn == words[idxs[1]][1]:
						#cursor is inside of word or is on begining of word, so move on begining of next word
						if idxs[1] + 1 < len(words):
							#there is next word on line
							self.cursorColumn = words[idxs[1] + 1][1]
						else:
							#we must jump to begining first word on next line
							if self.cursorRow < len(self.text) - 1:
								self.cursorRow += 1
								words2 = splitter(self.text[self.cursorRow])
								if len(words2) > 0:
									self.cursorColumn = words2[0][1]
								else:
									#on next line are only separators (or is empty), so move to column 0
									self.cursorColumn = 0
							else:
								#we are on last line, so move cursor to end of line
								self.cursorColumn = len(self.text[self.cursorRow])
					elif idxs[0] == -1:
						#cursor is before first word, jump to beginig of fist word
						self.cursorColumn = words[idxs[1]][1]
					elif idxs[1] == -1:
						#cursor is after last word, we must jump to begining first word on next line
						if self.cursorRow < len(self.text) - 1:
							self.cursorRow += 1
							words2 = splitter(self.text[self.cursorRow])
							if len(words2) > 0:
								self.cursorColumn = words2[0][1]
							else:
								#on next line are only separators (or is empty), so move to column 0
								self.cursorColumn = 0
						else:
							#we are on last line, so move cursor to end of line
							self.cursorColumn = len(self.text[self.cursorRow])
					else:
						#cursor is between words
						self.cursorColumn = words[idxs[1]][1]
			elif self.cursorColumn < len(self.text[self.cursorRow]): self.cursorColumn += 1
			elif self.cursorRow < len(self.text):
				# move to the next row
				if self.cursorRow < len(self.text) - 1:
					self.cursorRow += 1
					self.cursorColumn = 0
		elif evt.key == K_UP:
			if self.cursorRow > 0:
				self.cursorRow -= 1
				self.cursorColumn = min(self.cursorColumn, len(self.text[self.cursorRow]))
		elif evt.key == K_DOWN:
			if self.cursorRow < len(self.text) - 1:
				self.cursorRow += 1
				self.cursorColumn = min(self.cursorColumn, len(self.text[self.cursorRow]))
		elif evt.key == K_TAB:
			pass
		elif evt.key == K_END:
			self.cursorColumn = len(self.text[self.cursorRow])
		elif evt.key == K_HOME:
			self.cursorColumn = 0
		elif evt.unicode:
			# TODO this is ugly windows only hack
			char = unicode(chr(ord(evt.unicode)), 'cp1250')
			self.text[self.cursorRow] = u'%s%s%s' % (
				self.text[self.cursorRow][:self.cursorColumn], char, self.text[self.cursorRow][self.cursorColumn:]
			)
			self.cursorColumn += 1
		elif mapping.has_key(evt.key):
			self.text[self.cursorRow] = u'%s%s%s' % (
				self.text[self.cursorRow][:self.cursorColumn], mapping[evt.key], self.text[self.cursorRow][self.cursorColumn:]
			)
			self.cursorColumn += 1
		return Widget.processKeyDown(self, NoEvent)

	def onFocusGained(self):
		Widget.onFocusGained(self)
		self.cursorRow = len(self.text) - 1
		self.cursorColumn = len(self.text[self.cursorRow])

	def onFocusLost(self):
		Widget.onFocusLost(self)
		self.processAction(self.action)

	# redirect mouse wheel events to the scollbar
	def processMWUp(self, evt):
		return self.vertScrollbar.processMWUp(evt)

	def processMWDown(self, evt):
		return self.vertScrollbar.processMWDown(evt)

registerWidget(Text, 'text')

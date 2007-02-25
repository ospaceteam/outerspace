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

from types import StringType, UnicodeType

class Item:

	def __init__(self, text, **kwargs):
		self.text = text
		self.align = 0
		self.selected = 0
		self.icons = []
		self.font = None
		self.children = []
		self.expanded = 0
		self.tooltip = None
		self.statustip = None
		self.foreground = None
		self.background = None
		self.index = None
		self.enabled = 1
		for key, value in kwargs.items():
			setattr(self, key, value)

	def getAsString(self, key):
		if hasattr(self, key):
			value = getattr(self, key)
			valType = type(value)
			if valType == StringType or valType == UnicodeType:
				return value
			else:
				return str(value)
		else:
			raise AttributeError(key)
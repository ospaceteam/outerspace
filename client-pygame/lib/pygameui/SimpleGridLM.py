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

class SimpleGridLM:

	def __init__(self, rowSize = None, colSize = None):
		self.metaWidget = None
		self.rowSize = rowSize
		self.colSize = colSize
		self.padx = 1
		self.pady = 1

	def layoutWidgets(self):
		wa = self.metaWidget._widgetArea
		if not (self.rowSize or self.colSize):
			self.rowSize, self.colSize = self.metaWidget.app.theme.getGridParams()
		for widget in self.metaWidget.widgets:
			if widget.layout:
				#x = widget.layout[0] * self.colSize + self.padx
				#y = widget.layout[1] * self.rowSize + self.pady
				#w = widget.layout[2] * self.colSize - 2 * self.padx
				#h = widget.layout[3] * self.rowSize - 2 * self.pady
				x = widget.layout[0] * self.colSize
				y = widget.layout[1] * self.rowSize
				w = widget.layout[2] * self.colSize
				h = widget.layout[3] * self.rowSize
				widget.rect = Rect(int(x), int(y), int(w), int(h))

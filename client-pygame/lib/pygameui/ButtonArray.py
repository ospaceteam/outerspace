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
from Widget import registerWidget
from MetaWidget import MetaWidget
from Scrollbar import Scrollbar
from Button import Button

class ButtonArray(MetaWidget):

	def __init__(self, parent, **kwargs):
		MetaWidget.__init__(self, parent)
		# data
		self.items = []
		self.buttons = []
		self.action = None
		self.rmbAction = None
		self.selected = None
		self.selectedButton = None
		self.buttonSize = (1, 1)
		self.rows = 0
		self.columns = 0
		self.showSlider = 1
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)
		# create widgets
		self.bar = Scrollbar(self, action = 'onScroll')
		self.bar.subscribeAction('*', self)

	def layoutWidgets(self):
		gx, gy = self.theme.getGridParams()
		r = self.rect
		self.bar.rect = Rect(r.width - gx, 0, gx, r.height)
		self.bar.visible = self.showSlider
		self.labels = []
		bwidth, bheight = self.buttonSize
		self.rows = r.height / gy / bheight
		if self.showSlider:
			self.columns = (r.width - gx) / gx / bwidth
		else:
			self.columns = r.width / gx / bwidth
		for row in xrange(0, self.rows):
			for column in xrange(0, self.columns):
				x = column * gx * bwidth
				y = row * gy * bheight
				button = Button(self, action = 'onButtonPressed', rmbAction = 'onRButtonPressed', toggle = 1)
				button.subscribeAction('*', self)
				button.rect = Rect(x, y, bwidth * gx, bheight * gy)
				self.buttons.append(button)
		self.bar.slider.position = 0
		self.bar.slider.min = 0
		self.bar.slider.shown = self.rows
		self.itemsChanged()

	def onScroll(self, widget, action, data):
		self.itemsChanged()

	def clearSelection(self):
		if self.selectedButton:
			self.selectedButton.pressed = 0
			self.selectedButton = None

	def selectItem(self, item):
		if not item:
			self.clearSelection()
		elif item != self.selected:
			self.clearSelection()
		self.selected = item
		self.itemsChanged()

	def onButtonPressed(self, widget, action, data):
		if self.selectedButton:
			self.clearSelection()
		if widget.pressed:
			self.selected = widget.data
			self.selectedButton = widget
		else:
			self.selected = None
		self.processAction(self.action, self.selected)

	def onRButtonPressed(self, widget, action, data):
		self.processAction(self.rmbAction, widget.data)

	def itemsChanged(self):
		if self.columns == 0 or self.rows == 0:
			return
		if self.items:
			self.bar.slider.max = len(self.items) / self.columns + 1
		else:
			self.bar.slider.max = 1

		index = 0
		pos = int(self.bar.slider.position) * self.columns
		# TODO should be changed
		if pos >= len(self.items): pos = len(self.items) - 1
		for item in self.items[pos:]:
			if index < len(self.buttons):
				button = self.buttons[index]
				button.text = item.text
				button.align = item.align
				button.icons = item.icons
				button.tooltip = item.tooltip
				button.statustip = item.statustip
				button.font = item.font
				button.data = item
				button.foreground = item.foreground
				button.background = item.background
				button.enabled = item.enabled
				if not button.visible: button.visible = 1
				if item == self.selected:
					button.pressed = 1
					# do not trigger auto update
					self.__dict__['selectedButton'] = button
				else:
					button.pressed = 0
			else:
				break
			index += 1
		while index < len(self.buttons):
			button = self.buttons[index]
			button.text = None
			button.icons = None
			button.data = None
			button.tooltip = None
			button.statustip = None
			button.pressed = 0
			button.enabled = 0
			button.foreground = None
			button.background = None
			if button.visible: button.visible = 0
			index += 1
		self.clearSelection()
		self.parent.redraw(self)

	def drawMetaWidget(self, surface):
		return self.theme.drawListbox(surface, self)

registerWidget(ButtonArray, 'buttonarray')

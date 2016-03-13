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

from ArrowButton import ArrowButton
from ScrollSlider import ScrollSlider

class Scrollbar(MetaWidget):

	def __init__(self, parent, **kwargs):
		MetaWidget.__init__(self, parent)
		# data
		self.action = None
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)
		# create widgets
		self.button1 = ArrowButton(self, action = 'onButton1')
		self.button1.subscribeAction('*', self)
		self.button2 = ArrowButton(self, action = 'onButton2')
		self.button2.subscribeAction('*', self)
		self.slider = ScrollSlider(self, action = 'onSlider')
		self.slider.subscribeAction('*', self)

	def layoutWidgets(self):
		gx, gy = self.theme.getGridParams()
		r = self.rect
		if self.rect.width > self.rect.height:
			# horizontal
			self.button1.rect = Rect(0, 0, gx, gy)
			self.button1.direction = ALIGN_W
			self.button2.rect = Rect(r.width - gx, 0, gx, gy)
			self.button2.direction = ALIGN_E
			self.slider.rect = Rect(gx, 0, r.width - 2 * gx, gy)
		else:
			# vertical
			self.button1.rect = Rect(0, 0, gx, gy)
			self.button1.direction = ALIGN_N
			self.button2.rect = Rect(0, r.height - gy, gx, gy)
			self.button2.direction = ALIGN_S
			self.slider.rect = Rect(0, gy, gx, r.height - 2 * gy)
		MetaWidget.layoutWidgets(self)

	def drawMetaWidget(self, surface):
		return self.theme.drawScrollbar(surface, self)

	def onButton1(self, widget, actionName, data):
		s = self.slider
		s.position -= s.shown
		if s.position < s.min:
			s.position = s.min
		self.processAction(self.action)

	def onButton2(self, widget, actionName, data):
		s = self.slider
		s.position += s.shown
		if s.position + s.shown > s.max:
			s.position = s.max - s.shown
		# if shown is greater then max, then position is negative
		if s.position < s.min:
			s.position = s.min
		self.processAction(self.action)

	def onSlider(self, widget, actionName, data):
		self.processAction(self.action)

	# redirect mouse wheel events to the slider
	def processMWUp(self, evt):
		return self.slider.processMWUp(evt)

	def processMWDown(self, evt):
		return self.slider.processMWDown(evt)

registerWidget(Scrollbar, 'scrollbar')

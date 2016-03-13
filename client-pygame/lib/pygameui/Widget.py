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

"""
Member variables naming convention:
   _  non watched variable (not changing visual representation of widget)
   *  'watched' variable (change of this variable will force widget update)
"""

from pygame.locals import *
from Const import *
import types

class DataHolder:
	pass

class Widget:
	def __init__(self, parent, **kwargs):
		# set attributes
		# bypass change detection
		self.__dict__['_changeReported'] = 0
		self.__dict__['parent'] = parent
		self.__dict__['metaType'] = TYPE_WIDGET
		self.__dict__['app'] = parent.getApp()
		self.__dict__['theme'] = self.app.theme
		self.__dict__['foreground'] = None
		self.__dict__['background'] = None
		self.__dict__['style'] = None
		self.__dict__['font'] = None
		self.__dict__['align'] = ALIGN_NONE
		self.__dict__['tooltip'] = None
		self.__dict__['statustip'] = None
		self.__dict__['visible'] = 0
		self.__dict__['enabled'] = 1
		self.__dict__['focused'] = 0
		self.__dict__['mouseOver'] = 0
		self.__dict__['focusable'] = 1
		self.__dict__['dragSource'] = 0
		self.__dict__['dragTarget'] = 0
		self.__dict__['layout'] = None
		self.__dict__['tags'] = []
		self.__dict__['id'] = None
		self.__dict__['orderNo'] = 0
		self.__dict__['rect'] = Rect((0, 0, 0, 0))
		self.__dict__['_handleMap'] = {'*': []}
		self.__dict__['data'] = DataHolder()
		# notify parent
		self.visible = 1
		self.processKWArguments(kwargs)

	def processKWArguments(self, kwargs):
		# process keyword arguments
		for key in kwargs:
			if hasattr(self, key):
				self.__dict__[key] = kwargs[key]
			else:
				raise AttributeError(key)

	def subscribeAction(self, actionName, handler):
		handleList = self._handleMap.get(actionName, [])
		handleList.append(handler)
		self._handleMap[actionName] = handleList

	def processAction(self, actionName, data = None, widget = None):
		if not actionName: return
		if not widget: widget = self
		handlers = self._handleMap.get(actionName, self._handleMap['*'])
		if handlers:
			for handler in handlers:
				if type(handler) == types.InstanceType:
					handler = getattr(handler, actionName)
				apply(handler, (widget, actionName, data))
		else:
			self.parent.processAction(actionName, data, widget)

	def draw(self, surface):
		raise NotImplementedError('%s.draw' % self.__class__)

	def getSize(self):
		raise NotImplementedError

	def onFocusLost(self):
		self.focused = 0

	def onFocusGained(self):
		self.focused = 1

	def onMouseOut(self):
		self.mouseOver = 0

	def onMouseOver(self):
		self.mouseOver = 1

	def onCursorChanged(self):
		return

	def processMB1Down(self, evt):
		return NoEvent

	def processMB1Up(self, evt):
		return NoEvent

	def processMB1UpMissed(self, evt):
		return NoEvent

	def processMB2Down(self, evt):
		return NoEvent

	def processMB2Up(self, evt):
		return NoEvent

	def processMB2UpMissed(self, evt):
		return NoEvent

	def processMB3Down(self, evt):
		return NoEvent

	def processMB3Up(self, evt):
		return NoEvent

	def processMB3UpMissed(self, evt):
		return NoEvent

	def processMWUp(self, evt):
		return NoEvent

	def processMWDown(self, evt):
		return NoEvent

	def processMMotion(self, evt):
		return NoEvent

	def processKeyDown(self, evt):
		return evt

	def processKeyUp(self, evt):
		return evt

	def getApp(self):
		return self.parent.getApp()

	def redraw(self):
		self.parent.redraw(self)
		self.__dict__['_changeReported'] = 1

	def __setattr__(self, name, value):
		#@name = intern(name)
		dict = self.__dict__
		if value == dict.get(name, NoValue):
			return
		dict[name] = value
		if name == 'visible' and self.parent:
			self.parent.redraw(self, 1)
			dict['_changeReported'] = 1
			#@print 'set', self, name , value
		elif not self._changeReported and name[0] != '_' and self.parent:
			self.parent.redraw(self)
			dict['_changeReported'] = 1
			#@print 'set', self, name , value

	def set(self, **kwargs):
		self.processKWArguments(kwargs)

##
## All elements are registered here
##

widgets = {}

def registerWidget(widget, name):
	widgets[name] = widget

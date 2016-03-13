#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

# general holder for ALL data in game
class IDataHolder:

	#def __setattr__(self, key, value):
	#	self.__dict__[key] = value
	#	self.__dict__['_v_modified'] = 1

	#def setModified(self, modified):
	#	self.__dict__['_v_modified'] = modified

	# for debug only
	def __repr__(self):
		result = '<%s.%s %X ' % (self.__class__.__module__, self.__class__.__name__, id(self))
		items = self.__dict__.items()
		items.sort()
		for key, value in items:
			result += '%s=%s, ' % (key, repr(value))
		result += '>'
		return result

def makeIDataHolder(**kwargs):
	obj = IDataHolder()
	for key, value in kwargs.items():
		setattr(obj, key, value)
	return obj

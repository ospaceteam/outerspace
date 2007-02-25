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

from Exception import *
import pygame
import pygame.locals

TIMEREVENT = pygame.locals.USEREVENT
if TIMEREVENT >= pygame.locals.NUMEVENTS:
	raise 'Cannot create TIMEREVENT.'

USEREVENT = TIMEREVENT + 1
if USEREVENT >= pygame.locals.NUMEVENTS:
	raise 'Cannot create USEREVENT.'

NoEvent = pygame.event.Event(pygame.locals.NOEVENT)

# Alignment
ALIGN_NONE = 0x00
ALIGN_N = 0x01
ALIGN_S = 0x02
ALIGN_E = 0x04
ALIGN_W = 0x08
ALIGN_NE = ALIGN_N | ALIGN_E
ALIGN_NW = ALIGN_N | ALIGN_W
ALIGN_SE = ALIGN_S | ALIGN_E
ALIGN_SW = ALIGN_S | ALIGN_W
ALIGN_MASK = 0x0f

# Flags
F_EDITABLE = 0x10

# Special value
class NoValue:
	pass

# Class of Rect
RectType = type(pygame.locals.Rect(0, 0, 0, 0))

# Meta types of widgets
TYPE_WIDGET = 0
TYPE_METAWIDGET = 1


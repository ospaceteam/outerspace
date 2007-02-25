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

from pygame.font import Font
from types import StringType, UnicodeType

__all__ = ['initFont', 'renderText', 'getTextSize', 'getLineSize']

fontFaces = {}
fontCache = {}
misses = 0
hits = 0

def initFont(name, ttfFile, size, bold = 0, italic = 0, underline = 0):
	global fontFaces
	if name in fontFaces:
		del fontFaces[name]
	font = Font(ttfFile, size)
	font.set_bold(bold)
	font.set_italic(italic)
	font.set_underline(underline)
	fontFaces[name] = font

def renderText(name, text, antialias, fg, bg = None):
	antialias = 1
	tType = type(text)
	if tType != StringType and tType != UnicodeType:
		text = str(text)
	if len(text) == 0:
		# TODO return very small surface
		text = " "
	#@print "->", text, "<-", type(text)
	global misses, hits, fontCache
	surface = fontCache.get((name, text, antialias, fg, bg), None)
	if not surface:
		misses += 1
		if bg:
			surface = fontFaces[name].render(text, antialias, fg, bg)
		else:
			surface = fontFaces[name].render(text, antialias, fg)
		fontCache[name, text, antialias, fg, bg] = surface
	else:
		hits += 1
	# clean up cache if size is > 1000
	if misses > 1000:
		print 'FONT CACHE STATS:', misses, hits, hits / float(misses + hits)
		misses = 0
		fontCache.clear()
	return surface

def renderSmartText(surface, x, y, name, text, antialias, fg, bg = None):
	# TODO
	pass

def getTextSize(name, text):
	#return renderText(name, text, 1, (0x00, 0x00, 0x00)).get_size()
	return fontFaces[name].size(text)

def getLineSize(name):
	return fontFaces[name].get_linesize()

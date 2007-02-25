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

import pygame, pygame.draw, pygame.time
from pygame.locals import *
from Const import *
from Fonts import *
import os, os.path

try:
	import _winreg
except ImportError:
	pass

themeForeground = 0x00, 0xd0, 0x00
themeWindowBck = 0x20, 0x30, 0x20
themeBackground = 0x20, 0x40, 0x20
themeHighlightbck = 0x40, 0x60, 0x40
themeHighlightfrg = 0x40, 0xf0, 0x40
themeGaugecolor = 0x00, 0x80, 0x00
themeDefaultFont = 'normal'
themeBoldFont = 'normal-bold'
themeSelectionFrg = 0x00, 0xd0, 0x00
themeSelectionBck = 0x40, 0x80, 0x40
themeTitleLine1 = 0x30, 0x50, 0x30
themeTitleLine2 = 0x40, 0x60, 0x40

def init():
	if os.name == 'nt':
		# get "Fonts" folder location
		handle = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders')
		path, valueType = _winreg.QueryValueEx(handle, 'Fonts')
		handle.Close()
		try:
			# try tahoma
			filename = os.path.join(path, 'tahoma.ttf')
			if os.path.exists(filename):
				initFont('normal', filename, 13)
				initFont('normal-bold', filename, 13, bold = 1)
				initFont('large', filename, 15)
				initFont('large-bold', filename, 15, bold = 1)
				initFont('small', filename, 11)
				initFont('small-bold', filename, 11, bold = 1)
				return
			# try arial
			filename = os.path.join(path, 'arial.ttf')
			if os.path.exists(filename):
				initFont('normal', filename, 13)
				initFont('normal-bold', filename, 13, bold = 1)
				initFont('large', filename, 15)
				initFont('large-bold', filename, 15, bold = 1)
				initFont('small', filename, 11)
				initFont('small-bold', filename, 11, bold = 1)
				return
		except:
			import traceback, sys
			traceback.print_exc(file = sys.stderr)
	# default font
	try:
		initFont('normal', 'res/fonts/os.font', 12)
		initFont('normal-bold', 'res/fonts/os.font', 12, bold = 1)
		initFont('large', 'res/fonts/os.font', 15)
		initFont('large-bold', 'res/fonts/os.font', 15, bold = 1)
		initFont('small', 'res/fonts/os.font', 10)
		initFont('small-bold', 'res/fonts/os.font', 10, bold = 1)
	except RuntimeError:
		# fallback
		initFont('normal', None, 16)
		initFont('normal-bold', None, 16)
		initFont('large', None, 20)
		initFont('large-bold', None, 20)
		initFont('small', None, 14)

def getGridParams():
	#getLineSize(themeDefaultFont)
	return 20, 20

def getDRect(rect):
	rect = Rect(rect)
	rect.left += 1
	rect.top += 1
	rect.width -= 2
	rect.height -= 2
	return rect

def drawButton(surface, widget):
	rect = getDRect(widget.rect)
	surface.fill(themeWindowBck, rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# rectangle
	r = getDRect(widget.rect)
	if widget.pressed:
		surface.fill(themeHighlightbck, r)
	else:
		surface.fill(themeBackground, r)
	# icon
	if widget.icons:
		for img, align in widget.icons:
			r = getDRect(rect)
			if align & ALIGN_W: r.left += 1
			elif align & ALIGN_E: r.left += rect.width - img.get_width()
			else: r.left += (rect.width - img.get_width()) / 2
			if align & ALIGN_N: r.top += 1
			elif align & ALIGN_S: r.top += rect.height - img.get_height()
			else: r.top += (rect.height - img.get_height()) / 2
			surface.blit(img, r)
	# text
	if widget.text != None:
		img = renderText(font, widget.text, 1, foreground)
		r = getDRect(rect)
		if widget.align & ALIGN_W: r.left += 2
		elif widget.align & ALIGN_E: r.left += rect.width - img.get_width() - 1
		else: r.left += (rect.width - img.get_width()) / 2
		if widget.align & ALIGN_N: r.top += 2
		elif widget.align & ALIGN_S: r.top += rect.height - img.get_height() - 1
		else: r.top += (rect.height - img.get_height()) / 2
		surface.blit(img, r)
	# rectangle
	r = getDRect(widget.rect)
	if widget.pressed:
		pygame.draw.lines(surface, themeHighlightfrg, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
		r.left += 1
		r.top += 1
		r.width -= 2
		r.height -= 2
		pygame.draw.lines(surface, themeForeground, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
	else:
		pygame.draw.lines(surface, themeForeground, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))

def drawArrowButton(surface, widget):
	rect = getDRect(widget.rect)
	surface.fill(themeWindowBck, rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# rectangle
	r = getDRect(widget.rect)
	if widget.pressed:
		pygame.draw.lines(surface, themeHighlightfrg, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
		r.left += 1
		r.top += 1
		r.width -= 2
		r.height -= 2
		surface.fill(themeHighlightbck, r)
		pygame.draw.lines(surface, themeForeground, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
	else:
		surface.fill(themeBackground, r)
		pygame.draw.lines(surface, themeForeground, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
	# arrow
	r = getDRect(rect)
	r.left += 3
	r.top += 3
	r.width -= 6
	r.height -= 6
	if widget.direction == ALIGN_N:
		points = (r.midtop, r.bottomright, r.bottomleft)
	elif widget.direction == ALIGN_S:
		points = (r.midbottom, r.topleft, r.topright)
	elif widget.direction == ALIGN_E:
		points = (r.midright, r.topleft, r.bottomleft)
	elif widget.direction == ALIGN_W:
		points = (r.midleft, r.topright, r.bottomright)
	pygame.draw.lines(surface, themeForeground, 1, points)

def drawTitleButton(surface, widget):
	rect = getDRect(widget.rect)
	oldClip = surface.get_clip()
	surface.set_clip(rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeBoldFont
	# nicer background
	surface.fill(themeTitleLine1, rect)
	x1 = rect.left
	x2 = rect.right
	for y in xrange(rect.top, rect.bottom, 2):
		pygame.draw.line(surface, themeTitleLine2, (x1, y), (x2, y), 1)
	# icon
	if widget.icons:
		for img, align in widget.icons:
			r = getDRect(rect)
			if align & ALIGN_W: r.left += 1
			elif align & ALIGN_E: r.left += rect.width - img.get_width()
			else: r.left += (rect.width - img.get_width()) / 2
			if align & ALIGN_N: r.top += 1
			elif align & ALIGN_S: r.top += rect.height - img.get_height()
			else: r.top += (rect.height - img.get_height()) / 2
			surface.blit(img, r)
	# text
	if widget.text != None:
		if widget.pressed:
			foreground = themeHighlightfrg
		img = renderText(font, widget.text, 1, foreground)
		r = getDRect(rect)
		if widget.align & ALIGN_W: r.left += 2
		elif widget.align & ALIGN_E: r.left += rect.width - img.get_width() - 1
		else: r.left += (rect.width - img.get_width()) / 2
		if widget.align & ALIGN_N: r.top += 2
		elif widget.align & ALIGN_S: r.top += rect.height - img.get_height() - 1
		else: r.top += (rect.height - img.get_height()) / 2
		surface.blit(img, r)
	surface.set_clip(oldClip)

def drawLabel(surface, widget):
	rect = getDRect(widget.rect)
	oldClip = surface.get_clip()
	surface.set_clip(rect)
	foreground = widget.foreground or themeForeground
	background = widget.background or themeWindowBck
	surface.fill(background, rect)
	font = widget.font or themeDefaultFont
	# icon
	if widget.icons:
		for img, align in widget.icons:
			r = getDRect(rect)
			if align & ALIGN_W: r.left += 1
			elif align & ALIGN_E: r.left += rect.width - img.get_width()
			else: r.left += (rect.width - img.get_width()) / 2
			if align & ALIGN_N: r.top += 1
			elif align & ALIGN_S: r.top += rect.height - img.get_height()
			else: r.top += (rect.height - img.get_height()) / 2
			surface.blit(img, r)
	# text
	if widget.text != None:
		img = renderText(font, widget.text, 1, foreground)
		r = getDRect(rect)
		if widget.align & ALIGN_W: r.left += 2
		elif widget.align & ALIGN_E: r.left += rect.width - img.get_width() - 1
		else: r.left += (rect.width - img.get_width()) / 2
		if widget.align & ALIGN_N: r.top += 2
		elif widget.align & ALIGN_S: r.top += rect.height - img.get_height() - 1
		else: r.top += (rect.height - img.get_height()) / 2
		surface.blit(img, r)
	surface.set_clip(oldClip)

def drawTitle(surface, widget):
	rect = getDRect(widget.rect)
	oldClip = surface.get_clip()
	surface.set_clip(rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# nicer background
	surface.fill(themeTitleLine1, rect)
	x1 = rect.left
	x2 = rect.right
	for y in xrange(rect.top, rect.bottom, 2):
		pygame.draw.line(surface, themeTitleLine2, (x1, y), (x2, y), 1)
	# icon
	if widget.icons:
		for img, align in widget.icons:
			r = getDRect(rect)
			if align & ALIGN_W: r.left += 1
			elif align & ALIGN_E: r.left += rect.width - img.get_width()
			else: r.left += (rect.width - img.get_width()) / 2
			if align & ALIGN_N: r.top += 1
			elif align & ALIGN_S: r.top += rect.height - img.get_height()
			else: r.top += (rect.height - img.get_height()) / 2
			surface.blit(img, r)
	# text
	if widget.text != None:
		img = renderText(font, widget.text, 1, foreground)
		r = getDRect(rect)
		if widget.align & ALIGN_W: r.left += 2
		elif widget.align & ALIGN_E: r.left += rect.width - img.get_width() - 1
		else: r.left += (rect.width - img.get_width()) / 2
		if widget.align & ALIGN_N: r.top += 2
		elif widget.align & ALIGN_S: r.top += rect.height - img.get_height() - 1
		else: r.top += (rect.height - img.get_height()) / 2
		surface.blit(img, r)
	surface.set_clip(oldClip)

def drawEntry(surface, widget):
	rect = getDRect(widget.rect)
	oldClip = surface.get_clip()
	surface.set_clip(rect)
	surface.fill(widget.background or themeHighlightbck, rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# text
	if widget.showChar and widget.text: text = widget.showChar * len(widget.text)
	else: text = widget.text
	if text != None:
		textToCursor = text[:widget.cursorPos]
	else:
		textToCursor = ''
	img = renderText(font, text, 1, foreground)
	r = getDRect(rect)
	if widget.align & ALIGN_W: r.left += 2
	elif widget.align & ALIGN_E: r.left += rect.width - img.get_width() - 2
	else: r.left += (rect.width - img.get_width()) / 2
	if widget.align & ALIGN_N: r.top += 2
	elif widget.align & ALIGN_S: r.top += rect.height - img.get_height() - 1
	else: r.top += (rect.height - img.get_height()) / 2
	surface.blit(img, r)
	if widget.focused and widget.app.cursorOn:
		offset = getTextSize(font, textToCursor)
		r.move_ip(offset[0], 0)
		pygame.draw.line(surface, foreground, r.topleft, r.bottomleft, 1)
	surface.set_clip(oldClip)

def drawDecoratedWindow(surface, window):
	surface.fill(themeWindowBck)
	wa = surface.get_clip()
	# title
	if window.title:
		font = window.font or 'large-bold'
		if window.focused:
			color = themeForeground
		else:
			color = themeBackground
		text = renderText(font, window.title, 1, color)
		r = surface.get_clip()
		r.height = getGridParams()[1]
		# nicer background
		surface.fill(themeTitleLine1, r)
		if window.focused:
			x1 = r.left
			x2 = r.right
			for y in xrange(r.top, r.bottom, 2):
				pygame.draw.line(surface, themeTitleLine2, (x1, y), (x2, y), 1)
		r.move_ip(3, (r.height - text.get_height()) / 2)
		surface.blit(text, r)
		wa.top += r.height
		wa.height -= r.height
	# lines around the window
	if not window.titleOnly:
		r = surface.get_clip()
		r.width -= 1
		r.height -= 1
		pygame.draw.lines(surface, themeTitleLine1, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
		wa.top += 2
		wa.height -= 3
		wa.left += 2
		wa.width -= 3
	return wa

def drawPlainWindow(surface, window):
	surface.fill(themeWindowBck)
	return surface.get_clip()

def drawScrollSlider(surface, widget):
	foreground = widget.foreground or themeForeground
	r = getDRect(widget.rect)
	# frame
	surface.fill(themeBackground, r)
	pygame.draw.lines(surface, themeForeground, 1,
		(r.topleft, r.topright, r.bottomright, r.bottomleft))
	r.top += 2
	r.left += 2
	r.height -= 4
	r.width -= 4
	if r.width > r.height:
		# horizontal
		width = widget.max - widget.min
		slider = widget.shown * r.width / width
		if slider < 18: slider = 18
		if slider > r.width: slider = r.width
		pos = (widget.position - widget.min) * (r.width - slider) / width
		left = r.left
		r.width = slider
		r.left = left + pos
	else:
		# vertical
		height = widget.max - widget.min
		slider = widget.shown * r.height / height
		if slider < 18: slider = 18
		if slider > r.height: slider = r.height
		pos = (widget.position - widget.min) * (r.height - slider) / height
		top = r.top
		r.height = slider
		r.top = top + pos
	surface.fill(themeHighlightbck, r)
	if widget.dragging:
		pygame.draw.lines(surface, themeHighlightfrg, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
		r.left += 1
		r.top += 1
		r.width -= 2
		r.height -= 2
		pygame.draw.lines(surface, themeForeground, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
	else:
		pass
		#pygame.draw.lines(surface, themeForeground, 1,
		#	(r.topleft, r.topright, r.bottomright, r.bottomleft))
	return r

def drawTooltip(surface, widget):
	rect = getDRect(widget.rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# text
	img = renderText(font, widget.text, 1, foreground)
	r = getDRect(rect)
	r.left += 20
	r.width = img.get_width() + 4
	r.height = img.get_height() + 4
	surface.fill(themeBackground, r)
	pygame.draw.lines(surface, themeForeground, 1,
		(r.topleft, r.topright, r.bottomright, r.bottomleft))
	r.left += 2
	r.top += 2
	surface.blit(img, r)

def drawScrollbar(surface, widget):
	r = Rect(widget.rect)
	surface.fill(themeWindowBck, r)
	return r

def drawListbox(surface, widget):
	r = Rect(widget.rect)
	surface.fill(widget.background or themeBackground, r)
	return r

def drawCursor(surface, pos):
	surface.fill((0xff, 0xff, 0xff), (pos, (2, 2)))

def drawProgressBar(surface, widget):
	foreground = widget.foreground or themeForeground
	r = getDRect(widget.rect)
	# frame
	surface.fill(themeBackground, r)
	pygame.draw.lines(surface, themeForeground, 1,
		(r.topleft, r.topright, r.bottomright, r.bottomleft))
	r.top += 2
	r.left += 2
	r.height -= 3
	r.width -= 3
	perc = float(widget.value - widget.min) / (widget.max - widget.min)
	if r.width > r.height:
		# horizontal
		r.width = int(r.width * perc)
	else:
		# vertical
		r.top = r.bottom - int(r.height * perc)
	surface.fill(themeHighlightbck, r)

def drawText(surface, widget):
	oldClip = surface.get_clip()
	surface.set_clip(widget.rect)
	foreground = widget.foreground or themeForeground
	background = widget.background or themeBackground
	font = widget.font or 'normal'
	r = getDRect(widget.rect)
	surface.fill(background, r)
	# split wo
	line = 1
	x = r.left
	y = r.top
	space = getTextSize(font, ' ')[0]
	row = 0
	for para in widget.text:
		if row < widget.offsetRow:
			row += 1
			continue
		column = 0
		for word in para.split(' '):
			img = renderText(font, word, 1, foreground)
			newX = x + img.get_width()
			if newX > r.right:
				x = r.left
				newX = x + img.get_width()
				y += img.get_height()
				if y > r.bottom:
					surface.set_clip(oldClip)
					return
			surface.blit(img, (x, y))
			newColumn = column + len(word) + 1
			if widget.editable and row == widget.cursorRow and widget.focused and \
				widget.app.cursorOn and column <= widget.cursorColumn and \
				newColumn > widget.cursorColumn:
				#@print "CURSOR DRAW", widget.cursorRow, widget.cursorColumn
				# draw cursor
				offset = getTextSize(font, word[:widget.cursorColumn - column])
				cX = offset[0] + x
				pygame.draw.line(surface, foreground, (cX, y), (cX, y + img.get_height()), 1)
			# update position and current column
			x = newX + space
			column = newColumn
		x = r.left
		y += img.get_height()
		row += 1
		if y > r.bottom:
			surface.set_clip(oldClip)
			return
	surface.set_clip(oldClip)

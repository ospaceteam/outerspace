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

import pygame
from pygame.locals import *
from Const import *
from Fonts import *
import os, os.path, sys, ConfigParser
from ige import log
import time

try:
	import _winreg
except ImportError:
	pass

skinDir = file = os.path.join(os.path.dirname(sys.modules[__name__].__file__), "DefaultSkin")
config = None
boxes = {}
sounds = {}
gridParams = None
soundEnabled = True
soundVolume = True
musicEnabled = True
musicVolume = True
themeMusic = None

class Box:
	"""Holds all boxed graphics"""
	pass

def init():
	global themeMusic
	try:
		themeMusic = config.get("general","music")
	except ConfigParser.Error:
		themeMusic = None
	pass
	#setSkin(skinDir)

def initMixer():
	global soundEnabled
	global musicEnabled
	if (soundEnabled == False) and (musicEnabled == False):
		pygame.mixer.init(44100, -16, 2, 4096)
		
def closeMixer():
	global soundEnabled
	global musicEnabled
	if (soundEnabled == False) and (musicEnabled == False):
		pygame.mixer.quit()
		
def enableSound(enable):
    global soundEnabled
    if (enable == True) :
    	initMixer()
    soundEnabled = enable
    if (enable == False) :
    	closeMixer()

def setVolume(volume):
    global soundVolume
    soundVolume = volume

def enableMusic(enable):
 	global musicEnabled
 	if (enable == True) :
 		initMixer()
 	else:
 		closeMixer()
	musicEnabled = enable
	if musicEnabled == True:
		loadMusic(None)
		playMusic()
	else:
		stopMusic()
		time.sleep(1)
		closeMixer()

def setMusicVolume(volume):
	global musicVolume 
	global musicEnabled
	musicVolume = volume
	try:
		if musicEnabled :
			pygame.mixer.music.set_volume(volume)
	except:
		log.warning("Cannot set music volume")

def setSkin(directory = skinDir):
	global skinDir, config, gridParams
	skinDir = directory
	# load skin specification
	config = ConfigParser.ConfigParser()
	config.read(os.path.join(skinDir, "config.ini"))
	# grid
	w, h = config.get("general", "grid").split(",")
	gridParams = (int(w), int(h))
	# basic colors
	global themeForeground, themeBackground, themeTitleLine1, themeTitleLine2
	global themeHighlightbck, themeHighlightfrg, themeCritical, themeMajor
	global themeMinor, themeNone, themeDisabled
	global themeMusic
	themeForeground = hex2color(config.get("general", "foreground"))
	themeBackground = hex2color(config.get("general", "background"))
	themeTitleLine1 = hex2color(config.get("general", "line1"))
	themeTitleLine2 = hex2color(config.get("general", "line2"))
	themeHighlightbck = hex2color(config.get("general", "highlightbck"))
	themeHighlightfrg = hex2color(config.get("general", "highlightfrg"))
	themeCritical = hex2color(config.get("general", "critical"))
	themeMajor = hex2color(config.get("general", "major"))
	themeMinor = hex2color(config.get("general", "minor"))
	themeNone = hex2color(config.get("general", "none"))
	themeDisabled = hex2color(config.get("general", "disabled"))
	try:
		themeMusic = config.get("general","music")
	except ConfigParser.Error:
		themeMusic = None
	# create elements
	createFont()
	for section in config.sections():
		if section.endswith("box"):
			createBox(section)

def createFont():
	# create font
	for fontName in config.get("general", "fonts").split(","):
		section = "%s font" % fontName
		fontType = config.get(section, "type")
		log.debug("Loading font", fontName, fontType)
		if fontType == "windowsttf":
			if os.name == "nt":
				# get "Fonts" folder location
				handle = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders')
				path, valueType = _winreg.QueryValueEx(handle, 'Fonts')
				handle.Close()
				filename = os.path.join(path, config.get(section, "file"))
			else:
				continue
		elif fontType == "ttf":
			filename = config.get(section, "file")
		elif fontType == "default":
			filename = None
		# load font
		if filename == None or os.path.exists(filename):
			initFont('small', filename, config.getint(section, "small"))
			initFont('small-bold', filename, config.getint(section, "small"), bold = 1)
			initFont('normal', filename, config.getint(section, "normal"))
			initFont('normal-bold', filename, config.getint(section, "normal"), bold = 1)
			initFont('large', filename, config.getint(section, "large"))
			initFont('large-bold', filename, config.getint(section, "large"), bold = 1)
			return

def createBox(section):
	global boxes
	boxName = section[:-4]
	for option in config.options(section):
		if option.startswith("sound-"):
			createSounds(section, option)
			continue
		box = Box()
		opt = config.get(section, option).split(",")
		filename, x, y, r, b = opt[:5]
		foreground, tl, tt, tr, tb = opt[5:]
		if foreground == "-":
			box.foreground = None
		else:
			box.foreground = hex2color(foreground)
		box.cMargins = int(tl), int(tt), int(tr), int(tb)
		# graphical reprezentation
		x, y, r, b = int(x), int(y), int(r), int(b)
		box.img = pygame.image.load(os.path.join(skinDir, filename)).convert_alpha()
		w, h = box.img.get_size()
		box.margins = x, y, r, b
		box.rect = Rect(x, y, w - r, h - b)
		box.topleft = box.img.subsurface(0, 0, x, y)
		box.bottomleft = box.img.subsurface(0, h - b, x, b)
		box.topright = box.img.subsurface(w - r, 0, r, y)
		box.bottomright = box.img.subsurface(w - r, h - b, r, b)
		box.top = box.img.subsurface(x, 0, w - r - x, y)
		box.bottom = box.img.subsurface(x, h - b, w - r - x, b)
		box.left = box.img.subsurface(0, y, x, h - b - r)
		box.right = box.img.subsurface(w - r, y, r, h - b - r)
		box.center = box.img.subsurface(x, y, w - r - x, h - b - y)
		boxes["%s-%s" % (boxName, option)] = box

def createSounds(section, option):
	global sounds
	name = "%s-%s" % (section[:-4], option[6:])
	filename = os.path.join(skinDir, config.get(section, option))
	try:
		sounds[name] = {}
		sounds[name]["fname"] = filename
		if soundEnabled:
			sounds[name]["sound"] = pygame.mixer.Sound(filename)
		else:
			sounds[name]["sound"] = None
	except pygame.error:
		log.warning("Cannot create sound", name, filename)

def playSound(style):
	if soundEnabled and style in sounds:
		try:
			if sounds[style]["sound"] == None:
				filename = sounds[style]["fname"]
				sounds[style]["sound"] = pygame.mixer.Sound(filename)
			sounds[style]["sound"].set_volume(soundVolume)
			sounds[style]["sound"].play()
		except pygame.error:
			log.warning("Cannot play sound", style)

def loadMusic(file):
	if musicEnabled and pygame.mixer.music.get_busy() == False:
		global themeMusic
		if file != None:
			musicFile = "res.ext/music/" + file
		elif themeMusic != None:
			musicFile = "res.ext/music/" + themeMusic
		else:
			musicFile = "res.ext/music/riddleofsteel.ogg"
		if os.path.exists(musicFile):
			try:
				pygame.mixer.music.load(musicFile)
			except pygame.error:
				log.warning("Cannot load music ",musicFile)

def playMusic():
	if musicEnabled:
		try:
			if pygame.mixer.music.get_busy() == False:
				pygame.mixer.music.play(-1)
		except pygame.error:
			log.warning("Cannot play music")

def stopMusic():
	try:
		if pygame.mixer.music.get_busy() == True:
			 pygame.mixer.music.fadeout(1000)
	except pygame.error:
		log.warning("Cannot stop music")
	except error:
		pass

def getGridParams():
	return gridParams

def drawBox(surface, widget, style):
	box = boxes[style]
	rect = widget.rect
	l, t, r, b = box.margins
	oldClip = surface.get_clip()
	# corners
	surface.blit(box.topleft, rect.topleft)
	surface.blit(box.topright, (rect.right - r, rect.top))
	surface.blit(box.bottomleft, (rect.left, rect.bottom - b))
	surface.blit(box.bottomright, (rect.right - r, rect.bottom - b))
	# center
	surface.set_clip(rect.left + l, rect.top + t, rect.width - l - r, rect.height - t - b)
	w, h = box.center.get_size()
	for x in xrange(rect.left + l, rect.left + rect.width - r -l, w):
		for y in xrange(rect.top + t, rect.top + rect.height - t - b, h):
			surface.blit(box.center, (x, y))
	# top + bottom
	surface.set_clip(rect.left + l, rect.top, rect.width - l - r, rect.height)
	w = box.top.get_width()
	y1 = rect.top
	y2 = rect.bottom - b
	for x in xrange(rect.left + l, rect.left + rect.width - r - l, w):
			surface.blit(box.top, (x, y1))
			surface.blit(box.bottom, [x, y2])
	# left + right
	surface.set_clip(rect.left, rect.top + t, rect.width, rect.height - t - b)
	h = box.left.get_height()
	for y in xrange(rect.top + t, rect.top + rect.height - t - b + h, h):
		surface.blit(box.left, (rect.left, y))
		surface.blit(box.right, (rect.right - r, y))
	# restore
	surface.set_clip(oldClip)

def drawTextAndIcons(surface, widget, style):
	box = boxes[style]
	rect = widget.rect
	l, t, r, b = box.cMargins
	oldClip = surface.get_clip()
	rect = Rect(rect.left + l, rect.top + t, rect.width - l - r, rect.height - t - b)
	surface.set_clip(rect)
	# icons
	if widget.icons:
		for img, align in widget.icons:
			r = Rect(rect)
			if align & ALIGN_W: pass
			elif align & ALIGN_E: r.left += rect.width - img.get_width()
			else: r.left += (rect.width - img.get_width()) / 2
			if align & ALIGN_N: pass
			elif align & ALIGN_S: r.top += rect.height - img.get_height()
			else: r.top += (rect.height - img.get_height()) / 2
			surface.blit(img, r)
	# text
	if widget.text != None:
		font = widget.font or themeDefaultFont
		foreground = box.foreground or widget.foreground or themeForeground
		background = widget.background

		img = renderText(font, widget.text, 1, foreground, background)
		r = Rect(rect)
		if widget.align & ALIGN_W: pass
		elif widget.align & ALIGN_E: r.left += rect.width - img.get_width()
		else: r.left += (rect.width - img.get_width()) / 2
		if widget.align & ALIGN_N: pass
		elif widget.align & ALIGN_S: r.top += rect.height - img.get_height()
		else: r.top += (rect.height - img.get_height()) / 2
		surface.blit(img, r)
	surface.set_clip(oldClip)

def playButtonSound(widget):
	if widget.pressed:
		style = "%s-up" % (widget.style or "button")
	else:
		style = "%s-down" % (widget.style or "button")
	playSound(style)

def drawButton(surface, widget):
	if not widget.enabled:
		s2 = "disabled"
	elif widget.focused:
		s2 = "focused"
	else:
		s2 = "enabled"
	if widget.pressed:
		s3 = "down"
	else:
		s3 = "up"
	if widget.toggle:
		style = "%s-%s-%s" % (widget.style or "togglebutton", s2, s3)
	else:
		style = "%s-%s-%s" % (widget.style or "button", s2, s3)
	drawBox(surface, widget, style)
	drawTextAndIcons(surface, widget, style)
	return widget.rect

def drawCheck(surface, widget):
	if not widget.enabled:
		s2 = "disabled"
	elif widget.focused:
		s2 = "focused"
	else:
		s2 = "enabled"
	if widget.checked:
		s3 = "on"
	else:
		s3 = "off"
	style = "%s-%s-%s" % (widget.style or "check", s2, s3)
	drawBox(surface, widget, style)
	drawTextAndIcons(surface, widget, style)
	return widget.rect

def drawLabel(surface, widget, highlight = 0):
	if not widget.enabled:
		style = "%s-disabled" % (widget.style or "label")
	else:
		if highlight:
			style = "%s-highlight" % (widget.style or "label")
		else:
			style = "%s-clean" % (widget.style or "label")
	drawBox(surface, widget, style)
	drawTextAndIcons(surface, widget, style)
	return widget.rect

## utils
def hex2color(text):
	if len(text) == 8:
		return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16), int(text[6:8], 16)
	else:
		return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)

##
## OLD CODE (for compatibility only)
##

themeForeground = 0x00, 0xd0, 0x00
#themeWindowBck = 0x20, 0x30, 0x20
themeBackground = 0x20, 0x40, 0x20
themeHighlightbck = 0x40, 0x60, 0x40
themeHighlightfrg = 0x40, 0xf0, 0x40
#themeGaugecolor = 0x00, 0x80, 0x00
themeDefaultFont = 'normal'
themeBoldFont = 'normal-bold'
#themeSelectionFrg = 0x00, 0xd0, 0x00
#themeSelectionBck = 0x40, 0x80, 0x40
themeTitleLine1 = 0x30, 0x50, 0x30
themeTitleLine2 = 0x40, 0x60, 0x40
themeSliderMin = 18
themeCritical = 0xFF, 0x80, 0x80
themeMajor = 0xFF, 0xFF, 0x00
themeMinor = 0xFF, 0xFF, 0xFF
themeNone = 0xC0, 0xC0, 0xC0
themeDisabled = 0x80, 0x80, 0x80


def getDRect(rect):
	rect = Rect(rect)
	rect.left += 1
	rect.top += 0
	rect.width -= 3
	rect.height -= 2
	return rect

def drawArrowButton(surface, widget):
	if not widget.enabled:
		s2 = "disabled"
	elif widget.focused:
		s2 = "focused"
	else:
		s2 = "enabled"
	if widget.pressed:
		s3 = "down"
	else:
		s3 = "up"
	if widget.toggle:
		style = "%s-%s-%s" % (widget.style or "togglebutton", s2, s3)
	else:
		style = "%s-%s-%s" % (widget.style or "button", s2, s3)
	drawBox(surface, widget, style)
	# arrow
	fg = boxes[style].foreground or widget.foreground or themeForeground
	r = getDRect(widget.rect)
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
	pygame.draw.lines(surface, fg, 1, points)
	return widget.rect

def drawTitleButton(surface, widget):
	rect = getDRect(widget.rect)
	rect.height += 1
	rect.width += 1
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

def drawTitle(surface, widget):
	rect = getDRect(widget.rect)
	rect.height += 1
	rect.width += 1
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
	drawBox(surface, widget, "entry-enabled")
	surface.set_clip(rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# text
	if widget.showChar and widget.text:
		text = widget.showChar * len(widget.text)
	else:
		text = widget.text

	if text:
		textToCursor = text[:widget.cursorPos]
	else:
		textToCursor = ''

	textSize = getTextSize(font, text)

	r = getDRect(rect)

	# rendered text is longer than we can display
	if textSize[0] > r.width:
		text2 = textToCursor
		textToIdx = widget.cursorPos
		textFromIdx = 0
		text2Size = getTextSize(font, text2)

		if text2Size[0] > r.width:
			# if text to cursor is longer then width
			# then delete some chars
			while text2Size[0] > r.width:
				text2 = text[textFromIdx:textToIdx]
				textFromIdx += 1
				text2Size = getTextSize(font, text2)
		else:
			# if text to cursor is shorter then width
			# then add some chars
			while text2Size[0] < r.width:
				text2 = text[textFromIdx:textToIdx]
				textToIdx += 1
				text2Size = getTextSize(font, text2)

		text = text2

	img = renderText(font, text, 1, foreground)

	if widget.align & ALIGN_E:
		r.left += rect.width - img.get_width() - 2
	elif not widget.align & ALIGN_W:
		r.left += (rect.width - img.get_width()) / 2

	if widget.align & ALIGN_N:
		r.top += 2
	elif widget.align & ALIGN_S:
		r.top += rect.height - img.get_height() - 1
	else:
		r.top += (rect.height - img.get_height()) / 2

	surface.blit(img, r)

	if widget.focused and widget.app.cursorOn:
		offset = getTextSize(font, textToCursor)
		if offset[0] < r.width:
			# draw cursor in middle of displayed text
			r.move_ip(offset[0], 0)
		else:
			# draw cursor at end of drawed surface
			r.left += img.get_width()
		pygame.draw.line(surface, foreground, r.topleft, r.bottomleft, 1)

	surface.set_clip(oldClip)

def drawDecoratedWindow(surface, window):
	surface.fill(themeBackground)
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
		r.top += 1
		r.left += 1
		r.width -= 2
		r.height -= 2
		pygame.draw.lines(surface, themeTitleLine2, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
		wa.top += 2
		wa.height -= 3
		wa.left += 2
		wa.width -= 3
	return wa

def drawPlainWindow(surface, window):
	surface.fill(themeBackground)
	return surface.get_clip()

def drawScrollSlider(surface, widget):
	foreground = widget.foreground or themeForeground
	r = getDRect(widget.rect)
	r.left -= 1
	r.width += 1
	# draw frame
	surface.fill(themeBackground, r)
	pygame.draw.lines(surface, themeHighlightbck, 1,
		(r.topleft, r.topright, r.bottomright, r.bottomleft))

	# size of slider
	r.top += 2
	r.left += 2
	r.height -= 3
	r.width -= 3
	if r.width > r.height:
		# horizontal slider
		# number of items
		width = widget.max - widget.min
		# proportional size of slider
		slider = widget.shown * r.width / width
		trunc = 0
		if slider < themeSliderMin:
			# slider has lesser size then minimal size for slider
			# so we store difference between minimal slider size
			# and size, which should slider have
			trunc = themeSliderMin - slider
			# set minimal slider size
			slider = themeSliderMin
		if slider > r.width:
			# if slider is longer then drawing area, cut it
			slider = r.width

		# compute drawing position withing slider
		pos = (widget.position - widget.min) * (r.width - trunc) / width

		# set drawing area width to slider size
		r.width = slider
		# move draving area to slider position
		r.left += pos
	else:
		# vertical slider
		# number of items
		height = widget.max - widget.min
		# proportional size of slider
		slider = widget.shown * r.height / height
		trunc = 0
		if slider < themeSliderMin:
			# slider has lesser size then minimal size for slider
			# so we store difference between minimal slider size
			# and size, which should slider have
			trunc = themeSliderMin - slider
			# set minimal slider size
			slider = themeSliderMin
		if slider > r.height:
			# if slider is longer then drawing area, cut it
			slider = r.height

		# compute drawing position withing slider
		pos = (widget.position - widget.min) * (r.height - trunc) / height

		# set drawing area height to slider size
		r.height = slider
		# move draving area to slider position
		r.top += pos

	# draw slider
	surface.fill(themeHighlightbck, r)

	if widget.dragging:
		# slider is dragged by mouse
		# we are drawing lines, so we must shorten width and height
		# of slider drawing area to be 'inside' rectangle
		r.width -= 1
		r.height -= 1
		# draw lines around slider
		pygame.draw.lines(surface, themeHighlightfrg, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))

		# shorten drawing area one pixel inside
		r.left += 1
		r.top += 1
		r.width -= 2  # one pixel from left and one from right
		r.height -= 2 # one pixel from top and one from bottom
		# draw lines inside slider
		pygame.draw.lines(surface, foreground, 1,
			(r.topleft, r.topright, r.bottomright, r.bottomleft))
	else:
		pass

	# return last drawing area
	return r

def drawTooltip(surface, widget):
	rect = getDRect(widget.rect)
	foreground = widget.foreground or themeForeground
	font = widget.font or themeDefaultFont
	# text
	img = renderText(font, widget.text, 1, foreground)
	r = getDRect(rect)
	r.left += 20
	screenWidth, screenHeight = pygame.display.get_surface().get_size()
	if r.left + img.get_width() > screenWidth:
		r.left = screenWidth - img.get_width() - 6
	if r.left < 0:
		r.left = 0
	r.width = img.get_width() + 4
	r.height = img.get_height() + 4
	changed = Rect(r)
	changed.width += 1
	changed.height += 1
	surface.fill(themeBackground, r)
	pygame.draw.lines(surface, themeForeground, 1,
		(r.topleft, r.topright, r.bottomright, r.bottomleft))
	r.left += 2
	r.top += 2
	surface.blit(img, r)
	return changed

def drawScrollbar(surface, widget):
	r = Rect(widget.rect)
	surface.fill(themeBackground, r)
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
	pygame.draw.lines(surface, themeHighlightbck, 1,
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

def getTextDrawLines(widget):
	r = getDRect(widget.rect)
	img = renderText(widget.font or 'normal', ' ', 1, widget.foreground or themeForeground)
	return r.height / img.get_height()

def isTextBeyondEnd(widget, text):
	r = getDRect(widget.rect)
	size = getTextSize(widget.font or 'normal', text)
	#img = renderText(widget.font or 'normal', text, 1, widget.foreground or themeForeground)
	return size[0] >= r.right

def drawText(surface, widget):
	oldClip = surface.get_clip()
	surface.set_clip(widget.rect)
	fore = foreground = widget.foreground or themeForeground
	back = background = widget.background or themeBackground
	font = widget.font or 'normal'
	r = getDRect(widget.rect)
	drawBox(surface, widget, "entry-enabled")
	line = 0
	x = r.left
	y = r.top
	img = renderText(font, ' ', 1, foreground)
	row = 0
	for para in widget.text:
		if row < widget.offsetRow:
			row += 1
			continue
		onlyword = False
		column = 0
		charIdx = 0
		firstY = y
		for char in para:
			fore = foreground
			back = None
			if widget.selStart != None:
				# last line in multiline selection OR
				# lines between first and last line in multiline selection OR
				# first line in multiline selection OR
				# one line selection
				if (line == widget.selEnd[0] and \
					line > widget.selStart[0] and \
					column < widget.selEnd[1]) or \
					(line < widget.selEnd[0] and \
					line > widget.selStart[0]) or \
					(line == widget.selStart[0] and \
					line < widget.selEnd[0] and \
					column >= widget.selStart[1]) or \
					(widget.selStart[0] == widget.selEnd[0] and \
					widget.selStart[0] == line and \
					column >= widget.selStart[1] and \
					column < widget.selEnd[1]):
						#switch colors for foreground/background
						fore = background
						back = foreground
			else:
				back = None

			# simple hack to add word wrapping
			# get words from current drawed chat to end of paragraph
			words = para[charIdx:].split(' ')
			# compute length of rendered first word
			lastWordSize = getTextSize(font, words[0])
			# if word doesn't fit to current line,
			# move to next line
			if x + lastWordSize[0] + 10 > r.right:
				if x == r.left or onlyword: #only word on line, and still too large! Render as much as we can, then move to next line.
					onlyword = True
					if x + 10 > r.right:
						if not r.left + lastWordSize[0] + 10 > r.right: #finally, end of word
							onlyword = False
						x = r.left;
						y += lastWordSize[1]
						if y + img.get_height() > r.bottom:
							surface.set_clip(oldClip)
							return
				else:
					x = r.left;
					y += lastWordSize[1]
					if y + img.get_height() > r.bottom:
						surface.set_clip(oldClip)
						return
			# render next char
			img = renderText(font, char, 1, fore, back)
			# compute next char position
			newX = x + img.get_width()
			#if newX > r.right:
			#	x = r.left
			#	y += img.get_height()
			#	if y + img.get_height() > r.bottom:
			#		surface.set_clip(oldClip)
			#		return

			surface.blit(img, (x, y))
			column += 1
			charIdx += 1

			if widget.editable and row == widget.cursorRow and \
				widget.focused and widget.app.cursorOn and \
				column == widget.cursorColumn:
				pygame.draw.line(surface, foreground, (newX, y), (newX, y + img.get_height()), 1)

			x = newX

		# draw cursor in case of zero lenght paragraph or begining of line
		if (len(para) == 0 or widget.cursorColumn == 0) and \
			widget.editable and row == widget.cursorRow and \
			widget.focused and widget.app.cursorOn:
			pygame.draw.line(surface, foreground, (r.left, firstY), (r.left, firstY + img.get_height()), 1)

		x = r.left
		y += img.get_height()
		row += 1
		line += 1
		if y + img.get_height() > r.bottom:
			surface.set_clip(oldClip)
			return
	surface.set_clip(oldClip)

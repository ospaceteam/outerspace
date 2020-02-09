#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
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

import string
import pygame
import Const
import Fonts
import os, os.path, sys, ConfigParser
from ige import log
import time
import resources

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
    # setSkin(skinDir)

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
    global themeMinor, themeNone, themeDisabled, themeIcons
    global themeMusic
    themeForeground = hex2color(config.get("general", "foreground"))
    themeIcons = hex2color(config.get("general", "icons"))
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
            filename = resources.get(config.get(section, "file"))
        elif fontType == "default":
            filename = None
        # load font
        if filename == None or os.path.exists(filename):
            Fonts.initFont('small', filename, config.getint(section, "small"))
            Fonts.initFont('small-bold', filename, config.getint(section, "small"), bold = 1)
            Fonts.initFont('small-italic', filename, config.getint(section, "small"), italic = 1)
            Fonts.initFont('normal', filename, config.getint(section, "normal"))
            Fonts.initFont('normal-bold', filename, config.getint(section, "normal"), bold = 1)
            Fonts.initFont('normal-italic', filename, config.getint(section, "normal"), italic = 1)
            Fonts.initFont('large', filename, config.getint(section, "large"))
            Fonts.initFont('large-bold', filename, config.getint(section, "large"), bold = 1)
            Fonts.initFont('large-italic', filename, config.getint(section, "large"), italic = 1)
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
        box.rect = pygame.Rect(x, y, w - r, h - b)
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
    rect = pygame.Rect(rect.left + l, rect.top + t, rect.width - l - r, rect.height - t - b)
    surface.set_clip(rect)
    # icons
    if widget.icons:
        for img, align in widget.icons:
            r = pygame.Rect(rect)
            if align & Const.ALIGN_W:
                rect.left += img.get_width()
                rect.width -= img.get_width()
                pass
            elif align & Const.ALIGN_E:
                r.left += rect.width - img.get_width()
                rect.width -= img.get_width()
            else:
                r.left += (rect.width - img.get_width()) / 2
            if align & Const.ALIGN_N: pass
            elif align & Const.ALIGN_S: r.top += rect.height - img.get_height()
            else: r.top += (rect.height - img.get_height()) / 2
            surface.blit(img, r)
    # text
    if widget.text != None:
        font = widget.font or themeDefaultFont
        foreground = box.foreground or widget.foreground or themeForeground
        background = widget.background

        img = Fonts.renderText(font, widget.text, 1, foreground, background)
        r = pygame.Rect(rect)
        if widget.align & Const.ALIGN_W: pass
        elif widget.align & Const.ALIGN_E: r.left += rect.width - img.get_width()
        else: r.left += (rect.width - img.get_width()) / 2
        if widget.align & Const.ALIGN_N: pass
        elif widget.align & Const.ALIGN_S: r.top += rect.height - img.get_height()
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
    elif widget.highlighted and widget.enabled:
        s3 = "highlighted"
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
# themeWindowBck = 0x20, 0x30, 0x20
themeBackground = 0x20, 0x40, 0x20
themeHighlightbck = 0x40, 0x60, 0x40
themeHighlightfrg = 0x40, 0xf0, 0x40
# themeGaugecolor = 0x00, 0x80, 0x00
themeDefaultFont = 'normal'
themeBoldFont = 'normal-bold'
themeItalicFont = 'normal-italic'
# themeSelectionFrg = 0x00, 0xd0, 0x00
# themeSelectionBck = 0x40, 0x80, 0x40
themeTitleLine1 = 0x30, 0x50, 0x30
themeTitleLine2 = 0x40, 0x60, 0x40
themeSliderMin = 18
themeCritical = 0xFF, 0x80, 0x80
themeMajor = 0xFF, 0xFF, 0x00
themeMinor = 0xFF, 0xFF, 0xFF
themeNone = 0xC0, 0xC0, 0xC0
themeDisabled = 0x80, 0x80, 0x80


def getDRect(rect):
    rect = pygame.Rect(rect)
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
    if widget.direction == Const.ALIGN_N:
        points = (r.midtop, r.bottomright, r.bottomleft)
    elif widget.direction == Const.ALIGN_S:
        points = (r.midbottom, r.topleft, r.topright)
    elif widget.direction == Const.ALIGN_E:
        points = (r.midright, r.topleft, r.bottomleft)
    elif widget.direction == Const.ALIGN_W:
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
            if align & Const.ALIGN_W: r.left += 1
            elif align & Const.ALIGN_E: r.left += rect.width - img.get_width()
            else: r.left += (rect.width - img.get_width()) / 2
            if align & Const.ALIGN_N: r.top += 1
            elif align & Const.ALIGN_S: r.top += rect.height - img.get_height()
            else: r.top += (rect.height - img.get_height()) / 2
            surface.blit(img, r)
    # text
    if widget.text != None:
        if widget.pressed:
            foreground = themeHighlightfrg
        img = Fonts.renderText(font, widget.text, 1, foreground)
        r = getDRect(rect)
        if widget.align & Const.ALIGN_W: r.left += 2
        elif widget.align & Const.ALIGN_E: r.left += rect.width - img.get_width() - 1
        else: r.left += (rect.width - img.get_width()) / 2
        if widget.align & Const.ALIGN_N: r.top += 2
        elif widget.align & Const.ALIGN_S: r.top += rect.height - img.get_height() - 1
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
            if align & Const.ALIGN_W: r.left += 1
            elif align & Const.ALIGN_E: r.left += rect.width - img.get_width()
            else: r.left += (rect.width - img.get_width()) / 2
            if align & Const.ALIGN_N: r.top += 1
            elif align & Const.ALIGN_S: r.top += rect.height - img.get_height()
            else: r.top += (rect.height - img.get_height()) / 2
            surface.blit(img, r)
    # text
    if widget.text != None:
        img = Fonts.renderText(font, widget.text, 1, foreground)
        r = getDRect(rect)
        if widget.align & Const.ALIGN_W: r.left += 2
        elif widget.align & Const.ALIGN_E: r.left += rect.width - img.get_width() - 1
        else: r.left += (rect.width - img.get_width()) / 2
        if widget.align & Const.ALIGN_N: r.top += 2
        elif widget.align & Const.ALIGN_S: r.top += rect.height - img.get_height() - 1
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

    textSize = Fonts.getTextSize(font, text)

    r = getDRect(rect)

    # rendered text is longer than we can display
    if textSize[0] > r.width:
        text2 = textToCursor
        textToIdx = widget.cursorPos
        textFromIdx = 0
        text2Size = Fonts.getTextSize(font, text2)

        if text2Size[0] > r.width:
            # if text to cursor is longer then width
            # then delete some chars
            while text2Size[0] > r.width:
                text2 = text[textFromIdx:textToIdx]
                textFromIdx += 1
                text2Size = Fonts.getTextSize(font, text2)
        else:
            # if text to cursor is shorter then width
            # then add some chars
            while text2Size[0] < r.width:
                text2 = text[textFromIdx:textToIdx]
                textToIdx += 1
                text2Size = Fonts.getTextSize(font, text2)

        text = text2

    img = Fonts.renderText(font, text, 1, foreground)

    if widget.align & Const.ALIGN_E:
        r.left += rect.width - img.get_width() - 2
    elif not widget.align & Const.ALIGN_W:
        r.left += (rect.width - img.get_width()) / 2

    if widget.align & Const.ALIGN_N:
        r.top += 2
    elif widget.align & Const.ALIGN_S:
        r.top += rect.height - img.get_height() - 1
    else:
        r.top += (rect.height - img.get_height()) / 2

    surface.blit(img, r)

    if widget.focused and widget.app.cursorOn:
        offset = Fonts.getTextSize(font, textToCursor)
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
        text = Fonts.renderText(font, window.title, 1, color)
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
    # position rectangle is used only for fetching position
    pos_r = getDRect(widget.rect)

    # to know what we are dealing with, we have to render all the text first
    foreground = widget.foreground or themeForeground
    title_font = widget.font or "small"
    body_font = widget.font or themeDefaultFont
    if not body_font.endswith('-italic'):
        body_font = body_font + "-italic"

    if widget.title:
        title_img = Fonts.renderText(title_font, widget.title, 1, foreground)
        title_width = title_img.get_width()
        title_height = title_img.get_height()
        max_width = title_width
        max_height = title_height
    else:
        max_width = 0
        max_height = 0

    text_images = []
    if widget.text:
        for line in string.split(widget.text, '\n'):
            line_img = Fonts.renderText(body_font, line, 1, foreground)
            text_images += [line_img]
            max_height += line_img.get_height()
            max_width = max(max_width, line_img.get_width())

    # now we have to decide how to fit the tooltip fully into the window
    screen_width, screen_height = pygame.display.get_surface().get_size()
    envelope = 8 # so we don't overflow the screen
    pos_r.left += 20
    if pos_r.left + max_width > screen_width:
        pos_r.left = max(0, screen_width - max_width - envelope)
    if pos_r.top + max_height > screen_height:
        pos_r.top = max(0, screen_height - max_height - envelope)

    # title
    title_r = getDRect(pos_r)
    title_text_r = getDRect(title_r)
    if widget.title:
        title_text_r.width = title_width
        title_text_r.height = title_height
        # making 2 pixel free space around text
        title_text_r.top += 2
        title_text_r.left += 2
        title_r.width = title_text_r.width + 4
        title_r.height = title_text_r.height + 4
    else:
        # have to zero the widget
        title_r.width = 0
        title_r.height = 0

    # body tooltip
    body_r = getDRect(pos_r)
    if widget.text:
        body_r.top += title_r.height
    body_text_r = getDRect(body_r)
    body_height = 0
    body_width = 0
    for line_img in text_images:
        body_height += line_img.get_height()
        body_width = max(body_width, line_img.get_width())
    body_text_r.height = body_height
    body_text_r.width = body_width
    # making 2 pixel free space around text
    body_text_r.top += 2
    body_text_r.left += 2
    body_r.width = body_text_r.width + 4
    body_r.height = body_text_r.height + 4

    # let's draw!
    # title
    if widget.title:
        surface.fill(themeBackground, title_r)
        pygame.draw.lines(surface, themeForeground, 0,
            (title_r.bottomleft, title_r.topleft, title_r.topright, title_r.bottomright))
        surface.blit(title_img, title_text_r)

    # body
    if text_images:
        surface.fill(themeBackground, body_r)
        pygame.draw.lines(surface, themeForeground, 0,
            (body_r.topright, body_r.bottomright, body_r.bottomleft, body_r.topleft))
        for img in text_images:
            surface.blit(img, body_text_r)
            body_text_r.top += img.get_height()
            body_text_r.height -= img.get_height()

    # finishing touches
    if text_images and widget.title:
        pygame.draw.line(surface, themeForeground, body_r.topright, title_r.bottomright)
    elif widget.title:
        # closing bottom of title
        pygame.draw.line(surface, themeForeground, title_r.bottomleft, title_r.bottomright)
    elif text_images:
        # closing top of body
        pygame.draw.line(surface, themeForeground, body_r.topleft, body_r.topright)


    # there is probably bug in pygameui, having one pixel off evaluation of rects
    title_r.height += 1
    title_r.width += 1
    body_r.width += 1
    body_r.height += 1

    return title_r, body_r

def drawScrollbar(surface, widget):
    r = pygame.Rect(widget.rect)
    surface.fill(themeBackground, r)
    return r

def drawListbox(surface, widget):
    r = pygame.Rect(widget.rect)
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
    img = Fonts.renderText(widget.font or 'normal', ' ', 1, widget.foreground or themeForeground)
    return r.height / img.get_height()

def isTextBeyondEnd(widget, text):
    r = getDRect(widget.rect)
    size = Fonts.getTextSize(widget.font or 'normal', text)
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
    img = Fonts.renderText(font, ' ', 1, foreground)
    row = 0
    for para in widget.text:
        if row < widget.offsetRow:
            row += 1
            continue
        onlyword = False
        column = 0
        charIdx = 0
        firstY = y
        previous_width = 0
        for char in para:
            fore = foreground
            back = None
            if widget.selection and widget.selection.first <= (row, column) < widget.selection.last:
                # switch colors for foreground/background
                fore = background
                back = foreground

            # simple hack to add word wrapping
            # get words from the current char to end of paragraph
            words = para[charIdx:].split(' ')
            # compute length of rendered first word
            remainingWordSize = Fonts.getTextSize(font, words[0])
            # if word doesn't fit to current line,
            # move to next line
            if x + remainingWordSize[0] + 10 > r.right:
                if x == (r.left + previous_width) or onlyword:  # only word on line, and still too large! Render as much as we can, then move to next line.
                    onlyword = True
                    if x + 10 > r.right:
                        if not r.left + remainingWordSize[0] + 10 > r.right:  # finally, end of word
                            onlyword = False
                        x = r.left;
                        y += remainingWordSize[1]
                        if y + img.get_height() > r.bottom:
                            surface.set_clip(oldClip)
                            return
                else:
                    x = r.left;
                    y += remainingWordSize[1]
                    if y + img.get_height() > r.bottom:
                        surface.set_clip(oldClip)
                        return
            # render next char
            img = Fonts.renderText(font, char, 1, fore, back)
            # compute next char position
            previous_width = img.get_width()
            newX = x + previous_width

            surface.blit(img, (x, y))
            column += 1
            charIdx += 1

            if widget.editable and row == widget.cursorRow and \
                widget.focused and widget.app.cursorOn and \
                column == widget.cursorColumn:
                pygame.draw.line(surface, foreground, (newX, y), (newX, y + img.get_height()), 1)

            x = newX

        # draw cursor in case of zero length paragraph or begining of line
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

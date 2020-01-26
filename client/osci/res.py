#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import bisect
import glob
import math
import os
import re

import gdata, client
import pygame, pygame.image
from osci import gdata
import ige.ospace.Const as Const
from ige.ospace import Rules
from ige import log

import resources

whiteShift = 80000
redShift = 90000

smallStarImgs = None
techImgs = None
bigStarImgs = None
planetImgs = None
planetImgCnt = None
buttonImgs = None
cmdInProgressImg = None
loginLogoImg = None
structProblemImg = None
structOffImg = None
icons = {}
ui_icons = {}

def initialize():
    # needed for progress dlg
    global loginLogoImg
    loginLogoImg = pygame.image.load(resources.get('logo-login.png')).convert_alpha()


def updateProgress(curr, progress_dlg):
    if not progress_dlg: return
    if curr % 30 == 0:
        periods = '.' * (curr / 30 % 4)
        progress_dlg.setProgress(_('Loading resources' + periods), curr)


def loadResources(progress_dlg=None):
    curr = 0
    max = len(glob.glob(resources.get('galaxy/*.png'))) \
        + len(glob.glob(resources.get('techs/*.png'))) \
        + len(glob.glob(resources.get('system/*.png'))) \
        + len(glob.glob(resources.get('icons/*.png'))) \
        + len(glob.glob(resources.get('buttons/*.png')))
    if progress_dlg:
        progress_dlg.display(_('Loading resources'), 0, max)
    # load star imgs
    global smallStarImgs
    smallStarImgs = {}
    for filename in glob.glob(resources.get('galaxy/star_*.png')):
        name = re.search("star_([^.]+).png", filename).group(1)
        smallStarImgs[name] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # load tech imgs
    global techImgs
    techImgs = {}
    white = pygame.Surface((37, 37))
    white.fill((255, 255, 255))
    white.set_alpha(64)
    red = pygame.Surface((37, 37))
    red.fill((255, 0, 0))
    red.set_alpha(64)
    for filename in glob.glob(resources.get('techs/????.png')):
        name = os.path.splitext(os.path.basename(filename))[0]
        imgID = int(name)
        techImgs[imgID] = pygame.image.load(filename).convert_alpha()
        copyImg = techImgs[imgID].convert_alpha()
        copyImg.blit(white, (0, 0))
        techImgs[imgID + whiteShift] = copyImg
        copyImg = techImgs[imgID].convert_alpha()
        copyImg.blit(red, (0, 0))
        techImgs[imgID + redShift] = copyImg
        curr += 1
        updateProgress(curr, progress_dlg)
    # load big star imgs
    global bigStarImgs
    bigStarImgs = {}
    for filename in glob.glob(resources.get('system/star_*.png')):
        name = re.search("star_([^.]+).png", filename).group(1)
        bigStarImgs[name] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # load planet images
    global planetImgs
    global planetImgCnt
    planetImgs = {}
    planetImgCnt = {}
    for filename in glob.glob(resources.get('system/planet_*.png')):
        matchobj = re.search("planet_((.)[^.]+).png", filename)
        name = matchobj.group(1)
        pltype = matchobj.group(2)
        if pltype in planetImgCnt:
            planetImgCnt[pltype] += 1
        else:
            planetImgCnt[pltype] = 1
        planetImgs[name] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # load ship imgs
    global shipImgs
    shipImgs = {}
    for filename in glob.glob(resources.get('ships/??.png')):
        name = os.path.splitext(os.path.basename(filename))[0]
        shipImgs[int(name)] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # load star imgs
    global icons
    icons = {}
    for filename in glob.glob(resources.get('icons/[!ui_]*.png')):
        name = os.path.splitext(os.path.basename(filename))[0]
        icons[name] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # load UI icons
    global ui_icons
    ui_icons = {}
    for filename in glob.glob(resources.get('icons/ui_*.png')):
        name = os.path.splitext(os.path.basename(filename))[0]
        ui_icons[name] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # load buttons
    global buttonImgs
    buttonImgs = {}
    for filename in glob.glob(resources.get('buttons/*.png')):
        name = os.path.splitext(os.path.basename(filename))[0]
        buttonImgs[name] = pygame.image.load(filename).convert_alpha()
        curr += 1
        updateProgress(curr, progress_dlg)
    # other icons
    global cmdInProgressImg
    cmdInProgressImg = pygame.image.load(resources.get('cmdInProgress.png')).convert_alpha()
    global structProblemImg
    structProblemImg = pygame.image.load(resources.get('struct_problem.png')).convert_alpha()
    global structOffImg
    structOffImg = pygame.image.load(resources.get('struct_off.png')).convert_alpha()


def prepareUIIcons(color):
    for image in ui_icons.values():
        image.fill((0, 0, 0, 255), None, pygame.BLEND_RGBA_MULT)
        image.fill(color[0:3] + (0, ), None, pygame.BLEND_RGBA_ADD)


def getUIIcon(icon_name):
    return ui_icons["ui_" + str(icon_name)]


def getTechImg(techID):
    return techImgs.get(techID, techImgs[0])


def getShipImg(combatClass, isMilitary):
    return shipImgs.get(int(combatClass) * 10 + int(isMilitary), shipImgs[99])


def getSmallStarImg(name):
    return smallStarImgs[name]


def getBigStarImg(name):
    return bigStarImgs[name]


def getPlanetImg(pltype, plid):
    global planetImgCnt
    name = '%s%d' % (pltype, plid % planetImgCnt[pltype])
    return planetImgs[name]


def getButton(name, state):
    if state:
        name = "%s_%s" % (name, 'active')
    else:
        name = "%s_%s" % (name, 'inactive')
    return buttonImgs[name]


def getUnknownName():
    return _('[Unknown]')


def getNA():
    return _('N/A')


def getSystemOverviewProblemColor(owner, problem):
    if problem:
        return gdata.sevColors[gdata.CRI]
    else:
        return getPlayerColor(owner)


def getFFColorCode(relationship):
    if relationship == Const.REL_UNDEF:
        return (0xc0, 0xc0, 0xc0)
    if relationship == Const.REL_UNITY:
        return (0x00, 0xff, 0x00)
    relColors = [(0xff, 0x80, 0x80),
                 (0xff, 0x90, 0x01),
                 (0xff, 0xff, 0x00),
                 (0xb0, 0xb0, 0xff),
                 (0x80, 0xff, 0xff)]
    return relColors[bisect.bisect(Const.REL_BOUNDARIES, relationship)]


def getHabitabilityColorCode(value):
    if value < 0:
        return (0xff, 0x00, 0xff)
    colorCodes = [(255, 5 * value, 0),  # end 255, 125, 0
                  (255 - 2 * (value - 25), 125 + 2 * (value - 25), 0),  # end 155, 225, 0
                  (155 - 3 * (value - 75), 225, 0),  # end 5, 225, 0
                  (0, 255, 2 * (value - 125)),  # end 0, 225, 250
                  (0, 255, 255)]
    boundaries = [25, 75, 125, 200]
    return colorCodes[bisect.bisect(boundaries, value)]


def getPirateColonyColorCode(pirate):
    if pirate is False:
        return (0xc0, 0xc0, 0xc0)
    elif pirate == 0:
        return (0xff, 0x00, 0xff)
    else:
        # rest is the same as Habitability
        return getHabitabilityColorCode(pirate)

def getFameColorCode(fame):
    if fame > 0 and fame < 200:
        # log.debug(fame, (0xff, 255 - int(255*(fame/200)), 0x00))
        return (0xff, 255 - int(255 * (fame / 200.0)), 0x00)
    if fame == 200:
        return (0xff, 0x00, 0xff)  # pirate colony
    return (0xc0, 0xc0, 0xc0)


def getMineralColorCode(minerals):
    if minerals >= 0:
        # use min, since it we occasionally get 201+ mineral levels,
        # but it is so rare that we can ignore it for colors.
        return (0xff, max(0, min(255, 255 - int(255 * (minerals / 200.0)))), 0x0)
    return (0xc0, 0xc0, 0xc0)


def getSlotColorCode(slots):
    if slots > 20:
        # in case sometime in the future we have larger worlds available
        return (0x0, 0xFF, min(255, (slots - 20) * 10))
    if slots > 0:
        return (int(255 * (slots / 20.0)), 255 - int(255 * (slots / 20.0)), 0x0)
    return (0xc0, 0xc0, 0xc0)


def getSlotSystemColorCode(slots, planets):
    if planets > 0:
        slots = int(float(slots) / planets)
        if slots > 20:
            # in case sometime in the future we have larger worlds available
            return (0x0, 0xFF, min(255, (slots - 20) * 10))
        if slots > 0:
            return (int(255 * (slots / 20.0)), 255 - int(255 * (slots / 20.0)), 0x0)
        return (0xc0, 0xc0, 0xc0)
    else:
        return (0xc0, 0xc0, 0xc0)


def getStargateColorCode(accel):
    accel = accel * 100 - 100
    colorCodes = [(0xc0, 0xc0, 0xc0),
                  (0xff, 0xff, 0x00),
                  (0xff, 0xc0, 0x00),
                  (0xff, 0x60, 0x00),
                  (0xff, 0x00, 0x00),
                  (0xff, 0x00, 0x80),
                  (0xff, 0x00, 0xff)]
    boundaries = [1, 50, 150, 250, 350, 450]
    return colorCodes[bisect.bisect(boundaries, accel)]


def getDockColorCode(refuel, upgrades):
    # refuel is based on best dock; upgrades are based on sum of all docks
    # refuel range: 0...6
    # upgrade range: 0...100 (cap 100)
    if (refuel > 1 and upgrades > 0) or (refuel > 2):
        # refuel > 2 for other player docks since they always read upgrades of 0
        # this probably should be corrected for allies
        refuelScale = max(0, min(1, (refuel - 1) / 5.0))
        upgradeScale = max(0, min(1, upgrades / 50))
        return (0xFF, int(refuelScale * (1 - upgradeScale) * 255), int(refuelScale * (upgradeScale) * 255))
    if refuel > 0:
        refuelScale = max(0, min(1, refuel / 2.0))
        return (0x00, 100 + 100 * int(refuelScale), 100 + 100 * int(refuelScale))  # cyan
    return (0xc0, 0xc0, 0xc0)


def getMoraleColors(morale):
    if morale >= 0:
        return (255 - int(255 * (morale / 100.0)), int(255 * (morale / 100.0)), 0x0)
    return (0xc0, 0xc0, 0xc0)


def getPlayerColor(owner, onlyDiplo = False):
    if owner == Const.OID_NONE:
        return getFFColorCode(Const.REL_UNDEF)
    if not onlyDiplo:
        if gdata.config.defaults.highlights == 'yes':
            if gdata.playersHighlightColors.has_key(owner):
                return gdata.playersHighlightColors[owner]
    rel = min(Const.REL_UNDEF, client.getRelationTo(owner))
    return getFFColorCode(rel)


def getControlColor(owner, onlyDiplo = False):
    if owner == Const.OID_NONE:
        return False
    if not onlyDiplo:
        if gdata.config.defaults.highlights == 'yes':
            if gdata.playersHighlightColors.has_key(owner):
                return fadeDarkColor(gdata.playersHighlightColors[owner])
    rel = min(Const.REL_UNDEF, client.getRelationTo(owner))
    return fadeDarkColor(getFFColorCode(rel))


def getGateLineWidth(owner):
    if owner == Const.OID_NONE:
        return 1
    rel = min(Const.REL_UNDEF, client.getRelationTo(owner))
    if rel == 1250:
        return 2
    return 1


def getStarmapWidgetPlanetColor(ownerid, bio, mineral, slot,
                                stargate, dockfuel, dockupgrade, fame,
                                stratres, morale, pirate=False):
    colors = {}
    for datatype in gdata.OVERLAY_TYPES:
        colors[datatype] = getStarmapWidgetPlanetColorPerDatatype(datatype, ownerid, bio, mineral, slot,
                                                                  stargate, dockfuel, dockupgrade, fame,
                                                                  stratres, morale, pirate)
    return colors


def getStarmapWidgetSystemColor(ownerid, bio, mineral, slot,
                                num_planets, stargate, dockfuel, dockupgrade, fame,
                                stratres, morale, pirate=False):
    # systems follow the same logic of the planets
    colors = getStarmapWidgetPlanetColor(ownerid, bio, mineral, slot,
                                         stargate, dockfuel, dockupgrade, fame,
                                         stratres, morale, pirate)
    # system has only one difference, which we have to override
    colors[gdata.OVERLAY_SLOT] = getSlotSystemColorCode(slot, num_planets)
    return colors


def getStarmapWidgetPlanetColorPerDatatype(datatype, ownerid, bio, mineral, slot,
                                           stargate, dockfuel, dockupgrade, fame,
                                           stratres, morale, pirate):
    if (datatype == gdata.OVERLAY_OWNER):
        return getPlayerColor(ownerid)
    if (datatype == gdata.OVERLAY_DIPLO):
        return getPlayerColor(ownerid, True)
    if (datatype == gdata.OVERLAY_BIO):
        return getHabitabilityColorCode(bio)
    if (datatype == gdata.OVERLAY_MIN):
        return getMineralColorCode(mineral)
    if (datatype == gdata.OVERLAY_SLOT):
        return getSlotColorCode(slot)
    if (datatype == gdata.OVERLAY_STARGATE):
        return getStargateColorCode(stargate)
    if (datatype == gdata.OVERLAY_DOCK):
        return getDockColorCode(dockfuel, dockupgrade)
    if (datatype == gdata.OVERLAY_FAME):
        return getFameColorCode(fame)
    if (datatype == gdata.OVERLAY_PIRATECOLONYCOST):
        return getPirateColonyColorCode(pirate)
    if (datatype == gdata.OVERLAY_MORALE):
        return getMoraleColors(morale)
    return getPlayerColor(ownerid)  # default


def fadeColor(triplet):
    return ((triplet[0] + 0xc0) / 2, (triplet[1] + 0xc0) / 2, (triplet[2] + 0xc0) / 2)


def fadeDarkColor(triplet):
    return ((triplet[0] + 0x00 * 2) / 3, (triplet[1] + 0x00 * 2) / 3, (triplet[2] + 0x00 * 2) / 3)


def formatTime(time, separator=':'):
    time = int(math.ceil(time))
    sign = ''
    if time < 0:
        time = - time
        sign = '-'
    days = time / Rules.turnsPerDay
    hours = time % Rules.turnsPerDay
    return '%s%d%s%02d' % (sign, days, separator, hours)


def formatBE(b, e):
    return '%d / %d' % (b, e)


def globalQueueName(index):
    return ['Default', 'Red', 'Blue', 'Yellow', 'Violet'][index]

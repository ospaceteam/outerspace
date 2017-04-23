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

import glob
import math
import os
import re

import gdata, client
import pygame, pygame.image
from osci import gdata
from ige.ospace.Const import *
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

def initialize():
    # needed for progress dlg
    global loginLogoImg
    loginLogoImg = pygame.image.load(resources.get('logo-login.png')).convert_alpha()

def loadResources():
    import dialog
    dlg = dialog.ProgressDlg(gdata.app)
    curr = 0
    max = len(glob.glob(resources.get('galaxy/*.png'))) + len(glob.glob(resources.get('techs/*.png'))) + \
        len(glob.glob(resources.get('system/*.png'))) + len(glob.glob(resources.get('icons/*.png'))) + len(glob.glob(resources.get('buttons/*.png')))
    dlg.display(_('Loading resources'), 0, max)
    # load star imgs
    global smallStarImgs
    smallStarImgs = {}
    for filename in glob.glob(resources.get('galaxy/star_*.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        name = re.search("star_([^.]+).png", filename).group(1)
        smallStarImgs[name] = pygame.image.load(filename).convert_alpha()
    # load tech imgs
    global techImgs
    techImgs = {}
    white = pygame.Surface((37,37))
    white.fill((255, 255, 255))
    white.set_alpha(64)
    red = pygame.Surface((37,37))
    red.fill((255, 0, 0))
    red.set_alpha(64)
    for filename in glob.glob(resources.get('techs/????.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        name = os.path.splitext(os.path.basename(filename))[0]
        imgID = int(name)
        techImgs[imgID] = pygame.image.load(filename).convert_alpha()
        copyImg = techImgs[imgID].convert_alpha()
        copyImg.blit(white, (0,0))
        techImgs[imgID + whiteShift] = copyImg
        copyImg = techImgs[imgID].convert_alpha()
        copyImg.blit(red, (0,0))
        techImgs[imgID + redShift] = copyImg
    # load big star imgs
    global bigStarImgs
    bigStarImgs = {}
    for filename in glob.glob(resources.get('system/star_*.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        name = re.search("star_([^.]+).png", filename).group(1)
        bigStarImgs[name] = pygame.image.load(filename).convert_alpha()
    # load planet images
    global planetImgs
    global planetImgCnt
    planetImgs = {}
    planetImgCnt = {}
    for filename in glob.glob(resources.get('system/planet_*.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        matchobj = re.search("planet_((.)[^.]+).png", filename)
        name = matchobj.group(1)
        pltype = matchobj.group(2)
        if pltype in planetImgCnt:
            planetImgCnt[pltype] += 1
        else:
            planetImgCnt[pltype] = 1
        planetImgs[name] = pygame.image.load(filename).convert_alpha()
    # load ship imgs
    global shipImgs
    shipImgs = {}
    for filename in glob.glob(resources.get('ships/??.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        name = os.path.splitext(os.path.basename(filename))[0]
        shipImgs[int(name)] = pygame.image.load(filename).convert_alpha()
    # load star imgs
    global icons
    icons = {}
    for filename in glob.glob(resources.get('icons/*.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        name = os.path.splitext(os.path.basename(filename))[0]
        icons[name] = pygame.image.load(filename).convert_alpha()
    # load buttons
    global buttonImgs
    buttonImgs = {}
    for filename in glob.glob(resources.get('buttons/*.png')):
        curr += 1
        if curr % 10 == 0:
            dlg.setProgress(_('Loading resources...'), curr)
        name = os.path.splitext(os.path.basename(filename))[0]
        buttonImgs[name] = pygame.image.load(filename).convert_alpha()
    # other icons
    global cmdInProgressImg
    cmdInProgressImg = pygame.image.load(resources.get('cmdInProgress.png')).convert_alpha()
    global structProblemImg
    structProblemImg = pygame.image.load(resources.get('struct_problem.png')).convert_alpha()
    global structOffImg
    structOffImg = pygame.image.load(resources.get('struct_off.png')).convert_alpha()
    dlg.hide()

def getTechImg(techID):
    return techImgs.get(techID, techImgs[0])

def getShipImg(combatClass, isMilitary):
    return shipImgs.get(int(combatClass) * 10 + int(isMilitary), shipImgs[99])

def getSmallStarImg(name):
    return smallStarImgs[name]

def getBigStarImg(name):
    return bigStarImgs[name]

def getPlanetImg(pltype,plid):
    global planetImgCnt
    name = '%s%d' % (pltype,plid % planetImgCnt[pltype])
    return planetImgs[name]

def getButton(name,state):
    if state:
        name = "%s_%s" % (name,'active')
    else:
        name = "%s_%s" % (name,'inactive')
    return buttonImgs[name]

def getUnknownName():
    return _('[Unknown]')

def getNA():
    return _('N/A')

def getSystemOverviewProblemColor(owner,problem):
    if problem:
        return gdata.sevColors[gdata.CRI]
    else:
        return getPlayerColor(owner)

def OLDgetFFColorCode(relationship):
    if relationship < 0:
        return (0xff, 0x00, 0xff)
    elif relationship < 500 and relationship >= 0:
        rel = relationship / 500.0
        r = 0xff
        g = int(0xff * rel)
        b = 0x00
        return (r, g, b)
    elif relationship >= 500 and relationship <= 1000:
        rel = (relationship - 500) / 500.0
        #r = int(0xff * (1 - rel))
        #g = 0xff
        #b = int(0xff * rel)
        r = 0xff
        g = 0xff
        b = int(0xff * rel)
        return (r, g, b)
    elif relationship == 1250:
        return (0x00, 0xff, 0x00)
    else:
        return (0xc0, 0xc0, 0xc0)

def getFFColorCode(relationship):
    if relationship < 0:
        return (0xff, 0x00, 0xff)
    elif relationship < REL_UNFRIENDLY_LO:
        return (0xff, 0x80, 0x80)
    elif relationship < REL_NEUTRAL_LO:
        return (0xff, 0x90, 0x01)
    elif relationship < REL_FRIENDLY_LO:
        return (0xff, 0xff, 0x00)
    elif relationship < REL_ALLY_LO:
        return (0xb0, 0xb0, 0xff)
    elif relationship <= REL_ALLY_HI:
        return (0x80, 0xff, 0xff)
    elif relationship == 1250:
        return (0x00, 0xff, 0x00)
    else:
        return (0xc0, 0xc0, 0xc0)

def getHabitabilityColorCode(bio):
    if bio < 0:
        return (0xff, 0x00, 0xff)
    if bio < 26:
        return((255),(5*bio),0x00) # end 255, 125, 0
    if bio < 76:
        return((255-2*(bio-25)),(125+2*(bio-25)),0x00) # end 155, 225, 0
    if bio < 126:
        return((155-3*(bio-75)),(225),0x00) #end 5, 225, 0
    if bio < 201:
        return(0x00,0xFF,(2*(bio-125))) #end 0, 225, 250
    if bio > 200:
        return (0x00, 0xff, 0xff)
    return (0xc0, 0xc0, 0xc0)

def getPirateColonyColorCode(pirate):
    if not pirate:
        return (0xc0, 0xc0, 0xc0)
    if pirate <= 0:
        return (0xff, 0x00, 0xff)
    if pirate < 26:
        return((255),(5*pirate),0x00) # end 255, 125, 0
    if pirate < 76:
        return((255-2*(pirate-25)),(125+2*(pirate-25)),0x00) # end 155, 225, 0
    if pirate < 126:
        return((155-3*(pirate-75)),(225),0x00) #end 5, 225, 0
    if pirate < 201:
        return(0x00,0xFF,(2*(pirate-125))) #end 0, 225, 250
    if pirate > 200:
        return (0x00, 0xff, 0xff)
    return (0xc0, 0xc0, 0xc0)

def getFameColorCode(fame):
    if fame > 0 and fame < 200:
        #log.debug(fame,(0xff,255 - int(255*(fame/200)),0x00))
        return (0xff,255 - int(255*(fame/200.0)),0x00)
    if fame == 200:
        return (0xff,0x00,0xff) #pirate colony
    return (0xc0, 0xc0, 0xc0)

def getMineralColorCode(minerals):
    if minerals >= 0:
        return (0xff,max(0,min(255,255 - int(255*(minerals/200.0)))),0x0) #use min, since it we occasionally get 201+ mineral levels, but it is so rare that we can ignore it for colors.
    return (0xc0, 0xc0, 0xc0)

def getSlotColorCode(slots):
    if slots > 20:
        return (0x0,0xFF,min(255,(slots-20)*10)) #in case sometime in the future we have larger worlds available
    if slots > 0:
        return (int(255*(slots/20.0)),255 - int(255*(slots/20.0)),0x0)
    return (0xc0, 0xc0, 0xc0)

def getSlotSystemColorCode(slots,planets):
    if planets > 0:
        slots = int(float(slots)/planets)
        if slots > 20:
            return (0x0,0xFF,min(255,(slots-20)*10)) #in case sometime in the future we have larger worlds available
        if slots > 0:
            return (int(255*(slots/20.0)),255 - int(255*(slots/20.0)),0x0)
        return (0xc0, 0xc0, 0xc0)
    else:
        return (0xc0, 0xc0, 0xc0)


def getStargateColorCode(accel):
    accel = accel * 100 - 100
    if accel < 1:
        return (0xc0, 0xc0, 0xc0)
    if accel < 50:
        return (0xff, 0xff, 0x00)
    if accel < 150:
        return (0xff, 0xc0, 0x00)
    if accel < 250:
        return (0xff, 0x60, 0x00)
    if accel < 350:
        return (0xff, 0x00, 0x00)
    if accel < 450:
        return (0xff, 0x00, 0x80)
    if accel > 449:
        return (0xff, 0x00, 0xff)
    return (0xc0, 0xc0, 0xc0)

def getDockColorCode(refuel,upgrades): #refuel is based on best dock; upgrades are based on sum of all docks
    #refuel range: 0...6
    #upgrade range: 0...100 (cap 100)
    if (refuel > 1 and upgrades > 0) or (refuel > 2): #refuel > 2 for other player docks since they always read upgrades of 0; this probably should be corrected for allies
        refuelScale = max(0,min(1,(refuel-1)/5.0))
        upgradeScale = max(0,min(1,upgrades/50))
        return (0xFF,int(refuelScale*(1-upgradeScale)*255),int(refuelScale*(upgradeScale)*255))
    if refuel > 0:
        refuelScale = max(0,min(1,refuel/2.0))
        return (0x00,100+100*int(refuelScale),100+100*int(refuelScale)) # cyan
    return (0xc0, 0xc0, 0xc0)

def getMoraleColors(morale):
    if morale >= 0:
        return (255-int(255*(morale/100.0)),int(255*(morale/100.0)),0x0)
    return (0xc0, 0xc0, 0xc0)

def getPlayerColor(owner, onlyDiplo = False):
    if owner == OID_NONE:
        return getFFColorCode(REL_UNDEF)
    if not onlyDiplo:
        if gdata.config.defaults.highlights == 'yes':
            if gdata.playersHighlightColors.has_key(owner):
                return gdata.playersHighlightColors[owner]
    rel = min(REL_UNDEF,client.getRelationTo(owner))
    return getFFColorCode(rel)

def getControlColor(owner, onlyDiplo = False):
    if owner == OID_NONE:
        return False
    if not onlyDiplo:
        if gdata.config.defaults.highlights == 'yes':
            if gdata.playersHighlightColors.has_key(owner):
                return fadeDarkColor(gdata.playersHighlightColors[owner])
    rel = min(REL_UNDEF,client.getRelationTo(owner))
    return fadeDarkColor(getFFColorCode(rel))

def getGateLineWidth(owner):
    if owner == OID_NONE:
        return 1
    rel = min(REL_UNDEF,client.getRelationTo(owner))
    if rel == 1250:
        return 2
    return 1

def getStarmapWidgetPlanetColor(ownerid,bio,mineral,slot,stargate,dockfuel,dockupgrade,fame,stratres,morale,pirate=False):
    colors = {}
    for datatype in gdata.OVERLAY_TYPES:
        colors[datatype] = getStarmapWidgetPlanetColorPerDatatype(datatype,ownerid,bio,mineral,slot,stargate,dockfuel,dockupgrade,fame,stratres,morale,pirate)
    return colors

def getStarmapWidgetSystemColor(ownerid,bio,mineral,slot,num_planets,stargate,dockfuel,dockupgrade,fame,stratres,morale,pirate=False):
    colors = {}
    for datatype in gdata.OVERLAY_TYPES:
        colors[datatype] = getStarmapWidgetSystemColorPerDatatype(datatype,ownerid,bio,mineral,slot,num_planets,stargate,dockfuel,dockupgrade,fame,stratres,morale,pirate)
    return colors


def getStarmapWidgetPlanetColorPerDatatype(datatype,ownerid,bio,mineral,slot,stargate,dockfuel,dockupgrade,fame,stratres,morale,pirate=False):
    if (datatype == gdata.OVERLAY_OWNER):
        return getPlayerColor(ownerid)
    if (datatype == gdata.OVERLAY_DIPLO):
        return getPlayerColor(ownerid,True)
    if (datatype == gdata.OVERLAY_BIO):
        return getHabitabilityColorCode(bio)
    if (datatype == gdata.OVERLAY_MIN):
        return getMineralColorCode(mineral)
    if (datatype == gdata.OVERLAY_SLOT):
        return getSlotColorCode(slot)
    if (datatype == gdata.OVERLAY_STARGATE):
        return getStargateColorCode(stargate)
    if (datatype == gdata.OVERLAY_DOCK):
        return getDockColorCode(dockfuel,dockupgrade)
    if (datatype == gdata.OVERLAY_FAME):
        return getFameColorCode(fame)
    if (datatype == gdata.OVERLAY_PIRATECOLONYCOST):
        return getPirateColonyColorCode(pirate)
#    if (datatype == "stratres"):
#        return getMoraleColors(stratres)
    if (datatype == gdata.OVERLAY_MORALE):
        return getMoraleColors(morale)
    return getPlayerColor(ownerid) #default


def getStarmapWidgetSystemColorPerDatatype(datatype,ownerid,bio,mineral,slot,num_planets,stargate,dockfuel,dockupgrade,fame,stratres,morale,pirate=False):
    if (datatype == gdata.OVERLAY_OWNER):
        return getPlayerColor(ownerid)
    if (datatype == gdata.OVERLAY_DIPLO):
        return getPlayerColor(ownerid,True)
    if (datatype == gdata.OVERLAY_BIO):
        return getHabitabilityColorCode(bio)
    if (datatype == gdata.OVERLAY_MIN):
        return getMineralColorCode(mineral)
    if (datatype == gdata.OVERLAY_SLOT):
        return getSlotSystemColorCode(slot,num_planets)
    if (datatype == gdata.OVERLAY_STARGATE):
        return getStargateColorCode(stargate)
    if (datatype == gdata.OVERLAY_DOCK):
        return getDockColorCode(dockfuel,dockupgrade)
    if (datatype == gdata.OVERLAY_FAME):
        return getFameColorCode(fame)
    if (datatype == gdata.OVERLAY_PIRATECOLONYCOST):
        return getPirateColonyColorCode(pirate)
#    if (datatype == "stratres"):
#        return getMoraleColors(stratres)
    if (datatype == gdata.OVERLAY_MORALE):
        return getMoraleColors(morale)
    return getPlayerColor(ownerid) #default

def fadeColor(triplet):
    return ((triplet[0]+0xc0)/2,(triplet[1]+0xc0)/2,(triplet[2]+0xc0)/2)

def fadeDarkColor(triplet):
    return ((triplet[0]+0x00*2)/3,(triplet[1]+0x00*2)/3,(triplet[2]+0x00*2)/3)

def formatTime(time,separator=':'):
    time = int(math.ceil(time))
    sign = ''
    if time < 0:
        time = - time
        sign = '-'
    days = time / 24
    hours = time % 24
    return '%s%d%s%02d' % (sign, days, separator, hours)

def formatBE(b, e):
    return '%d / %d' % (b, e)

def globalQueueName(index):
    return ['Default', 'Red', 'Blue', 'Yellow', 'Violet'][index]

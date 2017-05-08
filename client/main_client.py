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

# some default values as a workaround [midpoint]
import binascii
import os, os.path
import random
import re
import time
import sys

import pygame, pygame.image, pygame.font, pygame.time, pygame.version
import pygame.transform
from pygame.locals import *

from osci.config import Config
import osci.gdata as gdata
import ige.version
from ige import log
import osci
import resources
import osci.res



background = None
backgroundOffset = None
sponsorLogo = None
sponsorLogoOffset = None

def drawBackground():
    global background, backgroundOffset
    global sponsorLogo, sponsorLogoOffset
    if not background:
        image = random.choice([
            resources.get('bck1_1024x768.jpg'),
            resources.get('bck2_1024x768.jpg'),
            resources.get('bck3_1024x768.jpg'),
            resources.get('bck4_1024x768.jpg'),
            resources.get('bck5_1024x768.jpg'),
        ])
        background = pygame.image.load(image).convert_alpha()
        backgroundOffset = (
            (gdata.screen.get_width() - background.get_width()) / 2,
            (gdata.screen.get_height() - background.get_height()) / 2,
        )
    if not sponsorLogo:
        sponsorLogo = pygame.image.load(resources.get("sponsor_logo.png")).convert_alpha()
        sponsorLogoOffset = (
            (gdata.screen.get_width() - 5 - sponsorLogo.get_width()),
            (gdata.screen.get_height() - 5 - sponsorLogo.get_height()),
        )
    font = pygame.font.Font(resources.get('fonts/DejaVuLGCSans.ttf'), 12)
    font.set_bold(1)
    color = 0x40, 0x70, 0x40
    #
    gdata.screen.blit(background, backgroundOffset)
    gdata.screen.blit(sponsorLogo, sponsorLogoOffset)
    img = font.render(_("Server sponsored by:"), 1, (0xc0, 0xc0, 0xc0))
    gdata.screen.blit(img, (sponsorLogoOffset[0], sponsorLogoOffset[1] - img.get_height() - 2))
    # screen.fill((0x00, 0x00, 0x00))
    # OSCI version
    img = font.render(_('Outer Space %s') % ige.version.versionString, 1, color)
    gdata.screen.blit(img, (5, gdata.screen.get_height() - 4 * img.get_height() - 5))
    # Pygame version
    img = font.render(_('Pygame %s') % pygame.version.ver, 1, color)
    gdata.screen.blit(img, (5, gdata.screen.get_height() - 3 * img.get_height() - 5))
    # Python version
    img = font.render(_('Python %s') % sys.version, 1, color)
    gdata.screen.blit(img, (5, gdata.screen.get_height() - 2 * img.get_height() - 5))
    # Video driver
    w, h = pygame.display.get_surface().get_size()
    d = pygame.display.get_surface().get_bitsize()
    img = font.render(_('Video Driver: %s [%dx%dx%d]') % (pygame.display.get_driver(), w, h, d), 1, color)
    gdata.screen.blit(img, (5, gdata.screen.get_height() - 1 * img.get_height() - 5))

# update function
def update():
    if gdata.showBackground:
        drawBackground()
    rects = gdata.app.draw(gdata.screen)
    if gdata.cmdInProgress:
        img = osci.res.cmdInProgressImg
        wx, wy = gdata.screen.get_size()
        x, y = img.get_size()
        gdata.screen.blit(img, (wx - x, 0))
        rects.append(Rect(wx - x, 0, img.get_width(), img.get_height()))
    if gdata.isHWSurface:
        # paint mouse
        x, y = pygame.mouse.get_pos()
        gdata.screen.blit(cursorImg, (x - 1, y - 1))
        pygame.display.flip()
    else:
        #@log.debug("Sreen update", rects)
        pygame.display.update(rects)
    pygame.event.pump()

def runClient(options):

    # log initialization
    log.message("Starting Outer Space Client", ige.version.versionString)
    log.debug("sys.path =", sys.path)
    log.debug("os.name =", os.name)
    log.debug("sys.platform =", sys.platform)
    log.debug("os.getcwd() =", os.getcwd())
    log.debug("sys.frozen =", getattr(sys, "frozen", None))

    # create required directories
    if not os.path.exists(options.configDir):
        os.makedirs(options.configDir)

    running = 1
    first = True
    while running:
            if not first:
                    reload(osci)
            # parse configuration
            if first:
                    import osci.gdata as gdata
            else:
                    reload(gdata)
            #from ConfigParser import ConfigParser

            gdata.config = Config(os.path.join(options.configDir, options.configFilename))

            gdata.config.game.server = options.server
            gdata.config.galaxer.server = options.galaxer

            if gdata.config.client.language == None:
                    gdata.config.client.language = 'en'

            language = gdata.config.client.language

            if gdata.config.defaults.minfleetsymbolsize == None:
                    gdata.config.defaults.minfleetsymbolsize = 4

            if gdata.config.defaults.minplanetsymbolsize == None:
                    gdata.config.defaults.minplanetsymbolsize = 5

            if gdata.config.defaults.maxfleetsymbolsize == None:
                    gdata.config.defaults.maxfleetsymbolsize = 0

            if gdata.config.defaults.maxplanetsymbolsize == None:
                    gdata.config.defaults.maxplanetsymbolsize = 0

            import gettext
            log.debug('OSCI', 'Installing translation for:', language)
            if language == 'en':
                log.debug('OSCI', 'English is native - installing null translations')
                tran = gettext.NullTranslations()
            else:
                try:
                    tran = gettext.translation('OSPACE', resources.get('translations'), languages = [language])
                except IOError:
                    log.warning('OSCI', 'Cannot find catalog for', language)
                    log.message('OSCI', 'Installing null translations')
                    tran = gettext.NullTranslations()

            tran.install(unicode = 1)

            # read Highlights
            if gdata.config.defaults.colors != None:
                    for coldef in gdata.config.defaults.colors.split(' '):
                        m = re.match('(\d+):(0[xX].*?),(0[xX].*?),(0[xX].*)',coldef)
                        if m != None :
                            id = int(m.group(1))
                            red = min(int(m.group(2),16),255)
                            green = min(int(m.group(3),16),255)
                            blue = min(int(m.group(4),16),255)
                            gdata.playersHighlightColors[id] = (red,green,blue)
                        else:
                            log.warning('OSCI','Unrecognized highlight definition :',coldef)
            # read Object Keys
            if gdata.config.defaults.objectkeys != None:
                    for objectkey in gdata.config.defaults.objectkeys.split(' '):
                        m = re.match('(\d+):(\d+)',objectkey)
                        if m != None :
                            key = int(m.group(1))
                            objid = int(m.group(2))
                            gdata.objectFocus[key] = objid
                        else:
                            log.warning('OSCI','Unrecognized object key definition :',objectkey)

            #initialize pygame and prepare screen
            if (gdata.config.defaults.sound == "yes") or (gdata.config.defaults.music == "yes"):
                    pygame.mixer.pre_init(44100, -16, 2, 4096)

            os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
            os.environ['SDL_DEBUG'] = '1'
            pygame.init()

            # step by step initialization
            #pygame.display.init()
            #pygame.font.init()

            # flags = HWSURFACE | DOUBLEBUF | FULLSCREEN
            # flags = HWSURFACE | FULLSCREEN
            flags = SWSURFACE

            gdata.isHWSurface = 0

            if gdata.config.display.flags != None:
                    strFlags = gdata.config.display.flags.split(' ')
                    flags = 0
                    if 'swsurface' in strFlags: flags |= SWSURFACE
                    if 'hwsurface' in strFlags:
                        flags |= HWSURFACE
                        gdata.isHWSurface = 1
                    if 'doublebuf' in strFlags: flags |= DOUBLEBUF
                    if 'fullscreen' in strFlags: flags |= FULLSCREEN

            gdata.scrnSize = (800, 600)
            if gdata.config.display.resolution != None:
                    width, height = gdata.config.display.resolution.split('x')
                    gdata.scrnSize = (int(width), int(height))

            if gdata.config.display.depth == None:
                    # guess best depth
                    bestdepth = pygame.display.mode_ok(gdata.scrnSize, flags)
            else:
                    bestdepth = int(gdata.config.display.depth)

            # initialize screen
            screen = pygame.display.set_mode(gdata.scrnSize, flags, bestdepth)
            gdata.screen = screen
            log.debug('OSCI', 'Driver:', pygame.display.get_driver())
            log.debug('OSCI', 'Using depth:', bestdepth)
            log.debug('OSCI', 'Display info:', pygame.display.Info())

            pygame.mouse.set_visible(1)

            pygame.display.set_caption(_('Outer Space %s') % ige.version.versionString)

            # set icon
            pygame.display.set_icon(pygame.image.load(resources.get('icon48.png')).convert_alpha())

            # load cursor
            cursorImg = pygame.image.load(resources.get('cursor.png')).convert_alpha()


            pygame.event.clear()
            drawBackground()
            pygame.display.flip()

            # UI stuff
            if first:
                    import pygameui as ui
            else:
                    reload(ui)

            theme = "green"
            if gdata.config.client.theme != None:
                    theme = gdata.config.client.theme
            ui.SkinableTheme.enableMusic(gdata.config.defaults.music == "no")
            ui.SkinableTheme.enableSound(gdata.config.defaults.sound == "yes")
            ui.SkinableTheme.setSkin(os.path.join(resources.get("themes"), theme))
            ui.SkinableTheme.loadMusic(gdata.config.defaults.mymusic)
            if gdata.config.defaults.musicvolume:
                    ui.SkinableTheme.setMusicVolume(float(gdata.config.defaults.musicvolume)/ 100.0)
            if gdata.config.defaults.soundvolume:
                    ui.SkinableTheme.setVolume(float(gdata.config.defaults.soundvolume) / 100.0)

            gdata.sevColors[gdata.CRI] = (ui.SkinableTheme.themeCritical)
            gdata.sevColors[gdata.MAJ] = (ui.SkinableTheme.themeMajor)
            gdata.sevColors[gdata.MIN] = (ui.SkinableTheme.themeMinor)
            gdata.sevColors[gdata.NONE] = (ui.SkinableTheme.themeNone)
            gdata.sevColors[gdata.DISABLED] = (ui.SkinableTheme.themeDisabled)

            app = ui.Application(update, theme = ui.SkinableTheme)
            app.windowSurfaceFlags = SWSURFACE | SRCALPHA
            gdata.app = app

            # resources
            import osci.res

            osci.res.initialize()

            # load resources
            osci.res.loadResources()


            # client
            if first:
                    import osci.client, osci.handler
                    from igeclient.IClient import IClientException
            else:
                    reload(osci.client)
                    reload(osci.handler)
            osci.client.initialize(gdata.config.game.server, osci.handler, options)

            # create initial dialogs
            if first:
                    import osci.dialog
            else:
                    reload(osci.dialog)
            gdata.savePassword = gdata.config.game.lastpasswordcrypted != None

            if options.login and options.password:
                    gdata.config.game.lastlogin = options.login
                    gdata.config.game.lastpassword = options.password
                    gdata.config.game.lastpasswordcrypted = binascii.b2a_base64(options.password).strip()
                    gdata.config.game.autologin = 'yes'
                    gdata.savePassword = 'no'

            if not first:
                    gdata.config.game.autologin = 'no'




            loginDlg = osci.dialog.LoginDlg(gdata.app)
            updateDlg = osci.dialog.UpdateDlg(gdata.app)

            # event loop
            update()

            lastSave = time.clock()
            # set counter to -1 to trigger Update dialog (see "if" below)
            counter = -1
            needsRefresh = False
            session = 1
            first = False
            while running and session:
                    try:
                            counter += 1
                            if counter == 0:
                                    # display initial dialog in the very first cycle
                                    updateDlg.display(caller = loginDlg, options = options)
                            # process as many events as possible before updating
                            evt = pygame.event.wait()
                            evts = pygame.event.get()
                            evts.insert(0, evt)

                            forceKeepAlive = False
                            saveDB = False

                            for evt in evts:
                                    if evt.type == QUIT:
                                            running = 0
                                            break
                                    if evt.type == (USEREVENT + 1):
                                            if getattr(evt, 'action', None) == 'localExit':
                                                    session = 0
                                                    break
                                    if evt.type == ACTIVEEVENT:
                                            if evt.gain == 1 and evt.state == 6:
                                                    # pygame desktop window focus event
                                                    needsRefresh = True
                                    if evt.type == KEYUP and evt.key == K_F12:
                                            running = 0
                                            break
                                    if evt.type == KEYUP and evt.key == K_F9:
                                            forceKeepAlive = True
                                    evt = gdata.app.processEvent(evt)

                            if gdata.app.needsUpdate() or gdata.isHWSurface or needsRefresh:
                                    needsRefresh = False
                                    update()
                            # keep alive connection
                            osci.client.keepAlive(forceKeepAlive)

                            # save DB every 4 hours in case of a computer crash
                            # using "counter" to limit calls to time.clock() to approximately every 10-15 minutes
                            if counter > 5000:
                                    # set this to zero so we don't display Update dialog
                                    counter = 0
                                    if time.clock() - lastSave > 14400:
                                            saveDB = True
                            if saveDB:
                                    osci.client.saveDB()
                                    lastSave = time.clock();

                    except IClientException, e:
                            osci.client.reinitialize()
                            gdata.app.setStatus(e.args[0])
                            loginDlg.display(message = e.args[0])
                    except Exception, e:
                            log.warning('OSCI', 'Exception in event loop')
                            if not isinstance(e, SystemExit) and not isinstance(e, KeyboardInterrupt):
                                    log.debug("Processing exception")
                                    # handle exception
                                    import traceback, StringIO
                                    fh = StringIO.StringIO()
                                    exctype, value, tb = sys.exc_info()
                                    funcs = [entry[2] for entry in traceback.extract_tb(tb)]
                                    faultID = "%06d-%03d" % (
                                            hash("/".join(funcs)) % 1000000,
                                            traceback.extract_tb(tb)[-1][1] % 1000,
                                    )
                                    del tb
                                    # high level info
                                    print >>fh, "Exception ID:", faultID
                                    print >>fh
                                    print >>fh, "%s: %s" % (exctype, value)
                                    print >>fh
                                    print >>fh, "--- EXCEPTION DATA ---"
                                    # dump exception
                                    traceback.print_exc(file = fh)
                                    excDlg = osci.dialog.ExceptionDlg(gdata.app)
                                    excDlg.display(faultID, fh.getvalue())
                                    del excDlg # reference to the dialog holds app's intance
                                    fh.close()
                                    del fh
                            else:
                                    break

            # write configuration
            log.debug("Saving configuration.")
            # Save highlights
            hl = ""
            for playerID in gdata.playersHighlightColors.keys():
                    color = gdata.playersHighlightColors[playerID]
                    r = hex(color[0])
                    g = hex(color[1])
                    b = hex(color[2])
                    hl = "%s %s:%s,%s,%s" % (hl,playerID,r,g,b)
            gdata.config.defaults.colors = hl
            # Save objects
            of = ""
            for keyNum in gdata.objectFocus.keys():
                    objid = gdata.objectFocus[keyNum]
                    of = "%s %s:%s" % (of,keyNum,objid)
            gdata.config.defaults.objectkeys = of
            #
            if gdata.savePassword == False:
                    gdata.config.game.lastpasswordcrypted = None
            gdata.config.save()

            # logout
            osci.client.logout()

    log.debug("Shut down")
    return osci.client

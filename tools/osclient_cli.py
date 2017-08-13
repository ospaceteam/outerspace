#!/usr/bin/env python2
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

# tweak PYTHONPATH
import os
import sys

# setup system path
baseDir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(baseDir, '..', 'server', "lib"))

from igeclient.IClient import IClient
from ige.Const import OID_UNIVERSE
import pprint, traceback
from getpass import getpass
from optparse import OptionParser
import ige
from ige import log

def msgHandler(id, data):
    if id >= 0:
        print 'Message', id, data

def getPlayer(name):
    u = s.getInfo(1)
    for playerID in u.players:
        pl = s.getInfo(playerID)
        if pl.name == name:
            return pl
    return None

# parse command line arguments
parser = OptionParser(usage = "usage: %prog [options] login")
parser.add_option("-c", "--cleanup", dest = "cleanup", default = False,
    action = "store_true", help = "Cleanup server sessions")
parser.add_option("-t", "--turn", dest = "turns", default = 0,
    action = "store_const", const = 1, help = "Process one turn on server")
parser.add_option("--shutdown", dest = "shutdown", default = 0,
    action = "store_true", help = "Tells server to shutdown")
parser.add_option("--ping", dest = "ping", default = 0,
    action = "store_true", help = "Just tries to connect")
parser.add_option("--chronicler", dest = "chronicler", default = 0,
    action = "store_true", help = "Makes a picture snap of every galaxy in the game")
parser.add_option("--chronicler_dir", dest = "chronicler_dir", default = '.',
    action = "store", type = "string",  help = "Directory where to put chronicler pictures")
parser.add_option("--turns", dest = "turns", default = 0,
    action = "store", type = "int", metavar = "N", help = "Process N turns on server")
parser.add_option("--starttime", dest = "startTime", default = 0,
    action = "store_true", help = "Start time in all galaxies of the game")
parser.add_option("--adduser", dest = "addUser", nargs=4,
    metavar = "LOGIN PASSWD NICKNAME EMAIL", help = "Add new user")
parser.add_option("--newgalaxy", dest = "newGalaxy", nargs=2,
    metavar = "NAME TYPE", help = "Create new galaxy")
parser.add_option("--deletegalaxy", dest = "deleteGalaxy",
    metavar = "GALAXY_ID", help = "Delete galaxy")
parser.add_option("-b", "--backup", dest = "backup", default = None,
    action = "store", type = "string", metavar = "BASEFILENAME",
    help = "Backup server databases into BASEFILENAME-<database name>.osbackup")
parser.add_option("",  "--configdir", dest = "configDir",
    metavar = "DIRECTORY", default = os.path.join(os.path.expanduser("~"), ".outerspace"),
    help = "Override default configuration directory",)
parser.add_option("",  "--configfile", dest = "configFilename",
    metavar = "DIRECTORY", default = "admin_user.ini",
    help = "Override default configuration file (applicable only for chronicler)",)
parser.add_option("", "--game", dest = "game",
    metavar = "GAME", default = "Alpha",
    help = "Name of the game")


options, args = parser.parse_args()

#s = IClient('ospace.net:9080', None, msgHandler, 'IClient/osc')
s = IClient('localhost:9080', None, msgHandler, None, 'IClient/osc')

if len(args) != 1:
    parser.error("no login name specified")

login = args[0]

if login == "admin":
    # get admin login from <configDir>/token
    password = open(os.path.join(options.configDir, "token"), "r").read()
else:
    password = getpass("Password: ")

s.connect(login)
s.login(options.game, login, password)

if options.backup:
    s.backup(options.backup)
elif options.cleanup:
    log.debug('OSCLIENT', 'Cleaning up sessions')
    s.cleanupSessions()
elif options.turns > 0:
    s.processTurns(options.turns)
elif options.startTime:
    galaxies = s.getInfo(OID_UNIVERSE).galaxies
    for galaxyID in galaxies:
        s.enableTime(galaxyID, 1)
elif options.shutdown:
    s.shutdown()
    sys.exit()
elif options.ping:
    pass
elif options.addUser:
    login, passwd, nick, email = options.addUser
    s.createAccount(login, passwd, nick, email)
elif options.newGalaxy:
    galaxy_name, galaxy_type = options.newGalaxy
    list_of_players = []
    s.createNewSubscribedGalaxy(OID_UNIVERSE, galaxy_name, galaxy_type, list_of_players)
elif options.deleteGalaxy:
    s.delete(options.deleteGalaxy)
elif options.chronicler:
    sys.path.insert(0, os.path.join(baseDir, '..', 'client'))
    sys.path.insert(0, os.path.join(baseDir, '..', 'client', 'osci'))
    sys.path.insert(0, os.path.join(baseDir, '..', 'client-ai'))
    from osci.StarMap import StarMap
    import resources
    import osci.res
    import pygame, pygame.ftfont, pygame.freetype
    import pygameui, pygameui.SkinableTheme
    from osci.config import Config
    import osci.gdata as gdata
    import osci.client
    import ige.version
    import ai_handler
    import gettext
    import hashlib
    gettext.NullTranslations().install(unicode = 1)
    gdata.config = Config(os.path.join(options.configDir, options.configFilename))

    gdata.config.game.server = 'localhost:9080'
    gdata.config.galaxer.server = 'localhost:9081'

    gdata.config.defaults.minfleetsymbolsize = 4
    gdata.config.defaults.minplanetsymbolsize = 5
    gdata.config.defaults.maxfleetsymbolsize = 0
    gdata.config.defaults.maxplanetsymbolsize = 0

    options.heartbeat = 60
    osci.client.initialize('localhost:9080', ai_handler, options)
    osci.client.login(options.game, login, password)
    osci.client.updateDatabase()

    pygame.init()
    screen = pygame.display.set_mode((10,10))
    osci.res.initialize()
    osci.res.loadResources()
    pygameui.SkinableTheme.setSkin(os.path.join(resources.get("themes"), 'green'))
    control_modes = {}  # mutable, thus updating here will update StarMap
    control_modes['systems'] = 1
    control_modes['planets'] = 1
    control_modes['fleets'] = 1
    control_modes['civilian_fleets'] = 1
    control_modes['pirate_areas'] = 1
    control_modes['hotbuttons'] = 0
    control_modes['minimap'] = 0
    control_modes['redirects'] = 0
    control_modes['map_grid_coords'] = 1
    control_modes['map_grid'] = 1
    control_modes['scanners'] = 0
    control_modes['fleet_lines'] = 1
    control_modes['gate_systems'] = 1
    control_modes['alternative_mode'] = 1
    control_modes['control_areas'] = 1
    control_modes['pirate_dialogs'] = 0  # only for pirate, obv.

    # pick individual color for each player (needs to happen before precompute)
    gdata.config.defaults.highlights = 'yes'
    players = s.getInfo(OID_UNIVERSE).players
    for player_id in players:
        player = s.getInfo(player_id)
        osci.client.db[player_id] = player
        c_hash = hashlib.sha256(player.login.encode('utf-8')).hexdigest()[:6]
        color_code = (int(c_hash[:2], 16), int(c_hash[2:4], 16), int(c_hash[4:], 16))
        gdata.playersHighlightColors[player_id] = color_code
        # we have to explicitly pick fleets, as they are invisible for admin
        for obj in osci.client.cmdProxy.multiGetInfo(1, player.fleets[:]):
            osci.client.db[obj.oid] = obj

    painter = StarMap(control_modes)
    turn_string = osci.res.formatTime(osci.client.getTurn(), '_')
    painter.precompute()
    # we are not using default zoom - it's too much
    painter.scale = 30
    galaxies = s.getInfo(OID_UNIVERSE).galaxies
    for galaxy_id in galaxies:
        galaxy = s.getInfo(galaxy_id)
        #if galaxy.name.startswith("Single -"): continue
        painter.currX, painter.currY = galaxy.x, galaxy.y
        surface_side = (galaxy.radius + 0.5) * 2 * painter.scale
        surface = pygame.Surface((surface_side, surface_side))
        painter.rect = surface.get_rect()
        new_surf, empty, empty = painter.draw(surface)
        pic_name = galaxy.name + '.' + turn_string + '.png'
        pic_path = os.path.join(options.chronicler_dir, pic_name)
        pygame.image.save(new_surf, pic_path)

else:
    # interactive console
    from code import InteractiveConsole
    console = InteractiveConsole(locals())
    console.interact()

s.logout()

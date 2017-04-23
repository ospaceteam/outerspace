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

import os
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
parser.add_option("--turns", dest = "turns", default = 0,
    action = "store", type = "int", metavar = "N", help = "Process N turns on server")
parser.add_option("--starttime", dest = "startTime", default = 0,
    action = "store_true", help = "Start time in all galaxies of the game")
parser.add_option("--adduser", dest = "addUser", nargs=4,
    metavar = "LOGIN PASSWD NICKNAME EMAIL", help = "Add new user")
parser.add_option("-b", "--backup", dest = "backup", default = None,
    action = "store", type = "string", metavar = "BASEFILENAME",
    help = "Backup server databases into BASEFILENAME-<database name>.osbackup")
parser.add_option("",  "--configdir", dest = "configDir",
    metavar = "DIRECTORY", default = os.path.join(os.path.expanduser("~"), ".outerspace"),
    help = "Override default configuration directory",)
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
else:
    # interactive console
    from code import InteractiveConsole
    console = InteractiveConsole(locals())
    console.interact()

s.logout()

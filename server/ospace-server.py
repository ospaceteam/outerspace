#!/usr/bin/python
#
#  Copyright 2001 - 2012 Ludek Smid [http://www.ospace.net/]
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

import os
import sys

# setup system path
baseDir = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, os.path.join(baseDir, "lib"))
sys.path.insert(0, os.path.join(baseDir, "..", "client-ai"))

import atexit
import optparse

from ai_parser import AIList

parser = optparse.OptionParser()
parser.add_option("", "--configdir", dest="configDir",
    metavar="DIRECTORY",
    default="var",
    help="Override default configuration directory",
)
parser.add_option("", "--configfile", dest="configFile",
    metavar="DIRECTORY",
    default="config.ini",
    help="Override default name of configuration file",
)
parser.add_option("", "--restore", dest="restore",
    metavar="STRING",
    default=None,
    help="Restore from backup files beginning with STRING",
)
parser.add_option("", "--reset", dest="reset",
    action="store_true", default=False,
    help="Sets server to reset itself" 
)
parser.add_option("", "--upgrade", dest="upgrade",
    action="store_true", default=False,
    help="Server will undergo upgrade routine"
)
parser.add_option("", "--devel", dest="devel",
    action="store_true", default=False,
    help="Server will run in debug mode",
)

options, args = parser.parse_args()

if args:
  parser.error("No additional arguments are supported")

# legacy logger
from ige import log
log.setMessageLog(os.path.join(options.configDir, 'logs/messages.log'))
log.setErrorLog(os.path.join(options.configDir, 'logs/errors.log'))

import ige.version
log.message("Outer Space %s" % ige.version.versionStringFull)

# record my pid
pidFd = os.open(os.path.join(options.configDir, "server.pid"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
os.write(pidFd, str(os.getpid()))
# TODO: check if server.pid points to the running process

gameServer = None

# define and register exit function
def cleanup():
    """Shutdown game properly"""
    try:
        if gameServer:
            log.message('Shutting down game...')
            gameServer.shutdown()
    except:
        log.exception("Shutdown of the server failed")

    # delete my pid
    os.close(pidFd)
    os.remove(os.path.join(options.configDir, "server.pid"))
    log.message("GAME SHUT DOWN")

atexit.register(cleanup)

# startup game
import ige
import ige.RPCServer as server

# set runtime mode
ige.setRuntimeMode(not options.devel)

# create game server
from ige.GameServer import GameServer

gameServer = GameServer(os.path.join(options.configDir, options.configFile))

server.init(gameServer.clientMngr)
for game in gameServer.games:
    server.register(game)

log.message('Initialized. Starting server...')

try:
    import psyco
    psyco.full()
    log.message("Using psyco with full acceleration")
except ImportError:
    log.message("NOT using psyco")

server.start()
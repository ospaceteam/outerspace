#!/usr/bin/python
#
#  Copyright 2001 - 2010 Ludek Smid [http://www.ospace.net/]
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

import sys

# setup system path
sys.path.insert(0,"lib")
sys.path.insert(0,"../client-ai")

import os, atexit
import getopt
import optparse

from ai_parser import AIList

parser = optparse.OptionParser()
parser.add_option("",  "--configdir", dest = "configDir", 
    metavar = "DIRECTORY", 
    default = "var", 
    help = "Override default configuration directory", 
)
parser.add_option("",  "--configfile", dest = "configFile", 
    metavar = "DIRECTORY", 
    default = "config.ini", 
    help = "Override default name of configuration file", 
)
parser.add_option("",  "--restore", dest = "restore", 
    metavar = "STRING", 
    default = None, 
    help = "Restore from backup files beginning with STRING", 
)
parser.add_option("",  "--reset", dest = "reset", 
    action = "store_true", default=False,
    help = "Sets server to reset itself" 
)
parser.add_option("",  "--upgrade", dest = "upgrade", 
    action = "store_true", default=False,
    help = "Server will undergo upgrade routine"
)
parser.add_option("",  "--devel", dest = "devel", 
    action = "store_true", default=False,
    help = "Server will run in debug mode", 
)

options, args = parser.parse_args()

if args:
  parser.error("No additional arguments are supported")

#configure gc
#import gc
#gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_COLLECTABLE | gc.DEBUG_UNCOLLECTABLE |
#	gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS)


# legacy logger
from ige import log
log.setMessageLog(os.path.join(options.configDir,'logs/messages.log'))
log.setErrorLog(os.path.join(options.configDir,'logs/errors.log'))

import ige.version
log.message("Outer Space %s" % ige.version.versionStringFull)
#~ # standard logger
#~ import logging, logging.handlers
#~ log = logging.getLogger()
#~ log.setLevel(logging.DEBUG)
#~ # file handler
#~ h = logging.handlers.RotatingFileHandler(os.path.join(options.configDir,'log/server.log'), 'a', 16 * 1024 * 1024, 5)
#~ h.setLevel(logging.INFO)
#~ h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
#~ log.addHandler(h)
#~ # stdout handler (TODO: disable in productin server)
#~ h = logging.StreamHandler(sys.stdout)
#~ h.setLevel(logging.DEBUG)
#~ h.setFormatter(logging.Formatter('%(created)d %(levelname)-5s %(name)-8s %(message)s'))
#~ log.addHandler(h)


# record my pid

# pid
pidFd = os.open(os.path.join(options.configDir,"server.pid"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
os.write(pidFd, str(os.getpid()))
# TODO: check if server.pid points to the running process

game = None
msgMngr = None
clientMngr = None
issueMngr = None

# define and register exit function
def cleanup():
# shut down game
	try:
		if game:
			log.message('Shutting down game...')
			game.shutdown()

		if msgMngr:
			log.message('Shutting down message manager...')
			msgMngr.shutdown()

		if clientMngr:
			log.message('Shutting down client manager...')
			clientMngr.shutdown()

		if issueMngr:
			log.message('Shutting down issue manager...')
			issueMngr.shutdown()
	except:
		log.exception("Shutdown of the server failed")

	log.message('Shutted down')
	log.message("Cleaning up...")
	# delete my pid
	os.close(pidFd)
	os.remove(os.path.join(options.configDir,"server.pid"))

atexit.register(cleanup)

#~fh = open(pidFilename, 'w')
#~print >> fh, os.getpid()
#~fh.close()

# startup game
log.debug('Importing IGE modules...')

import ige.RPCServer as server
import ige
from ige.ClientMngr import ClientMngr
from ige.MsgMngr import MsgMngr
from ige.IssueMngr import IssueMngr
from ige.ospace.GameMngr import GameMngr

# read configuration
from ige.Config import Config
log.message("Reading configuration from", os.path.join(options.configDir, options.configFile))
config = Config(os.path.join(options.configDir, options.configFile))

# set runtime mode
ige.setRuntimeMode(not options.devel)

gameName = 'Alpha'

# open database
if config.server.dbbackend == "metakit":
    log.message("Using metakit database backend")
    from ige.MetakitDatabase import Database, DatabaseString
else:
    log.message("Using sqlite3 dabase backend")
    from ige.SQLiteDatabase import Database, DatabaseString
# set type of generated galaxies
if not config.server.newgalaxytype:
	config.server.newgalaxytype = 'Circle42P'

log.debug("Creating databases...")
gameDB = Database(os.path.join(options.configDir,"db_data"), "game_%s" % gameName, cache = 15000)
clientDB = DatabaseString(os.path.join(options.configDir,"db_data"), "accounts", cache = 100)
msgDB = DatabaseString(os.path.join(options.configDir,"db_data"), "messages", cache = 1000)

if options.restore:
	gameDB.restore("%s-game_Alpha.osbackup" % options.restore)
	clientDB.restore("%s-accounts.osbackup" % options.restore)
	# TODO: remove afer fix of the message database
	# the following code imports to the message database only valid entries
        # and forces mailbox scan
	incl = [1]
	incl.extend(gameDB[1].galaxies)
	incl.extend(gameDB[1].players)
	def include(k, l = incl):
		for i in l:
			if k.startswith("Alpha-%d-" % i) or (k == "Alpha-%d" % i):
				return True
		return False
	msgDB.restore("%s-messages.osbackup" % options.restore, include = include)
	aiList = AIList(options.configDir)
	aiList.restore("%s-ais.osbackup" % options.restore)

# initialize game
log.message('Initializing game \'%s\'...' % gameName)

log.debug("Initializing issue manager")
issueMngr = IssueMngr()
log.debug("Initializing client manager")
clientMngr = ClientMngr(clientDB, options.configDir)
log.debug("Initializing message manager")
msgMngr = MsgMngr(msgDB)

log.debug("Initializing game manager")
game = GameMngr(gameName, config, clientMngr, msgMngr, gameDB, options.configDir)

if options.reset:
	# reset game
	log.message('Resetting game \'%s\'...' % gameName)
	game.reset()
else:
	# normal operations
	game.init()

	if options.upgrade:
		game.upgrade()
		msgMngr.upgrade()

	game.start()

	server.init(clientMngr)
	server.register(game)

	server.xmlrpcPublish('clientmngr', clientMngr)
	server.xmlrpcPublish('issuemngr', issueMngr)

	log.message('Initialized. Starting server...')

	try:
		import psyco
		psyco.full()
		log.message("Using psyco with full acceleration")
	except ImportError:
		log.message("NOT using psyco")
	server.start()

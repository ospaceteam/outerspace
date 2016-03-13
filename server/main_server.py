#
#  Copyright 2001 - 2014 Ludek Smid [http://www.ospace.net/]
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

def runServer(options):
	import os
	import sys
	import time

	# setup system path
	baseDir = os.path.abspath(os.path.dirname(__file__))

	sys.path.insert(0, os.path.join(baseDir, "lib"))
	sys.path.insert(0, os.path.join(baseDir, "..", "client-ai"))
	sys.path.insert(0, os.path.join(baseDir, "data"))

	import os, atexit
	from ai_parser import AIList



	#configure gc
	#import gc
	#gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_COLLECTABLE | gc.DEBUG_UNCOLLECTABLE |
	#	gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS)


	# legacy logger
	from ige import log
	log.setMessageLog(os.path.join(options.configDir,'logs/messages.log'))
	log.setErrorLog(os.path.join(options.configDir,'logs/errors.log'))

	import ige.version
	log.message("Outer Space %s" % ige.version.versionString)
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
	pidFd = os.open(os.path.join(options.configDir,"server.pid"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
	os.write(pidFd, str(os.getpid()))
	# TODO: check if server.pid points to the running process

	game = None
	msgMngr = None
	clientMngr = None
	issueMngr = None

	# define and register exit function

	def _save():
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

	def _cleanup(pidFd):
		_save()
		# delete my pid
		os.close(pidFd)
		os.remove(os.path.join(options.configDir,"server.pid"))

	cleanup = _cleanup

	atexit.register(cleanup, pidFd)

	#~fh = open(pidFilename, 'w')
	#~print >> fh, os.getpid()
	#~fh.close()

	# startup game
	log.debug('Importing IGE modules...')

	# set runtime mode
	ige.setRuntimeMode(options.mode)

	import ige.RPCServer as server
	import ige
	from ige.ClientMngr import ClientMngr
	from ige.MsgMngr import MsgMngr
	from ige.IssueMngr import IssueMngr
	from ige.ospace.GameMngr import GameMngr

	# read configuration
	from ige.Config import Config
	log.message("Reading configuration from", os.path.join(options.configDir, options.configFilename))
	config = Config(os.path.join(options.configDir, options.configFilename))


	gameName = 'Alpha'

	# open database
	if config.server.dbbackend == "metakit":
		# Legacy database backend
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
		gameDB.restore("%s-game_%s.osbackup" % (options.restore, gameName))
		clientDB.restore("%s-accounts.osbackup" % options.restore)
		# TODO: remove afer fix of the message database
		# the following code imports to the message database only valid entries
		    # and forces mailbox scan
		incl = [1]
		incl.extend(gameDB[1].galaxies)
		incl.extend(gameDB[1].players)
		def include(k, l = incl):
			for i in l:
				if k.startswith("%s-%d-" % (gameName, i)) or (k == "%s-%d" % (gameName, i)):
					return True
			return False
		msgDB.restore("%s-messages.osbackup" % options.restore, include = include)
		aiList = AIList(options.configDir, options.gameName)
		aiList.restore("%s-ais.osbackup" % options.restore)
	metaserver = None
	if config.wordpressmetaserver.url:
		from ige.MetaServer import WordpressMetaServer
		metaserver = WordpressMetaServer(config.wordpressmetaserver.url)
		assert config.server.authmethod in ("plain", "rsa"), "Only plain and rsa authmethod supported for metaservers"

	# initialize game
	log.message('Initializing game \'%s\'...' % gameName)

	log.debug("Initializing issue manager")
	issueMngr = IssueMngr()
	log.debug("Initializing client manager")
	clientMngr = ClientMngr(clientDB, config.server.authmethod, options.configDir, metaserver)
	log.debug("Initializing message manager")
	msgMngr = MsgMngr(msgDB)
	log.debug("Initializing game manager")
	game = GameMngr(gameName, config, clientMngr, msgMngr, gameDB, options.configDir)

        # either forced reset, or uninitialized server
	if options.reset or not gameDB.keys():
		# reset game
		log.message('Resetting game \'%s\'...' % gameName)
		game.reset()

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


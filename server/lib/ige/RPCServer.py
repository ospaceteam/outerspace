#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import traceback
import time
import log
import ige
from medusa import igerpc_handler, http_server, asyncore, logger, status_handler
from medusa import filesys, default_handler, counter, producers, xmlrpc_handler

callMap = {}
objMap = {}

running = 0

## Handlers
def shutdownHandler(obj, passPhrase):
	global running
	if passPhrase == 123456:
		running = 0
		#raise asyncore.ExitNow("Shutdown Handler")
		return 1, None
	else:
		return 0, None

## IGE RPC medusa handler
class igerpc(igerpc_handler.igerpc_handler):

	def __init__(self):
		igerpc_handler.igerpc_handler.__init__(self)
		self.seriousExcCounter = counter.counter()

	def call(self, packet):
		global callMap
		global running

		try:
			params = [packet.sid]
			params.extend(packet.params)
			packet.result, packet.messages = apply(callMap[intern(packet.method)], params)
			packet.method = None
			packet.params = None
			return packet
		except ige.NoAccountException, e:
			raise e
		except ige.GameException, e:
			raise e
		except ige.SecurityException, e:
			raise e
		except ige.CreatePlayerException, e:
			raise e
		except ige.ServerStatusException, e:
			raise e
		except ige.NoSuchObjectException, e:
			raise e
		except asyncore.ExitNow, e:
			raise e
		except Exception, e:
			log.warning('Cannot complete RPC call')
			self.seriousExcCounter.increment()
			raise e

	def status (self):
		return producers.simple_producer (
			'<li>%s' % status_handler.html_repr (self)
			+ '<ul>'
			+ '  <li><b>Total Commands:</b> %s' % self.commandCounter
			+ '  <li><b>Completed:</b> %s' % self.completedCounter
			+ '  <li><b>Serious Exceptions:</b> %s' % self.seriousExcCounter
			+ '  <li><b>Total Exceptions:</b> %s' % self.exceptionsCounter
			+ '</ul>'
			)

## XML RPC medusa handler
class xmlrpc(xmlrpc_handler.xmlrpc_handler):

	IDENT = 'XML RPC Request Handler'

	def __init__(self):
		xmlrpc_handler.xmlrpc_handler.__init__(self)
		self.commandCounter = counter.counter()
		self.completedCounter = counter.counter()
		self.exceptionsCounter = counter.counter()
		self.seriousExcCounter = counter.counter()

	def call(self, method, params):
		log.debug('CALL', method, params)
		try:
			instanceName, methodName = method.split('.')
			return apply(getattr(objMap[instanceName], 'rpc_%s' % methodName), params)
			#except ige.NoAccountException, e:
			#	raise e
			#except ige.GameException, e:
			#	raise e
			#except ige.SecurityException, e:
			#	raise e
			#except ige.ServerStatusException, e:
			#	raise e
		except asyncore.ExitNow, e:
			raise e
		except Exception, e:
			log.warning('Cannot complete RPC call')
			self.seriousExcCounter.increment()
			raise e

	def status (self):
		return producers.simple_producer (
			'<li>%s' % status_handler.html_repr (self)
			+ '<ul>'
			+ '  <li><b>Total Commands:</b> %s' % self.commandCounter
			+ '  <li><b>Completed:</b> %s' % self.completedCounter
			+ '  <li><b>Serious Exceptions:</b> %s' % self.seriousExcCounter
			+ '  <li><b>Total Exceptions:</b> %s' % self.exceptionsCounter
			+ '</ul>'
			)

	def __repr__ (self):
		return '<%s at %x>' % (
			self.IDENT,
			id (self)
			)

## Public interface
def init(clientMngr):
	global callMap

	callMap['login'] = clientMngr.login
	callMap['logout'] = clientMngr.logout
	callMap['hello'] = clientMngr.hello
	callMap['createAccount'] = clientMngr.createAccount
	callMap['changePassword'] = clientMngr.changePassword
	callMap['shutdown'] = shutdownHandler
	callMap['cleanupSessions'] = clientMngr.cleanupSessions
	callMap['exportAccounts'] = clientMngr.exportAccounts

def register(game):
	global callMap

	callMap[game.gameID + '.execute'] = game.execute
	callMap[game.gameID + '.createNewPlayer'] = game.createNewPlayer
	callMap[game.gameID + '.takeOverAIPlayer'] = game.takeOverAIPlayer
	callMap[game.gameID + '.takeOverPirate'] = game.takeOverPirate
	callMap[game.gameID + '.getStartingPositions'] = game.getStartingPositions
	callMap[game.gameID + '.getTurnData'] = game.getTurnData
	callMap[game.gameID + '.turnFinished'] = game.turnFinished
	callMap[game.gameID + '.processTurn'] = game.processTurn
	callMap[game.gameID + '.backup'] = game.backup

def xmlrpcPublish(name, obj):
	objMap[name] = obj

class emptyLogger:

	def log(self, data):
		pass
		#log.debug("MEDUSA", data)

def start():
	global running

	# install signal handler for SIGTERM
	import signal

	def signalHandler(signum, frame):
		global running

		log.message("RECEIVED SIGNAL", signum)
		running = 0

	signal.signal(signal.SIGTERM, signalHandler)

	# create server
	logger = emptyLogger()
	server = http_server.http_server('', 9080, logger_object = logger)

	fsys = filesys.os_filesystem ('website')
	default = default_handler.default_handler (fsys)
	server.install_handler(default)

	handler = igerpc()
	server.install_handler(handler)

	handler = xmlrpc()
	server.install_handler(handler)

	status = status_handler.status_extension([server])
	server.install_handler(status)

	running = 1

	# get poll function
	import select
	if hasattr(select, "poll"):
		poll = asyncore.poll3
	else:
		poll = asyncore.poll

	# main loop
	try:
		while running:
			poll(timeout = 1.0)
	except KeyboardInterrupt:
		log.message("KeyboardInterrupt")
	except asyncore.ExitNow:
		log.message("ExitNow")
	except:
		traceback.print_exc()

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

import md5
import ige
from ige.IMarshal import IMarshal, IPacket
from ige import ServerStatusException, log
import httplib, urllib
import exceptions
import time
from binascii import hexlify
import threading

MSG_CMD_BEGIN = -1000
MSG_CMD_END = -1001

class IClientException(Exception):
	pass

class IClient:

	def __init__(self, server, proxy, msgHandler, idleHandler, clientIdent):
		self.clientIdent = clientIdent
		self.gameID = None
		self.server = server
		self.logged = 0
		self.sid = None
		self.httpConn = None
		self.keepAliveTime = 180
		self.proxy = proxy
		self.msgHandler = msgHandler
		self.idleHandler = idleHandler
		self.lastCommand = time.time()
		self.hostID = 'FILLMEWITHREALVALUE'
		self.statsBytesIn = 0
		self.statsBytesOut = 0
		self.lastClientVersion = None

	def connect(self, login):
		# to enable sending commands
		self.connected = 1
		# create connection
		log.debug('Connecting to the server', self.server)
		# send hello message
		log.debug('Sending hello')
		try:
			self.sid, self.challenge = self.hello(login, self.clientIdent)
		except:
			log.warning('Cannot connect to the server.')
			self.connected = 0
			raise IClientException('Cannot connect to the server.')
		log.debug(self.sid, self.challenge)

	def login(self, gameID, login, password):
		self.gameID = gameID.encode("ascii")
		# hash password with challenge
		passwd = md5.new(password + self.challenge).hexdigest()
		#@log.debug(login, password, passwd)
		try:
			apply(IProxy('login', None, self), (login, passwd, self.hostID))
		except:
			log.warning('login failed')
			return 0
		log.debug('login succeeded')
		self.logged = 1
		return 1

	def logout(self):
		self.logged = 0
		return apply(IProxy('logout', None, self), ())

	def cleanupSessions(self):
		return apply(IProxy('cleanupSessions', None, self), ())

	def reloadAccounts(self):
		return apply(IProxy('reloadAccounts', None, self), ())

	def createAccount(self, login, password, nick, email):
		return apply(IProxy('createAccount', None, self), (login, password, nick, email))

	def exportAccounts(self):
		return apply(IProxy('exportAccounts', None, self), ())

	def changePassword(self, old, new):
		return apply(IProxy('changePassword', None, self), (old, new))

	def createNewPlayer(self, galaxyID):
		return apply(IProxy('%s.createNewPlayer' % self.gameID, None, self), (galaxyID,))

	def takeOverAIPlayer(self, playerID):
		return apply(IProxy('%s.takeOverAIPlayer' % self.gameID, None, self), (playerID,))

	def takeOverPirate(self, playerID, password):
		return apply(IProxy('%s.takeOverPirate' % self.gameID, None, self), (playerID, password))

	def getStartingPositions(self):
		return apply(IProxy('%s.getStartingPositions' % self.gameID, None, self), ())

	def processTurn(self):
		return apply(IProxy('%s.processTurn' % self.gameID, None, self), ())

	def backup(self, basename):
		return apply(IProxy('%s.backup' % self.gameID, None, self), (basename,))

	def getTurnData(self):
		return apply(IProxy('%s.getTurnData' % self.gameID, None, self), ())

	def turnFinished(self):
		return apply(IProxy('%s.turnFinished' % self.gameID, None, self), ())

	def doKeepAlive(self):
		return time.time() - self.lastCommand > self.keepAliveTime and self.logged

	def keepAlive(self):
		if time.time() - self.lastCommand > self.keepAliveTime and self.logged:
			# get all messages
			self.getIntroInfo(1)

	def __nonzero__(self):
		return 1

	def __getattr__(self, name):
		if self.gameID:
			return IProxy('%s.execute' % self.gameID, name, self)
		else:
			return IProxy(name, None, self)

class ProtocolException(Exception):

	def __init__(self, url, errcode, errmsg, headers):
		self.url = url
		self.errcode = errcode
		self.errmsg = errmsg
		self.headers = headers

	def __repr__(self):
		return "<ProtocolError for %s: %s %s>" % (self.url, self.errcode, self.errmsg)

	def __str__(self):
		return '%s %s' % (self.errcode, self.errmsg)

class IProxy:

	def __init__(self, method, command, client):
		self.client = client
		self.method = method
		self.command = command
		self.marshal = IMarshal()

	def __call__(self, *args):
		if self.client.msgHandler:
			apply(self.client.msgHandler, (MSG_CMD_BEGIN, None))
		# retry 'turn in progress' and server restart situations
		retries = 10
		ok = 0
		while retries > 0:
			try:
				result = self.processCall(args)
				ok = 1
				break
			except ServerStatusException, e:
				log.warning("Cannot complete request - retrying...")
				retries -= 1
				time.sleep(1)
			# this was commented out
			except Exception, e:
				log.warning("Cannot complete request")
				if self.client.msgHandler:
					apply(self.client.msgHandler, (MSG_CMD_END, None))
				raise e
		if self.client.msgHandler:
			apply(self.client.msgHandler, (MSG_CMD_END, None))
		if ok:
			return result
		else:
			raise IClientException('Cannot send request to the server')

	def processCall(self, args):
		if not self.client.connected:
			raise IClientException('Not connected.')
		# record time of command
		self.client.lastCommand = time.time()
		# packet init
		packet = IPacket()
		packet.sid = self.client.sid
		packet.method = self.method
		if self.command:
			packet.params = [self.command]
			packet.params.extend(args)
		else:
			packet.params = args
		log.debug('calling', packet.method, packet.params)
		# encode
		# V11
		# data = self.marshal.encode(packet).encode('utf-8')
		data = self.marshal.encode(packet)
		self.client.statsBytesOut += len(data)
		#@log.debug('->', data)
		# make call
		# init connection
		if self.client.proxy:
			# use urllib
			if not self.client.httpConn:
				log.debug('Using proxy', self.client.proxy)
				self.client.httpConn = urllib.FancyURLopener({'http': self.client.proxy})
		else:
			if self.client.httpConn:
				h = self.client.httpConn
			else:
				h = httplib.HTTPConnection(self.client.server)
				self.client.httpConn = h
		try:
			if self.client.proxy:
				fh = self.client.httpConn.open('http://%s/IGERPC' % self.client.server, data)
				# use thread to read response and invoke idle handler
				# regularly
				reader = Reader(fh.read)
				reader.start()
				while reader.isAlive():
					reader.join(0.1)
					if self.client.idleHandler:
						self.client.idleHandler()
				if reader.exception:
					raise reader.exception
				else:
					rspData = reader.result
				# end of thread dispatcher
				fh.close()
			else:
				h.putrequest('POST', '/IGERPC')
				# required by HTTP/1.1
				h.putheader('Host', self.client.server)
				# required by IGE-RPC
				h.putheader("Content-Type", "text/plain")
				h.putheader("Content-Length", str(len(data)))
				h.endheaders()
				h.send(data)
				# use thread to read response and invoke idle handler
				# regularly
				reader = Reader(h.getresponse)
				reader.start()
				while reader.isAlive():
					reader.join(0.1)
					if self.client.idleHandler:
						self.client.idleHandler()
				if reader.exception:
					raise reader.exception
				else:
					response = reader.result
				# end of thread dispatcher
				if response.status != 200:
					raise ProtocolException(self.client.server + '/IGERPC',
						response.status, response.reason, response.msg)
				# use thread to read response and invoke idle handler
				# regularly
				reader = Reader(response.read)
				reader.start()
				while reader.isAlive():
					reader.join(0.1)
					if self.client.idleHandler:
						self.client.idleHandler()
				if reader.exception:
					raise reader.exception
				else:
					rspData = reader.result
				# end of thread dispatcher
		except Exception, e:
			log.warning('Cannot send request to the server')
			self.client.logged = 0
			self.client.connected = 0
			raise IClientException('Cannot send request to the server')
		#@log.debug('<-', rspData)
		# V11
		# packet = self.marshal.decode(unicode(rspData, "utf-8"))
		self.client.statsBytesIn += len(rspData)
		packet = self.marshal.decode(rspData)
		if packet.exception:
			#@log.debug('raising exception', packet.exception)
			exception = eval('%s()' % packet.exception[0])
			exception.args = packet.exception[1]
			raise exception
		# process messages in packet.messages
		if self.client.msgHandler and packet.messages:
			for message in packet.messages:
				log.debug('got message', message)
				apply(self.client.msgHandler, message)
		elif packet.messages:
			log.debug('throwing away messages', packet.messages)
		log.debug("Stats: %d B IN / %d B OUT" % (self.client.statsBytesIn, self.client.statsBytesOut))
		return packet.result

class Reader(threading.Thread):

	def __init__(self, callable):
		threading.Thread.__init__(self)
		self.callable = callable
		self.result = None
		self.exception = None

	def run(self):
		try:
			self.result = self.callable()
		except Exception, e:
			self.exception = e

import http_server, producers, asyncore
import status_handler
from counter import counter
from ige.IMarshal import IMarshal, IPacket

import string
import sys

from ige import log

class igerpc_handler:

	IDENT = 'IGE RPC Request Handler'

	def __init__(self):
		self.marshal = IMarshal()
		self.commandCounter = counter()
		self.completedCounter = counter()
		self.exceptionsCounter = counter()

	def __repr__ (self):
		return '<%s at %x>' % (
			self.IDENT,
			id (self)
			)

	def match (self, request):
		if request.uri[:7] == '/IGERPC':
			return 1
		else:
			return 0

	def handle_request (self, request):
		[path, params, query, fragment] = request.split_uri()

		if request.command in ('post', 'put'):
			request.collector = collector (self, request)
		else:
			request.error (400)

	def continue_request (self, data, request):
		# V11
		# packet = self.marshal.decode(unicode(data, 'utf-8'))
		#@log.debug("RX", len(data), "b")
		packet = self.marshal.decode(data)
		packet.clientAddr = request.channel.addr
		self.commandCounter.increment()
		try:
			# generate response
			try:
				response = self.call(packet)
				response.exception = None
				del response.clientAddr
				self.completedCounter.increment()
			except asyncore.ExitNow, e:
				raise e
			except Exception, e:
				# report exception back to client
				response = packet
				response.method = None
				response.params = None
				response.result = None
				response.messages = None
				response.exception = ('%s.%s' % (e.__class__.__module__, e.__class__.__name__), e.args)
				self.exceptionsCounter.increment()
		except asyncore.ExitNow, e:
			raise e
		except Exception, e:
			# internal error, report as HTTP server error
			request.error (500)
		else:
			# got a valid XML RPC response
			request['Content-Type'] = 'application/x-ige-packet'
			# V11
			# request.push(self.marshal.encode(response).encode('utf-8'))
			rsp = self.marshal.encode(response)
			#@log.debug("TX", len(rsp), "b")
			request.push(rsp)
			request.done()

	def call (self, packet):
		# override this method to implement RPC methods
		raise "NotYetImplemented"

	def status (self):
		return producers.simple_producer (
			'<li>%s' % status_handler.html_repr (self)
			+ '<ul>'
			+ '  <li><b>Total Commands:</b> %s' % self.commandCounter
			+ '  <li><b>Completed:</b> %s' % self.completedCounter
			+ '  <li><b>Exceptions:</b> %s' % self.exceptionsCounter
			+ '</ul>'
			)

class collector:

	"gathers input for POST and PUT requests"

	def __init__ (self, handler, request):

		self.handler = handler
		self.request = request
		self.data = ''

		# make sure there's a content-length header
		cl = request.get_header ('content-length')

		if not cl:
			request.error (411)
		else:
			cl = string.atoi (cl)
			# using a 'numeric' terminator
			self.request.channel.set_terminator (cl)

	def collect_incoming_data (self, data):
		self.data = self.data + data

	def found_terminator (self):
		# set the terminator back to the default
		self.request.channel.set_terminator ('\r\n\r\n')
		self.handler.continue_request (self.data, self.request)

if __name__ == '__main__':

	class rpc_demo (igerpc_handler):

		def call (self, packet):
			print 'IGERPC call'
			for attr in dir(packet):
				print attr, '=', getattr(packet, attr)
			packet.result = 'Hello!'
			packet.messages = ()
			return packet

	import asyncore
	import http_server

	hs = http_server.http_server ('', 8000)
	rpc = rpc_demo()
	hs.install_handler (rpc)

	asyncore.loop(timeout = 1.0)

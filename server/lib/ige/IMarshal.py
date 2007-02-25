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

from types import *
from IDataHolder import IDataHolder
import zlib, string

__all__ = ('EncodeException', 'DecodeException', 'IPacket', 'IMarshal')

class EncodeException(Exception):
	pass

class DecodeException(Exception):
	pass

class IPacket:

	def __init__(self):
		self.sid = None
		self.method = None
		self.params = None
		self.result = None
		self.messages = None
		self.exception = None
		self.clientAddr = None

	def __repr__(self):
		result = '<%s.%s %d ' % (self.__class__.__module__, self.__class__.__name__, id(self))
		for key, value in self.__dict__.items():
			result += '%s=%s, ' % (key, repr(value))
		result += '>'
		return result

class IMarshal:

	def __init__(self):
		pass

	def encode(self, data, version = "V20"):
		if version == "V11":
			return u'V11%s' % string.join(self.__encodeV11(data), '')
			# Profiling code TODO remove profiling code
			data = u'V11%s' % self.__encodeV11(data)
			stats.encBytes += len(data)
			# TODO remove zlib profiling
			stats.zipBytes += len(zlib.compress(data))
			# End of profiling code
			return data
		elif version == "V20":
			return "V20%s" % zlib.compress(pickle.dumps(data, 1))
		else:
			raise EncodeException("Cannot handle version %s." % version)

	def __encodeV11(self, data, isKey = 0):
		t = type(data)
		if t == NoneType:
			return [u'|N']
		elif t == IntType:
			return [u'|I%d' % (data,)]
		elif t == LongType:
			return [u'|G%d' % (data,)]
		elif t == FloatType:
			return [u'|F%.2f' % (data,)]
		elif t == StringType:
			# Profiling code TODO comment this code
			#if isKey:
			#	global stats
			#	stats.data[data] = stats.data.get(data, 0) + 1
			#	stats.total += 1
			#	stats.totalBytes += len(data)
			#	if stats.total % 100 == 0:
			#		saveStats()
			#	if compress.has_key(data):
			#		stats.hits += 1
			#		stats.savedBytes += len(data) - len(compress[data])
			# End of profiling code
			if compress.has_key(data):
				return [u'|C%s' % (compress[data])]
			return [u'|S%s' % (data.replace('\\','\\\\').replace('|', '\\/').replace('\n', '\\n').replace('\r', '\\r'),)]
		elif t == UnicodeType:
			return [u'|U%s' % (data.replace('\\','\\\\').replace('|', '\\/').replace('\n', '\\n').replace('\r', '\\r'),)]
		elif t == ListType:
			result = [u'|L']
			for item in data:
				result.extend(self.__encodeV11(item))
			result.append(u'|E')
			return result
		elif t == TupleType:
			result = [u'|T']
			for item in data:
				result.extend(self.__encodeV11(item))
			result.append(u'|E')
			return result
		elif t == DictType:
			result = [u'|D']
			for item in data.keys():
				result.extend(self.__encodeV11(item, 1))
				result.extend(self.__encodeV11(data[item]))
			result.append(u'|E')
			return result
		elif t == InstanceType:
			result = [u'|O']
			result.extend(self.__encodeV11('%s.%s' % (data.__class__.__module__, data.__class__.__name__), 1))
			for item in data.__dict__.keys():
				result.extend(self.__encodeV11(item, 1))
				result.extend(self.__encodeV11(data.__dict__[item]))
			result.append(u'|E')
			return result
		else:
			raise EncodeException('Cannot handle ' + repr(t))

	def decode(self, str):
		prefix = str[:3]
		if prefix == u'V11':
			self.index = 0
			list = str.split('|')
			self.list = list[1:]
			data = self.__decodeV11()
		elif prefix == u'V20':
			data = pickle.loads(zlib.decompress(str[3:]))
		else:
			raise DecodeException('Cannot handle version %s [message: %s]' % (prefix, str))
		return data

	def __decodeV11(self):
		item = self.list[self.index]
		self.index += 1
		#@print self.index,
		t = item[0]
		if t == u'N':
			#@print 'None'
			return None
		if t == u'I':
			return int(item[1:])
		if t == u'G':
			return long(item[1:])
		if t == u'F':
			return float(item[1:])
		elif t == u'S':
			#@print 'String', item[1:]
			str = item[1:]
			i = str.find('\\')
			index = 0
			result = ''
			while i > -1:
				#@print str, i,
				result += str[index:i]
				index = i + 2
				c = str[i + 1]
				if c == 'n': result += '\n'
				elif c == 'r': result += '\r'
				elif c == '/': result += '|'
				else: result += c
				#@print repr(result)
				i = str.find('\\', i + 2)
			result += str[index:]
			return result.encode('ascii')
		elif t == u'U':
			#@print 'String', item[1:]
			str = item[1:]
			i = str.find('\\')
			index = 0
			result = ''
			while i > -1:
				#@print str, i,
				result += str[index:i]
				index = i + 2
				c = str[i + 1]
				if c == 'n': result += '\n'
				elif c == 'r': result += '\r'
				elif c == '/': result += '|'
				else: result += c
				#@print repr(result)
				i = str.find('\\', i + 2)
			result += str[index:]
			return result
		elif t == u'C':
			return decompress[item[1:]]
		elif t == u'T':
			#@print 'Tuple'
			result = []
			while self.list[self.index][0] != 'E':
				result.append(self.__decodeV11())
			self.index += 1
			#@print ':=', result
			return tuple(result)
		elif t == u'L':
			#@print 'Tuple'
			result = []
			while self.list[self.index][0] != 'E':
				result.append(self.__decodeV11())
			self.index += 1
			#@print ':=', result
			return result
		elif t == u'D':
			#@print 'Dict'
			result = {}
			while self.list[self.index][0] != 'E':
				key = self.__decodeV11()
				value = self.__decodeV11()
				result[key] = value
			self.index += 1
			#@print ':=', result
			return result
		elif t == u'O':
			#@print 'Dict'
			str = self.__decodeV11()
			if str == 'ige.IMarshal.IPacket':
				result = IPacket()
			elif str == 'ige.IDataHolder.IDataHolder':
				result = IDataHolder()
			else:
				DecodeException('Unsupported class %s' % str)
			while self.list[self.index][0] != 'E':
				key = self.__decodeV11()
				value = self.__decodeV11()
				setattr(result, key ,value)
			self.index += 1
			#@print ':=', result
			return result
		else:
			raise DecodeException('Cannot handle type <%s>' % t)

# (de)compress dictionary
#try:
#	from ICompressScheme import compress
#except ImportError:
compress = {}

decompress = {}

for key, value in compress.items():
	decompress[str(value)] = key

# statistics
import cPickle as pickle

class Stats:
	def __init__(self):
		self.data = {}
		self.total = 0
		self.hits = 0
		self.totalBytes = 0
		self.savedBytes = 0
		self.encBytes = 0
		self.zipBytes = 0

# load stats TODO remove profiling code
try:
	fh = open('var/marshal.stats.data', 'rb')
	stats = pickle.load(fh)
	fh.close()
except IOError, e:
	stats = Stats()
except EOFError, e:
	stats = Stats()

def saveStats():
	print 'Saving IMarshal statistics'
	# stats
	fh = open('var/marshal.stats.data', 'wb')
	pickle.dump(stats, fh, 1)
	fh.close()
	# various data
	keys = []
	for key in stats.data.keys():
		keys.append((len(key) * stats.data[key],key))
	keys.sort()
	keys.reverse()
	fstats = open('var/marshal.stats', 'w')
	fscheme = open('var/marshal.cscheme', 'w')
	fpysrc = open('var/marshal.cscheme.py', 'w')
	print >> fpysrc, 'compress = {'
	print >> fstats, '# Summary'
	print >> fstats, '# Total strings:', stats.total
	print >> fstats, '# Compressed strings:', stats.hits
	print >> fstats, '# Uncompressed strings:', stats.total - stats.hits
	print >> fstats, '# Ratio:', stats.hits / stats.total * 100L, '%'
	print >> fstats, '# Uncompressed size:', stats.totalBytes
	print >> fstats, '# Compressed size:', stats.totalBytes - stats.savedBytes
	print >> fstats, '# Saved bytes:', stats.savedBytes
	print >> fstats, '# Ratio:', stats.savedBytes / stats.totalBytes * 100L, '%'
	print >> fstats, '# Encoded pckt bytes total:', stats.encBytes
	print >> fstats, '# Encoded pckt bytes total (no compression, est.):', stats.encBytes + stats.savedBytes
	print >> fstats, '# Ratio:', stats.encBytes / (stats.encBytes + stats.savedBytes) * 100L, '%'
	print >> fstats, '# Encoded pckt bytes total (zipped):', stats.zipBytes
	print >> fstats, '# Ratio (to compressed):', stats.zipBytes / stats.encBytes * 100L, '%'
	print >> fstats, '# Ratio (to uncompressed):', stats.zipBytes / (stats.encBytes + stats.savedBytes)* 100L , '%'
	print >> fstats, '# total bytes,number of items,string'
	index = 0
	for key in keys:
		count, name = key
		print >> fstats, '%d,%d,%s' % (count, stats.data[name], name)
		code = makeCode(index)
		# include in scheme when there is save in bytes
		if len(code) < len(name):
			print >> fscheme, code, name
			print >> fpysrc, "	'%s' : '%s'," % (name, code)
		index += 1
	print >>fpysrc, '}'
	fstats.close()
	fscheme.close()
	fpysrc.close()

codeChars = '0123456789abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def makeCode(index):
	if index < len(codeChars):
		return codeChars[index]
	elif index / len(codeChars) - 1 < len(codeChars):
		return '%s%s' % (
			codeChars[index / len(codeChars) - 1],
			codeChars[index % len(codeChars)]
		)
	else:
		return None

# testing only
if __name__ == '__main__':

	packet = IPacket()
	packet.sid = '0123456789'
	packet.method = 'test'
	packet.params = { 'name':u'Corvus', 'componentOf':1001, 'rules':[1,2], 'isA': (1,2) }
	marshal = IMarshal()

	str = marshal.encode(packet)

	print repr(str)
	print len(str)
	packet = marshal.decode(str)
	print packet.params

	import pprint
	pprint.pprint(packet.params)


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
import types

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
        if version == "V20":
            return "V20%s" % zlib.compress(pickle.dumps(data, 1))
        else:
            raise EncodeException("Cannot handle version %s." % version)

    def decode(self, str):
        prefix = str[:3]
        if prefix == u'V20':
            data = pickle.loads(zlib.decompress(str[3:]))
        else:
            raise DecodeException('Cannot handle version %s [message: %s]' % (prefix, str))
        return data

# (de)compress dictionary
#try:
#    from ICompressScheme import compress
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
# TODO change dir according to config file
try:
    fh = open('var/marshal.stats.data', 'rb')
    stats = pickle.load(fh)
    fh.close()
except IOError, e:
    stats = Stats()
except EOFError, e:
    stats = Stats()

def saveStats(directory):
    print 'Saving IMarshal statistics'
    # stats
    fh = open(os.path.join(directory, 'marshal.stats.data'), 'wb')
    pickle.dump(stats, fh, 1)
    fh.close()
    # various data
    keys = []
    for key in stats.data.keys():
        keys.append((len(key) * stats.data[key],key))
    keys.sort()
    keys.reverse()
    fstats = open(os.path.join(directory, 'marshal.stats'), 'w')
    fscheme = open(os.path.join(directory, 'marshal.cscheme'), 'w')
    fpysrc = open(os.path.join(directory, 'marshal.cscheme.py'), 'w')
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
            print >> fpysrc, "    '%s' : '%s'," % (name, code)
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


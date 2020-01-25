#!/usr/bin/env python2

import os
import sys
from optparse import OptionParser
baseDir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(baseDir, '..', 'server', "lib"))

import types
from ige import Const
import ige.ospace.Const as osConst
from ige.IDataHolder import IDataHolder
from ige.SQLiteDatabase import Database, DatabaseString

# parse command line arguments
parser = OptionParser(usage = "usage: %prog [--configdir=]")
parser.add_option("",  "--configdir", dest = "configDir",
    metavar = "DIRECTORY", default = os.path.join(os.path.expanduser("~"), ".outerspace"),
    help = "Override default configuration directory",
)
options, args = parser.parse_args()

gameDB = Database(os.path.join(options.configDir, "db_data"), "game_Alpha", cache = 15000)
#~ gameDB = DatabaseString("var/db_data", "messages", cache = 15000)

def typeIdToString(obj):
    if not isinstance(obj, IDataHolder):
        return "?"
    for _type in ['T_GALAXY', 'T_SYSTEM', 'T_PLANET', 'T_FLEET', 'T_TECHNOLOGY', 'T_NATURE',
                  'T_AIPLAYER', 'T_AIRENPLAYER', 'T_AIMUTPLAYER', 'T_AIPIRPLAYER', 'T_AIEDENPLAYER', 'T_PIRPLAYER']:
        if obj.type == getattr(osConst, _type):
            return _type
    for _type in ['T_PLAYER', 'T_UNIVERSE', 'T_UNKNOWN', 'T_OBJECT']:
        if obj.type == getattr(Const, _type):
            return _type
    return "? (%d)" % obj.type

count = {}
total = {}
maxval = {}

for oid in gameDB.keys():
    t = typeIdToString(gameDB[oid])
    #~ print oid, t, gameDB.view.itemsize(gameDB.view.data, i)
    if t not in count:
        count[t] = 0
        total[t] = 0
        maxval[t] = 0
    count[t] += 1
    total[t] += gameDB.getItemLength(oid)
    maxval[t] = max(maxval[t], gameDB.getItemLength(oid))

print "%15s %10s %10s %10s %10s" % ("TYPE", "COUNT", "TOTAL", "AVG", "MAX")
print 59 * "-"
for key in count:
    print "%15s %10d %10d %10d %10d" % (key, count[key], total[key], total[key] / count[key], maxval[key])

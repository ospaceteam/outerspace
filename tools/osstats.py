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

    if obj.type == osConst.T_GALAXY:
        return "T_GALAXY"
    elif obj.type == osConst.T_SYSTEM:
        return "T_SYSTEM"
    elif obj.type == osConst.T_PLANET:
        return "T_PLANET"
    elif obj.type == osConst.T_FLEET:
        return "T_FLEET"
    elif obj.type == osConst.T_TECHNOLOGY:
        return "T_TECHNOLOGY"
    elif obj.type == osConst.T_NATURE:
        return "T_NATURE"
    elif obj.type == osConst.T_AIPLAYER:
        return "T_AIPLAYER"
    elif obj.type == osConst.T_AIRENPLAYER:
        return "T_AIRENPLAYER"
    elif obj.type == osConst.T_AIMUTPLAYER:
        return "T_AIMUTPLAYER"
    elif obj.type == osConst.T_AIPIRPLAYER:
        return "T_AIPIRPLAYER"
    elif obj.type == osConst.T_AIEDENPLAYER:
        return "T_AIEDENPLAYER"
    elif obj.type == osConst.T_PIRPLAYER:
        return "T_PIRPLAYER"
    elif obj.type == Const.T_PLAYER:
        return "T_PLAYER"
    elif obj.type == Const.T_UNIVERSE:
        return "T_UNIVERSE"
    elif obj.type == Const.T_UNKNOWN:
        return "T_UNKNOWN"
    elif obj.type == Const.T_OBJECT:
        return "T_OBJECT"
    else:
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

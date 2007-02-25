import sys
sys.path.insert(0,"lib")

import types
from ige.Const import *
from ige.ospace.Const import *
from ige.IDataHolder import IDataHolder
from ige.MetakitDatabase import MetakitDatabase, MetakitDatabaseString

gameDB = MetakitDatabase("var/db_data", "game_Alpha", cache = 15000)
#~ gameDB = MetakitDatabaseString("var/db_data", "messages", cache = 15000)

def typeIdToString(obj):
    if not isinstance(obj, IDataHolder):
        return "?"

    if obj.type == T_GALAXY:
        return "T_GALAXY"
    elif obj.type == T_SYSTEM:
        return "T_SYSTEM"
    elif obj.type == T_PLANET:
        return "T_PLANET"
    elif obj.type == T_FLEET:
        return "T_FLEET"
    elif obj.type == T_ALLIANCE:
        return "T_ALLIANCE"
    elif obj.type == T_TECHNOLOGY:
        return "T_TECHNOLOGY"
    elif obj.type == T_ASTEROID:
        return "T_ASTEROID"
    elif obj.type == T_NATURE:
        return "T_NATURE"
    elif obj.type == T_AIPLAYER:
        return "T_AIPLAYER"
    elif obj.type == T_AIRENPLAYER:
        return "T_AIRENPLAYER"
    elif obj.type == T_AIMUTPLAYER:
        return "T_AIMUTPLAYER"
    elif obj.type == T_AIPIRPLAYER:
        return "T_AIPIRPLAYER"
    elif obj.type == T_AIEDENPLAYER:
        return "T_AIEDENPLAYER"
    elif obj.type == T_PIRPLAYER:
        return "T_PIRPLAYER"
    elif obj.type == T_PLAYER:
        return "T_PLAYER"
    elif obj.type == T_UNIVERSE:
        return "T_UNIVERSE"
    elif obj.type == T_UNKNOWN:
        return "T_UNKNOWN"
    elif obj.type == T_OBJECT:
        return "T_OBJECT"
    else:
        return "? (%d)" % obj.type

count = {}
total = {}
maxval = {}

for i in range(0, len(gameDB.view)):
    oid = gameDB.view[i].oid
    t = typeIdToString(gameDB[oid])
    #~ print oid, t, gameDB.view.itemsize(gameDB.view.data, i)
    if t not in count:
        count[t] = 0
        total[t] = 0
        maxval[t] = 0
    count[t] += 1
    total[t] += gameDB.view.itemsize(gameDB.view.data, i)
    maxval[t] = max(maxval[t], gameDB.view.itemsize(gameDB.view.data, i))

print "%15s %10s %10s %10s %10s" % ("TYPE", "COUNT", "TOTAL", "AVG", "MAX")
print 59 * "-"
for key in count:
    print "%15s %10d %10d %10d %10d" % (key, count[key], total[key], total[key] / count[key], maxval[key])

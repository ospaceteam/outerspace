# tweak PYTHONPATH
import sys
sys.path.insert(0, '../server/lib')

from igeclient.IClient import IClient
import pprint, traceback

def msgHandler(id, data):
	if id >= 0:
		print 'Message', id, data

def getPlayer(name):
    u = s.getInfo(1)
    for playerID in u.players:
        pl = s.getInfo(playerID)
        if pl.name == name:
            return pl
    return None

s = IClient('ospace.net:9080', None, msgHandler, None, 'IClient/osc')
#s = IClient('localhost:9080', None, msgHandler, None, 'IClient/osc')

s.connect('admin')
s.login('Alpha', 'admin', '**PASS**')

u = s.getInfo(1)

for playerID in u.players:
	pl = s.getInfo(playerID)
	if len(pl.planets) == 1:
		print "Skipping", playerID, pl.name
		continue
	print "Processing", playerID, pl.name
	pl.stratRes[1000] = 2
	s.set(playerID, 'stratRes', pl.stratRes)

s.logout()

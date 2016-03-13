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

log = open("log.txt", "wt")

for playerID in u.players:
	pl = s.getInfo(playerID)
	for specID in pl.shipDesigns:
		spec = pl.shipDesigns[specID]
		if spec.hullID not in pl.techs:
			if spec.hullID == 2401:
				print >> log, "!!",
			print >> log, "Warning - invalid hull (%d) for spec %d (%s), player %d" % (
				spec.hullID,
				specID,
				spec.name,
				playerID,
			)

s.logout()

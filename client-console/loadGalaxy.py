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

s.connect('admin')
s.login('Alpha', 'admin', '**PASS**')

galaxyID = s.createGalaxy(1)
#galaxyID = 10000

#s.loadFromXML(galaxyID, 'galaxy-Argo42P.xml', 'Circle42P', 100, 100, 'Argo')
s.loadFromXML(galaxyID, 'galaxy-Beidos42P.xml', 'Circle42P', 300, 100, 'Beidos')
#s.loadFromXML(galaxyID, 'galaxy-Ceelia42P.xml', 'Circle42P', 500, 100, 'Ceelia')
#s.loadFromXML(galaxyID, 'galaxy-Daela42P.xml', 'Circle42P', 700, 100, 'Daela')
#s.loadFromXML(galaxyID, 'galaxy-Everen42P.xml', 'Circle42P', 100, 300, 'Everen')
#s.loadFromXML(galaxyID, 'galaxy-Ferun42P.xml', 'Circle42P', 300, 300, 'Ferun')
#s.loadFromXML(galaxyID, 'galaxy-Garis42P.xml', 'Circle42P', 500, 300, 'Garis')
#s.loadFromXML(galaxyID, 'galaxy-Hiron42P.xml', 'Circle42P', 700, 300, 'Hiron')
#s.loadFromXML(galaxyID, 'galaxy-Inera42P.xml', 'Circle42P', 100, 500, 'Inera')
#s.loadFromXML(galaxyID, 'galaxy-Jinx42P.xml', 'Circle42P', 300, 500, 'Jinx')
#s.loadFromXML(galaxyID, 'galaxy-Kelenor42P.xml', 'Circle42P', 500, 500, 'Kelenor')
#s.loadFromXML(galaxyID, 'galaxy-???42P.xml', 'Circle42P', 700, 500, '???')

s.setupEnvironment(galaxyID)

#from code import InteractiveConsole
#console = InteractiveConsole(locals())
#console.interact()

s.logout()

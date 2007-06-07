#!/usr/bin/env python
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

# tweak PYTHONPATH
import sys, string, re
import os
sys.path.insert(0, 'lib')

from igeclient.IClient import IClient
import pprint, traceback
from getpass import getpass
from code import InteractiveConsole
from ige.ospace import Rules
import time

#not race specific:
levelTechs = {1: [
1000, 1100, 1101, 1102, 1104, 1106, 1107, 1110, 1112,
1400, 1401, 1402, 1403, 1404,
1500, 1510, 1511,
1800, 1801, 1802, 1803,
],
2: [
1105, 1111,
2001, 2006,
2400, 2401, 2403, 2404, 2405, 2406, 2407, 2408, 2409,
2800, 2801, 2802, 2803,
],
3: [
3000, 3010, 3013,
3401, 3402, 3403, 3404, 3405, 3406, 3407, 3409, 3410,
3450, 3451,
3800, 3802,
],
4: [
4000, 4004, 4005, 
],
5: [
5000, 5001, 5002,
5800, 5801, 5802, 5803,
],
6: [
6000, 6001, 6005, 6025,
],
99: [
99001, 99002, 99003, 99004,
]}

#race specific:
levelTechsRaces = {
1: {'B': [], 'H': [], 'C': []},
2: {
'B': [2003, 2005, 2007, 2804, 2805],
'H': [2000, 2004],
'C': [2002, 2004]},
3: {
'B': [3001, 3003, 3007, 3008, 3412, 3420, 3421, 3452, 3454, 3803, ],
'H': [3002, 3004, 3006, 3009, 3408, 3411, 3453, 3455, 3803, ],
'C': [3001, 3005, 3006, 3411, 3453, 3456, ]},
4: {
'B': [4003, 4400, 4401, 4402, 4403, 4404, 4405, 4406, 4458, 4460, 4476, 4502, 4504, ],
'H': [4002, 4407, 4408, 4409, 4410, 4411, 4412, 4413, 4459, 4461, 4477, 4479, 4480, 4500, 4503, ],
'C': [4001, 4414, 4415, 4416, 4417, 4418, 4419, 4420, 4459, 4462, 4477, 4479, 4501, 4503, ]},
5: {
'B': [5400, 5401, 5402, 5403, 5404, 5405, 5406, 5007, 5431, 5433, 5465, 5467, 5470, 5475, 5503, 5504, 5507, 5805, 5808],
'H': [5003, 5004, 5005, 5008, 5408, 5409, 5410, 5411, 5412, 5413, 5414, 5430, 5434, 5466, 5468, 5471, 5474, 5501, 5502, 5508, 5804, 5807],
'C': [5006, 5416, 5417, 5418, 5419, 5420, 5421, 5432, 5435, 5466, 5469, 5472, 5473, 5476, 5505, 5506, 5806]},
6: {
'B': [6200, 6201, 6202, 6203, 6204, 6205, 6220, 6221, 6222, 6241, ],
'H': [6100, 6101, 6102, 6103, 6104, 6105, 6120, 6121, 6140, 6141, 6160, ],
'C': [6301, 6302, 6303, 6304, 6305, 6306, 6320, 6321, 6322, 6323, 6340, 6360, ]
},
99: {'B': [], 'H': [], 'C': []},
}

advTechLevel = {
1: {},
2: {"B" : 1990, "H" : 1991, "C" : 1992},
3: {"B" : 2990, "H" : 2991, "C" : 2992},
4: {"B" : 3990, "H" : 3991, "C" : 3992},
5: {"B" : 4990, "H" : 4991, "C" : 4992},
6: {"B" : 5990, "H" : 5991, "C" : 5992},
99: {}
}

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

def showPlayers():
	un = s.getInfo(1)
	players = []
	for playerID in un.players:
		player = s.getInfo(playerID)
		players.append((playerID, player.name))

	print
	print
	print "List of current players:"
	for pl in players:
		print "%5d: %s" % pl

	print
	print "Press Enter to continue"
	raw_input()

def showGalaxies():
	un = s.getInfo(1)
	galaxies = []
	for galaxyID in un.galaxies:
		galaxy = s.getInfo(galaxyID)
		galaxies.append((galaxyID, galaxy.name))

	print
	print
	print "List of current galaxies:"
	for gal in galaxies:
		print "%5d: %s" % gal

	print

def setCurrentObject():
	objId = raw_input("oid: ")
	newObjID = 0
	try:
		newObjID = int(objId)
	except:
		print "Invalid object"

	return newObjID

def initDevelTesting(objID):
	levels = 6
	resources = 8
	
	race = string.upper(raw_input("race: "))
	if not (race=='b' or race=='B' or race=='c' or race=='C' or race =='h' or race =='H'):
		print "Invalid race"
		return objID
	
	for level in range(2,levels+1):
		advanceLevelRace(objID,level,race)
	for level in range(1,levels+1):
		giveTechsNum(objID,level)
	giveTechsNum(objID,99)
	for stratResID in range(1,resources+1):
		giveStratResNum(objID,stratResID,50)
	
	return objID

def giveTechs(objID):
	lvl = raw_input("level: ")
	level = 0
	try:
		level = int(lvl)
	except:
		print "Invalid level"
		return objId

	if level > 6 and not level == 99:
		print "Invalid level"
		return objId
	giveTechsNum(objID,level)

def giveTechsNum(objID,level):
	player = s.getInfo(objID)
	plTechs = player.techs
	for techId in levelTechs[level]:
		plTechs[techId] = 5

	if len(player.race) > 0:
		print "setting race dependent techs"
		for techId in levelTechsRaces[level][player.race]:
			plTechs[techId] = 5

	s.set(objID, "techs", plTechs)
	print "Techs at level %d added to player %d." % (level, objID)
	return objID

def giveTech(objID):
	tid = raw_input("techId: ")
	try:
		techId = int(tid)
	except:
		print "Invalid techId"
		return objID

	player = s.getInfo(objID)
	plTechs = player.techs
	try:
        	plTechs[techId] = 5
	except:
		print "Invalid techId"
		return objID

	s.set(objID, "techs", plTechs)
	print "Tech %d added to player %d." % (techId, objID)
	return objID

def advanceLevel(objID):
	lvl = raw_input("level: ")
	try:
		level = int(lvl)
	except:
		print "Invalid level"
		return objID

	if level > 6 or level < 2:
		print "Invalid level"
		return objID
	race = string.upper(raw_input("race: "))
	if not (race=='b' or race=='B' or race=='c' or race=='C' or race =='h' or race =='H'):
		print "Invalid race"
		return objID
	advanceLevelRace(objID,level)

def advanceLevelRace(objID,level,race):
	player = s.getInfo(objID)
	plTechs = player.techs
	plTechs[advTechLevel[level][race]] = 5

	s.set(objID, "techs", plTechs)
	s.set(objID, "techLevel", level)
	s.set(objID, "race", race)
	print "Tech %d added, techLevel advance to %d to player %d." % (advTechLevel[level][race], level, objID)
	return objID

def promoteToImperator(objID):
	galID = raw_input("galaxy id: ")
	try:
		galaxyID = int(galID)
	except:
		print "Invalid galaxy id"
		return objID

	s.set(objID, "imperator", 3)
	s.set(galaxyID, "imperator", objID)
	print "Galaxy %d has now imperator %d." % (galaxyID, objID)
	return objID

def giveStratRes(objID):
	resID = raw_input("strategy resource ('a' for all resources): ")
	if not (resID == 'a'):
            try:
                    stratResID = int(resID)
            except:
                    print "Invalid strategy resource"
                    return objID

	qty = raw_input("qty: ")
	try:
		quantity = int(qty)
	except:
		print "Invalid quantity"
		return objID

	if (resID == 'a'):
            for stratResID in range(1,9):
                giveStratResNum(objID,stratResID,quantity)
        else:
            giveStratResNum(objID,stratResID,quantity)
	return objID

def giveStratResNum(objID,stratResID,quantity):
	plQty = 0
	player = s.getInfo(objID)
	if stratResID in player.stratRes:
		plQty = player.stratRes[stratResID]

	stratRes = player.stratRes
	stratRes[stratResID] = plQty + quantity
	s.set(objID, "stratRes", stratRes)
	print "Player %d has now %d pieces of %d." % (objID, stratRes[stratResID], stratResID)
    

def startGalaxy():
        showGalaxies()
	objId = raw_input("oid: ")
	newObjID = 0
	try:
		newObjID = int(objId)
	except:
		print "Invalid object"
	un = s.getInfo(1)
	galaxyObj = 0
        print newObjID
	for galaxyID in un.galaxies:
            print galaxyID
            if galaxyID==newObjID:
                galaxyObj = newObjID
	if galaxyObj == 0:
		print "Not a galaxy"
	else:
                s.enableTime(galaxyObj,1)
                print "Galaxy will start on next turn process"

def showObj(objID):
	try:
                obj = s.getInfo(objID)
                objstr = repr(obj)
                #insanely complex regex to chunk {data} and [data] parts during split by ,'s
                objarr = re.findall("[^,\{\]]*(?:\{[^\}]*[\}\{]),?|[^,\{\]]*(?:\[[^\]]*[\]\[]),?|[^,\}\]]+,?",objstr)
                for line in objarr:
                        print line
        except:
                print "Cannot get object",objID

def showMenu(objID):
	print
	print "----- OSpace admin console menu -----"
	print "Current object: %s" % objID
	print
	print "1. Set current object          6. Give particular tech"
	print "2. Show Players                7. Give techs"
	print "3. Show Galaxies               8. Give Strat Res"
	print "4. Advance to level            9. Finish prod queue"
	print "5. Make imperator              0. Object Info"
	print
	print "T. Process turn                R. Process X turns"
	print "C. Interactive console         S. Start Galaxy Time"
	print "D. Init Developer testing race (all techs, 50 each strat resource)"
	print
	print "Ctrl+Z to End"
	print

def processTurns():
	numT = raw_input("Number of turns: ")
	try:
		num = int(numT)
	except:
		print "invalid number of turns"

	for i in range(1, num + 1):
		s.processTurn()

def finishProdQueue(objId):
	p = s.get(objId)
	for i in p.prodQueue:
		i.currProd = 38400
	s.set(p.oid, "prodQueue", p.prodQueue)

def processMenu(inp, objId, s):
	if inp == "2":
		showPlayers()
	elif inp == "1":
		return setCurrentObject()
	elif inp == "3":
		giveTechs(objId)
	elif inp == "7":
		giveTech(objId)
	elif inp == "6":
		advanceLevel(objId)
	elif inp == "3":
		showGalaxies()
	elif inp == "5":
		promoteToImperator(objId)
	elif inp == "8":
		giveStratRes(objId)
	elif inp == "9":
		finishProdQueue(objId)
	elif inp == "0":
		showObj(objID)
	elif string.upper(inp) == "R":
		processTurns()
	elif string.upper(inp) == "T":
		s.processTurn()
	elif string.upper(inp) == "C":
		console = InteractiveConsole(locals())
		console.interact()
	elif string.upper(inp) == "S":
		startGalaxy()
	elif string.upper(inp) == "D":
		initDevelTesting(objID)

	return objId

#s = IClient('ospace.net:9080', None, msgHandler, None, 'IClient/osc')
s = IClient('localhost:9080', None, msgHandler, None, 'IClient/osc')

if len(sys.argv) != 2:
	print "Usage: osclient LOGIN"
	sys.exit(1)

login = sys.argv[1]

if login == "admin":
	# get admin login from var/token
	password = open(os.path.join("var", "token"), "r").read()
else:
	password = getpass("Password: ")

s.connect(login)
s.login('Alpha', login, password)

try:
	objID = 0
	while True:
		showMenu(objID)
		objID = processMenu(raw_input(), objID, s)
except EOFError:
       pass

s.logout()

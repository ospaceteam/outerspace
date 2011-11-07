#
#  Copyright 2001 - 2011 Ludek Smid [http://www.ospace.net/]
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

import atexit
import math
import optparse
import os
import random
import sys
import time
import xmlrpclib
import sqlite3
from SimpleXMLRPCServer import SimpleXMLRPCServer

sys.path.insert(0, 'lib')

from igeclient.IClient import IClient
from ige.ClientMngr import Session
from ige.Const import *
from ige.ospace import Const

def msgHandler(id, data):
	if id >= 0:
		print 'Message', id, data

def _adminLogin():
	s = IClient(options.server, None, msgHandler, None, 'IClient/osc')
	login = 'admin'
	password = open(os.path.join(options.configDir, "token"), "r").read()
	s.connect(login)
	s.login('Alpha', login, password)
	return s

def _adminLogout(s):
	s.logout()
		
def _getActualGalaxies():
	un = s.getInfo(OID_UNIVERSE)
	galaxies = {}
	response = ''
	for galaxyID in un.galaxies:
		galaxerInfo = s.getGalaxerInfo(galaxyID)
		galaxies[galaxyID] = galaxerInfo
	return galaxies

def _getActivePlayers():
	return s.getActivePlayers(OID_UNIVERSE)

def _removePlayingPlayers():
	activePlayers = _getActivePlayers()
	query = db.execute('SELECT DISTINCT nick FROM players', ()).fetchall()
	bookingPlayers = []
	for (nick,) in query:
		bookingPlayers.append(nick)
	zombiePlayers = set(bookingPlayers) & set(activePlayers)
	for nick in zombiePlayers:
		db.execute('DELETE FROM players\
						WHERE nick=?',
						(nick,))
	
def setPlayerPreference(token, galType):
	global db
	session = s.getSessionByToken(token)
	if session:
		if session.nick in _getActivePlayers():
			# player is already in the game
			return True
		query = db.execute('SELECT nick FROM players\
								WHERE nick=? AND galType=?',
								(session.nick, galType)).fetchone()
		if query:
			db.execute('DELETE FROM players\
							WHERE nick=? AND galType=?',
							(session.nick, galType))
		else:
			db.execute('INSERT INTO players (nick, login, email, time, galType)\
							VALUES (?, ?, ?, ?, ?)',
							(session.nick, session.login, session.email, time.time(), galType))

			result = testBooking()
			if result:
				return result
	db.commit()
	return getDataForPlayer(token)

def getDataForPlayer(token):
	global db
	session = s.getSessionByToken(token)
	types = s.getPossibleGalaxyTypes(OID_UNIVERSE)
	finalInfo = {}
	if session:
		playerNick = session.nick
		for galType in types:
			playerCapacity, infoText, radius = types[galType]
			query = db.execute('SELECT COUNT(*), galType\
									FROM players GROUP BY galType\
										HAVING galType=?', (galType,)).fetchone()
			if query:
				actualBooked = query[0]
			else:
				actualBooked = 0
			hasBooked = bool(db.execute('SELECT nick FROM players\
											WHERE nick=? AND galType=?',
											(playerNick, galType)).fetchone())
			# find out, when was the galaxy created for the last time
			query = db.execute('SELECT lastCreation FROM galaxies\
									WHERE galType=?',
									(galType,)).fetchone()

			if query:
				lastTime = query[0]
			else:
				lastTime = 0
			finalInfo[galType] = (infoText, playerCapacity, actualBooked, lastTime, hasBooked)
	return finalInfo

def testBooking():
	global db
	_removePlayingPlayers()
	query = db.execute('SELECT galType, COUNT(*) FROM players\
							GROUP BY galType', ()).fetchall()
	types = s.getPossibleGalaxyTypes(OID_UNIVERSE)
	for galType, count in query:
		galCap, galInfo, radius = types[galType]
		if galCap * options.threshold <= count:		
			return createNewGalaxy(galType, galCap, radius)

def createNewGalaxy(galType, galCap, radius):
	actualGalaxies = _getActualGalaxies()
	# using sqlite to provide rtree, as it is part of the standard library
	tempdb = sqlite3.connect(':memory:')
	tempdb.execute('CREATE VIRTUAL TABLE galaxies_positions USING rtree(id INTEGER PRIMARY KEY, x_min, x_max, y_min, y_max)')
	galNames = set([])
	maxRadius = radius
	# reserve is half of the minimal range of the galaxies
	reserve = 50.0
	galRadius = radius + reserve
	# fill list of possible galaxy names
	names = []
	for name in open('data/GalaxyNames.txt'):
		names.append(name.strip())
	for galaxyID in actualGalaxies:
		galName, galX, galY, galRadius = actualGalaxies[galaxyID]
		maxRadius = max(maxRadius, galRadius)
		galRadius += reserve
		galNames.add(galName)
		tempdb.execute('INSERT INTO galaxies_positions VALUES (?, ?, ?, ?, ?)',
					(galaxyID, galX-galRadius, galX+galRadius, galY-galRadius, galY+galRadius))
	# get list of booked players, and delete
	# their records from the booking system
	query = db.execute('SELECT login, nick, email FROM players\
							WHERE galType=? ORDER BY time ASC',
							(galType,)).fetchall()
	listOfPlayers = []
	for playerInfo in query[:galCap]:
		nick = playerInfo[1]
		listOfPlayers.append(playerInfo)
		db.execute('DELETE FROM players\
						WHERE nick=?',
						(nick,))
	# now we need to find the place for it
	search = True
	# we don't want to have negative coordinates
	lowLimit = int(math.ceil(radius))
	# surface of biggest galaxy is multiplied by number of galaxies to get
	# filled surface. By adding the surface of new galaxy, we get the surface of
	# hypothetical square. 4.4 is magic constant that multiply length of side to
	# ensure that the new galaxy will fit in all cases (actually 4.3 should be
	# sufficient according to 10000 run Monte Carlo simulation)
	highLimit = int(math.ceil(((maxRadius ** 2 ) * len(actualGalaxies) + galRadius ** 2) ** 0.5 * 4.4 + radius))
	while search:
		posX = random.randrange(lowLimit, highLimit)
		posY = random.randrange(lowLimit, highLimit)
		search = bool(tempdb.execute('SELECT id FROM galaxies_positions WHERE\
							x_min<? AND x_max>? AND y_min<? AND y_max>?',
							(posX+galRadius, posX-galRadius, posY+galRadius, posY-galRadius)).fetchall())
	# searching for free name for the galaxy
	nameFound = False
	for name in names:
		if name in galNames:
			continue
		nameFound = True	
		break
	if not nameFound:
		# cannot be created, no free name
		# TODO: report it
		return False
	# create the galaxy
	s.createNewSubscribedGalaxy(OID_UNIVERSE, posX, posY, name, galType, listOfPlayers)
	# record the creation time
	query = db.execute('SELECT lastCreation FROM galaxies\
							WHERE galType=?',
							(galType,)).fetchone()
	if query:
		db.execute('UPDATE galaxies SET lastCreation=?\
						WHERE galType=?',
						(time.time(), galType))
	else:
		db.execute('INSERT INTO galaxies (galType, lastCreation)\
						VALUES (?, ?)',
						(galType, time.time()))
	db.commit()
	return True

def test():
	return True
	
def initDatabase():
	db = sqlite3.connect(os.path.join(options.configDir, 'galaxer.db'))
	rows = db.execute('SELECT name FROM sqlite_master WHERE type = "table"')
	tables = set([])
	for row in rows.fetchall():
		tables.add(row[0])
	if not 'players' in tables:
		db.execute('CREATE TABLE players (login,\
											nick,\
											email,\
											time,\
											galType,\
											PRIMARY KEY (nick,\
														galType))\
											')
	if not 'galaxies' in tables:
		db.execute('CREATE TABLE galaxies (galType,\
											lastCreation,\
											PRIMARY KEY (galType))\
											')
	return db
	
	
parser = optparse.OptionParser()
parser.add_option("",  "--configdir", dest = "configDir", 
	metavar = "DIRECTORY", 
	default = "var", 
	help = "Override default configuration directory", 
)
parser.add_option("",  "--OSserver", dest = "server", 
	metavar = "HOSTNAME:PORT", 
	default = "www.ospace.net:9080",
	help = "Outer Space server location"
)
parser.add_option("",  "--address", dest = "address", 
	metavar = "HOSTNAME:PORT", 
	default = "www.ospace.net:9081",
	help = "Outer Space galaxer location"
)
parser.add_option("",  "--threshold", dest = "threshold", 
	metavar = "REALNUMBER", 
	default = 1.0,
	type = "float",
	help = "Ratio of galaxy capacity, which is necessary to create it."
)

options, args = parser.parse_args()

if args:
	parser.error("No additional arguments are supported")

# record my pid
pidFd = os.open(os.path.join(options.configDir,"galaxer.pid"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
os.write(pidFd, str(os.getpid()))

# define and register exit function
def cleanup():
	# delete my pid
	os.close(pidFd)
	os.remove(os.path.join(options.configDir,"galaxer.pid"))

atexit.register(cleanup)

db = initDatabase()
s = _adminLogin()
address, strPort = options.address.split(':')
port = int(strPort)
server = SimpleXMLRPCServer((address, port))
server.register_function(setPlayerPreference, 'setPlayerPreference')
server.register_function(getDataForPlayer, 'getDataForPlayer')
server.register_function(test, 'test')
try:
	server.serve_forever()
except:
	db.commit()
	_adminLogout(s)

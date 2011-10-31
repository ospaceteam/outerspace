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
import optparse
import os
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
			playerCapacity, infoText = types[galType]
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
		galCap, galInfo = types[galType]
		if galCap * options.threshold <= count:
			#
			return createNewGalaxy(galType, galCap)

def createNewGalaxy(galType, galCap):
	actualGalaxies = _getActualGalaxies()
	galPositions = set([])
	galNames = set([])
	maxCoordinate = 0
	names = ['Argo', 'Beidos', 'Ceelia', 'Daela', 'Everen', 'Ferun', 'Garis', 'Hiron', 'Inera', 'Jinx', 'Kelenor', 'Larion', 'Merlis']
	for galaxyID in actualGalaxies:
		galName, galX, galY, galRadius = actualGalaxies[galaxyID]
		galX = int(galX)
		galY = int(galY)
		galRadius = int(galRadius)
		galNames.add(galName)
		galPositions.add((galX, galY))
		maxCoordinate = max(maxCoordinate, galX, galY)
		if galRadius > 50 or galX % 100 or galY % 100:
			raise NotImplementedError
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
	squareSide = maxCoordinate / 200 + 1
	if squareSide**2 == len(actualGalaxies):
		squareSide += 1
	hasFound = False
	for y in xrange(squareSide):
		posY = y * 200 + 100 
		for x in xrange(squareSide):
			posX = x * 200 + 100
			if (posX, posY) in galPositions:
				continue
			hasFound = True
			if hasFound:
				break
		if hasFound:
			break
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

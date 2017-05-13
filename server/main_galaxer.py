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

def runGalaxer(options):
    global db, isRunning
    import atexit
    import math
    import signal
    import os
    import re
    import random
    import sys
    import time
    import xmlrpclib
    import sqlite3
    from SimpleXMLRPCServer import SimpleXMLRPCServer


    # setup system path
    baseDir = os.path.abspath(os.path.dirname(__file__))

    sys.path.insert(0, os.path.join(baseDir, 'lib'))
    sys.path.insert(0, os.path.join(baseDir, 'data'))

    from igeclient.IClient import IClient, IClientException
    from ige.ClientMngr import Session
    import ige.Const
    from ige.ospace import Const

    def msgHandler(id, data):
        if id >= 0:
            print 'Message', id, data

    def _adminLogin():
        tries = 10
        while tries > 0:
            s = IClient(options.server, None, msgHandler, None, 'IClient/osc')
            login = 'admin'
            try:
                s.connect(login)
                tries = 0
            except IClientException:
                time.sleep(1)
                tries -= 1
        password = open(os.path.join(options.configDir, "token"), "r").read()
        gameName = 'Alpha'
        s.login(gameName, login, password)
        return s

    def _adminLogout(s):
        s.logout()

    def _getActualGalaxies():
        un = s.getInfo(ige.Const.OID_UNIVERSE)
        galaxies = {}
        response = ''
        for galaxyID in un.galaxies:
            galaxerInfo = s.getGalaxerInfo(galaxyID)
            galaxies[galaxyID] = galaxerInfo
        return galaxies

    def _getActivePlayers():
        return s.getActivePlayers(ige.Const.OID_UNIVERSE)

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
        types = s.getPossibleGalaxyTypes(ige.Const.OID_UNIVERSE)
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
        types = s.getPossibleGalaxyTypes(ige.Const.OID_UNIVERSE)
        for galType, count in query:
            galCap, galInfo, radius = types[galType]
            if galCap * options.threshold <= count:
                return createNewGalaxy(galType, galCap, radius)


    def findSpotForGalaxy(newGalRadius):
        """ We start with sum of surfaces of active galaxies (with borders) with this,
            we count the hypothetical square all galaxies should fit together. We then
            increase the size a bit, and try to place the new galaxy there randomly.
            If not successful, increase again and repeat.
        """
        actualGalaxies = _getActualGalaxies()

        attemptsAmount = 10000 # number of placement attempts within one resize
        magicConstant = 1.1
        magicConstantStep = 0.1
        border = 50

        # count surface required
        wholeSurface = 0
        for galaxyID in actualGalaxies:
            galName, galX, galY, galRadius = actualGalaxies[galaxyID]
            # border is counted only once as it can overlap
            wholeSurface += (galRadius * 2 + border) ** 2
        # adding wholeSurface of the galaxy currently processed
        wholeSurface += (newGalRadius * 2 + border) ** 2

        search = True
        attempts = attemptsAmount
        lowLimit = newGalRadius # only positive coordinates
        while search:
            highLimit = math.ceil(wholeSurface ** 0.5 * magicConstant)
            attempts -= 1
            posX = int(random.randrange(lowLimit, highLimit))
            posY = int(random.randrange(lowLimit, highLimit))
            isBlocked = False
            for galaxyID in actualGalaxies:
                galName, galX, galY, galRadius = actualGalaxies[galaxyID]
                neededSpace = galRadius + border + newGalRadius
                if abs(galX - posX) < neededSpace and abs(galY - posY) < neededSpace:
                    isBlocked = True
                    break
            search = isBlocked
            if not attempts:
                magicConstant += magicConstantStep
                attempts = attemptsAmount
        return (posX, posY)

    def findNameForGalaxy():
        allNames = []
        namesInUse = set([])
        for name in open(os.path.join(baseDir, 'data', 'GalaxyNames.txt')):
            allNames.append(name.strip())
        actualGalaxies = _getActualGalaxies()
        for galaxyID in actualGalaxies:
            galName, galX, galY, galRadius = actualGalaxies[galaxyID]
            namesInUse.add(galName)

        for name in allNames:
            if name in namesInUse:
                continue
            return name
        # no name available
        return None

    def createNewGalaxy(galType, galCap, radius):
        # first check if there is a galaxy name available
        name = findNameForGalaxy()
        if name is None:
            return False
        # now to get position for it - this cannot fail
        posX, posY = findSpotForGalaxy(radius)

        # get list of players
        query = db.execute('SELECT login, nick, email FROM players\
                            WHERE galType=? ORDER BY time ASC',
                            (galType,)).fetchall()
        listOfPlayers = []
        for playerInfo in query[:galCap]:
            nick = playerInfo[1]
            listOfPlayers.append(playerInfo)
        # trigger the creation
        s.createNewSubscribedGalaxy(ige.Const.OID_UNIVERSE, posX, posY, name, galType, listOfPlayers)

        # now, as the galaxy has been created, remove booked players from galaxer database
        for playerInfo in listOfPlayers:
            nick = playerInfo[1]
            db.execute('DELETE FROM players\
                        WHERE nick=?',
                        (nick,))

        # and record the creation time
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


    pidFd = os.open(os.path.join(options.configDir,"galaxer.pid"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(pidFd, str(os.getpid()))

    # define and register exit function
    def _cleanup(pidFd):
        global isRunning
        isRunning = False
        db.commit()
        _adminLogout(s)
        # delete my pid
        os.close(pidFd)
        os.remove(os.path.join(options.configDir,"galaxer.pid"))

    atexit.register(_cleanup, pidFd)
    signal.signal(signal.SIGTERM, _cleanup)
    match_obj = re.search('([^:]+):(\d+)', options.galaxer)
    address, strPort = match_obj.group(1,2)
    port = int(strPort)
    if options.local:
        address  = "localhost"
        port     = 9081
        options.server = "localhost:9080"
    db = initDatabase()
    s = _adminLogin()
    # to work properly, galaxer needs to listen to 0.0.0.0:PORT anyway
    server = SimpleXMLRPCServer(('0.0.0.0', port))
    server.register_function(setPlayerPreference, 'setPlayerPreference')
    server.register_function(getDataForPlayer, 'getDataForPlayer')
    server.register_function(test, 'test')

    isRunning = True

    while isRunning:
        server.handle_request()
    _adminLogout(s)

    db.commit()


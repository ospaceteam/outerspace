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

import json
import random, os, time, copy

import ige
from ige import log

from ige.ClientMngr import Session
from ige.GameMngr import GameMngr as IGEGameMngr
from ige.Index import Index
from ige.Transaction import Transaction
from ige.IDataHolder import IDataHolder
from ige import GameException, SecurityException, CreatePlayerException

import Const
import IPlayer, IUniverse, IGalaxy, ISystem, IWormHole, IPlanet, IFleet
import INature, IAIPlayer, IAIRenegadePlayer, IAIMutantPlayer, IAIPiratePlayer
import GalaxyGenerator
import IAIEDENPlayer, IPiratePlayer
import Rules, Utils

from Rules import Tech

class GameMngr(IGEGameMngr):

    #
    # Required methods
    #

    def __init__(self, gameID, config, clientMngr, msgMngr, database, configDir, gameName = None):
        IGEGameMngr.__init__(self, gameID, config, clientMngr, msgMngr, database, configDir, gameName)
        # register command object
        self.registerObject(IUniverse.IUniverse)
        self.registerObject(IPlayer.IPlayer)
        self.registerObject(IGalaxy.IGalaxy)
        self.registerObject(ISystem.ISystem)
        self.registerObject(IWormHole.IWormHole)
        self.registerObject(IPlanet.IPlanet)
        self.registerObject(IFleet.IFleet)
        self.registerObject(INature.INature)
        self.registerObject(IAIPlayer.IAIPlayer)
        self.registerObject(IAIRenegadePlayer.IAIRenegadePlayer)
        self.registerObject(IAIMutantPlayer.IAIMutantPlayer)
        self.registerObject(IAIPiratePlayer.IAIPiratePlayer)
        self.registerObject(IAIEDENPlayer.IAIEDENPlayer)
        self.registerObject(IPiratePlayer.IPiratePlayer)

    def init(self):
        IGEGameMngr.init(self)

    def start(self):
        IGEGameMngr.start(self)

    def stop(self, checkpoint = 1):
        IGEGameMngr.stop(self, checkpoint)

    def shutdown(self):
        IGEGameMngr.shutdown(self)

    def reset(self):
        # remove all AI accounts and their records in AI list
        self.clientMngr.resetAIAccounts()
        IGEGameMngr.reset(self)
        # save informations
        self.db.checkpoint()

    def upgrade(self):
        IGEGameMngr.upgrade(self)

    def createAdmin(self):
        obj = IPlayer.IPlayer(self).new(Const.T_PLAYER)
        obj.name = 'GameMaster'
        return obj

    def accountGalaxies(self, login):
        """ Returns set of galaxies account is already in. Empty set otherwise """
        galaxyIDs = set()
        try:
            for playerID in self.db[Const.OID_I_LOGIN2OID][login]:
                galaxyIDs.add(self.db[playerID].galaxy)
        except KeyError:
            # fresh account
            pass
        return galaxyIDs

    def registerPlayer(self, login, playerObj, oid = None):
        log.debug("Registering login {0}".format(login))

        # action
        if not oid:
            log.debug("Creating object")
            oid = self.db.create(playerObj)
        else:
            self.db.create(playerObj, id = oid)
        log.debug("Fixing indexes")
        try:
            self.db[Const.OID_I_LOGIN2OID][login].append(oid)
        except KeyError:
            self.db[Const.OID_I_LOGIN2OID][login] = [oid]
        playerObj.oid = oid
        playerObj.owner = oid
        return oid

    def createUniverse(self):
        universe = self.cmdPool[Const.T_UNIVERSE].new(Const.T_UNIVERSE)
        self.db.create(universe, Const.OID_UNIVERSE)
        tran = Transaction(self, Const.OID_ADMIN)
        # create 'NATURE' player
        player = self.cmdPool[Const.T_NATURE].new(Const.T_NATURE)
        self.registerPlayer(player.login, player, Const.OID_NATURE)

    def getTurnData(self, sid):
        IGEGameMngr.getTurnData(self, sid)
        universe = self.db[Const.OID_UNIVERSE]
        universe.turn += 1
        return (
            self.db[Const.OID_UNIVERSE].turn,
            (
                ((Const.OID_UNIVERSE,), ('INIT',)),
                (universe.galaxies, ('INIT', 'PROD', 'ACTION', 'BATTLE', 'SCAN2', 'FINAL')),
                ((Const.OID_UNIVERSE,), ('FINAL', 'FINAL2')),
            ),
            None
        ), None

    def turnFinished(self, sid):
        IGEGameMngr.turnFinished(self, sid)
        self.generateStats()
        self.generateGameInfo()
        return 1, None

    def getActivePositions(self, sid):
        session = self.clientMngr.getSession(sid)
        result = []
        for playerID in self.db[Const.OID_I_LOGIN2OID].get(session.login, []):
            player = self.db[playerID]
            galaxy = self.db[player.galaxy]
            result.append((playerID, galaxy.name, player.type))
        return result, None

    def getStartingPositions(self, sid):
        session = self.clientMngr.getSession(sid)
        universe = self.db[Const.OID_UNIVERSE]
        badGalaxies = self.accountGalaxies(session.login)
        result = []

        for galaxyID in set(universe.galaxies).difference(badGalaxies):
            galaxy = self.db[galaxyID]
            if galaxy.scenario == Const.SCENARIO_SINGLE:
                # single player scenarios are off limit :)
                continue
            if galaxy.startingPos:
                result.append((galaxyID, galaxy.name, Const.PLAYER_SELECT_NEWPLAYER))
        for playerID in universe.players:
            player = self.db[playerID]
            if player.galaxy in badGalaxies:
                continue
            try:
                system = self.db[self.db[player.planets[0]].compOf]
            except IndexError:
                # no planets, definitely not a good starting position
                continue
            galaxy = self.db[system.compOf]
            if galaxy.scenario == Const.SCENARIO_SINGLE:
                # single player scenarios are off limit :)
                continue
            if player.type == Const.T_AIPLAYER and player.planets:
                # check if home system is under attack
                if system.combatCounter > 0:
                    continue
                result.append((playerID, galaxy.name, Const.PLAYER_SELECT_AIPLAYER))
            if player.type == Const.T_AIPIRPLAYER:
                result.append((playerID, galaxy.name, Const.PLAYER_SELECT_PIRATE))
        return result, None

    def singleGamesLimit(self, sid):
        session = self.clientMngr.getSession(sid)
        noOfSingles = 0
        for galaxyID in self.accountGalaxies(session.login):
            galaxy = self.db[galaxyID]
            if galaxy.scenario == Const.SCENARIO_SINGLE:
                noOfSingles += 1
        if noOfSingles >= Const.ACCOUNT_SCENARIO_LIMITS[Const.SCENARIO_SINGLE]:
            # limit of single galaxies allowed to the account reached
            return True
        return False

    def takeOverAIPlayer(self, sid, playerID):
        log.debug('Creating new player in session', sid)
        session = self.clientMngr.getSession(sid)
        log.debug('Creating new player with CID', session.cid)
        universe = self.db[Const.OID_UNIVERSE]
        log.debug('Creating transaction')
        tran = Transaction(self, session.cid, session)
        player = self.db[playerID]
        if not (player.type == Const.T_AIPLAYER and player.planets):
            raise GameException('No such starting position.')
        if player.galaxy in self.accountGalaxies(session.login):
            raise GameException('Account already owns player in this galaxy.')
        galaxy = self.db[player.galaxy]
        if galaxy.scenario == Const.SCENARIO_SINGLE:
            raise GameException('AI in single scenario cannot be taken over.')


        # create player
        log.debug("Morphing AI player", playerID)
        player.type = Const.T_PLAYER
        self.cmdPool[Const.T_PLAYER].upgrade(tran, player)
        self.cmdPool[Const.T_PLAYER].update(tran, player)
        # reregister player
        self.removePlayer(player.oid)
        player.name = session.nick
        player.login = session.login
        self.registerPlayer(player.login, player, player.oid)
        # reset relations
        player.diplomacyRels.clear()
        # add player to the universe
        universe.players.append(playerID)
        log.debug('Processing scan phase')
        galaxy = tran.db[player.galaxy]
        self.cmdPool[Const.T_GALAXY].processSCAN2Phase(tran, galaxy, True)
        # save game info
        self.generateGameInfo()
        return player.oid, None

    def takeOverPirate(self, sid, playerID, vipPassword):
        # limit this now only to the qark
        session = self.clientMngr.getSession(sid)
        player = self.db[playerID]
        if vipPassword != self.config.vip.password:
            raise SecurityException('Wrong VIP password.')
        if player.galaxy in self.accountGalaxies(session.login):
            raise GameException('Account already owns player in this galaxy.')
        if player.galaxy:
            galaxy = self.db[player.galaxy]
            if galaxy.scenario == Const.SCENARIO_SINGLE:
                raise GameException('AI in single scenario cannot be taken over.')

        log.debug('Creating pirate in session {0} with CID {1}'.format(sid, session.cid))
        universe = self.db[Const.OID_UNIVERSE]
        log.debug('Creating transaction')
        tran = Transaction(self, session.cid, session)
        # create player
        #log.debug("Morphing Pirate player", playerID)
        log.debug("Player type", player.type)
        if player.type != Const.T_AIPIRPLAYER:
            raise GameException('No such starting position.')
        player.type = Const.T_PIRPLAYER
        self.cmdPool[Const.T_PIRPLAYER].upgrade(tran, player)
        self.cmdPool[Const.T_PIRPLAYER].update(tran, player)
        # reregister player
        self.removePlayer(player.oid)
        player.fullName = "Pirate %s" % session.nick
        player.name = session.nick
        player.login = session.login
        self.registerPlayer(player.login, player, player.oid)
        # add player to the universe
        universe.players.append(playerID)
        # initial scan
        scannerPwr = Rules.techs[9002].scannerPwr
        for planetID in player.planets:
            planet = self.db[planetID]
            system = self.db[planet.compOf]
            system.scannerPwrs[player.oid] = scannerPwr
        log.debug('Processing scan phase')
        galaxy = tran.db[player.galaxy]
        self.cmdPool[Const.T_GALAXY].processSCAN2Phase(tran, galaxy, True)
        # save game info
        self.generateGameInfo()
        return player.oid, None

    def _createNewPlayer(self, session, galaxyID):
        universe = self.db[Const.OID_UNIVERSE]
        galaxy = self.db[galaxyID]
        if not galaxy.startingPos:
            raise GameException('No such starting position.')
        if galaxyID in self.accountGalaxies(session.login):
            raise GameException('Account already owns player in this galaxy.')

        log.debug('Creating new player with CID', session.cid)
        player = self.cmdPool[Const.T_PLAYER].new(Const.T_PLAYER)
        player.name = session.nick
        player.login = session.login
        player.timeEnabled = galaxy.timeEnabled
        player.galaxy = galaxy.oid
        log.debug('Selecting starting point')
        planetID = IGalaxy.IGalaxy.getFreeStartingPosition(self.db, galaxy)

        player.planets.append(planetID)
        log.debug('Creating transaction')
        tran = Transaction(self, session.cid, session)
        IPlayer.IPlayer.setStartingTechnologies(player)
        # register player
        log.debug('Registering player for login {0}'.format(session.login))
        playerID = self.registerPlayer(session.login, player)
        log.debug('Player ID =', playerID)
        # singleplayer galaxy needs owner recorded so player can log back there
        # also provides access rights to control it
        if galaxy.scenario == Const.SCENARIO_SINGLE:
            galaxy.owner = playerID
        planet = self.db[planetID]
        planet.owner = playerID
        system = tran.db[planet.compOf]
        IPlayer.IPlayer.setStartingShipDesigns(player)
        IPlayer.IPlayer.setStartingPlanet(tran, playerID, planet)
        IPlayer.IPlayer.setStartingFleet(tran, playerID, system)
        # add player to universe
        log.debug('Adding player to universe')
        universe.players.append(playerID)
        # initial scan
        system = self.db[planet.compOf]
        log.debug('Processing scan phase')
        self.cmdPool[Const.T_PLANET].processPRODPhase(tran, planet, None)
        # this only works for one planet starting scenarios, it might be imprecise, as it's
        # calculated here
        # TODO: make proper difference between getting stats, and acting on them, and utilize that
        player.effSciPoints = planet.prodSci * (1 + ((Rules.baseGovPwr - planet.storPop)  / float(Rules.baseGovPwr) ) / 2.0)
        system.scannerPwrs[playerID] = planet.scannerPwr = Rules.startingScannerPwr
        self.cmdPool[Const.T_GALAXY].processSCAN2Phase(tran, galaxy, True)
        # check if galaxy can be "started" (for purpose of single player games)
        self.cmdPool[Const.T_GALAXY].enableTime(tran, galaxy)
        # save game info
        self.generateGameInfo()
        return playerID, None

    def createNewPlayer(self, sid, galaxyID):
        log.debug('Creating new player in session', sid)
        session = self.clientMngr.getSession(sid)
        return self._createNewPlayer(session, galaxyID)

    def createNewSubscribedPlayer(self, login, galaxyID):
        log.debug('Creating new subscribed player using fake session')
        player = self.clientMngr[login]
        session = Session(None)
        session.setAttrs(login, player.nick, player.email)
        return self._createNewPlayer(session, galaxyID)

    def removePlayer(self, playerID):
        log.debug('removePlayer', playerID)
        player = self.db[playerID]
        # unregister player
        self.unregisterPlayer(player)
        # remove player from universe
        universe = self.db[Const.OID_UNIVERSE]
        try:
            universe.players.remove(playerID)
        except ValueError:
            log.warning("Cannot remove player", playerID)

    def validateClient(self, session):
        # TODO better validation
        return 1


    #
    # Game related methods
    #

    def generateGameInfo(self):
        """Generate game related info."""
        # make directory
        try:
            os.makedirs(os.path.join(self.configDir, 'website/%s' % self.gameID))
        except OSError:
            pass
        # create structure to save
        stats = dict()
        universe = self.db[Const.OID_UNIVERSE]
        stats["players"] = len(universe.players)
        stats["turn"] = "%d:%02d" % (universe.turn / Rules.turnsPerDay, universe.turn % Rules.turnsPerDay)
        galaxies = list()
        stats["galaxies"] = galaxies
        for galaxyID in universe.galaxies:
            galaxy = self.db[galaxyID]
            galaxyStats = dict(
                name = galaxy.name,
                url = "http://www.ospace.net:9080/%s/galaxy%d.html" % (self.gameID, galaxyID),
                freePositions = len(galaxy.startingPos),
                players = 0,
                rebels = 0,
                age = int((galaxy.galaxyTurn - galaxy.creationTurn) / Rules.turnsPerDay ),
                running = galaxy.timeEnabled,
            )
            for playerID in universe.players:
                player = self.db[playerID]
                if galaxy.oid != player.galaxy:
                    continue
                if player.type == Const.T_PLAYER:
                    galaxyStats["players"] += 1
                elif player.type == Const.T_AIPLAYER:
                    galaxyStats["rebels"] += 1
            galaxies.append(galaxyStats)
        json.dump(stats, open(os.path.join(self.configDir, "website/%s/info.json" % self.gameID), "w"))

    def generateStats(self):
        """ Generate games statistics """
        # gather stats
        try:
            os.makedirs(os.path.join(self.configDir, 'website/%s' % self.gameID))
        except OSError:
            pass
        stats = {}
        galaxies = {}
        resolutions = {}
        universe = self.db[Const.OID_UNIVERSE]
        jsonComma = False
        fhjson = open(os.path.join(self.configDir, 'website/%s/json.txt' % (self.gameID)), 'w')
        print >>fhjson, '{"turn":"%s",' % universe.turn
        for playerID in universe.players:
            player = self.db[playerID]
            stats[playerID] = player.stats
            galaxies[playerID] = player.galaxy
            resolution = self.cmdPool[player.type].getResolution(player)
            if resolutions.has_key(resolution):
                resolutions[resolution] += 1
            else:
                resolutions[resolution] = 1
        for galaxyID in universe.galaxies:
            gStats = copy.deepcopy(stats)
            for playerID in gStats.keys():
                # huh, someone should have commented this
                if galaxyID != galaxies[playerID]:
                    del gStats[playerID]
                    continue
                try:
                    gStats[playerID].storPop
                except AttributeError:
                    # time has not been enabled yet
                    del gStats[playerID]

            if 0:
                # average
                storPop = 0
                planets = 0
                structs = 0
                prodProd = 0
                prodSci = 0
                for playerID in gStats:
                    pStats = gStats[playerID]
                    storPop += pStats.storPop
                    planets += pStats.planets
                    structs += pStats.structs
                    prodProd += pStats.prodProd
                    prodSci += pStats.prodSci
                if prodProd == 0: prodProd = 1000
                if prodSci == 0: prodSci = 1000
                for playerID in gStats:
                    pStats = gStats[playerID]
                    pStats.storPop = int(pStats.storPop * 1000 / storPop)
                    pStats.planets = int(pStats.planets * 1000 / planets)
                    pStats.structs = int(pStats.structs * 1000 / structs)
                    pStats.prodProd = int(pStats.prodProd * 1000 / prodProd)
                    pStats.prodSci = int(pStats.prodSci * 1000 / prodSci)
            # generate tables
            fh = open(os.path.join(self.configDir, 'website/%s/galaxy%d.html' % (self.gameID, galaxyID)), 'w')
            galaxy = self.db[galaxyID]
            if galaxy.imperator != Const.OID_NONE:
                if self.db[galaxy.imperator].imperator > 1:
                    imperator = " - Imperator %s" % self.db[galaxy.imperator].name
                    imperatoroid = self.db[galaxy.imperator].oid
                    leaderoid = 0
                else:
                    imperator = " - Leader %s" % self.db[galaxy.imperator].name
                    imperatoroid = 0
                    leaderoid = self.db[galaxy.imperator].oid
            else:
                imperator = ""
                imperatoroid = 0
                leaderoid = 0
            print >>fh, statsHeader % (self.gameID, galaxy.name, imperator)
            order = self.sortStatsBy(gStats, 'storPop')
            self.printJSONStatsTable(fhjson, gStats, order, galaxyID, galaxy.name, imperatoroid, leaderoid, jsonComma)
            jsonComma = True
            self.printStatsEcoTable(fh, 'Sorted by population', gStats, order)
            #order = self.sortStatsBy(gStats, 'systems')
            #self.printStatsEcoTable(fh, 'Sorted by number of systems', gStats, order)
            order = self.sortStatsBy(gStats, 'planets')
            self.printStatsEcoTable(fh, 'Sorted by number of planets', gStats, order)
            order = self.sortStatsBy(gStats, 'structs')
            self.printStatsEcoTable(fh, 'Sorted by number of structures', gStats, order)
            order = self.sortStatsBy(gStats, 'prodProd')
            self.printStatsEcoTable(fh, 'Sorted by production', gStats, order)
            order = self.sortStatsBy(gStats, 'prodSci')
            self.printStatsEcoTable(fh, 'Sorted by science', gStats, order)
            order = self.sortStatsBy(gStats, 'fleetPwr')
            self.printStatsEcoTable(fh, 'Sorted by military power', gStats, order)
            print >>fh, statsFooter
            fh.close()
        print >>fhjson, '}'
        fhjson.close()
        #write resolutions of clients in use for statistics tracking
        fhres = open(os.path.join(self.configDir, 'website/res.txt'), 'w')
        print >>fhres, 'Resoltion: Number of users'
        reskeys = resolutions.keys();
        reskeys.sort();
        for resolution in reskeys:
            print >>fhres, '%s: %s' % (resolution, resolutions[resolution])
        fhres.close()

    def sortStatsBy(self, stats, attr):
        keyF = lambda a: getattr(stats[a], attr)
        order = sorted(stats.keys(), key=keyF, reverse = True)
        return order

    def printJSONStatsTable(self, fh, stats, order, galaxyID, galaxyName, imperatoroid, leaderoid, jsonComma):
        if jsonComma:
            print >> fh, ','
        print >> fh, '"%s":{"galaxyname":"%s","imperatorid":"%s","leaderid":"%s","players":' % (galaxyID, galaxyName, imperatoroid, leaderoid)
        print >> fh, '{'
        print >> fh, '"order":["name","pop","planets","structs","prod","sci","mp"]'
        for playerID in order:
            print >> fh, ','
            needComma = True
            stat = stats[playerID]
            print >> fh, '"%s":["%s","%s","%s","%s","%s","%s","%s"]' % (playerID, self.db[playerID].name, stat.storPop, stat.planets, stat.structs, stat.prodProd, stat.prodSci, stat.fleetPwr)
        print >> fh, '}}'

    def printStatsEcoTable(self, fh, title, stats, order):
        print >> fh, '<table cellspacing="1" border="0" cellpadding="2" width="100%">'
        print >> fh, '<tr>'
        print >> fh, '<td class="title" align="center" colspan="8">%s</td>' % title
        print >> fh, '</tr>'
        print >> fh, '<tr>'
        print >> fh, '<td class="title" align="right">#</td>'
        print >> fh, '<td class="title" align="left">Player</td>'
        print >> fh, '<td class="title" align="right">Population</td>'
        print >> fh, '<td class="title" align="right">Planets</td>'
        print >> fh, '<td class="title" align="right">Structures</td>'
        print >> fh, '<td class="title" align="right">Production</td>'
        print >> fh, '<td class="title" align="right">Military pwr</td>'
        print >> fh, '<td class="title" align="right">Science</td>'
        print >> fh, '</tr>'
        print >> fh, '<tr>'
        # index
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d.<br>' % index
            else:  print >> fh, '<font color="#c0c0c0">%d</font>.<br>' % index
            index += 1
        print >> fh, '</td>'
        # name
        index = 1
        print >> fh, '<td align="left" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%s<br>' % self.db[playerID].name
            else: print >> fh, '<font color="#c0c0c0">%s</font><br>' % self.db[playerID].name
            index += 1
        print >> fh, '</td>'
        # storPop
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d<br>' % stat.storPop
            else: print >> fh, '<font color="#c0c0c0">%d</font><br>' % stat.storPop
            index += 1
        print >> fh, '</td>'
        # planets
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d<br>' % stat.planets
            else: print >> fh, '<font color="#c0c0c0">%d</font><br>' % stat.planets
            index += 1
        print >> fh, '</td>'
        # structs
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d<br>' % stat.structs
            else: print >> fh, '<font color="#c0c0c0">%d</font><br>' % stat.structs
            index += 1
        print >> fh, '</td>'
        # prodProd
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d<br>' % stat.prodProd
            else: print >> fh, '<font color="#c0c0c0">%d</font><br>' % stat.prodProd
            index += 1
        print >> fh, '</td>'
        # fleet
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d<br>' % stat.fleetPwr
            else: print >> fh, '<font color="#c0c0c0">%d</font><br>' % stat.fleetPwr
            index += 1
        # prodSci
        index = 1
        print >> fh, '<td align="right" nowrap>'
        for playerID in order:
            stat = stats[playerID]
            if index % 2: print >> fh, '%d<br>' % stat.prodSci
            else: print >> fh, '<font color="#c0c0c0">%d</font><br>' % stat.prodSci
            index += 1
        print >> fh, '</td>'
        print >> fh, '</tr>'
        print >> fh, '</table><br>'

statsHeader = '''\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<head>
    <title>Outer Space Statistics for Game %s</title>
    <link rel="STYLESHEET" href="../styles.css" type="text/css">
</head>
<body>

<center>

<h1>Statistics for galaxy %s%s</h1>

<table cellspacing=2 border=0 cellpadding=5 width="80%%" class="main">
<tr>
    <td valign="top">
<!-- body start -->
'''

statsFooter = '''\
<!-- body end -->
</td>
</tr>
<tr>
    <td class="footer" colspan=2 align="center">&copy; 2001 - %s Ludek Smid</td>
</tr>
</table>
</center>

</body>
</html>''' % time.localtime()[0]

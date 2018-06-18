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
import os

from ige import log
from ige.ClientMngr import ClientMngr
from ige.Config import Config
from ige.Const import OID_UNIVERSE
from ige.ospace.GameMngr import GameMngr
from ige.IssueMngr import IssueMngr
from ige.MsgMngr import MsgMngr
from ige.SQLiteDatabase import Database, DatabaseString

def rpc(f):
    return f

class GameServer(object):
    """GameServer object manages one or more GameMngr object representing
    individual games"""

    def __init__(self, configuration):
        self.loadConfigFile(configuration)
        # inititalization
        self.initializeSharedMngrs()
        # initialize games
        self.games = list()
        for section in self.config.sections():
            if not section.startswith("game"):
                continue
            config = self.config[section]
            log.message("INITIALIZING GAME", config.gameid)
            self.initializeGame(config)

    def shutdown(self):
        """Shutdown whole game server"""
        for game in self.games:
            game.shutdown()
        del self.games
        self.clientMngr.shutdown()
        del self.clientMngr
        self.issueMngr.shutdown()
        del self.issueMngr

    def loadConfigFile(self, configuration):
        defaults = dict(
            cwd = os.path.abspath(os.getcwd()),
        )
        self.config = Config(configuration, defaults)
        # make sure we have required keys defined
        assert self.config.server.datadir, "server.datadir MUST be defined"
        assert self.config.server.dbdir, "server.dbdir MUST be defined"

    def initializeSharedMngrs(self):
        """Initialize managers that are shared across all game instances"""
        self.issueMngr = IssueMngr()
        # client manager
        db = DatabaseString(self.config.server.dbdir, "accounts", cache = 100)
        self.clientMngr = ClientMngr(db, self.config.server.authmethod, self.config.server.datadir)

    def initializeGame(self, config):
        """Initialize game according to configuration file fragment"""
        gameID = config.gameid
        # make sure we have required keys defined
        assert config.galaxytype, "%s.galaxytype MUST be defined" % gameID
        assert config.name, "%s.name MUST be defined" % gameID
        # initialize database and objects
        gameDB = Database(self.config.server.dbdir, "%s_game" % gameID, cache = 15000)
        msgDB = DatabaseString(self.config.server.dbdir, "%s_msgs" % gameID, cache = 1000)
        msgMngr = MsgMngr(msgDB)
        gameMngr = GameMngr(gameID, config, self.clientMngr, msgMngr, gameDB, self.config.server.datadir, config.name)
        # reset game if Universe does not exist
        if not gameDB.has_key(OID_UNIVERSE):
            log.message('Resetting game \'%s\'...' % gameID)
            gameMngr.reset()
        # normal operations
        gameMngr.init()
        if self.config.server.upgradegames:
            gameMngr.upgrade()
        msgMngr.upgrade()
        gameMngr.start()
        # keep reference to this game
        self.games.append(gameMngr)

    @rpc
    def getConfiguration(self):
        """Return configuration of the server"""
        return

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

def runAIClient(options):
    import time
    import traceback
    import sys
    import os

    # tweak PYTHONPATH
    basepath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    sys.path.insert(0, os.path.join(basepath, "client/osci"))

    for item in ("libsrvr", "server/lib"):
        path = os.path.join(basepath, item)
        if os.path.exists(path):
            sys.path.insert(0, path)
            break

    from config import Config

    import osci, random, time
    import ige.version
    from ige import log
    import os, os.path
    import re

    # log initialization
    log.message("Starting Outer Space Client", ige.version.versionString)
    log.debug("sys.path =", sys.path)
    log.debug("os.name =", os.name)
    log.debug("sys.platform =", sys.platform)
    log.debug("os.getcwd() =", os.getcwd())
    log.debug("sys.frozen =", getattr(sys, "frozen", None))

    # create required directories
    if not os.path.exists(options.configDir):
        os.makedirs(options.configDir)

    # client
    import ai_client as client
    from igeclient.IClient import IClientException
    if options.ai:
        try:
            ai = __import__("AIs." + options.ai)
            ai = sys.modules["AIs." + options.ai]
        except:
            # This prints the type, value, and stack trace of the
            # current exception being handled.
            traceback.print_exc()
            raise
    else:
        raise Exception, 'You have to provide AI.'

    import ige.ospace.Const as Const

    import gdata
    # reload is here for multiprocessing support (as the process is used more
    # than once
    reload(client)
    gdata.config = Config(os.path.join(options.configDir, 'ais_dummy'))
    client.initialize(options.server, options)

    import gettext
    tran = gettext.NullTranslations()
    tran.install(unicode = 1)

    if options.login:
        login = options.login
    else:
        raise Exception, 'You have to provide login.'

    if options.password:
        password = options.password
    else:
        raise Exception, 'You have to provide password.'

    # first get list of sessions, then iterate over them
    # this is to prevent exceptions flooding logs
    # TODO: make session optional argument for main_ai_pool
    if client.login(options.game, login, password):
        activePositions = client.cmdProxy.getActivePositions()
        client.logout()
        if options.test:
            return True
    else:
        return False

    for playerID, galaxyName, playerType in activePositions:
        if options.galaxies and galaxyName not in options.galaxies:
            continue
        client.login(options.game, login, password)
        client.cmdProxy.selectPlayer(playerID)
        client.updateDatabase()
        try:
            ai.run(client)
        except Exception as e:
            # This prints the type, value, and stack trace of the
            # current exception being handled.
            traceback.print_exc()
            raise e
        client.logout()

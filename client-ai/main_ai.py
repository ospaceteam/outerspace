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
    import ai_handler
    from igeclient.IClient import IClientException
    if options.ai:
        ai = __import__("AIs." + options.ai)
        ai = sys.modules["AIs." + options.ai]
    else:
        raise Exception, 'You have to provide AI.'

    import ige.ospace.Const as Const

    import gdata
    # reload is here for multiprocessing support (as the process is used more
    # than once
    reload(client)
    gdata.config = Config(os.path.join(options.configDir, 'ais_dummy'))
    client.initialize(options.server, ai_handler, options)

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

    if client.login(options.game, login, password):
        if options.test:
            client.logout()
            return True
        # event loop
        client.updateDatabase()
        ai.run(client)
        client.logout()
        log.debug("Shut down")
    else:
        return False


    # event loop
    client.updateDatabase()
    ai.run(client)
    client.logout()
    log.debug("Shut down")


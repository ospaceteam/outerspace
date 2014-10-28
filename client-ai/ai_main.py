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

import time

from config import Config

import osci, random, time
import ige.version
from ige import log
import sys, os, os.path
import re
from optparse import OptionParser

# log initialization
log.message("Starting Outer Space Client", ige.version.versionString)
log.debug("sys.path =", sys.path)
log.debug("os.name =", os.name)
log.debug("sys.platform =", sys.platform)
log.debug("os.getcwd() =", os.getcwd())
log.debug("sys.frozen =", getattr(sys, "frozen", None))

# parse command line parameters
parser = OptionParser()
parser.add_option("",  "--configdir", dest = "configDir", 
    metavar = "DIRECTORY", 
    default = os.path.join(os.path.expanduser("~"), ".outerspace"), 
    help = "Override default configuration directory", 
)
parser.add_option("",  "--server", dest = "server", 
    metavar = "HOSTNAME:PORT", 
    default = "www.ospace.net:9080",
    help = "Outer Space server location"
)
parser.add_option("", "--login", dest = "login",
	metavar = "LOGIN",
	default = None,
	help = "Login name of the AI player.",
)
parser.add_option("", "--password", dest = "password",
	metavar = "PASSWORD",
	default = None,
	help = "Corresponding password of the AI player.",
)
parser.add_option("", "--ai", dest = "ai",
	metavar = "AI",
	default = None,
	help = "Type of the AI applied."
)

options, args = parser.parse_args()

if args:
  parser.error("No additional arguments are supported")

# create required directories
if not os.path.exists(options.configDir):
    os.makedirs(options.configDir)

# client
import ai_client as client
import ai_handler
from igeclient.IClient import IClientException
if options.ai:
	exec ("import AIs." + options.ai + " as ai")
else:
	raise Exception
from ige.ospace.Const import *

import gdata
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

client.login('Alpha', login, password)
# event loop
client.updateDatabase()
ai.run(client)

client.logout()

log.debug("Shut down")

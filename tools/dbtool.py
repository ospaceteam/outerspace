#!/usr/bin/env python2
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

# tweak PYTHONPATH
import os
import sys
from optparse import OptionParser

# setup system path
baseDir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(baseDir, '..', 'server', "lib"))

import ige
from ige import log
import ige.ospace.Const as Const
from ige.SQLiteDatabase import Database, DatabaseString

# parse command line arguments
parser = OptionParser(usage = "usage: %prog [options]")
parser.add_option("",  "--configdir", dest = "configDir",
    metavar = "DIRECTORY", default = os.path.join(os.path.expanduser("~"), ".outerspace"),
    help = "Override default configuration directory",)
options, args = parser.parse_args()

gameName = 'Alpha'

gameDB = Database(os.path.join(options.configDir,"db_data"), "game_%s" % gameName, cache = 15000)
clientDB = DatabaseString(os.path.join(options.configDir,"db_data"), "accounts", cache = 100)
msgDB = DatabaseString(os.path.join(options.configDir,"db_data"), "messages", cache = 1000)
bookingDB = DatabaseString(os.path.join(options.configDir,"db_data"), "bookings", cache = 100)

# insert code


# 

for db in gameDB, clientDB, msgDB, bookingDB:
    db.shutdown()


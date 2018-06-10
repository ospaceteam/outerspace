#!/usr/bin/env python2
#
#  Copyright 2001 - 2017 Ludek Smid [http://www.ospace.net/]
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
import argparse
import atexit
import os
import sys

import common as c

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--configdir", dest = "configdir", default = None,
        type = str, metavar = "CONFIGDIR", help = ("Directory where server data are stored, "
                "by default it is temporary directory. If existing directory is specified, "
                "it won't recreate galaxies but continue with what is already available."))
parser.add_argument("--history", dest = "history", default = "./history",
        type = str, metavar = "PATH", help = "Directory where screenshots will be saved.")
parser.add_argument("--days", dest = "days", default = 6,
    type = int, metavar = "N", help = "Process N turns on server")
parser.add_argument("--turn-skip", dest = "turnSkip", default = 6,
    type = int, metavar = "N", help = "Process N turns on server")
args = parser.parse_args()

c.initPaths(args.configdir)
if not c.startServer():
    sys.exit()
atexit.register(c.killServer)
if args.configdir is None:
    c.deleteGalaxy(10000) # legacy - too big to be a default
    c.createGalaxy("Circle1SP")
    c.createGalaxy("Circle3SP")
    c.createGalaxy("Circle9P")
    c.startServerTime()

for screenshot_cycle in xrange(args.days * 24 / args.turnSkip):
    c.doTurns(args.turnSkip, args.turnSkip, verbose=False)
    c.makeScreenshots(args.history)
c.stopServer()


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
import logging as log
import os
import sys
import time

import common as c

log.basicConfig(level=log.INFO, format='%(levelname)-7s: %(message)s')

def slicer(slices):
    slices = int(slices)
    if 24 % slices:
        raise ArgumentError
    return 24 / slices

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--configdir", dest = "configdir", default = None,
        type = str, metavar = "CONFIGDIR", help = ("Directory where server data are stored, "
                "by default it is temporary directory. If existing directory is specified, "
                "it won't recreate galaxies but continue with what is already available."))
parser.add_argument("--history", dest = "history", default = "./history",
        type = str, metavar = "PATH", help = "Directory where screenshots will be saved.")
parser.add_argument("--days", dest = "days", default = 0,
    type = int, metavar = "N", help = "Process N days of the gameplay, default is 0.")
parser.add_argument("--day-slices", dest = "turnSkip", default = slicer(4),
    type = slicer, metavar = "N", help = "Process N cycles per day, default is 4.")
parser.add_argument("--galaxy-check", dest = "galaxy_check", default = None, nargs = 2,
        metavar = "GALAXY_TYPE NUMBER", help = ("Allows visual checking of galaxy generator "
                  "settings by easily generating selected NUMBER of GALAXY_TYPE galaxies."))
args = parser.parse_args()

c.initPaths(args.configdir)
if not c.startServer():
    sys.exit()
atexit.register(c.killServer)
if args.configdir is None:
    if not args.galaxy_check:
        # default set
        #c.createGalaxy("Circle1SP")
        #c.createGalaxy("Circle3SP")
        #c.createGalaxy("Circle2CP")
        c.createGalaxy("Circle3CP")
        #c.createGalaxy("Circle9P")
        #c.createGalaxy("Circle42P")
    else:
        galaxy_type, quantity = args.galaxy_check[0], int(args.galaxy_check[1])
        for num in xrange(quantity):
            c.createGalaxy(galaxy_type, "{0}.{1}".format(galaxy_type, num + 1))

    c.startServerTime()

c.makeScreenshots(args.history)
for day in xrange(args.days):
    start_time = time.time()
    for _slice in xrange(24 / args.turnSkip):
        c.doTurns(args.turnSkip, args.turnSkip, verbose=False)
        c.makeScreenshots(args.history)
    log.info("Day {0} rendered ({1}s).".format(day + 1, int(time.time() - start_time)))
c.stopServer()


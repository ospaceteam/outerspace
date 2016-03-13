#
#  Copyright 2001 - 2010 Ludek Smid [http://www.ospace.net/]
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

# set current directory
import os
import os.path
import sys

def isFrozen():
	return (hasattr(sys, "frozen") or # new py2exe or py2app
		hasattr(sys, "importers") # old py2exe
	)

def getMainDir():
	if isFrozen():
		return os.path.dirname(os.path.abspath(sys.executable))
	return os.path.dirname(os.path.abspath(sys.argv[0]))

baseDir = os.path.join(os.path.expanduser("~"), ".outerspace")

if not os.path.exists(baseDir):
	os.makedirs(baseDir)

# create stdout, stderr (it will crash sometimes using py2exe without this)
sys.stdout = open(os.path.join(baseDir, "stdout.log"), "w")
sys.stderr = open(os.path.join(baseDir, "stderr.log"), "w")

if sys.platform.startswith("darwin"):
    # we are all set as py2app sets current directory correctly
    pass
else:
    os.chdir(getMainDir())

# start application
if not isFrozen():
	sys.path.insert(0, os.path.join(getMainDir(), "lib"))

	for item in (os.path.join(getMainDir(), "libsrvr"), os.path.join(getMainDir(), "../server/lib")):
    		if os.path.exists(item):
        		sys.path.insert(0, item)
        		break

import osci.main

# close file handles
sys.stdout.close()
sys.stderr.close()

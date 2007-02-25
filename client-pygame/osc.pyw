#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

# set current directory
import sys, os, os.path

os.chdir(os.path.dirname(sys.executable))

# create required directories
if not os.path.exists('var'):
	os.mkdir('var')

# create stdout, stderr (it will crash sometimes using py2exe without this)
sys.stdout = open('var/stdout.log', 'w')
sys.stderr = open('var/stderr.log', 'w')

# mount pyz libraries
sys.path.append("osclib.pyz")

# start application
import osci.main

# close file handles
sys.stdout.close()
sys.stderr.close()

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

import sys
from distutils.core import setup

# collect data files
data_files = []
data_files.append(
    (
        ".",
        ["../ChangeLog.txt", "../COPYING", "../README", "../README_CZ"]
    )
)
data_files.append(
    (
        "data",
        ["data/SystemNames.txt", "data/galaxy-Circle4P.xml"]
    )
)

# version
sys.path.append("../client-pygame/lib")
from osci import version
sys.path.remove("../client-pygame/lib")

setup(
    name = 'OuterSpaceServer',
    version = '%d.%d.%d%s' % version,
    description = 'OuterSpace Server',
    author = 'Ludek Smid',
    author_email = 'qark@ospace.net',
    maintainer = "Ludek Smid",
    maintainer_email = "qark@ospace.net",
    url = 'http://www.ospace.net/',
    data_files = data_files,
    package_dir = {"": "lib"},
    packages = ['ige', 'igeclient', 'medusa', 'ige.ospace', 'ige.ospace.Rules'],
    scripts = ["ospace-server", "osclient"],
)


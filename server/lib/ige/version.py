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

major = 0
minor = 5
revision = 70
# status must be either empty string or must start with a dash
status = ""

assert not status or status.startswith("-"), "Status MUST start with dash if set"

version = {
    "major": major,
    "minor": minor,
    "revision": revision,
    "status": status,
}

versionString = "%(major)d.%(minor)d.%(revision)d%(status)s" % version

clientURLs = {
    "*": (
        "browser",
        "https://github.com/ospaceteam/outerspace/archive/%(major)d.%(minor)d.%(revision)d%(status)s.tar.gz" % version,
    ),
}

#!/usr/bin/env python
#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
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

import xmlrpclib, sys

if len(sys.argv) != 5:
	print "Usage: useradd.py login password nick e-mail"
	sys.exit(1)

server = xmlrpclib.ServerProxy("http://localhost:9080/RPC2")

# send hello
sid, challenge = server.clientmngr.hello("dummy", "useradd.py")

# create account
server.clientmngr.createAccount(sid, sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

server.clientmngr.logout(sid)

print "User added"

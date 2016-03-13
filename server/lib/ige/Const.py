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

# return values
SUCC = 1
FAIL = 0

# reserved OIDs
OID_NONE = 0
OID_UNIVERSE = 1
OID_MAP = 2
OID_ADMIN = 10
OID_GUEST = 50
OID_I_LOGIN2OID = 100
OID_I_NAME2OID = 101

# Free oids starts at
OID_FREESTART = 10000

# Game status
GS_INIT = 0
GS_MAINT = 1
GS_RUNNING = 2
GS_BUSY = 3
GS_STOPPED = 4
GS_SDOWN = 5
GS_TURNINPROG = 6

# Access Rights Level
AL_NONE = 0
AL_INFO = 50
AL_FULL = 100
AL_OWNER = 110
AL_ADMIN = 1000

# Object types
T_UNKNOWN = 0
T_OBJECT = 1
T_UNIVERSE = 2
T_PLAYER = 3

# Session messages
SMESSAGE_NEWTURN = 1
SMESSAGE_NEWMESSAGE = 2

# Admin
ADMIN_LOGIN = 'admin'

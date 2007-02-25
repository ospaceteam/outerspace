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

def enableConstruction(client):
	enabled1 = 0
	enabled2 = 0
	player = client.getPlayer()
	for techID in player.techs:
		tech = client.getTechInfo(techID)
		if tech.isShipHull:
			enabled1 = 1
			if enabled2: break
		elif tech.isShipEquip and tech.subtype == "seq_ctrl":
			enabled2 = 1
			if enabled1: break

	return enabled1 and enabled2

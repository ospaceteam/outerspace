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

import client, string, gdata
from ige.ospace import Rules

SHORT = 1
LONG = 2

descr = {}

def id2Class(id):
	return gdata.shipClasses[id]

def num2Perc(num):
        return (num*100)

def num2ZeroPerc(num):
        val = ((num-1)*100)
        return val

def num2PlusZeroPerc(num): #make it positive without the + sign
        val = ((num-1)*100)
        if val < 0:
            val = -1*val
        return val


def add(subtype, detail, attr, text, filter, eff):
	global descr
	if subtype not in descr: descr[subtype] = []
	descr[subtype].append((detail, attr, text, filter, eff))

# i18n (delayed translation)
def N_(msg): return msg

add("*", SHORT, "engPwr", N_("power %+d"), int, 1)

add("seq_wpn", LONG, "weaponAtt", N_("wpn att %+d"), int, 1)
#add("seq_wpn", SHORT, "weaponClass", N_("trgt %s"), id2Class, 0)
add("seq_wpn", SHORT, "weaponDmgMin", N_("min dmg %d"), int, 1)
add("seq_wpn", SHORT, "weaponDmgMax", N_("max dmg %d"), int, 1)
add("seq_wpn", SHORT, "weaponROF", N_("ROF %.1f"), float, 0)
add("seq_wpn", SHORT, "weaponIgnoreShield", N_("ignores shield"), None, 0)

add("*", SHORT, "scannerPwr", N_("scanner %d"), int, 1)

add("*", LONG, "minHull", N_("min hull %s"), id2Class, 0)
add("*", LONG, "maxHull", N_("max hull %s"), id2Class, 0)
add("*", LONG, "maxInstallations", N_("max %s"), int, 0)
add("*", LONG, "maxHP", N_("HP %+d"), int, 1)
add("*", LONG, "slots", N_("slots %d"), int, 0)
add("*", LONG, "weight", N_("weight %d"), int, 0)
add("*", LONG, "combatAtt", N_("att %+d"), int, 1)
add("*", LONG, "combatDef", N_("def %+d"), int, 1)
add("*", LONG, "missileDef", N_("mis. def %+d"), int, 1)
add("*", LONG, "signature", N_("sign. %+d"), int, 1)
add("*", LONG, "signatureCloak", N_("%d%% cloaking"), num2PlusZeroPerc, 0)
add("*", LONG, "signatureDecloak", N_("visibility %+d%%"), num2ZeroPerc, 0)
add("*", LONG, "combatAttPerc", N_("att %+d%%"), num2ZeroPerc, 1)
add("*", LONG, "combatDefPerc", N_("def %+d%%"), num2ZeroPerc, 1)
add("*", LONG, "missileDefPerc", N_("mis. def %+d%%"), num2ZeroPerc, 1)
add("*", LONG, "shieldPerc", N_("shield %d%%"), num2Perc, 1)
add("*", LONG, "hardShield", N_("hard shield %d%%"), num2Perc, 1)
add("*", LONG, "damageAbsorb", N_("absorb dmg %d"), int, 0)
add("*", LONG, "autoRepairPerc", N_("repair %d%%"), num2Perc, 1)
add("*", LONG, "autoRepairFix", N_("repair %d"), int, 1)


# i18n
del N_

def getShortDescr(techID, myDetail = SHORT):
	tech = client.getFullTechInfo(techID)
	techEff = Rules.techImprEff[client.getPlayer().techs.get(techID, Rules.techBaseImprovement)]
	result = []
	# specific
	if tech.subtype in descr:
		for detail, attr, text, filter, eff in descr[tech.subtype]:
			if tech.isDefault(attr):
				continue
			if detail <= myDetail:
				if not filter:
					result.append(_(text))
				elif eff:
					result.append(_(text) % filter(techEff * getattr(tech, attr)))
				else:
					result.append(_(text) % filter(getattr(tech, attr)))
	# general
	for detail, attr, text, filter, eff in descr["*"]:
		if tech.isDefault(attr):
			continue
		if detail <= myDetail:
			if not filter:
				result.append(_(text))
			elif eff:
				result.append(_(text) % filter(techEff * getattr(tech, attr)))
			else:
				result.append(_(text) % filter(getattr(tech, attr)))
	if result:
		return string.join(result, ", ")
	else:
		return _("N/A")

def getLongDescr(techID):
	return getShortDescr(techID, LONG)

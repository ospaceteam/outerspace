import string
from ige.ospace import Rules

SHORT = 1
LONG = 2

descr = {}

def cclass2Text(cclass):
    return ["small", "medium", "large", "planet"][cclass]

def add(subtype, detail, attr, text, filter, eff):
	global descr
	if subtype not in descr: descr[subtype] = []
	descr[subtype].append((detail, attr, text, filter, eff))

add("*", SHORT, "engPwr", "power %+d", int, 1)

add("seq_wpn", LONG, "weaponAtt", "wpn att %+d", int, 1)
add("seq_wpn", SHORT, "weaponClass", "trgt class %s", cclass2Text, 0)
add("seq_wpn", SHORT, "weaponDmgMin", "min dmg %d", int, 1)
add("seq_wpn", SHORT, "weaponDmgMax", "max dmg %d", int, 1)
add("seq_wpn", SHORT, "weaponROF", "ROF %.1f", float, 0)
add("seq_wpn", SHORT, "weaponIgnoreShield", "ignores shield", None, 0)

add("*", SHORT, "scannerPwr", "scanner %d", int, 1)

add("*", LONG, "maxHP", "HP %+d", int, 1)
add("*", LONG, "slots", "slots %d", int, 0)
add("*", LONG, "weight", "weight %d", int, 0)
add("*", LONG, "combatAtt", "att %+d", int, 1)
add("*", LONG, "combatDef", "def %+d", int, 1)
add("*", LONG, "missileDef", "mis. def %+d", int, 1)
add("*", LONG, "signature", "sign. %+d", int, 1)
add("*", LONG, "minHull", "min hull %s", cclass2Text, 0)

def getShortDescr(techID, myDetail = SHORT, improvement = 3):
	tech = Rules.techs[techID]
	techEff = Rules.techImprEff[improvement]
	result = []
	# specific
	if tech.subtype in descr:
		for detail, attr, text, filter, eff in descr[tech.subtype]:
			if tech.isDefault(attr):
				continue
			if detail <= myDetail:
				if not filter:
					result.append(text)
				elif eff:
					result.append(text % filter(techEff * getattr(tech, attr)))
				else:
					result.append(text % filter(getattr(tech, attr)))
	# general
	for detail, attr, text, filter, eff in descr["*"]:
		if tech.isDefault(attr):
			continue
		if detail <= myDetail:
			if not filter:
				result.append(text)
			elif eff:
				result.append(text % filter(techEff * getattr(tech, attr)))
			else:
				result.append(text % filter(getattr(tech, attr)))
	if result:
		return string.join(result, ", ")
	else:
		return _("N/A")

def getLongDescr(techID, improvement = 3):
	return getShortDescr(techID, LONG, improvement)

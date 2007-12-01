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

#
# This module contains messages
#
from ige.ospace.Const import *
from ige import NoSuchObjectException
import client, types, string, res, gdata
from ige import log

#
# Transform routines
#
def techID2Name(techID):
	if techID >= 1000:
		return _(client.getTechInfo(techID).name.encode())
	else:
		return client.getPlayer().shipDesigns[techID].name

def objID2Name(objID):
	obj = client.get(objID, noUpdate = 0, publicOnly = 1)
	return getattr(obj, 'name', res.getUnknownName())

def objIDList2Names(objIDs):
	names = []
	for objID in objIDs:
		obj = client.get(objID, noUpdate = 1, publicOnly = 1)
		if hasattr(obj, 'owner') and obj.owner != obj.oid:
			try:
				owner = _(' (%s)') % client.get(obj.owner, noUpdate = 1, publicOnly = 1).name
			except AttributeError:
				owner = ''
		else:
			owner = ''
		text = _('%s%s') % (getattr(obj, 'name', res.getUnknownName()), owner)
		names.append(text)
	return string.join(names, ', ')

def stratID2Name(resID):
	return _(gdata.stratRes[resID])

def float2percent(number):
	return int(number * 100)

def plType2Name(plType):
	return gdata.planetTypes[plType]

def designID2Name(designID):
	return client.getPlayer().shipDesigns[designID].name

def votes2Txt((votes, voters)):
	lines = []
	nominated = votes.keys()
	nominated.sort(lambda a, b: cmp(votes[b], votes[a]))
	for playerName in nominated:
		if playerName == None:
			continue
		l = []
		for name in voters[playerName]:
			l.append(name)
		text = "   %s got %d votes from %s." % (
			playerName,
			votes[playerName],
			", ".join(l),
		)
		lines.append(text)
	if None in votes:
		l = []
		for name in voters[None]:
			l.append(name)
		text = "   %s abstained [%d votes]." % (
			", ".join(l),
			votes[None],
		)
		lines.append(text)
	return "\n".join(lines)

def impMsg(msg):
	return "\n".join(msg)
#
# Data
#

# severity codes
CRI = 3
MAJ = 2
MIN = 1
INFO = 0
NONE = INFO

# i18n (delayed translation)
def N_(msg): return msg

msgData = {}

def addMsg(msgID, name, transform = None, severity = NONE):
	global msgData
	msgData[msgID] = (name, transform, severity)

addMsg(MSG_COMPLETED_RESEARCH, N_('Research completed: %(1)s'), (techID2Name,), CRI)
addMsg(MSG_WASTED_SCIPTS, N_('%(1)d research points not used.'), severity = MIN)
addMsg(MSG_CANNOTBUILD_SHLOST, N_('Cannot build on planet - ship may be lost.'), severity = CRI)
addMsg(MSG_CANNOTBUILD_NOSLOT, N_('Cannot build on planet - no free slot.'), severity = CRI)
# NOT NEEDED addMsg(MSG_DESTROYED_BUILDING, N_('Structure destroyed: %(1)s'), (techID2Name,), MAJ)
addMsg(MSG_WASTED_PRODPTS, N_('Construction problem: no task\n\n%(1)d construction points were not used because there was no task to fulfill.'), (int,), severity = INFO)
addMsg(MSG_LOST_PLANET, N_('Planet lost.'), severity = CRI)
addMsg(MSG_COMPLETED_STRUCTURE, N_('Structure completed: %(1)s'), (techID2Name,), MIN)
addMsg(MSG_DELOY_HANDLER, N_('A deployment of %(1)s was completed'), (techID2Name,), MIN)
addMsg(MSG_COMPLETED_SHIP, N_('Ship completed: %(1)s'), (techID2Name,), MIN)
addMsg(MSG_GAINED_PLANET, N_('New planet.'), severity = CRI)
addMsg(MSG_COMBAT_RESULTS, N_('Combat with: %(4)s. HP lost: we %(1)d, they %(2)d.\n\nEnemy lost %(2)d HP, we lost %(1)d HP and %(3)d ships/structures. We attacked/were attacked by %(4)s.'), (int, int, int, objIDList2Names), MAJ)
addMsg(MSG_COMBAT_LOST, N_('Battle lost: we were defeated by %(1)s.'), (objID2Name,), CRI)
addMsg(MSG_DESTROYED_FLEET, N_('Fleet destroyed.'), severity = CRI)
addMsg(MSG_COMBAT_WON, N_('Battle won: we defeated %(1)s.'), (objID2Name,), CRI)
addMsg(MSG_NEW_GOVCENTER, N_('A new government center established.'), severity = CRI)
addMsg(MSG_REVOLT_STARTED, N_('Planet revolt started - production halved for the next turns.'), severity = CRI)
addMsg(MSG_REVOLT_ENDED, N_('Planet revolt ended - production restored.'), severity = CRI)
addMsg(MSG_INVALID_TASK, N_('Construction of %(1)s is not valid - construction suspended.'), (techID2Name,), severity = CRI)
addMsg(MSG_NOSUPPORT_POP, N_('Population decreased.\n\nPopulation of this planet has decreased. Build more facilities producing food.'), severity = CRI)
addMsg(MSG_COMPLETED_PROJECT, N_('Project finished: %(1)s'), (techID2Name,), MIN)
addMsg(MSG_ENABLED_TIME, N_('Time in galaxy started to run...'), severity = CRI)
addMsg(MSG_MISSING_STRATRES, N_('Strategic resource missing: %(1)s'), (stratID2Name,), MAJ)
addMsg(MSG_DELETED_RESEARCH, N_('Research task deleted: %(1)s'), (techID2Name,), CRI)
addMsg(MSG_EXTRACTED_STRATRES, N_('Strategic resource extracted: %(1)s'), (stratID2Name,), MIN)
addMsg(MSG_EXTRACTED_ANTIMATTER_SYNTH, N_('Strategic resource synthesized: 4 units of %(1)s'), (stratID2Name,), MIN)
addMsg(MSG_DOWNGRADED_PLANET_ECO, N_('Planet downgraded to: %(1)s'), (plType2Name,), CRI)
addMsg(MSG_UPGRADED_PLANET_ECO, N_('Planet upgraded to: %(1)s'), (plType2Name,), CRI)
addMsg(MSG_UPGRADED_SHIP, N_('Ship upgraded from %(1)s to %(2)s'), (unicode,unicode), MIN)
addMsg(MSG_DELETED_DESIGN, N_('Obsolete ship design deleted: %(1)s'), (unicode,), CRI)
addMsg(MSG_CANNOT_UPGRADE_SR, N_('Cannot upgrade ship from %(1)s to %(2)s\n\nCannot upgrade ship from %(1)s to %(2)s because of we have not enough of %(3)s.'), (unicode,unicode,stratID2Name), MAJ)
addMsg(MSG_DAMAGE_BY_SG, N_('Malfunctional Star Gate, lost %(1)d %% HP\n\nOur fleet has arrived at system with no or malfunctional Star Gate or Comm/Scann Center. Every ship lost %(1)d %% hitpoints due to intensive deceleration.'), (int,), MAJ)
addMsg(MSG_GAINED_FAME, N_('Gained %(1)d fame.'), severity = INFO)
addMsg(MSG_LOST_FAME, N_('Lost %(1)d fame.'), severity = CRI)
addMsg(MSG_GAINED_TECH, N_('Gained %(1)s technology at sublevel %(2)d.'), (techID2Name, int), severity = INFO)
addMsg(MSG_ENTERED_WORMHOLE, N_('Your fleet entered a wormhole at %(1)s and exited at %(2)s.'), (unicode,unicode), MIN)
addMsg(MSG_NOT_ENTERED_WORMHOLE, N_('Cannot enter wormhole - ship may be lost.'), severity = MIN)
addMsg(MSG_FOUND_WORMHOLE, N_('You have located a wormhole'), severity = MIN) #todo

# GNC
addMsg(MSG_GNC_EMR_FORECAST, N_("EMR Forecast\n\nLevel of the electromagnetic radiation is believed to be about %(1)d %% of the average level for the next %(2)s turns"), (float2percent, res.formatTime), severity = MIN)
addMsg(MSG_GNC_EMR_CURRENT_LVL, N_("EMR Forecast\n\nCurrent level of the electromagnetic radiation is about %(1)d %% of the average level."), (float2percent,), severity = MIN)
addMsg(MSG_GNC_VOTING_COMING, N_("Elections!\n\nIt's 2:00 turns before elections! Don't hesitate and vote for the best commander!"), (), severity = MAJ)
addMsg(MSG_GNC_VOTING_NOWINNER, N_("Election results! Nobody won...\n\nThe results from the last elections have been published. Nobody was strong enough to be elected as a leader of our galaxy. Can we find such person another day?\n\nThe official election results follow:\n\n%(1)s\n\n"), (votes2Txt,), severity = MAJ)
addMsg(MSG_GNC_VOTING_LEADER, N_("Election results! Leader elected!\n\nThe results from the last elections have been published. %(1)s has proved to be the most supported person and has been elected as our Leader. May be, %(1)s can become an Imperator one day.\n\nThe official election results follow:\n\n%(2)s\n\n"), (unicode, votes2Txt,), severity = MAJ)
addMsg(MSG_GNC_VOTING_IMPERATOR, N_("Election results! Imperator elected!\n\nThe results from the last elections have been published. %(1)s has proved to be the most supported person and has been elected as our glorified Imperator. Congratulations - you proved to be the best of all of us!\n\nThe official election results follow:\n\n%(2)s\n\n"), (unicode, votes2Txt,), severity = MAJ)

addMsg(MSG_GNC_GALAXY_RESTARTED, N_("Galaxy %(2)s knows it's winner - Imperator %(1)s\n\nToday the galaxy %(2)s has been united and the peace has been restored. Majority of commanders voted for Imperator %(1)s as their supreme leader. Congratulations, Imperator, you were brave and wise!\n\nMessage from imperator:\n%(3)s"), (unicode, unicode, impMsg), severity = MAJ)
addMsg(MSG_GNC_GALAXY_GENERATOR, N_("Galaxy %(1)s generation is completed. Galaxy specifications:\n\n%(2)s"), (unicode, votes2Txt,), severity = INFO)
addMsg(MSG_GNC_GALAXY_AUTO_RESTARTED, N_("Galaxy %(1)s has ended\n\nToday the galaxy %(1)s has been automatically ended.\n\nReason:\n%(2)s"), (unicode, impMsg), severity = MAJ)

# i18n
del N_

#
# Interface
#

def getMsgText(msgID, data):
	msg, transform, severity = msgData.get(msgID, (None, None, None))
	# create default messages
	if not msg:
		return _('ERROR\nMissing text for msg %d: %s') % (msgID, repr(data))
	# there is message text -> create message
	# force unicode
	msg = _(msg)
	if data == None:
		return msg
	try:
		# tranform data
		newData = {}
		if not (type(data) == types.ListType or type(data) == types.TupleType):
			data = (data,)
		if transform:
			index = 1
			for tranFunc in transform:
				newData[str(index)] = tranFunc(data[index - 1])
				index += 1
		else:
			index = 1
			for item in data:
				newData[str(index)] = item
				index += 1
		text = msg % newData
	except Exception, e:
		# wrong arguments -> default message
		log.warning("Erorr while formating message")
		return _('ERROR\nWrong format for msg %d: %s\nException: %s: %s\nFormat: %s') % (msgID, repr(data), str(e.__class__), str(e), msg)
	return text

def getMsgSeverity(msgID):
	return msgData.get(msgID, (None, None, NONE))[2]

def getFullMessageText(message):
	"""Gets full text of automaticaly generated message

	If message has no data to generate, it returns empty
	string.
	"""
	text = ""
	if message.has_key("data"):
		sourceID, msgID, locationID, turn, data = message["data"]
		sev = getMsgSeverity(msgID)
		currTurn = client.getTurn()
		player = client.getPlayer()
		# source
		if sourceID != OID_NONE and sourceID != player.oid:
			obj = client.get(sourceID, noUpdate = 1, publicOnly = 1)
			if obj:
				if hasattr(obj,'customname') and obj.customname:
						source = _('"%s"') % obj.customname
				else:
						source = getattr(obj, 'name', res.getUnknownName())
			else:
				source = _('N/A')
		else:
			source = _('-')
		text = '%s%s\n' % (text, _("Source: %s") % source)
		# location
		if locationID != OID_NONE:
			obj = client.get(locationID, noUpdate = 1, publicOnly = 1)
			location = getattr(obj, 'name', res.getUnknownName())
		else:
			location = _('-')
		text = '%s%s\n' % (text, _("Location: %s") % location)
		text = '%s%s\n' % (text, _("Severity: %s") % _(gdata.msgSeverity[sev]))
		text = '%s%s\n' % (text, _("Time: %s [%s]") % (
			res.formatTime(turn),
			res.formatTime(turn - currTurn),
		))
		text = '%s%s\n' % (text, "")
		text = '%s%s\n' % (text, getMsgText(msgID, data))

	return text

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

from ige.IObject import IObject
from ige.IDataHolder import IDataHolder
from Const import *
import Rules
from IGalaxy import IGalaxy
import time, tempfile, os
import ige
from ige import log
from GalaxyGenerator import GenerateGalaxy
from ige import GameException

try:
	import ClientVersion
except ImportError:
	# fake it
	class ClientVersionClass:
		pass
	ClientVersion = ClientVersionClass()
	ClientVersion.version = (0, 0, 0, "?")
	ClientVersion.build = 0
	ClientVersion.revision = 0
	ClientVersion.versionString = "Version not specified"


class IUniverse(IObject):

	typeID = T_UNIVERSE

	forums = {"NEWS": 112, "QA": 112, "IDEAS": 112, "PUBLIC": 112, "ISSUES": 112}

	def init(self, obj):
		IObject.init(self, obj)
		#
		obj.name = "Outer Space"
		obj.turn = 0
		obj.owner = OID_ADMIN
		obj.galaxies = []
		obj.players = []
		# auto loading of galaxies
		obj.galX = 0.0
		obj.galY = 0.0
		obj.galXStep = 100.0
		obj.galYStep = 100.0
		obj.galFilename = ''
		obj.galID = ''

	def getIntroInfo(self, tran, obj):
		result = IDataHolder()
		result.cid = tran.cid
		result.turn = obj.turn
		result.serverTime = time.time()
		result.lastClientVersion = ClientVersion.version
		result.lastClientRevision = ClientVersion.revision
		return result

	getIntroInfo.public = 1
	getIntroInfo.accLevel = AL_NONE

	def multiGetInfo(self, tran, obj, objIDs):
		result = []
		messages = []
		# perform getInfo or getPublicInfo command for each objID
		for objID in objIDs:
			try:
				tmpObj, tmpMsgs = tran.gameMngr.execute(tran.session.sid, 'getInfo', objID)
			except ige.SecurityException:
				tmpObj, tmpMsgs = tran.gameMngr.execute(tran.session.sid, 'getPublicInfo', objID)
			except ige.NoSuchObjectException:
				tmpObj = None
			if tmpObj:
				result.append(tmpObj)
				messages.extend(tmpMsgs)
		# restore messages
		for msgID, data in messages:
			tran.session.messages[msgID] = data
		return result

	multiGetInfo.public = 1
	multiGetInfo.accLevel = AL_NONE

	def multiGetMsgs(self, tran, obj, mailboxes):
		result = []
		messages = []
		# perform getMsgs
		for objID, lastID in mailboxes:
			data, tmpMsgs = tran.gameMngr.execute(tran.session.sid, 'getMsgs', objID, lastID)
			result.append((objID, data))
			messages.extend(tmpMsgs)
		# restore messages
		for msgID, data in messages:
			tran.session.messages[msgID] = data
		return result

	multiGetMsgs.public = 1
	multiGetMsgs.accLevel = AL_NONE

	def createGalaxy(self, tran, obj):
		galaxy = self.new(T_GALAXY)
		galaxy.compOf = obj.oid
		oid = tran.db.create(galaxy)
		obj.galaxies.append(oid)
		return oid

	createGalaxy.public = 1
	createGalaxy.accLevel = AL_ADMIN

	def createAsteroid(self, tran, obj, x, y, targetID, speed, hp):
		asteroid = self.new(T_ASTEROID)
		tran.db.create(asteroid)
		self.cmd(asteroid).create(tran, asteroid, x, y, targetID, speed, hp)
		return asteroid.oid

	createAsteroid.public = 1
	createAsteroid.accLevel = AL_ADMIN

	def processINITPhase(self, tran, obj, data):
		try:
			## find active/inactive pacts
			# set all active/on pacts to active
			for playerID in obj.players:
				#@log.debug("Processing player", playerID)
				player = tran.db[playerID]
				for partyID in player.diplomacyRels:
					#@log.debug("Processing party", partyID)
					dipl = player.diplomacyRels[partyID]
					for pactID in dipl.pacts.keys():
						if pactID not in Rules.pactDescrs:
							# this is invalid pactID
							log.debug(playerID, "Deleting invalid pact with", partyID, "pact", pactID)
							del dipl.pacts[pactID]
							continue
						if dipl.pacts[pactID][0] > PACT_OFF:
							dipl.pacts[pactID][0] = PACT_ACTIVE
			# inactivate all pact that does not satisfy conditions
			changed = 1
			defaultPact = [PACT_OFF]
			while changed:
				changed = 0
				log.debug("Inactivate pacts iteration starting...")
				for playerID in obj.players:
					#@log.debug("Processing player", playerID)
					player = tran.db[playerID]
					# all parties of a player
					for partyID in player.diplomacyRels:
						#@log.debug("Processing party", partyID)
						party = tran.db[partyID]
						partyDipl = party.diplomacyRels.get(playerID, None)
						if not partyDipl:
							continue
						dipl = player.diplomacyRels[partyID]
						# correct relations
						dipl.relation = min(dipl.relation, partyDipl.relation)
						# all pacts with party
						for pactID in dipl.pacts:
							# check validity interval
							pactSpec = Rules.pactDescrs[pactID]
							if (dipl.relation < pactSpec.validityInterval[0] or \
								dipl.relation > pactSpec.validityInterval[1]) and \
								dipl.pacts[pactID][0] == PACT_ACTIVE:
								#@log.debug("Inactivating pact (validity interval)", playerID, pactID)
								dipl.pacts[pactID][0] = PACT_INACTIVE
								changed = 1
							# check conditions for the pact if pact is active
							if dipl.pacts[pactID][0] == PACT_ACTIVE:
								for condPactID in dipl.pacts[pactID][1:]:
									#@log.debug("Checking", playerID, pactID, "against", partyID, condPactID)
									if partyDipl and partyDipl.pacts.get(condPactID, defaultPact)[0] != PACT_ACTIVE:
										dipl.pacts[pactID][0] = PACT_INACTIVE
										changed = 1
		except Exception:
			log.warning("Cannot process diplomacy initialization")
		# TODO - send notifications if pacts are changed
		# remove old messages
		self.cmd(obj).deleteOldMsgs(tran, obj)
		return obj.players[:] + [OID_NATURE]

	processINITPhase.public = 1
	processINITPhase.accLevel = AL_ADMIN

	def processPRODPhase(self, tran, obj, data):
		raise NotImplementedError()

	processPRODPhase.public = 1
	processPRODPhase.accLevel = AL_ADMIN

	def processACTIONPhase(self, tran, obj, data):
		raise NotImplementedError()

	processACTIONPhase.public = 1
	processACTIONPhase.accLevel = AL_ADMIN

	def processBATTLEPhase(self, tran, obj, data):
		raise NotImplementedError()

	processBATTLEPhase.public = 1
	processBATTLEPhase.accLevel = AL_ADMIN

	def processFINALPhase(self, tran, obj, data):
		return obj.players[:] + [OID_NATURE]

	processFINALPhase.public = 1
	processFINALPhase.accLevel = AL_ADMIN

	def processFINAL2Phase(self, tran, obj, data):
		# distribute stats to contacts
		for playerID in obj.players:
			player = tran.db[playerID]
			for partyID in player.diplomacyRels:
				dipl = player.diplomacyRels[partyID]
				if dipl.contactType > CONTACT_NONE and tran.db.has_key(partyID):
					dipl.stats = tran.db[partyID].stats
				else:
					dipl.stats = None
		# imperator voting
		turn = tran.db[OID_UNIVERSE].turn
		if (turn + 2 * Rules.turnsPerDay) % Rules.voteForImpPeriod == 0:
			for galaxyID in obj.galaxies:
				galaxy = tran.db[galaxyID]
				if not galaxy.timeEnabled:
					# skip this galaxy
					continue
				message = {
					"sender": "GNC",
					"senderID": galaxyID,
					"forum": "NEWS",
					"data": (galaxyID, MSG_GNC_VOTING_COMING, galaxyID, turn, None),
					"topic": "EVENT",
				}
				self.cmd(galaxy).sendMsg(tran, galaxy, message)
		if turn % Rules.voteForImpPeriod == 0:
			# voting
			# process each galaxy
			for galaxyID in obj.galaxies:
				log.debug("Voting for galaxy", galaxyID)
				galaxy = tran.db[galaxyID]
				if not galaxy.timeEnabled:
					# skip this galaxy
					continue
				# compute votes
				activePlayerCount = 0
				piratePlayer = False
				selfName = None
				sum = 0
				votes = {}
				votesID = {}
				voters = {}
				for playerID in obj.players:
					player = tran.db[playerID]
					if galaxyID not in player.galaxies:
						log.debug("Skipping player", playerID, " - not in this galaxy")
						continue
					if player.type == T_PIRPLAYER:
						log.debug("Skipping player", playerID, " - he/she is a pirate")
						piratePlayer = True
						activePlayerCount += 1
						continue
					if player.type != T_PLAYER:
						log.debug("Skipping player", playerID, " - it's not a regular player")
						# skip non-regular players
						continue
					selfName = player.name
					# add to sum
					log.debug(playerID, "votes for", player.voteFor, "with votes", player.stats.slots)
					activePlayerCount += 1
					sum += player.stats.slots
					if player.voteFor == OID_NONE:
						voteFor = None
					else:
						tmpPlayer = tran.db.get(player.voteFor, None)
						if not tmpPlayer or tmpPlayer.type != T_PLAYER:
							# reset vote
							player.voteFor = OID_NONE
							voteFor = None
						else:
							voteFor = tmpPlayer.name
					# count votes
					votes[voteFor] = votes.get(voteFor, 0) + player.stats.slots
					votesID[player.voteFor] = votesID.get(player.voteFor, 0) + player.stats.slots
					if voteFor in voters:
						voters[voteFor].append(player.name)
					else:
						voters[voteFor] = [player.name]
				# check winner
				nominated = votesID.keys()
				nominated.sort(lambda a, b: cmp(votesID[b], votesID[a]))
				winnerID = OID_NONE
				# remove OID_NONE from the list
				if OID_NONE in nominated:
					nominated.remove(OID_NONE)
				# check winner
				if nominated and float(votesID[nominated[0]]) / sum >= Rules.ratioNeededForImp:
					# we have the imperator!
					imperator = tran.db[nominated[0]]
					# 2 imperator, 3+ winner
					imperator.imperator = max(2, imperator.imperator + 1)
					if galaxy.imperator != OID_NONE and galaxy.imperator != imperator.oid:
						tran.db[galaxy.imperator].imperator = 0
					galaxy.imperator = imperator.oid
					# send message
					message = {
						"sender": "GNC",
						"senderID": galaxyID,
						"forum": "NEWS",
						"data": (galaxyID, MSG_GNC_VOTING_IMPERATOR, galaxyID, turn, (imperator.name, (votes,voters))),
						"topic": "EVENT",
					}
					self.cmd(galaxy).sendMsg(tran, galaxy, message)
				elif len(nominated) >= 1:
					# we have the leader!
					leader = tran.db[nominated[0]]
					leader.imperator = 1
					if galaxy.imperator != OID_NONE:
						tran.db[galaxy.imperator].imperator = 0
					galaxy.imperator = leader.oid
					# send message
					message = {
						"sender": "GNC",
						"senderID": galaxyID,
						"forum": "NEWS",
						"data": (galaxyID, MSG_GNC_VOTING_LEADER, galaxyID, turn, (leader.name, (votes,voters))),
						"topic": "EVENT",
					}
					self.cmd(galaxy).sendMsg(tran, galaxy, message)
				else:
					# nobody wins
					galaxy.imperator = OID_NONE
					message = {
						"sender": "GNC",
						"senderID": galaxyID,
						"forum": "NEWS",
						"data": (galaxyID, MSG_GNC_VOTING_NOWINNER, galaxyID, turn, ((votes,voters),)),
						"topic": "EVENT",
					}
					self.cmd(galaxy).sendMsg(tran, galaxy, message)
				# check one player win conditions, but only in normal mode (not development)
                                if activePlayerCount <= 1 and tran.gameMngr.config.server.mode == "normal":
					log.message("AUTO RESTARTING GALAXY", galaxyID)
					if activePlayerCount == 0:
						self.restartGalaxy2(tran, obj, galaxyID, ["The galaxy was ended with no active players."])
					elif piratePlayer: #if the pirate is still alive, then he must be the victor.
						self.restartGalaxy2(tran, obj, galaxyID, ["The galaxy was automatically ended with the Pirate as victor!"])
					elif selfName: #if there is only one player, selfName must be themselves if it isn't null
						self.restartGalaxy2(tran, obj, galaxyID, ["The galaxy was automatically ended with commander %s as the only remaining player." % selfName])
		# collect mailboxes
		used = [self.cmd(obj).getMailboxName(tran, obj)]
		for galaxyID in obj.galaxies:
			tmpObj = tran.db[galaxyID]
			used.append(self.cmd(tmpObj).getMailboxName(tran, tmpObj))
		for playerID in obj.players:
			tmpObj = tran.db[playerID]
			used.append(self.cmd(tmpObj).getMailboxName(tran, tmpObj))
		# trash unused mailboxes
		tran.gameMngr.msgMngr.trashUnusedMailboxes(used)
		return obj.galaxies

	processFINAL2Phase.public = 1
	processFINAL2Phase.accLevel = AL_ADMIN

	def update(self, tran, obj):
		# check existence of all galaxies
		if 0:
			for galaxyID in obj.galaxies:
				if not tran.db.has_key(galaxyID):
					log.debug("CONSISTENCY - galaxy %d from universe %d does not exists" % (galaxyID, obj.oid))
				elif tran.db[galaxyID].type != T_GALAXY:
					log.debug("CONSISTENCY - galaxy %d from universe %d is not a T_GALAXY" % (galaxyID, obj.oid))
		# check existence of all players
		for playerID in obj.players[:]:
			if not tran.db.has_key(playerID):
				log.debug("CONSISTENCY - player %d from universe %d does not exists" % (playerID, obj.oid))
				log.debug("Removing reference to player", playerID)
				obj.players.remove(playerID)
			elif tran.db[playerID].type not in PLAYER_TYPES:
				log.debug("CONSISTENCY - player %d from universe %d is not a %s, it's %d" % (playerID, obj.oid, str(PLAYER_TYPES), tran.db[playerID].type))
				log.debug("Removing reference to player", playerID)
				obj.players.remove(playerID)
		# create NATURE if needed
		if not tran.db.has_key(OID_NATURE):
			# create "nature player"
			player = self.new(T_NATURE)
			tran.gameMngr.registerPlayer(player.login, player, OID_NATURE)

	update.public = 0

	def getReferences(self, tran, obj):
		return obj.players[:] + obj.galaxies[:] + [OID_NATURE]

	getReferences.public = 0

	def getPublicInfo(self, tran, obj):
		result = IDataHolder()
		result.oid = obj.oid
		result.type = obj.type
		result.name = obj.name
		result.turn = obj.turn
		return result

	getPublicInfo.public = 1
	getPublicInfo.accLevel = AL_NONE

	## messaging
	def canGetMsgs(self, tran, obj, oid):
		return 1

	canGetMsgs.public = 0

	def canSendMsg(self, tran, obj, oid, forum):
		if forum == "QA":
			return 1
		elif forum == "PUBLIC":
			return 1
		elif forum == "IDEAS":
			return 1
		elif forum == "ISSUES":
			return 1
		elif forum == "NEWS":
			return 1
		return 0

	canSendMsg.public = 0

	def restartGalaxy(self, tran, obj, galaxyID, imperatorMessage): #client-initiated restart
		log.debug("Restarting Galaxy", galaxyID)
		galaxy = tran.db[galaxyID]
		if galaxy.imperator == 0 or galaxy.imperator != tran.cid:
			raise GameException('Only galaxy imperator can restart galaxy')

		imperator = tran.db[tran.cid]
		if imperator.imperator < 3:
			raise GameException('Only imperator elected three times and more can restart galaxy')

		log.debug("Sending message", imperatorMessage)
		message = {
			"sender": imperator.name,
			"senderID": tran.cid,
			"forum": "NEWS",
			"data": (galaxyID, MSG_GNC_GALAXY_RESTARTED, galaxyID, tran.db[OID_UNIVERSE].turn, (imperator.name, galaxy.name, imperatorMessage)),
			"topic": "EVENT",
		}
		self.cmd(obj).sendMsg(tran, obj, message)

		fh, galaxyFileName = tempfile.mkstemp(text = True)
		log.debug("Generating new galaxy to temporary file", galaxyFileName)
		strGalaxyID = 'Circle42P'
		GenerateGalaxy(strGalaxyID, os.fdopen(fh, "w+b"))
		oldX = galaxy.x
		oldY = galaxy.y
		oldName = galaxy.name
		log.debug("Deleting galaxy", galaxyID)
		self.cmd(galaxy).delete(tran, galaxy)
		log.debug("Creating new galaxy")
		newGalaxyID = self.createGalaxy(tran, obj)
		log.debug("Created new galaxy", newGalaxyID)
		newGalaxy = tran.db[newGalaxyID]
		log.debug("Loading new ", newGalaxyID)
		self.cmd(newGalaxy).loadFromXML(tran, newGalaxy, galaxyFileName, strGalaxyID, oldX, oldY, oldName)
		log.debug("Setup Enviroment", newGalaxyID)
		self.cmd(newGalaxy).setupEnvironment(tran, newGalaxy)
		log.debug("Sending Announcement Message", newGalaxyID)
		#self.cmd(newGalaxy).announceGalaxy(tran,newGalaxy)
		log.debug("Removing temp file", galaxyFileName)
		os.remove(galaxyFileName)
		# TODO: find you what's this code about
		#message = {
		#    "sender": 'Galaxy %s' % oldName,
		#    "senderID": obj.oid,
		#    "forum": "NEWS",
		#    "data": (obj.oid, MSG_GNC_GALAXY_GENERATOR, obj.oid, tran.db[OID_UNIVERSE].turn, (oldName, newGalaxy.description)),
		#    "topic": "EVENT",
                #}
		log.debug("Galaxy Restarting END")

	restartGalaxy.public = 1
	restartGalaxy.accLevel = AL_NONE


	def restartGalaxy2(self, tran, obj, galaxyID, imperatorMessage): #server-initiated restart
		log.debug("Restarting Galaxy", galaxyID)
		galaxy = tran.db[galaxyID]
		log.debug("Sending message", imperatorMessage)
		message = {
			"sender": "Galaxy %s" % galaxy.name,
			"senderID": tran.cid,
			"forum": "NEWS",
			"data": (galaxyID, MSG_GNC_GALAXY_AUTO_RESTARTED, galaxyID, tran.db[OID_UNIVERSE].turn, (galaxy.name, imperatorMessage)),
			"topic": "EVENT",
		}
		self.cmd(obj).sendMsg(tran, obj, message)

		fh, galaxyFileName = tempfile.mkstemp(text = True)
		log.debug("Generating new galaxy to temporary file", galaxyFileName)
		strGalaxyID = 'Circle42P'
		GenerateGalaxy(strGalaxyID, os.fdopen(fh, "w+b"))
		oldX = galaxy.x
		oldY = galaxy.y
		oldName = galaxy.name
		log.debug("Deleting galaxy", galaxyID)
		self.cmd(galaxy).delete(tran, galaxy)
		log.debug("Creating new galaxy")
		newGalaxyID = self.createGalaxy(tran, obj)
		log.debug("Created new galaxy", newGalaxyID)
		newGalaxy = tran.db[newGalaxyID]
		log.debug("Loading new ", newGalaxyID)
		self.cmd(newGalaxy).loadFromXML(tran, newGalaxy, galaxyFileName, strGalaxyID, oldX, oldY, oldName)
		log.debug("Setup Enviroment", newGalaxyID)
		self.cmd(newGalaxy).setupEnvironment(tran, newGalaxy)
		log.debug("Sending Announcement Message", newGalaxyID)
		#self.cmd(newGalaxy).announceGalaxy(tran,newGalaxy)
		log.debug("Removing temp file", galaxyFileName)
		os.remove(galaxyFileName)
		# TODO: find you what's this code about
		#message = {
		#    "sender": 'Galaxy'+galaxyName,
		#    "senderID": obj.oid,
		#    "forum": "NEWS",
		#    "data": (obj.oid, MSG_GNC_GALAXY_GENERATOR, obj.oid, tran.db[OID_UNIVERSE].turn, (galaxyName, newGalaxy.description)),
		#    "topic": "EVENT",
                #}
		log.debug("Galaxy Restarting END")

	restartGalaxy2.public = 1
	restartGalaxy2.accLevel = AL_ADMIN

	def createNewGalaxy(self, tran, obj, x, y, galaxyName):
		log.message("Adding new galaxy '%s' to (%d, %d)" % (galaxyName, x, y))
		fh, galaxyFileName = tempfile.mkstemp(text = True)
		log.debug("Generating new galaxy to temporary file", galaxyFileName)
		strGalaxyID = 'Circle42P'
		GenerateGalaxy(strGalaxyID, os.fdopen(fh, "w+b"))
		log.debug("Creating new galaxy")
		newGalaxyID = self.createGalaxy(tran, obj)
		log.debug("Created new galaxy", newGalaxyID)
		newGalaxy = tran.db[newGalaxyID]
		log.debug("Loading new ", newGalaxyID)
		self.cmd(newGalaxy).loadFromXML(tran, newGalaxy, galaxyFileName, strGalaxyID, x, y, galaxyName)
		log.debug("Setup Enviroment", newGalaxyID)
		self.cmd(newGalaxy).setupEnvironment(tran, newGalaxy)
		log.debug("Sending Announcement Message", newGalaxyID)
		#self.cmd(newGalaxy).announceGalaxy(tran,newGalaxy)
		log.debug("Removing temp file", galaxyFileName)
		os.remove(galaxyFileName)
		# TODO: find you what's this code about
		#message = {
		#    "sender": 'Galaxy %s' % galaxyName,
		#    "senderID": obj.oid,
		#    "forum": "NEWS",
		#    "data": (obj.oid, MSG_GNC_GALAXY_GENERATOR, obj.oid, tran.db[OID_UNIVERSE].turn, (galaxyName, newGalaxy.description)),
		#    "topic": "EVENT",
                #}
		log.debug("Galaxy Restarting END")

	createNewGalaxy.public = 1
	createNewGalaxy.accLevel = AL_ADMIN

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

import math
import os
import random
import tempfile
import time

import ige
import ige.version

import Const
import GalaxyGenerator
import Rules

from ige import log
from ige.IObject import IObject, public
from ige.IDataHolder import IDataHolder
from ige import GameException, NoSuchObjectException

class IUniverse(IObject):

    typeID = Const.T_UNIVERSE

    forums = {
        # Official English forums
        "NEWS": 112, "PUBLIC": 112,
    }

    def init(self, obj):
        IObject.init(self, obj)
        #
        obj.name = "Outer Space"
        obj.turn = 0
        obj.owner = Const.OID_ADMIN
        obj.galaxies = []
        obj.players = []
        obj.waitingPlayers = []
        # auto loading of galaxies
        obj.galX = 0.0
        obj.galY = 0.0
        obj.galXStep = 100.0
        obj.galYStep = 100.0
        obj.galFilename = ''
        obj.galID = ''

    @public(Const.AL_NONE)
    def getIntroInfo(self, tran, obj):
        result = IDataHolder()
        result.cid = tran.cid
        result.turn = obj.turn
        result.serverTime = time.time()
        result.version = ige.version.version
        return result

    @public(Const.AL_NONE)
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

    @public(Const.AL_NONE)
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

    @public(Const.AL_ADMIN)
    def createGalaxy(self, tran, obj):
        galaxy = self.new(Const.T_GALAXY)
        galaxy.compOf = obj.oid
        oid = tran.db.create(galaxy)
        obj.galaxies.append(oid)
        return oid

    @public(Const.AL_ADMIN)
    def processINITPhase(self, tran, obj, data):
        for galaxyID in obj.galaxies:
            galaxy = tran.db[galaxyID]
            self.cmd(galaxy).enableTime(tran, galaxy)
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
                        if dipl.pacts[pactID][0] > Const.PACT_OFF:
                            dipl.pacts[pactID][0] = Const.PACT_ACTIVE
            # inactivate all pact that does not satisfy conditions
            changed = 1
            defaultPact = [Const.PACT_OFF]
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
                                dipl.pacts[pactID][0] == Const.PACT_ACTIVE:
                                #@log.debug("Inactivating pact (validity interval)", playerID, pactID)
                                dipl.pacts[pactID][0] = Const.PACT_INACTIVE
                                changed = 1
                            # check conditions for the pact if pact is active
                            if dipl.pacts[pactID][0] == Const.PACT_ACTIVE:
                                for condPactID in dipl.pacts[pactID][1:]:
                                    #@log.debug("Checking", playerID, pactID, "against", partyID, condPactID)
                                    if partyDipl and partyDipl.pacts.get(condPactID, defaultPact)[0] != Const.PACT_ACTIVE:
                                        dipl.pacts[pactID][0] = Const.PACT_INACTIVE
                                        changed = 1
        except Exception:
            log.warning("Cannot process diplomacy initialization")
        # TODO - send notifications if pacts are changed
        # remove old messages
        self.cmd(obj).deleteOldMsgs(tran, obj)
        return obj.players[:] + [Const.OID_NATURE]

    @public(Const.AL_ADMIN)
    def processPRODPhase(self, tran, obj, data):
        raise NotImplementedError()

    @public(Const.AL_ADMIN)
    def processACTIONPhase(self, tran, obj, data):
        raise NotImplementedError()

    @public(Const.AL_ADMIN)
    def processBATTLEPhase(self, tran, obj, data):
        raise NotImplementedError()

    @public(Const.AL_ADMIN)
    def processFINALPhase(self, tran, obj, data):
        return obj.players[:] + [Const.OID_NATURE]

    @public(Const.AL_ADMIN)
    def processFINAL2Phase(self, tran, obj, data):
        # distribute stats to contacts
        for playerID in obj.players:
            player = tran.db[playerID]
            for partyID in player.diplomacyRels:
                dipl = player.diplomacyRels[partyID]
                if dipl.contactType > Const.CONTACT_NONE and tran.db.has_key(partyID):
                    dipl.stats = tran.db[partyID].stats
                else:
                    dipl.stats = None

        # process each galaxy winning checking routines
        for galaxyID in obj.galaxies:
            log.debug("Voting for galaxy", galaxyID)
            galaxy = tran.db[galaxyID]
            if not galaxy.timeEnabled:
                # skip this galaxy
                continue
            if galaxy.scenario == Const.SCENARIO_OUTERSPACE:
                self.processScenarioOuterspace(tran, obj, galaxy)
                continue
            elif galaxy.scenario == Const.SCENARIO_SINGLE:
                self.processScenarioSingle(tran, obj, galaxy)
                continue
            elif galaxy.scenario == Const.SCENARIO_COOP:
                self.processScenarioCoop(tran, obj, galaxy)
                continue
            elif galaxy.scenario == Const.SCENARIO_BRAWL:
                self.processScenarioBrawl(tran, obj, galaxy)
                continue

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

    def _announceImperatorVoting(self, tran, obj, galaxy):
        message = {
            "sender": "GNC",
            "senderID": galaxy.oid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_VOTING_COMING, galaxy.oid, obj.turn, Rules.voteForImpAnnounceOffset),
            "topic": "EVENT",
        }
        self.cmd(galaxy).sendMsg(tran, galaxy, message)

    def _countVotes(self, tran, obj, galaxy):
        VALID_TYPES = [Const.T_PLAYER, Const.T_AIPLAYER]
        log.debug("Voting for galaxy", galaxy.oid)
        # compute votes
        votesByName = {}
        votesByID = {}
        voterNames = {}
        for playerID in obj.players:
            player = tran.db[playerID]
            if galaxy.oid != player.galaxy:
                continue
            if player.type not in VALID_TYPES:
                continue
            # add to sum
            log.debug(playerID, "votes for", player.voteFor, "with votes", player.stats.slots)

            tmpPlayer = tran.db.get(player.voteFor, None)
            if not tmpPlayer or tmpPlayer.type not in VALID_TYPES:
                # reset vote
                player.voteFor = Const.OID_NONE
                votedName = None
            else:
                votedName = tmpPlayer.name

            # count votes
            votesByName[votedName] = votesByName.get(votedName, 0) + player.stats.slots
            votesByID[player.voteFor] = votesByID.get(player.voteFor, 0) + player.stats.slots
            try:
                voterNames[votedName].append(player.name)
            except KeyError:
                voterNames[votedName] = [player.name]
        return votesByName, votesByID, voterNames

    def _processElectedImperator(self, tran, obj, galaxy, imperator, votesByName, voterNames):
        # 2 imperator, 3+ winner
        imperator.imperator = max(2, imperator.imperator + 1)
        if galaxy.imperator != Const.OID_NONE and galaxy.imperator != imperator.oid:
            tran.db[galaxy.imperator].imperator = 0
        galaxy.imperator = imperator.oid
        # send message
        message = {
            "sender": "GNC",
            "senderID": galaxy.oid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_VOTING_IMPERATOR, galaxy.oid, obj.turn, (imperator.name, (votesByName, voterNames))),
            "topic": "EVENT",
        }
        self.cmd(galaxy).sendMsg(tran, galaxy, message)

    def _processElectedLeader(self, tran, obj, galaxy, leader, votesByName, voterNames):
        leader.imperator = 1
        if galaxy.imperator != Const.OID_NONE and galaxy.imperator != leader.oid:
            tran.db[galaxy.imperator].imperator = 0
        galaxy.imperator = leader.oid
        # send message
        message = {
            "sender": "GNC",
            "senderID": galaxy.oid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_VOTING_LEADER, galaxy.oid, obj.turn, (leader.name, (votesByName, voterNames))),
            "topic": "EVENT",
        }
        self.cmd(galaxy).sendMsg(tran, galaxy, message)

    def _processNoWinner(self, tran, obj, galaxy, votesByName, voterNames):
        # nobody wins
        if galaxy.imperator != Const.OID_NONE:
            tran.db[galaxy.imperator].imperator = 0
            galaxy.imperator = Const.OID_NONE
        message = {
            "sender": "GNC",
            "senderID": galaxy.oid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_VOTING_NOWINNER, galaxy.oid, obj.turn, ((votesByName, voterNames),)),
            "topic": "EVENT",
        }
        self.cmd(galaxy).sendMsg(tran, galaxy, message)

    def _processImperatorVoting(self, tran, obj, galaxy):
        votesByName, votesByID, voterNames = self._countVotes(tran, obj, galaxy)
        # check winner
        totalVotes = sum(votesByID.values())
        nominated = sorted(votesByID, key=lambda a: votesByID[a], reverse = True)
        winnerID = Const.OID_NONE
        # Const.OID_NONE is not valid target
        if Const.OID_NONE in nominated:
            nominated.remove(Const.OID_NONE)
        # check winner
        try:
            winnerID = nominated[0]
            winner = tran.db[winnerID]
            if float(votesByID[winnerID]) / totalVotes >= Rules.ratioNeededForImp:
                self._processElectedImperator(tran, obj, galaxy, winner, votesByName, voterNames)
            elif len(nominated) > 1 and votesByID[winnerID] == votesByID[nominated[1]]:
                # oh no, more than one winner
                self._processNoWinner(tran, obj, galaxy, votesByName, voterNames)
            else:
                self._processElectedLeader(tran, obj, galaxy, winner, votesByName, voterNames)
        except IndexError:
            # no nominations?
            self._processNoWinner(tran, obj, galaxy, votesByName, voterNames)

    def _autoFinishOuterspace(self, tran, obj, galaxy):
        if tran.gameMngr.config.server.mode != "normal":
            # check autoend conditions, but only in normal mode
            # development mode does not end galaxies
            return
        for playerID in obj.players:
            player = tran.db[playerID]
            if galaxy.oid != player.galaxy:
                continue
            if player.type == Const.T_PIRPLAYER:
                piratePlayer = True
                activePlayerCount += 1
                continue
            if player.type != Const.T_PLAYER:
                continue
            selfName = player.name
            activePlayerCount += 1

        if activePlayerCount <= 1:
            log.message("AUTO FINISHING GALAXY", galaxy.oid)
            if activePlayerCount == 0:
                self.finishGalaxyAutomated(tran, obj, galaxy.oid, ["The galaxy was ended with no active players."])
            elif piratePlayer: #if the pirate is still alive, then he must be the winner.
                self.finishGalaxyAutomated(tran, obj, galaxy.oid, ["The galaxy was automatically ended with the Pirate as a winner!"])
            elif selfName: #if there is only one player, selfName must be themselves if it isn't null
                self.finishGalaxyAutomated(tran, obj, galaxy.oid, ["The galaxy was automatically ended with commander %s as the only remaining player." % selfName])

    def processScenarioOuterspace(self, tran, obj, galaxy):
        if (galaxy.galaxyTurn + Rules.voteForImpAnnounceOffset) % Rules.voteForImpPeriod == 0:
            self._announceImperatorVoting(tran, obj, galaxy)
        if galaxy.galaxyTurn % Rules.voteForImpPeriod == 0:
            # voting
            self._processImperatorVoting(tran, obj, galaxy)
        self._autoFinishOuterspace(tran, obj, galaxy)

    def processScenarioSingle(self, tran, obj, galaxy):
        """ If owner of the galaxy is not present anymore, remove it.
        There are no winning conditions right now.
        """
        try:
            player = tran.db[galaxy.owner]
            if galaxy.oid == player.galaxy:
                # all is well
                return True
            # new player has nothing to do with this galaxy
        except NoSuchObjectException:
            # there is no object with owner OID
            pass
        except AttributeError:
            # there is object with owner OID, but it's not player object
            pass
        # let's clean it
        if tran.gameMngr.config.server.mode == "normal":
            self.cmd(galaxy).delete(tran, galaxy)

    def processScenarioCoop(self, tran, obj, galaxy):
        ENEMIES = [Const.T_AIEDENPLAYER, Const.T_AIMUTPLAYER, Const.T_AIPIRPLAYER]
        clear = True
        players = []
        for playerID in obj.players:
            player = tran.db[playerID]
            if galaxy.oid != player.galaxy:
                continue
            if player.type in ENEMIES:
                clear = False
                continue
            if player.type == Const.T_AIPLAYER:
                players.append(player)
            if player.type != Const.T_PLAYER:
                # skip non-regular players
                continue
            players.append(player)
        if not len(players):
            # no player left? what a strange state! Let's delete it quick!
            self.cmd(galaxy).delete(tran, galaxy)
            return False
        if not clear:
            # struggle is ongoing
            return True
        # no enemies left, let's celebrate by sending a message, and finish the galaxy
        victors = map(lambda x: x.name, players)
        message = {
            "sender": "Galaxy %s" % galaxy.name,
            "senderID": tran.cid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_GALAXY_COOP_WON, galaxy.oid, obj.turn, (galaxy.name, victors)),
            "topic": "EVENT",
        }
        self.cmd(obj).sendMsg(tran, obj, message)
        self.cmd(galaxy).delete(tran, galaxy)

    def processScenarioBrawl(self, tran, obj, galaxy):
        players = []
        for playerID in obj.players:
            player = tran.db[playerID]
            if galaxy.oid != player.galaxy:
                continue
            if player.type != Const.T_PLAYER:
                # skip non-regular players
                continue
            players.append(player)
        if len(players) > 1:
            # fight continues
            return True
        if not len(players):
            # no player left? what a strange state! Let's delete it quick!
            self.cmd(galaxy).delete(tran, galaxy)
            return False
        # last man standing! Let's send announcement, and change the galaxy
        # to Const.SCENARIO_SINGLE for winner to enjoy it (and pause / finish at will)
        winner = players[0]
        message = {
            "sender": "Galaxy %s" % galaxy.name,
            "senderID": tran.cid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_GALAXY_BRAWL_WON, galaxy.oid, obj.turn, (galaxy.name, winner.name)),
            "topic": "EVENT",
        }
        self.cmd(obj).sendMsg(tran, obj, message)
        galaxy.scenario = Const.SCENARIO_SINGLE
        galaxy.name += " won on {0}".format(obj.turn)
        galaxy.owner = winner.oid
        return False

    def update(self, tran, obj):
        # check existence of all galaxies
        log.debug('Game turn is',obj.turn)
        if 0:
            for galaxyID in obj.galaxies:
                if not tran.db.has_key(galaxyID):
                    log.debug("CONSISTENCY - galaxy %d from universe %d does not exists" % (galaxyID, obj.oid))
                elif tran.db[galaxyID].type != Const.T_GALAXY:
                    log.debug("CONSISTENCY - galaxy %d from universe %d is not a Const.T_GALAXY" % (galaxyID, obj.oid))
        # check existence of all players
        for playerID in obj.players[:]:
            if not tran.db.has_key(playerID):
                log.debug("CONSISTENCY - player %d from universe %d does not exists" % (playerID, obj.oid))
                log.debug("Removing reference to player", playerID)
                obj.players.remove(playerID)
            elif tran.db[playerID].type not in Const.PLAYER_TYPES:
                log.debug("CONSISTENCY - player %d from universe %d is not a %s, it's %d" % (playerID, obj.oid, str(Const.PLAYER_TYPES), tran.db[playerID].type))
                log.debug("Removing reference to player", playerID)
                obj.players.remove(playerID)

    def getReferences(self, tran, obj):
        return obj.players[:] + obj.galaxies[:] + [Const.OID_NATURE]

    @public(Const.AL_ADMIN)
    def getActivePlayers(self, tran, obj):
        playerNames = []
        for playerID in obj.players:
            player = tran.db[playerID]
            if not player.type in Const.AI_PLAYER_TYPES:
                playerNames.append(player.name)
        return playerNames

    @public(Const.AL_NONE)
    def getPublicInfo(self, tran, obj):
        result = IDataHolder()
        result.oid = obj.oid
        result.type = obj.type
        result.name = obj.name
        result.turn = obj.turn
        return result

    ## messaging
    def canGetMsgs(self, tran, obj, oid):
        return 1

    def canSendMsg(self, tran, obj, oid, forum):
        if forum.endswith("PUBLIC"):
            return 1
        elif forum.endswith("NEWS"):
            return 1
        return 0
    
    @public(Const.AL_NONE)
    def finishGalaxyImperator(self, tran, obj, galaxyID, imperatorMessage):
        log.debug("Finishing Galaxy", galaxyID)
        galaxy = tran.db[galaxyID]
        if galaxy.scenario == Const.SCENARIO_OUTERSPACE:
            if galaxy.imperator == 0 or galaxy.imperator != tran.cid:
                raise GameException('Only galaxy imperator can finish galaxy')

            imperator = tran.db[tran.cid]
            if imperator.imperator < 3:
                raise GameException('Only imperator elected three times and more can finish galaxy')

            log.debug("Sending message", imperatorMessage)
            message = {
                "sender": imperator.name,
                "senderID": tran.cid,
                "forum": "NEWS",
                "data": (galaxyID, Const.MSG_GNC_GALAXY_FINISHED, galaxyID, obj.turn, (imperator.name, galaxy.name, imperatorMessage)),
                "topic": "EVENT",
            }
            self.cmd(obj).sendMsg(tran, obj, message)
        else:
            raise GameException('Galaxy finish not permitted.')

        log.debug("Deleting galaxy", galaxyID)
        self.cmd(galaxy).delete(tran, galaxy)

    @public(Const.AL_ADMIN)
    def finishGalaxyAutomated(self, tran, obj, galaxyID, imperatorMessage): #server-initiated restart
        log.debug("Restarting Galaxy", galaxyID)
        log.debug("Sending message", imperatorMessage)
        galaxy = tran.db[galaxyID]
        message = {
            "sender": "Galaxy %s" % galaxy.name,
            "senderID": tran.cid,
            "forum": "NEWS",
            "data": (galaxyID, Const.MSG_GNC_GALAXY_AUTO_FINISHED, galaxyID, obj.turn, (galaxy.name, imperatorMessage)),
            "topic": "EVENT",
        }
        self.cmd(obj).sendMsg(tran, obj, message)
        log.debug("Deleting galaxy", galaxyID)
        self.cmd(galaxy).delete(tran, galaxy)

    def _sendCreationMessage(self, tran, obj, galaxy):
        message = {
            "sender": "GNC",
            "senderID": galaxy.oid,
            "forum": "NEWS",
            "data": (galaxy.oid, Const.MSG_GNC_GALAXY_CREATED, galaxy.oid, obj.turn, (obj.turn)),
            "topic": "EVENT",
        }
        self.cmd(galaxy).sendMsg(tran, galaxy, message)

    @public(Const.AL_ADMIN)
    def createNewSubscribedGalaxy(self, tran, obj, galaxyName, galaxyType, listOfPlayers):
        galGen = GalaxyGenerator.GalaxyGenerator()
        galaxyRadius = galGen.getGalaxyTemplate(galaxyType).radius
        posX, posY = self.cmd(obj).findSpotForGalaxy(tran, obj, galaxyRadius)
        log.message("Adding new galaxy '%s' to (%d, %d)" % (galaxyType, posX, posY))
        galaxyFileName = galGen.generateGalaxy(galaxyType)
        log.debug("Creating new galaxy")
        newGalaxyID = self.createGalaxy(tran, obj)
        log.debug("Created new galaxy", newGalaxyID)
        newGalaxy = tran.db[newGalaxyID]
        log.debug("Loading new ", newGalaxyID)
        self.cmd(newGalaxy).loadFromXML(tran, newGalaxy, galaxyFileName, galaxyType, posX, posY, galaxyName)

        log.debug("Setup Enviroment", newGalaxyID)
        self.cmd(newGalaxy).setupEnvironment(tran, newGalaxy)
        log.debug("Sending Announcement Message", newGalaxyID)
        #self.cmd(newGalaxy).announceGalaxy(tran,newGalaxy)
        log.debug("Removing temp file", galaxyFileName)
        os.remove(galaxyFileName)
        for playerLogin in listOfPlayers:
            tran.gameMngr.createNewSubscribedPlayer(playerLogin, newGalaxyID)
        if newGalaxy.scenario != Const.SCENARIO_SINGLE:
            # no point in announcing single scenario - it starts ticking right away
            self._sendCreationMessage(tran, obj, newGalaxy)
        log.debug("Galaxy creation END")
        return newGalaxyID

    @public(Const.AL_ADMIN)
    def deleteGalaxy(self, tran, galaxyID):
        galaxy = tran.db[galaxyID]
        log.debug("Deleting galaxy", galaxyID)
        self.cmd(galaxy).delete(tran, galaxy)

    @public(Const.AL_ADMIN)
    def findSpotForGalaxy(self, tran, obj, new_gal_radius):
        """ We start with sum of surfaces of active galaxies (with borders) with this,
            we count the hypothetical square all galaxies should fit together. We then
            increase the size a bit, and try to place the new galaxy there randomly.
            If not successful, increase again and repeat.
        """
        log.debug("Seeking position for new galaxy")

        attempts_amount = 10000 # number of placement attempts within one resize
        magic_constant = 1.1
        magic_constant_step = 0.1
        border = 50

        # count surface required
        whole_surface = 0
        for galaxy_id in obj.galaxies:
            galaxy = tran.db[galaxy_id]
            # border is counted only once as it can overlap
            whole_surface += (galaxy.radius * 2 + border) ** 2
        # adding whole_surface of the galaxy currently processed
        whole_surface += (new_gal_radius * 2 + border) ** 2

        search = True
        attempts = attempts_amount
        low_limit = new_gal_radius # only positive coordinates
        while search:
            high_limit = math.ceil(whole_surface ** 0.5 * magic_constant)
            attempts -= 1
            pos_x = int(random.randrange(low_limit, high_limit))
            pos_y = int(random.randrange(low_limit, high_limit))
            is_blocked = False
            for galaxy_id in obj.galaxies:
                galaxy = tran.db[galaxy_id]
                needed_space = galaxy.radius + border + new_gal_radius
                if math.hypot(galaxy.x - pos_x, galaxy.y - pos_y) < needed_space:
                    is_blocked = True
                    break
            search = is_blocked
            if not attempts:
                magic_constant += magic_constant_step
                attempts = attempts_amount
        return (pos_x, pos_y)

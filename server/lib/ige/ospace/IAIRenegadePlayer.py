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

from ige import *
from xml.dom.minidom import Node
from IPlayer import IPlayer
from ige.IDataHolder import IDataHolder
import Rules, Utils
from Const import *
import math, time, random

class IAIRenegadePlayer(IPlayer):

	typeID = T_AIRENPLAYER

	def init(self, obj):
		IPlayer.init(self, obj)
		#
		obj.name = u'Renegade'
		obj.login = '*'
		obj.techLevel = 99
		obj.techs[Rules.Tech.CANNON1] = 3
		obj.techs[Rules.Tech.SSROCKET] = 3
		obj.techs[Rules.Tech.RENEGADEBASE] = 3
		obj.techs[Rules.Tech.RENEGADEBASE2] = 3
		obj.techs[Rules.Tech.RENEGADEBASE2MINOR] = 3
		obj.techs[Rules.Tech.RENEGADEBASE3] = 3
		obj.techs[Rules.Tech.RENEGADEBASE3MINOR] = 3
		obj.techs[Rules.Tech.RENEGADECOSMODROME] = 3


	def register(self, tran, obj):
		log.debug("Registering player", obj.oid)
		counter = 1
		while 1:
			try:
				obj.name = u'Renegade faction %d' % counter
				obj.login = '*AIP*renegade%d' % counter
				tran.gameMngr.registerPlayer(obj.login, obj, obj.oid)
				tran.db[OID_UNIVERSE].players.append(obj.oid)
				return
			except CreatePlayerException:
				counter += 1

	def processINITPhase(self, tran, obj, data):
		IPlayer.processINITPhase(self, tran, obj, data)
		# fill with the ship designs
		if not len(obj.shipDesigns) == 3:
			tempTechs = [Rules.Tech.SCOCKPIT1, Rules.Tech.SMALLHULL1, Rules.Tech.MEDIUMHULL2, Rules.Tech.STEELARM2, Rules.Tech.SBRIDGE1]
			for techID in tempTechs:
				obj.techs[techID] = 1
			self.cmd(obj).addShipDesign(tran, obj, 'Fighter', Rules.Tech.SMALLHULL1,
				{Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:1})
			self.cmd(obj).addShipDesign(tran, obj, "Corvette", Rules.Tech.SMALLHULL1,
				{Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:2, Rules.Tech.STEELARM2:1})
			self.cmd(obj).addShipDesign(tran, obj, "Frigate", Rules.Tech.MEDIUMHULL2,
				{Rules.Tech.SBRIDGE1:1, Rules.Tech.CANNON1:2, Rules.Tech.SSROCKET:2})
			for techID in tempTechs:
				del obj.techs[techID]

		obj.lastLogin = time.time()
		# delete itself if there are no fleets and planets
		if not obj.fleets and not obj.planets:
			self.cmd(obj).delete(tran, obj)

		# AI is for each planet separately, behaviour is:
		# 1->2; 2 fill whole planet with 2m; if TL2 resource: 2->3;
		# 3 build 1x 2 on every empty planet; 3 fill whole planet with 3m
		for planetID in obj.planets:
			planet = tran.db[planetID]
			planetPhase = 0
			hasFreeSlot = planet.plSlots > len(planet.slots)
			otherStructID = None
			baseIndex = -1
			zeroBase = 0
			isStarport = False
			# 1, 2, 2m, 3, 3m
			bases = [0, 0, 0, 0, 0]
			if planet.prodQueue or not len(planet.slots):
				# something is in the production queue or empty planet
				continue
			# now we need to know, in which phase of development we are
			index = 0
			for struct in planet.slots:
				techID = struct[STRUCT_IDX_TECHID]
				if techID == Rules.Tech.RENEGADEBASE:
					planetPhase = max(planetPhase, 1)
					bases[0] = 1
					baseIndex = index
				elif techID == Rules.Tech.RENEGADEBASE2MINOR:
					planetPhase = max(planetPhase, 1)
					bases[2] = 1
					baseIndex = index
				elif techID == Rules.Tech.RENEGADEBASE2:
					planetPhase = max(planetPhase, 2)
					bases[1] = 1
					baseIndex = index
				elif techID == Rules.Tech.RENEGADEBASE3MINOR:
					planetPhase = max(planetPhase, 2)
					bases[4] = 1
					baseIndex = index
				elif techID == Rules.Tech.RENEGADEBASE3:
					planetPhase = 3
					bases[3] = 1
					baseIndex = index
				elif techID == Rules.Tech.RENEGADECOSMODROME:
					isStarport = True
				else:
					otherStructID = tech.techID
				if baseIndex == 0:
					zeroBase = 1
				index += 1
			# if there is renegade building, but not on the first position, move it there
			# [to prevent unsustainable captured/renegade colony]
			if not zeroBase and baseIndex:
				client.cmd(planet).moveStruct(planetID, baseIndex, -1 * baseIndex)
			# zero phase - try to build lvl1 instead of any building there [to have it simple]
			if not planetPhase:
				self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE,
					1, planet.oid, False, False, otherStructID)
			# first phase - task is to build lvl2 structure
			elif planetPhase == 1:
				log.debug(obj.oid, "RENEGADEAI - entering phase 1", planet.oid)
				# find renegadebase, is not found, try free slot, if even that not go well, select any other building
				if bases[0]:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
						1, planet.oid, False, False, Rules.Tech.RENEGADEBASE)
				elif hasFreeSlot:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
						1, planet.oid, False, False, OID_NONE)
				elif otherStructID:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
						1, planet.oid, False, False, otherStructID)
				else:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
						1, planet.oid, False, False, Rules.Tech.RENEGADEBASE2MINOR)

			elif planetPhase == 2:
				# second phase, part zero - if there is no lvl2, build one!
				if not bases[1]:
					if hasFreeSlot:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
							1, planet.oid, False, False, OID_NONE)
					elif otherStructID:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
							1, planet.oid, False, False, otherStructID)
					elif bases[4]:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2,
							1, planet.oid, False, False, Rules.Tech.RENEGADEBASE2MINOR)		
				# second phase, part one - all non-lvl2+ buildings rebuild as lvl2 minors
				elif bases[0]:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2MINOR,
						1, planet.oid, False, False, Rules.Tech.RENEGADEBASE)
				elif hasFreeSlot:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2MINOR,
						1, planet.oid, False, False, OID_NONE)
				elif otherStructID:
					self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2MINOR,
						1, planet.oid, False, False, otherStructID)
				# second phase, part two - rebuild lvl2 or lvl2 minor to lvl3, just on planets with special resource
				elif planet.plStratRes:
					if bases[1]:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3,
							1, planet.oid, False, False, Rules.Tech.RENEGADEBASE2)
					elif bases[2]:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3,
							1, planet.oid, False, False, Rules.Tech.RENEGADEBASE2MINOR)
				# search for free planets with special resources, and colonize them
				else:
					system = tran.db[planet.compOf]
					isBuilding = False
					for targetID in system.planets:
						target = tran.db[targetID]
						if target.owner == OID_NONE and target.plSlots > 0 and target.plStratRes:
							isBuilding = True
							self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE, 1, targetID, False, False, OID_NONE)
							break
						elif target.owner == obj.oid and planet.slots:
							for struct in planet.slots:
								techID = struct[STRUCT_IDX_TECHID]
								if techID == Rules.Tech.RENEGADECOSMODROME:
									isStarport = True
					if isStarport:
						# there is our airbase in the system - we can build some random ship
						log.debug(obj.oid, "RENEGADEAI - building ship", planet.oid)
						shipDraw = random.randint(1, 10)
						if shipDraw == 1:
							self.cmd(planet).startConstruction(tran, planet, 3, 1, planet.oid, False, False, OID_NONE)
						elif shipDraw <= 3:
							self.cmd(planet).startConstruction(tran, planet, 2, 1, planet.oid, False, False, OID_NONE)
						else:
							self.cmd(planet).startConstruction(tran, planet, 1, 1, planet.oid, False, False, OID_NONE)
					
			elif planetPhase == 3:
				# third phase, part zero - if there is no lvl3, build it
				if not bases[3]:
					if hasFreeSlot:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3,
							1, planet.oid, False, False, OID_NONE)
					elif otherStructID:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3,
							1, planet.oid, False, False, otherStructID)
					elif bases[4]:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3,
							1, planet.oid, False, False, Rules.Tech.RENEGADEBASE3MINOR)				
				# third phase, part one - build one lvl2 on all free planets in the system
				system = tran.db[planet.compOf]
				isSystemFull = 1
				for targetID in system.planets:
					target = tran.db[targetID]
					if (target.owner == OID_NONE and target.plSlots > 0) or (target.owner == obj.oid and len(target.slots) == 0):
						isSystemFull = 0
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE2, 1, targetID, False, False, OID_NONE)
						break
				# third phase, part two - rebuild all non lvl3+ structures to lvl3 minors
				# fill the free slots [made by fights] and rebuild alien structures
				if isSystemFull:
					if hasFreeSlot:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3MINOR,
							1, planet.oid, False, False, OID_NONE)
					elif otherStructID:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3MINOR,
							1, planet.oid, False, False, otherStructID)
					elif bases[2]:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADEBASE3MINOR,
							1, planet.oid, False, False, Rules.Tech.RENEGADEBASE2MINOR)
					# in the end, build starport and start building ships
					elif not isStarport:
						self.cmd(planet).startConstruction(tran, planet, Rules.Tech.RENEGADECOSMODROME,
							1, planet.oid, False, False, Rules.Tech.RENEGADEBASE3MINOR)
					else:
						log.debug(obj.oid, "RENEGADEAI - building ship", planet.oid)
						shipDraw = random.randint(1, 10)
						if shipDraw == 1:
							self.cmd(planet).startConstruction(tran, planet, 3, 1, planet.oid, True, False, OID_NONE)
						elif shipDraw <= 3:
							self.cmd(planet).startConstruction(tran, planet, 2, 1, planet.oid, True, False, OID_NONE)
						else:
							self.cmd(planet).startConstruction(tran, planet, 1, 1, planet.oid, True, False, OID_NONE)

	def update(self, tran, obj):
		obj.techLevel = 99
		# grant technologies
		obj.techs[Rules.Tech.CANNON1] = 3
		obj.techs[Rules.Tech.SSROCKET] = 3
		obj.techs[Rules.Tech.RENEGADEBASE] = 3
		obj.techs[Rules.Tech.RENEGADEBASE2] = 3
		obj.techs[Rules.Tech.RENEGADEBASE2MINOR] = 3
		obj.techs[Rules.Tech.RENEGADEBASE3] = 3
		obj.techs[Rules.Tech.RENEGADEBASE3MINOR] = 3
		obj.techs[Rules.Tech.RENEGADECOSMODROME] = 3
		if not len(obj.shipDesigns) == 3:
			tempTechs = [Rules.Tech.SCOCKPIT1, Rules.Tech.SMALLHULL1, Rules.Tech.MEDIUMHULL2, Rules.Tech.STEELARM2, Rules.Tech.SBRIDGE1]
			for techID in tempTechs:
				obj.techs[techID] = 1
			self.cmd(obj).addShipDesign(tran, obj, "Fighter", Rules.Tech.SMALLHULL1,
				{Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:1, Rules.Tech.STEELARM2:1})
			self.cmd(obj).addShipDesign(tran, obj, "Corvette", Rules.Tech.SMALLHULL1,
				{Rules.Tech.SCOCKPIT1:1, Rules.Tech.CANNON1:3, Rules.Tech.STEELARM2:1})
			self.cmd(obj).addShipDesign(tran, obj, "Frigate", Rules.Tech.MEDIUMHULL2,
				{Rules.Tech.SBRIDGE1:1, Rules.Tech.CANNON1:2, Rules.Tech.SSROCKET:2})
			for techID in tempTechs:
				del obj.techs[techID]
		# call super method
		IPlayer.update(self, tran, obj)

	def getDiplomacyWith(self, tran, obj, playerID):
		if obj.oid == playerID:
			return REL_UNITY
		# renegade battles with overyone
		# make default
		dipl = IDataHolder()
		dipl.type = T_DIPLREL
		dipl.pacts = {}
		dipl.relation = REL_ENEMY
		dipl.relChng = 0
		dipl.lastContact = tran.db[OID_UNIVERSE].turn
		dipl.contactType = CONTACT_NONE
		dipl.stats = None
		return dipl

	def processFINALPhase(self, tran, obj, data):
		IPlayer.processFINALPhase(self, tran, obj, data)
		# fix goverment power
		obj.govPwrCtrlRange = 10000
        
	# allow normal pacts
	#def isPactActive(self, tran, obj, partnerID, pactID):
	#	return 0

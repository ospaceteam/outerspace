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

import random, math, sys

# galaxy specification
sectorSize = [10, 10]
sectorsOffset = [0, 0]

galaxyID = 'Center90'
sectorsSpec = [
	[ 5,  5,  5],
	[ 5, 50,  5],
	[ 5,  5,  5],
]

galaxyID = 'Circle4P'
galaxyCenter = (20.0, 20.0)
galaxyRadius = 20.0
galaxyStartR = (14.0, 16.0)
galaxyPlayers = 4
galaxyDensity = {5: 2, 10: 2, 20: 3, 30: 4, 40: 5, 50: 6}
galaxyResources = {
	# format resourceID : (minDist, maxDist, number of resources)
	1 : (12, 15, 2), # TL 1 + 2
	2 : (12, 15, 2), # TL 1 + 2
	3 : (8, 11, 1), # TL 3 + 4
	4 : (8, 11, 1), # TL 3 + 4
	5 : (8, 11, 1), # TL 3 + 4
	6 : (5, 6, 1), # TL 5
	7 : (5, 6, 1), # TL 5
	8 : (5, 6, 1), # TL 5
}

if 1: # THIS IS THE RECOMENDED MEDIUM GALAXY
	galaxyID = 'Circle42P'
	galaxyCenter = (50.0, 50.0)
	galaxyRadius = 50.0
	galaxyStartR = (32.0, 36.0)
	#galaxyPlayers = 30
	#galaxyPlayerGroup = 2
	galaxyPlayers = 42
	galaxyPlayerGroup = 3
	galaxyGroupDist = 4.0
	galaxyMinR = 7.5
	galaxyDensity = {7.5: 3, 10: 4, 20: 5, 30: 5.5, 40: 6, 50: 6}
	galaxyResources = {
		# format resourceID : (minDist, maxDist, number of resources)
		1 : (20, 45, 15), # TL 1 + 2
		2 : (20, 45, 15), # TL 1 + 2
		3 : (8, 15, 7), # TL 3 + 4
		4 : (8, 15, 7), # TL 3 + 4
		5 : (8, 15, 7), # TL 3 + 4
		6 : (7.5, 9, 1), # TL 5
		7 : (7.5, 9, 1), # TL 5
		8 : (7.5, 9, 1), # TL 5
	}
	galaxyDiseases = {
		# format diseaseID : (minDist, maxDist, number of diseases)
		1 : (20, 45, 8), # TL 1 + 2
		2 : (20, 45, 8), # TL 1 + 2
		3 : (5, 15, 4), # TL 3 + 4
		4 : (5, 15, 4), # TL 3 + 4
		5 : (5, 15, 4), # TL 3 + 4
		6 : (0, 5, 1), # TL 5
		7 : (0, 5, 1), # TL 5
		8 : (0, 5, 1), # TL 5
	}

if 0: # Large Galaxy
	galaxyID = 'Circle65P'
	galaxyCenter = (75.0, 75.0)
	galaxyRadius = 75.0
	galaxyStartR = (45.0, 52.5)
	galaxyPlayers = 65
	galaxyPlayerGroup = 5
	#galaxyPlayers = 48
	#galaxyPlayerGroup = 4
	galaxyGroupDist = 8
	galaxyMinR = 7.5
	galaxyDensity = {7.5: 3, 10: 4, 20: 5, 30: 5.5, 60: 6, 75: 6}
	galaxyResources = {
		# format resourceID : (minDist, maxDist, number of resources)
		1 : (20, 67.5, 45), # TL 1 + 2
		2 : (20, 67.5, 45), # TL 1 + 2
		3 : (10, 20, 10), # TL 3 + 4
		4 : (10, 20, 10), # TL 3 + 4
		5 : (10, 20, 10), # TL 3 + 4
		6 : (7.5, 9, 1), # TL 5
		7 : (7.5, 9, 1), # TL 5
		8 : (7.5, 9, 1), # TL 5
	}
	galaxyDiseases = {
		# format diseaseID : (minDist, maxDist, number of diseases)
		1 : (20, 67.5, 16), # TL 1 + 2
		2 : (20, 67.5, 16), # TL 1 + 2
		3 : (5, 15, 4), # TL 3 + 4
		4 : (5, 15, 4), # TL 3 + 4
		5 : (5, 15, 4), # TL 3 + 4
		6 : (0, 5, 1), # TL 5
		7 : (0, 5, 1), # TL 5
		8 : (0, 5, 1), # TL 5
	}

class Galaxy:

	def __init__(self):
		self.systems = []
		self.centerX = 0.0
		self.centerY = 0.0
		self.radius = 0.0

class System:

	def __init__(self):
		self.x = 0.0
		self.y = 0.0
		self.name = '?'
		self.compOf = None
		self.starClass = '?'
		self.starSubclass = 0
		self.planets = []
		self._closest = []
		self.hasSR = 0
		self.hasDisease = 0
		self._moveable = 1

class Planet:

	def __init__(self):
		self.compOf = None
		self.type = '?'
		self.diameter = 0
		self.minerals = 0
		self.environ = 0
		self.energy = 0
		self.slots = 0
		self.maxSlots = 0
		self.starting = 0
		self.strategicRes = 0
		self.disease = 0

def generateGalaxy(galaxy):
	secX = 0
	for sectors in sectorsSpec:
		secY = 0
		for sector in sectors:
			minX = secX * sectorSize[0] + sectorsOffset[0]
			maxX = minX + sectorSize[0]
			minY = secY * sectorSize[1] + sectorsOffset[1]
			maxY = minY + sectorSize[1]
			for i in xrange(0, sector):
				system = System()
				galaxy.systems.append(system)
				system.x = random.uniform(minX, maxX)
				system.y = random.uniform(minY, maxY)
				system.compOf = galaxy
				generateSystem(system)
			secY += 1
		secX += 1

def generateGalaxy2(galaxy):
	galaxy.centerX = galaxyCenter[0]
	galaxy.centerY = galaxyCenter[1]
	galaxy.radius = galaxyRadius
	r = galaxyMinR + random.uniform(0, 0.5)
	dkeys = galaxyDensity.keys()
	dkeys.sort()
	dkeys.reverse()
	prevR = 5
	while r <= galaxyRadius:
		for key in dkeys:
			if key <= r:
				density = galaxyDensity[key]
				break
		print r, density
		d = 2 * math.pi * r
		aoff = random.uniform(0, math.pi * 2)
		dangle = density / d * math.pi * 0.9
		for i in range(0, int(d / density)):
			angle = aoff + i * density / d * math.pi * 2
			angle += random.uniform(-dangle, dangle)
			tr = random.uniform(prevR + 0.1, r)
			while 1:
				acceptable = 0
				system = System()
				generateSystem(system)
				# check requirements
				for planet in system.planets:
					if planet.type in ('D', 'R', 'C', 'H', 'M', 'E') and \
						planet.slots > 0:
						acceptable = 1
						break
				if acceptable:
					break
			galaxy.systems.append(system)
			system.x = math.cos(angle) * tr + galaxyCenter[0]
			system.y = math.sin(angle) * tr + galaxyCenter[1]
			system.compOf = galaxy
			system.dist = tr
			system.angle = angle
		prevR = r
		r += random.uniform(2, 4)
	# generate central black hole
	system = System()
	system.x = galaxyCenter[0]
	system.y = galaxyCenter[1]
	system.starClass = "b-"
	system.starSubclass = 7
	system.compOf = galaxy
	system._moveable = 0
	galaxy.systems.append(system)
	# generate starting systems
	if galaxyPlayers:
		r = (galaxyStartR[0] + galaxyStartR[1]) / 2
		d = 2 * math.pi * r
		print "Player distance:", d / galaxyPlayers
		gaoff = random.uniform(0, math.pi * 2)
		for i in range(0, galaxyPlayers / galaxyPlayerGroup):
			print "Placing group:", i + 1, "of", galaxyPlayers / galaxyPlayerGroup
			angle = gaoff + i * math.pi * 2 / (galaxyPlayers / galaxyPlayerGroup)
			tr = random.uniform(galaxyStartR[0], galaxyStartR[1])
			gx = math.cos(angle) * tr + galaxyCenter[0]
			gy = math.sin(angle) * tr + galaxyCenter[1]
			aoff = random.uniform(0, math.pi * 2)
			for j in range(0, galaxyPlayerGroup):
				angle = aoff + j * math.pi * 2 / galaxyPlayerGroup
				x = math.cos(angle) * galaxyGroupDist + gx
				y = math.sin(angle) * galaxyGroupDist + gy
				while 1:
					system = System()
					system.x = x
					system.y = y
					system.compOf = galaxy
					generateSystem(system)
					# check system properties
					e = 0
					h = 0
					d = 0
					ok = 1
					for planet in system.planets:
						if planet.type == 'E': e += 1; planet.starting = 1
						elif planet.type in ('D', 'R', 'C'):
							if planet.slots > 5: d += 1
							else: ok = 0; break
						elif planet.type == 'H': h += 1
						elif planet.type == 'M': ok = 0; break
					# fast rule
					#if ok and e == 1:
					#	break
					# slow (better) rule
					if ok and e == 1 and h == 1 and d == 1:
						break
				galaxy.systems.append(system)
	# strategic resources
	keys = galaxyResources.keys()
	keys.sort()
	keys.reverse()
	for key in keys:
		print "Placing resource", key
		minR, maxR, count = galaxyResources[key]
		aoff = random.uniform(0, math.pi * 2)
		for i in range(0, count):
			angle = aoff + i * math.pi * 2 / count
			tr = random.uniform(minR, maxR)
			x = math.cos(angle) * tr + galaxyCenter[0]
			y = math.sin(angle) * tr + galaxyCenter[1]
			# find closest system
			closest = galaxy.systems[0]
			minDist = 99999 #(closest.x - x) ** 2 + (closest.y - y) ** 2
			for system in galaxy.systems:
				dist = (system.x - x) ** 2 + (system.y - y) ** 2
				if dist < minDist and system.hasSR == 0:
					hasDRC = 0
					starting = 0
					# find suitable planet
					for planet in system.planets:
						if planet.starting:
							starting = 1
						if planet.type in ("D", "R", "C"):
							hasDRC = 1
					if not starting and hasDRC:
						minDist = dist
						closest = system
			print "	System", closest.x, closest.y, math.sqrt(minDist)
			# find planet on the closest system
			planets = []
			for planet in closest.planets:
				if planet.type in ("D", "R", "C"):
					planets.append(planet)
			planet = random.choice(planets)
			planet.strategicRes = key
			system = planet.compOf
			system.hasSR = 1
			print "	Planet", planet.type
	# diseases
	keys = galaxyDiseases.keys()
	keys.sort()
	keys.reverse()
	for key in keys:
		print "Placing disease", key
		minR, maxR, count = galaxyDiseases[key]
		aoff = random.uniform(0, math.pi * 2)
		for i in range(0, count):
			angle = aoff + i * math.pi * 2 / count
			tr = random.uniform(minR, maxR)
			x = math.cos(angle) * tr + galaxyCenter[0]
			y = math.sin(angle) * tr + galaxyCenter[1]
			# find closest system
			closest = galaxy.systems[0]
			minDist = 99999 #(closest.x - x) ** 2 + (closest.y - y) ** 2
			for system in galaxy.systems:
				dist = (system.x - x) ** 2 + (system.y - y) ** 2
				if dist < minDist and system.hasDisease == 0:
					hasHME = 0
					starting = 0
					# find suitable planet
					for planet in system.planets:
						if planet.starting:
							starting = 1
						if planet.type in ("M", "E"):
							hasHME = 1
					if not starting and hasHME:
						minDist = dist
						closest = system
			print "	System", closest.x, closest.y, math.sqrt(minDist)
			# find planet on the closest system
			planets = []
			for planet in closest.planets:
				if planet.type in ("M", "E"):
					planets.append(planet)
			planet = random.choice(planets)
			planet.disease = key
			system = planet.compOf
			system.hasDisease = 1
			print "	Planet", planet.type

def generateSystem(system, ranges = None):
	# system class and subclass
	# c -> supergiant
	# g -> giant
	# D -> dwarf
	# NS -> neutron star
	# BH -> black hole
	num = random.randrange(1, 1000000 + 1)
	system.starSubclass = random.randrange(0, 10)
	if   num < 10: system.starClass = 'cB'
	elif num < 20: system.starClass = 'cA'
	elif num < 40: system.starClass = 'cF'
	elif num < 60: system.starClass = 'cG'
	elif num < 80: system.starClass = 'cK'
	elif num < 100: system.starClass = 'cM'
	elif num < 500: system.starClass = 'gF'
	elif num < 1000: system.starClass = 'gG'
	elif num < 5500: system.starClass = 'gK'
	elif num < 10000: system.starClass = 'gM'
	elif num < 20000: system.starClass = 'mO'; system.starSubclass = random.randrange(5, 10)
	elif num < 30000: system.starClass = 'mB'
	elif num < 40000: system.starClass = 'mA'
	elif num < 120000: system.starClass = 'mF'
	elif num < 225000: system.starClass = 'mG'
	elif num < 465000: system.starClass = 'mK'
	elif num < 930000: system.starClass = 'mM'
	elif num < 940000: system.starClass = 'dB'
	elif num < 960000: system.starClass = 'dA'
	elif num < 980000: system.starClass = 'dF'
	elif num < 990000: system.starClass = 'dG'
	elif num < 999500: system.starClass = 'dK'
	elif num < 999995: system.starClass = 'n-'
	elif num < 1000000: system.starClass = 'b-'
	else: system.starClass = 'b-'
	# planets
	num = random.randrange(0, 100)
	planets = (0, 0, 0)
	mod = 1.0 / 2.0 # was 2 / 3
	if system.starClass[0] in ('c', 'g'):
		if num < 25:
			planets = distributePlanets(mod * random.randrange(1, 7))
	elif system.starClass[1] in ('O', 'B'):
		if num < 25:
			planets = distributePlanets(mod * random.randrange(1, 11))
	elif system.starClass[1] == 'A':
		if num < 75:
			planets = distributePlanets(mod * random.randrange(1, 11))
	elif system.starClass[1] == 'F' or system.starClass[1] == 'G':
		if num < 95:
			num = random.randrange(1, 7) + random.randrange(1, 7) + 3
			planets = distributePlanets(mod * num)
	elif system.starClass[1] == 'K':
		if num < 95:
			num = random.randrange(1, 7) + random.randrange(1, 7)
			planets = distributePlanets(mod * num)
	elif system.starClass[1] == 'M':
		if num < 95:
			num = random.randrange(1, 7)
			planets = distributePlanets(mod * num)
	elif system.starClass[0] == 'd':
		if num < 10:
			num = int(mod * random.randrange(1, 7) / 2)
			planets = (0, 0, num)
	elif system.starClass[0] == 'n' or system.starClass[0] == 'b':
		if num < 5:
			num = int(mod * random.randrange(1, 7) / 2)
			planets = (0, 0, num)
	# planets
	zone = 0
	for num in planets:
		for i in xrange(0, num):
			planet = Planet()
			planet.compOf = system
			system.planets.append(planet)
			generatePlanet(zone, planet)
		zone += 1
	# sort planets by energy
	system.planets.sort(lambda a, b: cmp(b.energy, a.energy))

def distributePlanets(num):
	num = int(num)
	if num <= 3: return (0, 1, num - 1)
	elif num <= 5:	return (1, 1, num - 2)
	elif num <=7: return (1, 2, num - 3)
	elif num <=11: return (2, 2, num - 4)
	elif num <=15: return (2, 3, num - 5)

def generatePlanet(zone, planet):
	sc = planet.compOf.starClass
	if sc == 'mF' or sc == 'mG' or sc == 'mK': isFGK = 1
	else: isFGK = 0
	if sc[0] == 'd' or sc == 'n-' or sc == 'b-': isDNB = 1
	else: isDNB = 0
	# diameter and type of planet
	num = random.randrange(0, 100)
	if zone == 0: # Zone A
		if num < 5: planet.type = 'A'
		elif num < 10: planet.type = 'G'; planet.diameter = dice(3, 6, 0) * 10000
		elif num < 60: planet.type = 'R'; planet.diameter = dice(1, 10, 0) * 1000
		elif num < 70: planet.type = 'D'; planet.diameter = dice(2, 6, 2) * 1000
		elif num < 100: planet.type = 'H'; planet.diameter = dice(3, 6, 1) * 1000
	elif zone == 1: # Zone B
		if num < 10: planet.type = 'A'
		elif num < 15: planet.type = 'G'; planet.diameter = dice(3, 6, 0) * 10000
		elif num < 25: planet.type = 'R'; planet.diameter = dice(1, 10, 0) * 1000
		elif num < 45: planet.type = 'D'; planet.diameter = dice(2, 6, 2) * 1000
		elif num < 70: planet.type = 'H'; planet.diameter = dice(3, 6, 1) * 1000
		elif num < 90:
			if isFGK:
				planet.type = 'M'; planet.diameter = dice(2, 6, 5) * 1000
			else:
				planet.type = 'H'; planet.diameter = dice(3, 6, 1) * 1000
		elif num < 100:
			if isFGK:
				# planet.type = 'E'; planet.diameter = dice(2, 6, 5) * 1000
				planet.type = 'E'; planet.diameter = dice(1, 4, 13) * 1000
			else:
				planet.type = 'H'; planet.diameter = dice(3, 6, 1) * 1000
	elif zone == 2: # Zone C
		if num < 15: planet.type = 'A'
		elif num < 75: planet.type = 'G'; planet.diameter = dice(3, 6, 0) * 10000
		elif num < 80: planet.type = 'R'; planet.diameter = dice(1, 10, 0) * 1000
		elif num < 90: planet.type = 'C'; planet.diameter = dice(1, 10, 0) * 1000
		elif num < 95: planet.type = 'D'; planet.diameter = dice(2, 6, 2) * 1000
		elif num < 100:
			if isDNB:
				planet.type = 'C'; planet.diameter = dice(1, 10, 0) * 1000
			else:
				planet.type = 'H'; planet.diameter = dice(3, 6, 1) * 1000
	# energy
	planet.energy = random.randrange(100 - zone * 50, 150 - zone * 50)
	# minerals
	if planet.type[0] in ('R', 'D', 'H', 'M'):
		density = dice(1, 6, 0) / 2.0 + 3
		planet.minerals = int(((planet.diameter / 500.0) + density * 10.0 + random.randrange(1, 101) / 2.0 - 45) * 2)
	elif planet.type[0] == 'A':
		diameter = dice(1, 10, 0) * 1000 # rock planet
		density = dice(1, 6, 0) / 2.0 + 3
		planet.minerals = int(((diameter / 500.0) + density * 10.0 + random.randrange(1, 101) / 2.0 - 45) * 2)
	elif planet.type[0] == 'G':
		diameter = dice(3, 6, 1) * 1000 # earth like planet
		density = dice(1, 6, 0) / 2.0 + 3
		planet.minerals = int(((diameter / 500.0) + density * 10.0 + random.randrange(1, 101) / 2.0 - 45) * 2)
	elif planet.type == 'E':
		planet.minerals = 100
	else:
		planet.minerals = 0
	if planet.minerals < 0:
		planet.minerals = 0
	# environment
	if planet.type == 'E': planet.environ = 100
	elif planet.type == 'M': planet.environ = random.randrange(25, 51)
	elif planet.type == 'H': planet.environ = random.randrange(12, 26)
	elif planet.type == 'D': planet.environ = random.randrange(6, 13)
	elif planet.type == 'C': planet.environ = random.randrange(0, 7)
	elif planet.type == 'R': planet.environ = random.randrange(0, 7)
	else: planet.environ = 0
	# slots
	slotsMod = 0.67
	planet.maxSlots = int((planet.diameter / 1000) * 1.5 * slotsMod)
	if planet.type == 'E': planet.slots = 9 # planet.slots = int(planet.maxSlots * 0.50)
	elif planet.type == 'M': planet.slots = int(planet.maxSlots * 0.50)
	elif planet.type == 'H': planet.slots = int(planet.maxSlots * 0.50)
	elif planet.type == 'D': planet.slots = int(planet.maxSlots * 0.75)
	elif planet.type == 'C': planet.slots = int(planet.maxSlots * 0.75)
	elif planet.type == 'R': planet.slots = int(planet.maxSlots * 0.75)
	else: planet.slots = 0
	# make sure that all planets except A and G has at least one slot
	if planet.type in "EMHDCR" and planet.slots == 0:
		#@print "Fixing slots", planet.type, planet.slots, planet.maxSlots
		planet.maxSlots = max(1, planet.maxSlots)
		planet.slots = max(1, planet.slots)
	#print planet.type, planet.environ, planet.minerals

def dice(num, range, offset):
	result = offset
	for i in xrange(0, num):
		result += random.randrange(1, range + 1)
	return result

def shiftSystems(galaxy, min, max, delta):
	print 'Shifting...'
	min = min * min
	max = max * max
	minMinDist = 1000000
	maxMinDist = 0
	for system1 in galaxy.systems:
		if not system1._moveable:
			continue
		minDist = [1000000, 100000, 100000]
		closestSystems = [None, None, None]
		for system2 in galaxy.systems:
			if system1 == system2 or not system2._moveable:
				continue
			dist = (system1.x - system2.x) ** 2 + (system1.y - system2.y) ** 2
			if dist < minDist[0]:
				minDist.pop()
				minDist.insert(0, dist)
				closestSystems.pop()
				closestSystems.insert(0, system2)
			elif dist < minDist[1]:
				minDist.pop()
				minDist.insert(1, dist)
				closestSystems.pop()
				closestSystems.insert(1, system2)
			elif dist < minDist[2]:
				minDist.pop()
				minDist.insert(2, dist)
				closestSystems.pop()
				closestSystems.insert(2, system2)
		system1._closest = closestSystems
		for closestSystem in closestSystems:
			if not closestSystem:
				continue
			dist = (system1.x - closestSystem.x) ** 2 + (system1.y - closestSystem.y) ** 2
			if dist < min and closestSystem:
				# move system away
				if system1.x > closestSystem.x:
					system1.x += random.uniform(0, delta)
					closestSystem.x -= random.uniform(0, delta)
				else:
					system1.x -= random.uniform(0, delta)
					closestSystem.x += random.uniform(0, delta)
				if system1.y > closestSystem.y:
					system1.y += random.uniform(0, delta)
					closestSystem.y -= random.uniform(0, delta)
				else:
					system1.y -= random.uniform(0, delta)
					closestSystem.y += random.uniform(0, delta)
			elif dist > max and closestSystem:
				# move systems closer
				if system1.x < closestSystem.x:
					system1.x += random.uniform(0, delta)
					closestSystem.x -= random.uniform(0, delta)
				else:
					system1.x -= random.uniform(0, delta)
					closestSystem.x += random.uniform(0, delta)
				if system1.y < closestSystem.y:
					system1.y += random.uniform(0, delta)
					closestSystem.y -= random.uniform(0, delta)
				else:
					system1.y -= random.uniform(0, delta)
					closestSystem.y += random.uniform(0, delta)
			if dist < minMinDist: minMinDist = dist
			if dist > maxMinDist: maxMinDist = dist
	print 'Finished [min. dist = <%.2f; %.2f>]' % (math.sqrt(minMinDist), math.sqrt(maxMinDist))
	return math.sqrt(minMinDist), math.sqrt(maxMinDist)

## info
def getInfo(galaxy):
	starTypes = {}
	planetTypes = {}
	planets = 0
	maxPlanets = 0
	minPlanets = 999
	planetDist = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	for system in galaxy.systems:
		starTypes[system.starClass] = starTypes.get(system.starClass, 0) + 1
		for planet in system.planets:
			planetTypes[planet.type] = planetTypes.get(planet.type, 0) + 1
			planets += 1
		sysPlanets = len(system.planets)
		maxPlanets = max(maxPlanets, sysPlanets)
		minPlanets = min(minPlanets, sysPlanets)
		planetDist[sysPlanets] += 1
	stars = len(galaxy.systems)
	print 'Systems:', stars
	print starTypes
	print 'Planets per system:', planetDist
	print 'Planets:', planets
	print 'min %d, max %d, avg %.2f' % (minPlanets, maxPlanets, float(planets) / stars)
	print 'Types:', planetTypes
	return stars, starTypes, planets, planetTypes

## saving
## galaxy - instance of Galaxy object
## fh - handle of file where galaxy will be saved -
##		must be os.open() filelike object and must be opened.
##		function calls close() method
def saveGalaxy(id, galaxy, fh):
	print 'Saving...'
	# names
	loadSystemNames()
	# save
	print >>fh, '<?xml version="1.0" encoding="UTF-8"?>'
	print >>fh, '<universe>'
	print >>fh, '\t<galaxy id="%s" x="%.2f" y="%.2f">' % (
		id, galaxy.centerX, galaxy.centerY
	)
	print >>fh, '\t\t<properties radius="%.2f"/>' % galaxy.radius
	for system in galaxy.systems:
		saveSystem(fh, system)
	print >>fh, '\t</galaxy>'
	print >>fh, '</universe>'
	fh.close()
	print 'Saved.'

def saveSystem(fh, system):
	print >>fh, '\t\t<system x="%.2f" y="%.2f">' % (system.x, system.y)
	# name = 'SCN-%04d%04d' % (system.x * 10, system.y * 10)
	global systemNames
	name = random.choice(systemNames)
	systemNames.remove(name)
	print >>fh, '\t\t\t<properties starClass="%s%d" name="%s"/>' % \
		(system.starClass, system.starSubclass, name)
	for planet in system.planets:
		savePlanet(fh, planet)
	print >>fh, '\t\t</system>'

def savePlanet(fh, planet):
	print >>fh, '\t\t\t<planet>'
	print >>fh, '\t\t\t\t<properties plType="%s" plMin="%d" plBio="%d" plEn="%d" plDiameter="%d" plSlots="%d" plMaxSlots="%d" plStratRes="%d" plDisease="%d" plStarting="%d"/>' % \
		(planet.type, planet.minerals, planet.environ, planet.energy, planet.diameter, planet.slots, planet.maxSlots, planet.strategicRes, planet.disease, planet.starting)
	if planet.starting:
		print >>fh, '\t\t\t\t<startingpoint/>'
	print >>fh, '\t\t\t</planet>'

## load names
systemNames = []

def loadSystemNames():
    global systemNames
    names = {}
    for line in file('data/SystemNames.txt'):
        names[line.strip()] = None
    systemNames = names.keys()

## Generates new galaxy and saves it to specified file
## fh - handle of file where galaxy will be saved -
##		must be os.open() filelike object and must be opened.
##		function calls close() method
def GenerateGalaxy(GalaxyID, fh):
	galaxy = Galaxy()
	generateGalaxy2(galaxy)
	step = 0
	while step < 25:
		min, max = shiftSystems(galaxy, 1.5, 5.0, 0.25)
		if min >= 1.0 and max <= 5.0:
			break
		step += 1
	print fh
	saveGalaxy(GalaxyID, galaxy, fh)

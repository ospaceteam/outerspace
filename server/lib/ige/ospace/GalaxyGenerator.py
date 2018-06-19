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
import sys
import tempfile

import data

import Const

class GalaxyTemplate(object):
    def __init__(self):
        self.galaxyType = self.__class__.__name__
        self.scenario = Const.SCENARIO_NONE
        self.minPlanets = 0
        self.maxPlanets = 0
        self.startR = (0.0, 999.0)
        self.players = 0
        self.playerGroup = 0
        self.groupDist = 0
        self.minR = 0
        # format {maxRadius: density, nextCircleRadius: differentDensity}
        self.density = {1: 1, 2: 2}
        self.minSystemLoneliness = 1.5
        self.maxSystemLoneliness = 5
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            #Const.SR_TL1A : [(0, 0, 0)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            #Const.DISEASE_MUTANT : [(0, 0, 0)]
        }

    @property
    def center(self):
        return (self.radius, self.radius)

    @property
    def radius(self):
        # making radius a bit bigger, as that is used in minimaps and chronicler
        return max(self.density.keys()) + 2

class Circle1SP(GalaxyTemplate):
    def __init__(self):
        super(Circle1SP, self).__init__()

        self.scenario = Const.SCENARIO_SINGLE
        self.minPlanets = 100
        self.maxPlanets = 150
        self.startR = (9.0, 11.0)
        self.players = 1
        self.playerGroup = 1
        self.groupDist = 0
        self.minR = 2
        # format {minRadius: density, nextCircleRadius: differentDensity}
        self.density = {2: 4, 5: 4, 12: 4.5}
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(11, 13, 2)],
            Const.SR_TL1B : [(11, 13, 2)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(2, 5, 3)]
        }


class Circle3BP(Circle1SP):
    def __init__(self):
        super(Circle3BP, self).__init__()

        self.minPlanets = int(1.3 * self.minPlanets)
        self.maxPlanets = int(1.2 * self.maxPlanets)
        self.scenario = Const.SCENARIO_BRAWL
        self.startR = (0.0, 0.0)
        self.players = 3
        self.playerGroup = 3
        self.groupDist = 10
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(11, 13, 3)],
            Const.SR_TL1B : [(11, 13, 3)]
        }
        self.diseases = {}


class Circle3SP(GalaxyTemplate):
    def __init__(self):
        super(Circle3SP, self).__init__()

        self.scenario = Const.SCENARIO_SINGLE
        self.minPlanets = 280
        self.maxPlanets = 350
        self.startR = (13.0, 15.0)
        self.players = 3
        self.playerGroup = 3
        self.groupDist = 3
        self.minR = 2
        # format {minRadius: density, nextCircleRadius: differentDensity}
        self.density = {2: 2.5, 6: 4, 12: 4.5, 20: 5}
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(15, 17, 3)],
            Const.SR_TL1B : [(15, 17, 3)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(2, 4, 3)]
        }

class Circle2CP(Circle3SP):
    def __init__(self):
        super(Circle2CP, self).__init__()

        self.players = 2
        self.playerGroup = 2
        self.scenario = Const.SCENARIO_COOP

        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(2, 4, 4)]
        }

class Circle3CP(Circle3SP):
    def __init__(self):
        super(Circle3CP, self).__init__()

        self.scenario = Const.SCENARIO_COOP
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(2, 4, 5)]
        }


class Circle5BP(Circle3SP):
    def __init__(self):
        super(Circle5BP, self).__init__()

        self.scenario = Const.SCENARIO_BRAWL
        self.startR = (0.0, 0.0)
        self.players = 5
        self.playerGroup = 5
        self.groupDist = 10
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(15, 17, 5)],
            Const.SR_TL1B : [(15, 17, 5)]
        }
        self.diseases = {}


class Circle9P(GalaxyTemplate):
    def __init__(self):
        super(Circle9P, self).__init__()

        self.scenario = Const.SCENARIO_OUTERSPACE
        self.minPlanets = 500
        self.maxPlanets = 600
        self.startR = (15.0, 18.0)
        self.players = 9
        self.playerGroup = 3
        self.groupDist = 4
        self.minR = 5
        # format {minRadius: density, nextCircleRadius: differentDensity}
        self.density = {5: 4, 10: 4.5, 20: 4.5, 26: 5}
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(20, 25, 6)],
            Const.SR_TL1B : [(20, 25, 6)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(13, 20, 6), (5, 9, 6)]
        }

class Circle42P(GalaxyTemplate):
    def __init__(self):
        super(Circle42P, self).__init__()

        self.scenario = Const.SCENARIO_OUTERSPACE
        self.minPlanets = 1500
        self.maxPlanets = 1800
        self.startR = (32.0, 36.0)
        self.players = 42
        self.playerGroup = 3
        self.groupDist = 4
        self.minR = 7.5
        # format {minRadius: density, nextCircleRadius: differentDensity}
        self.density = {7.5: 3, 10: 4, 20: 5, 30: 5.5, 40: 6, 50: 6}
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(20, 45, 15)],
            Const.SR_TL1B : [(20, 45, 15)],
            Const.SR_TL3A : [(8, 15, 7)],
            Const.SR_TL3B : [(8, 15, 7)],
            Const.SR_TL3C : [(8, 15, 7)],
            Const.SR_TL5A : [(7.5, 9, 1)],
            Const.SR_TL5B : [(7.5, 9, 1)],
            Const.SR_TL5C : [(7.5, 9, 1)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(20, 45, 16), (5, 15, 12), (0, 5, 3)]
        }

class Circle65P(GalaxyTemplate):
    def __init__(self):
        super(Circle65P, self).__init__()

        self.scenario = Const.SCENARIO_OUTERSPACE
        self.minPlanets = 3200
        self.maxPlanets = 3500
        self.startR = (45.0, 52.5)
        self.players = 65
        self.playerGroup = 5
        self.groupDist = 8
        self.minR = 7.5
        # format {minRadius: density, nextCircleRadius: differentDensity}
        self.density = {7.5: 3, 10: 4, 20: 5, 30: 5.5, 60: 6, 75: 6}
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(20, 67.5, 45)],
            Const.SR_TL1B : [(20, 67.5, 45)],
            Const.SR_TL3A : [(10, 20, 10)],
            Const.SR_TL3B : [(10, 20, 10)],
            Const.SR_TL3C : [(10, 20, 10)],
            Const.SR_TL5A : [(7.5, 9, 2)],
            Const.SR_TL5B : [(7.5, 9, 2)],
            Const.SR_TL5C : [(7.5, 9, 2)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(20, 67.5, 32), (5, 15, 18), (0, 5, 6)]
        }

class Test(GalaxyTemplate):
    def __init__(self):
        super(Test, self).__init__()

        self.scenario = Const.SCENARIO_OUTERSPACE
        self.minPlanets = 0
        self.maxPlanets = 200
        self.startR = (1.0, 7.0)
        self.players = 1
        self.playerGroup = 1
        self.groupDist = 1
        self.minR = 1
        # format {minRadius: density, nextCircleRadius: differentDensity}
        self.density = {1:1, 7: 2}
        self.resources = {
            # format resourceID : [(minDist, maxDist, number of resources)]
            Const.SR_TL1A : [(1, 7, 1)],
            Const.SR_TL1B : [(1, 7, 1)],
            Const.SR_TL3A : [(1, 7, 1)],
            Const.SR_TL3B : [(1, 7, 1)],
            Const.SR_TL3C : [(1, 7, 1)],
            Const.SR_TL5A : [(1, 7, 1)],
            Const.SR_TL5B : [(1, 7, 1)],
            Const.SR_TL5C : [(1, 7, 1)]
        }
        self.diseases = {
            # format diseaseID : (minDist, maxDist, number of diseases)
            Const.DISEASE_MUTANT : [(1, 7, 2)]
        }

class GalaxyGenerator:
    def __init__(self):
        self.templates = {}
        # TODO: I guess we can autodetect this somehow, in a future
        for templateClass in [Circle1SP, Circle3BP, Circle2CP, Circle3SP, Circle3CP, Circle5BP, Circle9P, Circle42P, Circle65P, Test]:
            templateInstance = templateClass()
            self.templates[templateInstance.galaxyType] = templateInstance

    def generateGalaxy(self, galaxyType):
        if not galaxyType in self.templates:
            return False
        while True:
            try:
                galaxy = generateGalaxy2(self.templates[galaxyType])
                break
            except IndexError:
                # this happens, if generator fails to place special
                # planet - easier than handling it inside is to roll
                # dice again
                continue
        self.shiftSystems(galaxy)

        return self.saveGalaxy(galaxy)

    def getGalaxyTypes(self):
        return self.templates.keys()

    def getGalaxyTemplate(self, galaxyType):
        return self.templates[galaxyType]

    def saveGalaxy(self, galaxy):
        """ saving galaxy - instance of Galaxy object into xml-formated file

            returns file name
        """
        # names
        loadSystemNames()
        fileHandle, galaxyFileName = tempfile.mkstemp(text = True)
        fh = os.fdopen(fileHandle, "w")
        # save
        print >>fh, '<?xml version="1.0" encoding="UTF-8"?>'
        print >>fh, '<universe>'
        print >>fh, '\t<galaxy galaxyType="%s" x="%.2f" y="%.2f">' % (
            galaxy.galaxyType, galaxy.centerX, galaxy.centerY
        )
        print >>fh, '\t\t<properties radius="%.2f" scenario="%s"/>' % (galaxy.radius, galaxy.scenario)
        for system in galaxy.systems:
            self.saveSystem(fh, system)
        print >>fh, '\t</galaxy>'
        print >>fh, '</universe>'
        fh.close()
        return galaxyFileName

    def saveSystem(self, fh, system):
        print >>fh, '\t\t<system x="%.2f" y="%.2f">' % (system.x, system.y)
        # name = 'SCN-%04d%04d' % (system.x * 10, system.y * 10)
        global systemNames
        name = random.choice(systemNames)
        systemNames.remove(name)
        print >>fh, '\t\t\t<properties starClass="%s%d" name="%s"/>' % \
            (system.starClass, system.starSubclass, name)
        for planet in system.planets:
            self.savePlanet(fh, planet)
        print >>fh, '\t\t</system>'

    def savePlanet(self, fh, planet):
        print >>fh, '\t\t\t<planet>'
        print >>fh, '\t\t\t\t<properties plType="%s" plMin="%d" plBio="%d" plEn="%d" plDiameter="%d" plSlots="%d" plMaxSlots="%d" plStratRes="%d" plDisease="%d" plStarting="%d"/>' % \
            (planet.type, planet.minerals, planet.environ, planet.energy, planet.diameter, planet.slots, planet.maxSlots, planet.strategicRes, planet.disease, planet.starting)
        if planet.starting:
            print >>fh, '\t\t\t\t<startingpoint/>'
        print >>fh, '\t\t\t</planet>'

    def shiftSystems(self, galaxy):
        """ makes sure no two systems are closer than _min and there are
            no systems further than _max parsecs from their closest three neighbours).

            Quite naive implementation."""
        MAX_STEP = 25
        DELTA = 0.25
        galaxyTemplate = self.templates[galaxy.galaxyType]
        _min = galaxyTemplate.minSystemLoneliness
        _max = galaxyTemplate.maxSystemLoneliness
        for i in xrange(MAX_STEP):
            newMin, newMax = self._shiftSystems(galaxy, _min, _max, DELTA)
            if newMin >= _min and newMax <= _max:
                break

    def _shiftSystems(self, galaxy, _min, _max, delta):
        # _min and _max are squared, so dist frequently calculated later
        # doesn't have to be square rooted
        print 'Shifting...'
        _min = _min * _min
        _max = _max * _max
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
                # this has to be calculated again, even though we had it before in minDist
                # because every move can alter others
                dist = (system1.x - closestSystem.x) ** 2 + (system1.y - closestSystem.y) ** 2
                if dist < _min and closestSystem:
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
                elif dist > _max and closestSystem:
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

def generateGalaxy2(galaxyTemplate):
    galaxy = Galaxy()
    stats = galaxyTemplate
    galaxy.galaxyType = stats.galaxyType
    galaxy.centerX, galaxy.centerY = stats.center
    galaxy.radius = stats.radius
    galaxy.scenario = stats.scenario
    r = stats.minR + random.uniform(0, 0.5)
    dkeys = stats.density.keys()
    dkeys.sort()
    dkeys.reverse()
    prevR = 5
    while r <= galaxy.radius:
        for key in dkeys:
            if key <= r:
                density = stats.density[key]
                break
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
            system.x = math.cos(angle) * tr + galaxy.centerX
            system.y = math.sin(angle) * tr + galaxy.centerY
            system.compOf = galaxy
            system.dist = tr
            system.angle = angle
        prevR = r
        r += random.uniform(2, 4)
    # generate central black hole
    system = System()
    system.x = galaxy.centerX
    system.y = galaxy.centerY
    system.starClass = "b-"
    system.starSubclass = 7
    system.compOf = galaxy
    system._moveable = 0
    galaxy.systems.append(system)
    # generate starting systems
    if stats.players:
        r = (stats.startR[0] + stats.startR[1]) / 2
        d = 2 * math.pi * r
        print "Player distance:", d / stats.players
        gaoff = random.uniform(0, math.pi * 2)
        for i in range(0, stats.players / stats.playerGroup):
            print "Placing group:", i + 1, "of", stats.players / stats.playerGroup
            angle = gaoff + i * math.pi * 2 / (stats.players / stats.playerGroup)
            tr = random.uniform(stats.startR[0], stats.startR[1])
            gx = math.cos(angle) * tr + galaxy.centerX
            gy = math.sin(angle) * tr + galaxy.centerY
            aoff = random.uniform(0, math.pi * 2)
            for j in range(0, stats.playerGroup):
                angle = aoff + j * math.pi * 2 / stats.playerGroup
                x = math.cos(angle) * stats.groupDist + gx
                y = math.sin(angle) * stats.groupDist + gy
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
                    #    break
                    # slow (better) rule
                    if ok and e == 1 and h == 1 and d == 1:
                        break
                galaxy.systems.append(system)
    # strategic resources
    keys = stats.resources.keys()
    keys.sort()
    keys.reverse()
    for key in keys:
      print "Placing resource", key
      for minR, maxR, count in stats.resources[key]:
        aoff = random.uniform(0, math.pi * 2)
        for i in range(0, count):
            angle = aoff + i * math.pi * 2 / count
            tr = random.uniform(minR, maxR)
            x = math.cos(angle) * tr + galaxy.centerX
            y = math.sin(angle) * tr + galaxy.centerY
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
            print "    System", closest.x, closest.y, math.sqrt(minDist)
            # find planet on the closest system
            planets = []
            for planet in closest.planets:
                if planet.type in ("D", "R", "C"):
                    planets.append(planet)
            planet = random.choice(planets)
            # now make sure resources are placed on big enough planets
            # to promote more strategic and less tactical fights over them
            # and ensure some minimal barrier is there for player to
            # overcome
            planet.diameter = dice(1, 6, 12) * 1000
            planet.maxSlots = int(planet.diameter / 1000.)
            planet.slots = dice(1, 2, 7)
            planet.strategicRes = key
            system = planet.compOf
            system.hasSR = 1
            print "    Planet", planet.type
    # diseases
    keys = stats.diseases.keys()
    keys.sort()
    keys.reverse()
    for key in keys:
      print "Placing disease", key
      for minR, maxR, count in stats.diseases[key]:
        aoff = random.uniform(0, math.pi * 2)
        for i in range(0, count):
            angle = aoff + i * math.pi * 2 / count
            tr = random.uniform(minR, maxR)
            x = math.cos(angle) * tr + galaxy.centerX
            y = math.sin(angle) * tr + galaxy.centerY
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
            print "    System", closest.x, closest.y, math.sqrt(minDist)
            # find planet on the closest system
            planets = []
            for planet in closest.planets:
                if planet.type in ("M", "E"):
                    planets.append(planet)
            planet = random.choice(planets)
            planet.disease = key
            system = planet.compOf
            system.hasDisease = 1
            print "    Planet", planet.type
    # check if number of planets is in desired interval
    noOfPlanets = 0
    for system in galaxy.systems:
        noOfPlanets += len(system.planets)
    if noOfPlanets < stats.minPlanets or noOfPlanets > stats.maxPlanets:
        print 'There was {0} planets.\nStarting new generation...'.format(noOfPlanets)
        return generateGalaxy2(galaxyTemplate)
    else:
        return galaxy

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
    system.planets.sort(key=lambda a: a.energy, reverse = True)

def distributePlanets(num):
    num = int(num)
    if num <= 3: return (0, 1, num - 1)
    elif num <= 5:    return (1, 1, num - 2)
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


## load names
systemNames = []

def loadSystemNames():
    global systemNames
    names = set([])

    with open(data.SYSTEM_NAMES_FILE) as names_file:
        for line in names_file:
            names.add(line.strip())
    systemNames = list(names)

if __name__ == '__main__':
    import sys

    galaxyType = sys.argv[1]
    targetFile = sys.argv[2]
    with open(targetFile, 'w') as fileHandle:
        GenerateGalaxy(galaxyType, fileHandle)

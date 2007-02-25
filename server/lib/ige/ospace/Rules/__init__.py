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

from ige.ospace.Const import *
from ige.IDataHolder import makeIDataHolder

from Techs import techs, Tech
from Techs import noop as techDefaultHandler

## General
turnsPerDay = 24
rotationMod = 384.0
playerTimeout = 60 * 60 * 24 * 21 # 21 days
novicePlayerTimeout = 60 * 60 * 24 * 7 # 7 days
messageTimeout = 60 * 60 * 24 * 14 # 14 days

## New player
startingPopulation = 9000
startingBio = 1000
startingMin = 1000
startingEn = 1000
startingScannerPwr = 100

## Production
maxProdQueueLen = 10
buildOnSamePlanetMod = 1
buildOnAnotherPlanetMod = 2
unusedProdMod = 0.75

## Environment
envInterval = 1000
envAutoMod = 10.0
envMax = 200
envSelfUpgradeChance = {"H": 5, "C": 1, "B": 500} # in ten thousandths (10 000)
planetSpec = {}
planetSpec[u'A'] = makeIDataHolder(
	minBio = 0,
	maxBio = 0,
	upgradeTo = None,
	downgradeTo = None,
)
planetSpec[u'G'] = makeIDataHolder(
	minBio = 0,
	maxBio = 0,
	upgradeTo = None,
	downgradeTo = None,
)
planetSpec[u'C'] = makeIDataHolder(
	minBio = 0,
	maxBio = 6,
	upgradeTo = u'D',
	upgradeEnReqs = (5, 180),
	downgradeTo = None,
)
planetSpec[u'R'] = makeIDataHolder(
	minBio = 0,
	maxBio = 6,
	upgradeTo = u'D',
	upgradeEnReqs = (5, 180),
	downgradeTo = None,
)
planetSpec[u'D'] = makeIDataHolder(
	minBio = 6,
	maxBio = 12,
	upgradeTo = u'H',
	upgradeEnReqs = (25, 150),
	downgradeTo = u'R',
)
planetSpec[u'H'] = makeIDataHolder(
	minBio = 12,
	maxBio = 25,
	upgradeTo = u'M',
	upgradeEnReqs = (50, 125),
	downgradeTo = u'D',
)
planetSpec[u'M'] = makeIDataHolder(
	minBio = 25,
	maxBio = 75,
	upgradeTo = u'E',
	upgradeEnReqs = (50, 100),
	downgradeTo = u'H',
)
planetSpec[u'E'] = makeIDataHolder(
	minBio = 75,
	maxBio = 125,
	upgradeTo = u"I",
	upgradeEnReqs = (50, 100),
	downgradeTo = u'M',
)
planetSpec[u"I"] = makeIDataHolder( # gaia
	minBio = 125,
	maxBio = 200,
	upgradeTo = None,
	downgradeTo = u"E",
)

## New colony settings
colonyMinBio = 600
colonyMinMin = 600
colonyMinEn = 600

## Storage
popPerSlot = 0
bioPerSlot = 0
minPerSlot = 0
enPerSlot = 0

popBaseStor = 4800
bioBaseStor = 4800
minBaseStor = 4800
enBaseStor = 4800

autoMinStorTurns = 6
autoReqStorTurns = 1

maxPopReserve = 1.125
tlPopReserve = 250

## Resources
stratResRate = turnsPerDay * 6

## Population
popGrowthRate = 0.02
popDieRate = 0.1
popMinDieRate = 100
popKillMod = 0.25
popSlotKillMod = 5 # how many people per 1 DMG get killed when slot is hit
popSlotHP = 100 # HP of habitable structures on slot (where people live)

## Research
maxRsrchQueueLen = 10
techBaseImprovement = 1
techMaxImprovement = 5

techImprCostMod = {1:480, 2:480, 3:720, 4:960, 5:1200, 6: 1440, 7: 1680} #per level
sciPtsPerCitizen = {1: 0, 2: 0.00075, 3: 0.00150, 4: 0.00175, 5: 0.00200, 6: 0.002125, 7: 0.00225, 99: 0} #per level

techImprEff = {1:0.750, 2:0.875, 3:1.000, 4:1.125, 5:1.250} #per sublevel

#maxSciPtsTL = {1:100, 2:200, 3:300, 4:400, 5:500, 6:600, 7:700}
#sciPtsStepFraction = 0.25

## Scanner
maxSignature = 100
scannerMinPwr = 1
level1InfoScanPwr = 1000
level2InfoScanPwr = 1200
level3InfoScanPwr = 1400
level4InfoScanPwr = 1600
maxScanPwr = 200000
mapForgetScanPwr = 0.94
partnerScanPwr = 300000

## Fleets
maxCmdQueueLen = 10
signatureBase = 1.10
operProdRatio = 0.001
combatRetreatWait = 3
starGateDamage = 0.2 # damage for 100% speed boost (double for 200%, etc...)
shipDecayRatio = 0.04
maxDamageAbsorb = 5 # max absorbed damage for tech "damageAbsorb" property.

## Buildings
repairRatio = 0.02
repairRunningRatio = 0.01
decayRatio = 0.02
storCapacityOfOfflineStruct = 1.0
plShieldRegen = 0.05 #regen rate of planetary shield

## Diplomacy
baseRelationChange = -5
relLostWhenAttacked = -1000000
defaultRelation = REL_NEUTRAL
contactTimeout = 6 * turnsPerDay

voteForImpPeriod = 6 * turnsPerDay
ratioNeededForImp = 0.6666

pactDescrs = {}
pactDescrs[PACT_ALLOW_CIVILIAN_SHIPS] = makeIDataHolder(
	targetRel = 500,
	relChng = 10,
	validityInterval = (0, 10000),
)
pactDescrs[PACT_ALLOW_MILITARY_SHIPS] = makeIDataHolder(
	targetRel = 750,
	relChng = 8,
	validityInterval = (0, 10000),
)
pactDescrs[PACT_ALLOW_TANKING] = makeIDataHolder(
	targetRel = 750,
	relChng = 7,
	validityInterval = (0, 10000),
)
pactDescrs[PACT_MINOR_CP_COOP] = makeIDataHolder(
	targetRel = 1000,
	relChng = 6,
	effectivity = 0.05,
	validityInterval = (625, 10000),
)
pactDescrs[PACT_MAJOR_CP_COOP] = makeIDataHolder(
	targetRel = 1000,
	relChng = 1,
	effectivity = 0.05,
	validityInterval = (875, 10000),
)
pactDescrs[PACT_SHARE_SCANNER] = makeIDataHolder(
	targetRel = 1000,
	relChng = 1,
	validityInterval = (625, 10000),
)
pactDescrs[PACT_MINOR_SCI_COOP] = makeIDataHolder(
	targetRel = 750,
	relChng = 1,
	effectivity = 0.05,
	validityInterval = (625, 10000),
)
pactDescrs[PACT_MAJOR_SCI_COOP] = makeIDataHolder(
	targetRel = 1000,
	relChng = 1,
	effectivity = 0.05,
	validityInterval = (875, 10000),
)

## Morale
baseGovPwr = 50000
maxMorale = 100.0
minMoraleTrgt = 30.0
revoltThr = 25.0
moraleChngPerc = 0.03
moraleHighPopPenalty = 2.0
moraleBasePop = 10000
moraleLowPop = 5000
moraleLowPopBonus = 40.0
moraleLostWhenSurrender = 0.0
moraleLostNoFood = 1.0
moraleModPlHit = 96.0 # how many morale point per 1 per cent of damage
moralePerPointChance = 5.0 # for every point below revoltThr % chance for revolt
moraleProdStep = 10
moraleProdBonus = [-0.875, -0.75, -0.625, -0.50, -0.375, -0.25, -0.125, 0.0, 0.0, 0.125, 0.25]

## Revolt
revoltDestrBio = 0.05
revoltDestrMin = 0.05
revoltDestrEn = 0.05
revoltPenalty = 0.75

## Messages
messageMaxAge = turnsPerDay * 3

## Asteroid
asteroidPerHPBioMod = - 0.01
asteroidPerHPMinMod = + 0.001
asteroidGenerPerc = 0.001
asteroidMinPlMinAbund = 10
asteroidModPwr = 2.0
asteroidTargetInSystem = 0.2
asteroidMinHP = 100
asteroidMaxHP = 1000
asteroidMinSpeed = 2.0
asteroidMaxSpeed = 4.0
asteroidMisDef = 1
asteroidDef = 4
asteroidAttack = 4
asteroidImpactDelay = 6

## Projects
projECOINIT3PlBio = 1

## Ships
shipImprovementMod = 1.05
shipMaxImprovements = 5
shipMaxDesigns = 40
shipExpToLevel = {0:1, 1:2, 2:2, 3:3, 4:3, 5:3, 6:3, 7:4, 8:4, 9:4, 10:4, 11:4,
	12:4, 13:4, 15:5}
shipDefLevel = 5
shipLevelEff = {1:0.50, 2:0.75, 3:1.00, 4:1.25, 5:1.50}
shipBaseExpMod = 20
shipBaseExp = {0:10, 1:20, 2:40, 3:80, 4:160}
shipTargetPerc = [25, 50, 90, 100]

shipMinUpgrade = 120
shipUpgradeMod = 1.375
shipUpgradePts = [1, 3, 10]
weaponDmgDegrade = [1.0, 0.5, 0.25, 0.125]

## EMR
emrMinDuration = 36
emrMaxDuration = 60
emrPeriod = 576
emrSeasons = [None, None, None, None]
emrSeasons[0] = makeIDataHolder(
	name = "spring",
	startTime = 0,
	endTime = 143,
	emrLevelMin = 0.75,
	emrLevelMax = 1.25,
)
emrSeasons[1] = makeIDataHolder(
	name = "summer",
	startTime = 144,
	endTime = 287,
	emrLevelMin = 0.50,
	emrLevelMax = 1.00,
)
emrSeasons[2] = makeIDataHolder(
	name = "fall",
	startTime = 287,
	endTime = 431,
	emrLevelMin = 0.50,
	emrLevelMax = 1.50,
)
emrSeasons[3] = makeIDataHolder(
	name = "winter",
	startTime = 432,
	endTime = 575,
	emrLevelMin = 1.00,
	emrLevelMax = 1.50,
)

## Pirates
pirateInfluenceRange = 7.5 # in parsecs
pirateGainFamePropability = lambda d: 2 - d * 0.2
pirateLoseFameProbability = lambda d: 1 - (15 - d) * 0.2
pirateCaptureInRangeFame = 1
pirateSurvivalFame = 1
pirateCaptureOutOfRangeFame = -1
pirateColonyCostMod = 1.5
pirateTL3StratResColonyCostMod = 0.25
pirateGovPwr = int(500000 * 1.25)
pirateCanStealImprovements = 3
pirateGrantHSE = 60*24*3600    #60 days
pirateGrantASSEM = 105*24*3600  #105 days
pirateGrantCOND = 105*24*3600   #105 days

## Bonuses
galLeaderBonus = 0.05
galImperatorBonus = 0.10

## Combat
combatStructureHitMod = 0.75
combatShipHitMod = 0.75
combatHitXferMod = 3.00
combatStructDefense = 1

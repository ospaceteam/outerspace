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

from ige.Const import *

## additional object types
T_GALAXY = 100
T_SYSTEM = 101
T_PLANET = 102
T_FLEET = 103
T_ALLIANCE = 104
T_TECHNOLOGY = 105
T_ASTEROID = 106
T_NATURE = 107
T_AIPLAYER = 108
T_AIRENPLAYER = 109
T_AIMUTPLAYER = 110
T_AIPIRPLAYER = 111
T_AIEDENPLAYER = 112
T_PIRPLAYER = 113
T_WORMHOLE = 114

PLAYER_TYPES = (T_PLAYER, T_NATURE, T_AIPLAYER, T_AIRENPLAYER, T_AIMUTPLAYER,
	T_AIPIRPLAYER, T_AIEDENPLAYER, T_PIRPLAYER)

## debug types
T_STRUCT = 300
T_TASK = 301
T_SCAN = 302
T_RESTASK = 303
T_SHIP = 304
T_STATS = 305
T_DIPLREL = 306

## additional indexes and OIDs
OID_NATURE = 60

## messages
MSG_WASTED_SCIPTS = 1001 # waste research points
MSG_COMPLETED_RESEARCH = 1002 # research completed
MSG_CANNOTBUILD_SHLOST = 1003 # cannot colonize planets - ship lost
MSG_CANNOTBUILD_NOSLOT = 1004 # cannot build - no free slot
# NOT NEEDED MSG_DESTROYED_BUILDING = 1005 # building has been destroyed
MSG_WASTED_PRODPTS = 1006 # waste production points
MSG_LOST_PLANET = 1007 # planet lost
MSG_COMPLETED_STRUCTURE = 1008 # construction of structure completed
MSG_COMPLETED_SHIP = 1009 # construction of ship completed
MSG_GAINED_PLANET = 1010 # planet gained
MSG_COMBAT_RESULTS = 1011 # damage taken, caused and lost ships/structures
MSG_EXTRACTED_STRATRES = 1012 # found strategy resource
MSG_COMBAT_LOST = 1013 # surrender to
MSG_DESTROYED_FLEET = 1014 # fleet destroyed
MSG_COMBAT_WON = 1015 # combat won
MSG_NEW_GOVCENTER = 1016 # new government centre
MSG_REVOLT_STARTED = 1017 # somebody started rebelling
MSG_REVOLT_ENDED = 1018 # somebody ended rebelling
MSG_INVALID_TASK = 1019 # task does not pass validity checks
MSG_NOSUPPORT_POP = 1020 # population has not enought support
MSG_COMPLETED_PROJECT = 1021 # project has been completed
MSG_ENABLED_TIME = 1022 # time has been started
MSG_MISSING_STRATRES = 1023 # missing strategic resource
MSG_DOWNGRADED_PLANET_ECO = 1024 # planet's ecology system was downgraded
MSG_UPGRADED_PLANET_ECO = 1025 # planet's ecology system was upgraded
MSG_UPGRADED_SHIP = 1026 # ship upgraded
MSG_DELETED_DESIGN = 1027 # design has been deleted
MSG_CANNOT_UPGRADE_SR = 1028 # cannot upgrade ship, strat. res. missing
MSG_DELETED_RESEARCH = 1029 # research deleted (disabled)
MSG_DAMAGE_BY_SG = 1030 # deceleration damage from Star Gate
MSG_GAINED_FAME = 1031 # pirate gained fame
MSG_LOST_FAME = 1032 # pirate lost some fame
MSG_GAINED_TECH = 1033 # pirate gained technology
MSG_EXTRACTED_ANTIMATTER_SYNTH = 1034 # Antimatter Synthesis success
MSG_ENTERED_WORMHOLE = 1035 # Wormhole Entered
MSG_NOT_ENTERED_WORMHOLE = 1036 # Failed to enter wormhole on enter wormhole command
MSG_FOUND_WORMHOLE = 1037 #todo
MSG_DELOY_HANDLER = 1038

MSG_GNC_EMR_FORECAST = 2000 # Electromagnetic radiation (EMR) forecast
MSG_GNC_EMR_CURRENT_LVL = 2001 # Curren level of EMR
MSG_GNC_GALAXY_RESTARTED = 2002 # Galaxy was restarted
MSG_GNC_VOTING_COMING = 2003 # new voting in 1:00 turna
MSG_GNC_VOTING_NOWINNER = 2004 # no winner in elections
MSG_GNC_VOTING_LEADER = 2005 # winner is leader
MSG_GNC_VOTING_IMPERATOR = 2006 # winner is imperator
MSG_GNC_GALAXY_GENERATOR = 2007 # galaxy generator information
MSG_GNC_GALAXY_AUTO_RESTARTED = 2008 # Galaxy was automatically restarted

## relations
REL_ENEMY_LO = 0
REL_ENEMY = 0
REL_ENEMY_HI = 125
REL_UNFRIENDLY_LO = 125
REL_UNFRIENDLY = 250
REL_UNFRIENDLY_HI = 375
REL_NEUTRAL_LO = 375
REL_NEUTRAL = 500
REL_NEUTRAL_HI = 625
REL_FRIENDLY_LO = 625
REL_FRIENDLY = 750
REL_FRIENDLY_HI = 875
REL_ALLY_LO = 875
REL_ALLY = 1000
REL_ALLY_HI = 1000
REL_UNITY = 1250
REL_UNDEF = 100000
REL_DEFAULT = REL_NEUTRAL

## pact values
PACT_OFF = 0
PACT_INACTIVE = 1
PACT_ACTIVE = 2

## pacts
# fleet related
PACT_ALLOW_CIVILIAN_SHIPS = 100
PACT_ALLOW_MILITARY_SHIPS = 101
PACT_ALLOW_TANKING = 102

# civilian
PACT_MINOR_SCI_COOP = 200
PACT_MAJOR_SCI_COOP = 201
PACT_MINOR_CP_COOP = 202
PACT_MAJOR_CP_COOP = 203

# military
PACT_SHARE_SCANNER = 300

# governor
PACT_ACCEPT_AS_GOVERNOR = 400
PACT_OFFER_TO_BE_GOVERNOR = 401

## fleet actions
FLACTION_NONE = 0
FLACTION_MOVE = 1
FLACTION_DECLAREWAR = 1000
FLACTION_DEPLOY = 1002
FLACTION_REDIRECT = 1003
FLACTION_REFUEL = 1004
FLACTION_REPEATFROM = 1005
FLACTION_WAIT = 1006
FLACTION_ENTERWORMHOLE = 1007

## ship attributes
SHIP_IDX_DESIGNID = 0
SHIP_IDX_HP = 1
SHIP_IDX_SHIELDHP = 2
SHIP_IDX_EXP = 3

## structure status
STRUCT_STATUS_NOTOPER   = 0x0000
STRUCT_STATUS_OK        = 0x0001
STRUCT_STATUS_DETER     = 0x0002
STRUCT_STATUS_NOBIO     = 0x0004
# NOT NEEDED NOSTRUCT_STATUS_NOMIN     = 0x0008
STRUCT_STATUS_NOEN      = 0x0010
STRUCT_STATUS_NOPOP     = 0x0020
STRUCT_STATUS_NEW       = 0x0040
STRUCT_STATUS_REPAIRING = 0x0080
STRUCT_STATUS_ON        = 0x1000
STRUCT_STATUS_OFF       = 0x0000

STRUCT_STATUS_RESETFLGS = 0xf000

STRUCT_IDX_TECHID = 0
STRUCT_IDX_HP = 1
STRUCT_IDX_STATUS = 2
STRUCT_IDX_OPSTATUS = 3

## contact types
CONTACT_NONE = 0
CONTACT_DYNAMIC = 1
CONTACT_STATIC = 2

## starting positons types
STARTPOS_NEWPLAYER = 1
STARTPOS_AIPLAYER = 2
STARTPOS_PIRATE = 3

## strategic resources
SR_NONE = 0
# TL 1 + TL 2
SR_TL1A = 1 # URANIUM
SR_TL1B = 2 # TITAN
# TL 3 + TL 4
SR_TL3A = 3
SR_TL3B = 4
SR_TL3C = 5
# TL 5
SR_TL5A = 6
SR_TL5B = 7
SR_TL5C = 8
# TL ALIENS
SR_TLAA = 1000 # Unnilseptium
# "goods"
SR_BIO1 = 100

## ship improvements
SI_SPEED = 1
SI_TANKS = 2
SI_ATT = 3
SI_DEF = 4
SI_HP = 5
SI_SHIELDS = 6
SI_SIGNATURE = 7
SI_SCANNERPWR = 8

## type of buoys
BUOY_NONE = 0
BUOY_PRIVATE = 1
BUOY_TO_ALLY = 2
BUOY_FROM_ALLY = 3
BUOY_TO_SCANNERSHARE = 4

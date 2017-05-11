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

#
# This module contains global data
#
from ige.ospace import Const

showBackground = 1
app = None
mainGameDlg = None
updateDlgs = []
cmdInProgress = 0

# i18n (delayed translation)
def N_(msg): return msg

planetTypes = {
    'A': N_('Asteroid'),
    'G': N_('Gas Giant'),
    'R': N_('Rock'),
    'C': N_('Cold'),
    'D': N_('Desert'),
    'H': N_('Hostile'),
    'M': N_('Marginal'),
    'E': N_('Terrestrial'),
    'I': N_('Gaia'),
    None: N_('Unknown'),
}

starTypes = {
    'c': N_('Super giant'),
    'g': N_('Giant'),
    'm': N_('Main sequence'),
    'd': N_('Dwarf'),
    'b': N_('Black hole'),
    'n': N_('Neutron star'),
    'w': N_('Worm hole'),
}

shipClasses = {
    0: N_('small'),
    1: N_('medium'),
    2: N_('large'),
    3: N_('planet'),
}

fleetActions = {
    0: N_('None'),
    1: N_('Move to'),
    1000: N_("Declare War at"),
    1002: N_("Deploy Ship"),
    1003: N_("Redirect to"),
    1004: N_("Refuel at"),
    1005: N_("Repeat from"),
    1006: N_("Wait"),
    1007: N_("Enter Wormhole at"),
}

stratRes = {
    0: N_("None"),
    1: N_("Uranium"),
    2: N_("Titanium"),
    3: N_("Chromium"),
    4: N_("Silicium"),
    5: N_("Carboneum"),
    6: N_("Antimatter"),
    7: N_("Plutonium"),
    8: N_("Wolframium"),
    100: N_("Mutagen"),
    1000: N_("Unnilseptium")
}

relationNames = [N_("Enemy"), N_("Unfriendly"), N_("Unfriendly"), N_("Neutral"),
    N_("Neutral"), N_("Friendly"), N_("Friendly"), N_("Allied")]

pactNames = {
    Const.PACT_ALLOW_CIVILIAN_SHIPS: N_("Passage for civilian ships"),
    Const.PACT_ALLOW_MILITARY_SHIPS: N_("Passage for military ships"),
    Const.PACT_ALLOW_TANKING: N_("Permission to tank ships"),
    Const.PACT_MINOR_CP_COOP: N_("Limited trade agreement"),
    Const.PACT_MAJOR_CP_COOP: N_("Unlimited trade agreement"),
    Const.PACT_SHARE_SCANNER: N_("Scanner map exchange"),
    Const.PACT_MINOR_SCI_COOP: N_("Research information exchange"),
    Const.PACT_MAJOR_SCI_COOP: N_("Research cooperation"),
}

pacts = [
    Const.PACT_ALLOW_CIVILIAN_SHIPS,
    Const.PACT_ALLOW_MILITARY_SHIPS,
    Const.PACT_ALLOW_TANKING,
    Const.PACT_MINOR_CP_COOP,
    Const.PACT_SHARE_SCANNER,
    Const.PACT_MINOR_SCI_COOP,
    Const.PACT_MAJOR_CP_COOP,
    Const.PACT_MAJOR_SCI_COOP,
]

pactStates = [N_("Disabled"), N_("Enabled"), N_("Active")]

mailboxSpec = {
    (Const.T_PLAYER, "INBOX"): (N_("Mailbox"), "sender"),
    (Const.T_PLAYER, "OUTBOX"): (N_("Sent"), None),
    (Const.T_PLAYER, "EVENTS"): (N_("Events"), None),
    (Const.T_UNIVERSE, "NEWS"): (N_("News"), None),
    (Const.T_UNIVERSE, "PUBLIC"): (N_("Public"), "forum"),
    (Const.T_GALAXY, "PUBLIC"): (N_("Public"), "forum"),
    (Const.T_GALAXY, "NEWS"): (N_("News"), None),
}

def mailboxStripLang(forum):
    if "_" in forum:
        return forum.split("_")[1]
    else:
        return forum


# morale states
moraleStates = {
    -0.875: N_("MORALE IS TERRIBLE"),
    -0.75: N_("MORALE IS TERRIBLE"),
    -0.625: N_("MORALE IS TERRIBLE"),
    -0.50: N_("MORALE IS BAD"),
    -0.375: N_("MORALE IS VERY LOW"),
    -0.25: N_("MORALE IS LOW"),
    -0.125: N_("MORALE IS BELOW AVERAGE"),
    0.0: N_(" "),
    0.125: N_("MORALE IS HIGH"),
    0.25: N_("MORALE IS SUPERB"),
}
# severity

CRI = 3
MAJ = 2
MIN = 1
INFO = 0
NONE = INFO
DISABLED = -1

msgSeverity = {
    CRI: N_("Critical"),
    MAJ: N_("Major"),
    MIN: N_("Minor"),
    INFO: N_("Info"),
    DISABLED: N_("Disabled"),
}

sevColors = {
    CRI: (0xff, 0x80, 0x80),
    MAJ: (0xff, 0xff, 0x00),
    MIN: None,
    NONE: (0xc0, 0xc0, 0xc0),
    DISABLED: (0x80, 0x80, 0x80),
}

# StarMapWidget overlays
OVERLAY_OWNER = "owner"
OVERLAY_DIPLO = "diplomacy"
OVERLAY_BIO = "bio"
OVERLAY_FAME = "fame"
OVERLAY_MIN = "min"
OVERLAY_SLOT = "slot"
OVERLAY_STARGATE = "stargate"
OVERLAY_DOCK = "dock"
OVERLAY_MORALE = "morale"
OVERLAY_PIRATECOLONYCOST = "piratecolony"

OVERLAY_TYPES = [OVERLAY_OWNER, OVERLAY_DIPLO, OVERLAY_BIO, OVERLAY_FAME, OVERLAY_MIN, OVERLAY_SLOT, OVERLAY_STARGATE, OVERLAY_DOCK, OVERLAY_MORALE, OVERLAY_PIRATECOLONYCOST]

# colors
playerHighlightColor = (0xff, 0xa5, 0x4d)

playersHighlightColorsOld = {
    32935: (0x55, 0x55, 0x55), # plasmon
    32964: (0x00, 0xa0, 0xa0), # niki
    32921: (0xaa, 0xaa, 0xaa), # medved
    33216: (0xff, 0x00, 0x00), # artanis
    32917: (0x88, 0x00, 0x00), # johanka
    33400: (0xaa, 0x00, 0x00), # lev
    33166: (0x33, 0x00, 0x00), # pedasr
    32606: (0x00, 0x55, 0x55), # starlord
    33266: (0x00, 0xaa, 0xff), # mcc
}

playersHighlightColors = {
}

objectFocus = {
}

savePassword = False

# i18n
del N_

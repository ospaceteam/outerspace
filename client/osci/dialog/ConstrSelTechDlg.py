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

import pygameui as ui
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client, sequip
import ige.ospace.Const as Const

ENGINE = 1
SMALL = 2
MEDIUM = 4
LARGE = 8
PLANET = 16
OTHER = 32
ARMOR = 64
SHIELD = 128
POD = 256
SCANNER = 512

typeText = {
    ENGINE: _('Engine'),
    SMALL:  _('Anti-small'),
    MEDIUM: _('Anti-medium'),
    LARGE:  _('Anti-large'),
    PLANET: _('Anti-planet'),
    OTHER:  _('Other'),
    ARMOR:  _('Armor'),
    SHIELD: _('Shield'),
    POD:    _('Deployable'),
    SCANNER:_('Scanner'),
}

class ConstrSelTechDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self, techType, techSubtype, selectCallback, selected = 0, hullID = 0):
        self.techID = Const.OID_NONE
        self.selectCallback = selectCallback
        self.techType = techType
        self.techSubtype = techSubtype
        self.selected = selected
        if hullID:
            self.hullType = client.getFullTechInfo(hullID).combatClass
        else:
            self.hullType = 0
        self.typeFilter = ENGINE | \
                          SMALL | MEDIUM | LARGE | PLANET | \
                          OTHER | ARMOR | SHIELD | POD | SCANNER
        self.show()
        self.win.show()
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()
        # unregister updates
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)

    def update(self):
        self.show()

    def getTechType(self, tech):
        if getattr(tech, "subtype") == "seq_eng":
            return ENGINE
        if getattr(tech, "weaponClass") == 0 and getattr(tech, "weaponDmgMin") > 0:
            return SMALL
        if getattr(tech, "weaponClass") == 1:
            return MEDIUM
        if getattr(tech, "weaponClass") == 2:
            return LARGE
        if getattr(tech, "weaponClass") == 3:
            return PLANET
        if getattr(tech, "subtype") == "seq_mod" \
            and (
                getattr(tech, "maxHP") > 0
                or getattr(tech, "autoRepairFix") > 0
                or getattr(tech, "autoRepairPerc") > 0
                ):
            # armor modules
            return ARMOR
        if getattr(tech, "shieldPerc") > 0 or getattr(tech, "hardShield") > 0:
            return SHIELD
        if getattr(tech, "subtype") == "seq_struct":
            return POD
        if getattr(tech, "subtype") == "seq_mod" and getattr(tech, 'scannerPwr') > 0:
            return SCANNER
        return OTHER

    def show(self):
        self.showItems()

    def showItems(self):
        items = []
        selected = None
        player = client.getPlayer()
        for techID in player.techs:
            tech = client.getTechInfo(techID)
            if getattr(tech, self.techType) == 0:
                continue
            if self.techSubtype and tech.subtype not in self.techSubtype:
                continue
            # skip equipment not suitable for this hull
            if tech.minHull > self.hullType:
                continue
            if tech.maxHull < self.hullType:
                continue

            techType = self.getTechType(tech)
            if self.typeFilter & techType == 0:
                continue

            item = ui.Item(tech.name, tData = sequip.getLongDescr(techID), techID = techID,
                            tType = typeText[techType])

            if techID == self.selected:
                selected = item

            items.append(item)
        self.win.vList.items = items
        self.win.vList.itemsChanged()
        self.win.vList.selectItem(selected)

    def onCancel(self, widget, action, data):
        self.hide()

    def onFilter(self, widget, action, data):
        if widget.checked:
            self.typeFilter |= widget.data
        else:
            self.typeFilter &= ~widget.data
        self.showItems()

    def onSelect(self, widget, action, data):
        self.hide()
        if self.win.vList.selection:
            self.selectCallback(self.win.vList.selection[0].techID)

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _('Select component'),
            rect = ui.Rect((w - 764) / 2, (h - 304) / 2, 764, 304),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        # component list
        ui.Listbox(self.win, layout = (0, 0, 38, 13), id = "vList",
            columns = (
                (_('Name'), 'text', 9, ui.ALIGN_W),
                (_('Type'), 'tType', 4, ui.ALIGN_W),
                (_('Data'), 'tData', 0, ui.ALIGN_W),
            ),
            sortedBy = ('tType', 1),
            action = "onSelect",
            rmbAction = "onCancel"
        )

        # status bar + submit/cancel
        ui.TitleButton(self.win, layout = (33, 13, 5, 1), text = _('Cancel'), action = 'onCancel')
        ui.Title(self.win, id = 'vStatusBar', layout = (0, 13, 33, 1), align = ui.ALIGN_W)
        #self.win.statusBar = self.win.vStatusBar

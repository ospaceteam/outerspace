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
import bisect
import math

import pygameui as ui
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
import ige.ospace.Const as Const
from ige.ospace import Rules

class FleetsOverviewDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self):
        if gdata.config.defaults.showredirects != None:
            val = gdata.config.defaults.showredirects
            self.win.vRedirects.checked = val == 'yes'

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

    def _analyzeRelations(self, playerID, fleet):
        # this evaluates color, and if it should be shown at all
        # get check box selections
        checkBoxes = [self.win.vEnemy.checked,
                      self.win.vUnfriendy.checked,
                      self.win.vNeutral.checked,
                      self.win.vFriendly.checked,
                      self.win.vAllied.checked]

        # check fleet color and decide if display the fleet
        if hasattr(fleet, 'owner'):
            plRelation = client.getRelationTo(fleet.owner)
            fgColor = res.getPlayerColor(fleet.owner)
            if fleet.owner == playerID and self.win.vMine.checked:
                return fgColor
            return fgColor if checkBoxes[bisect.bisect(Const.REL_BOUNDARIES, plRelation)] else None
        else:
            # with no owner assume enemy
            return res.getFFColorCode(Const.REL_ENEMY_LO) if checkBoxes[0] else None

    def _populateName(self, fleet):
        return fleet.customname if hasattr(fleet, 'customname') and fleet.customname \
                                else getattr(fleet, 'name', res.getUnknownName())

    def _populatePopup(self, playerID, fleet):
        if hasattr(fleet, 'owner') and playerID != fleet.owner:
            owner = getattr(client.get(fleet.owner, noUpdate=1), "name", res.getUnknownName())
            ownerName = " (%s)" % owner
            ownerNameTip = owner
            ownerTipTitle = _("Owner")
        else:
            ownerName = ""
            ownerNameTip = ""
            ownerTipTitle = ""
        return ownerName, ownerNameTip, ownerTipTitle

    def _populateLocation(self, playerID, fleet):
        systemName = "-"
        if hasattr(fleet, 'orbiting') and fleet.orbiting:
            system = client.get(fleet.orbiting, noUpdate=1)
            systemName = getattr(system, "name", res.getUnknownName())
        elif hasattr(fleet, 'closeSystem'):
            system = client.get(fleet.closeSystem, noUpdate=1)
            systemName = _("%s (dst)") % getattr(system, "name", res.getUnknownName())
        return systemName

    def _populateOrder(self, fleet):
        # get fleet current action and target of action
        order = "-"
        targetName = "-"
        if hasattr(fleet, 'actions') and fleet.actionIndex < len(fleet.actions):
            action, target, data = fleet.actions[fleet.actionIndex]
            if action == Const.FLACTION_REDIRECT and not self.win.vRedirects.checked:
                # ok, not interested then
                return None
            order = gdata.fleetActions[action]
            if target != Const.OID_NONE:
                targetName = getattr(client.get(target, noUpdate=1), 'name', res.getUnknownName())
                order = "%s %s" % (order, targetName)
        return order

    def _populateEta(self, fleet):
        return res.formatTime(fleet.eta) if hasattr(fleet, "eta") else "?"

    def _populateFuel(self, fleet):
        if hasattr(fleet, "storEn"):
            fuel = 100 * fleet.storEn / fleet.maxEn if fleet.maxEn > 0 else 0
        else:
            fuel = "?"
        return fuel

    def _populateOpTime(self, fleet):
        if hasattr(fleet, 'storEn') and hasattr(fleet, 'operEn'):
            turns = fleet.storEn / fleet.operEn if fleet.operEn > 0 else 100000
            rawRange = turns * fleet.speed / Rules.turnsPerDay
            _range = "%.2f" % rawRange
            opTime = res.formatTime(turns)
        else:
            _range = "?"
            opTime = "?"
        return opTime, _range

    def _populateLastUpgrade(self, fleet):
        return res.formatTime(fleet.lastUpgrade) if hasattr(fleet, "lastUpgrade") else "?"

    def show(self):
        player = client.getPlayer()
        items = []
        for fleetID in client.db.keys():
            fleet = client.get(fleetID, noUpdate=1)
            # skip non-fleets
            if not hasattr(fleet, "type") or fleet.type != Const.T_FLEET:
                continue

            fgColor = self._analyzeRelations(player.oid, fleet)
            if fgColor is None:
                # nothing to show
                continue

            order = self._populateOrder(fleet)
            if order is None:
                # nothing to show - redirect, which is not ticked
                continue

            ownerName, ownerNameTip, ownerTipTitle = self._populatePopup(player.oid, fleet)
            opTime, _range = self._populateOpTime(fleet)

            # create ListBox Item for fleet
            item = ui.Item(
                "%s %s" % (self._populateName(fleet), ownerName),
                tooltipTitle=ownerTipTitle,
                tooltip=ownerNameTip,
                tLocation=self._populateLocation(player.oid, fleet),
                tOrder=self._populateOrder(fleet),
                tMP=getattr(fleet, "combatPwr", "?"),
                tETA=self._populateEta(fleet),
                tSignature=getattr(fleet, "signature", "?"),
                tFuel=self._populateFuel(fleet),
                tOpTime=opTime,
                tRange=_range,
                tLastUpgrade=self._populateLastUpgrade(fleet),
                tFleetID=fleetID,
                foreground=fgColor)
            items.append(item)

        self.win.vFleets.items = items
        self.win.vFleets.itemsChanged()

    def onSelectFleet(self, widget, action, data):
        item = self.win.vFleets.selection[0]
        fleet = client.get(item.tFleetID, noUpdate=1)
        if hasattr(fleet, "owner") and fleet.owner == client.getPlayerID():
            # show dialog
            gdata.mainGameDlg.onSelectMapObj(None, None, item.tFleetID)
        else:
            # center fleet on map
            if hasattr(fleet, "x"):
                gdata.mainGameDlg.win.vStarMap.highlightPos = (fleet.x, fleet.y)
                gdata.mainGameDlg.win.vStarMap.setPos(fleet.x, fleet.y)
                self.hide()
                return
            self.win.setStatus(_("Cannot show location"))

    def onShowLocation(self, widget, action, data):
        item = self.win.vFleets.selection[0]
        fleet = client.get(item.tFleetID, noUpdate=1)
        # center on map
        if hasattr(fleet, "x"):
            gdata.mainGameDlg.win.vStarMap.highlightPos = (fleet.x, fleet.y)
            gdata.mainGameDlg.win.vStarMap.setPos(fleet.x, fleet.y)
            self.hide()
            return
        self.win.setStatus(_("Cannot show location"))

    def onToggleCondition(self, widget, action, data):
        self.update()

    def onClose(self, widget, action, data):
        self.hide()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            titleOnly = w == 800 and h == 600,
            movable = 0,
            title = _('Fleets Overview'),
            rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        # playets listbox
        ui.Listbox(self.win, layout = (0, 0, 40, 26), id = 'vFleets',
            columns = [
                (_('Fleet'), 'text', 5, ui.ALIGN_W),
                (_('Location'), 'tLocation', 6.5, ui.ALIGN_W),
                (_('Current order'), 'tOrder', 7, ui.ALIGN_W),
                (_('ETA'), 'tETA', 3, ui.ALIGN_E),
                (_('Fuel %'), 'tFuel', 3, ui.ALIGN_E),
                (_('Op. time'), 'tOpTime', 3, ui.ALIGN_E),
                (_('Range'), 'tRange', 3, ui.ALIGN_E),
                (_('MP'), 'tMP', 3, ui.ALIGN_E),
                (_('Sign'), 'tSignature', 2, ui.ALIGN_E),
                (_("Last upgr."), "tLastUpgrade", 3.5, ui.ALIGN_E),
            ],
            columnLabels = 1, action = 'onSelectFleet', rmbAction = "onShowLocation")

        ui.Check(self.win, layout = (0, 26, 5, 1), text = _('Mine'), id = "vMine",
            checked = 1, action = "onToggleCondition")
        ui.Check(self.win, layout = (5, 26, 5, 1), text = _('Enemy'), id = "vEnemy",
            checked = 0, action = "onToggleCondition")
        ui.Check(self.win, layout = (10, 26, 5, 1), text = _('Unfriendly'), id = "vUnfriendy",
            checked = 0, action = "onToggleCondition")
        ui.Check(self.win, layout = (15, 26, 5, 1), text = _('Neutral'), id = "vNeutral",
            checked = 0, action = "onToggleCondition")
        ui.Check(self.win, layout = (20, 26, 5, 1), text = _('Friendly'), id = "vFriendly",
            checked = 0, action = "onToggleCondition")
        ui.Check(self.win, layout = (25, 26, 5, 1), text = _('Allied'), id = "vAllied",
            checked = 0, action = "onToggleCondition")
        ui.Check(self.win, layout = (34, 26, 6, 1), text = _('Show redirects'), id = "vRedirects",
            checked = 0, action = "onToggleCondition")
        # status bar + submit/cancel
        ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
        ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
        #self.win.statusBar = self.win.vStatusBar

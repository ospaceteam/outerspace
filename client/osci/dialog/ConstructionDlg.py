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

import pygame

import pygameui as ui

from ige import GameException
from ige.ospace import ShipUtils, Rules
import ige.ospace.Const as Const

from osci import gdata, res, client, sequip
from osci.StarMapWidget import StarMapWidget

from ConstrSelTechDlg import ConstrSelTechDlg
from ConstrUpgradeDlg import ConstrUpgradeDlg
from ConfirmDlg import ConfirmDlg

class ConstructionDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()
        self.selTechDlg = ConstrSelTechDlg(app)
        self.upgradeDlg = ConstrUpgradeDlg(app)
        self.confirmDlg = ConfirmDlg(app)
        self.selectedDesignID = None
        self.highlightedDesignID = None
        self.editMode = False

    def display(self):
        self.itemCache = {}
        self.hullID = Const.OID_NONE
        self.ctrlID = Const.OID_NONE
        self.eqIDs = {}
        self.selectedEqID = None
        self.update()
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
        self.showDesigns()
        self.showDetails()

    def _getNumberInFleets(self, designID):
        count = 0
        for fleetID in client.getPlayer().fleets:
            fleet = client.get(fleetID)
            count += len([designID for tmpDesignID, hp, shieldHP, exp in fleet.ships if tmpDesignID == designID])
        return count

    def _getNumberInBuild(self, designID):
        count = 0
        # planet queues
        for planetID in client.db.keys():
            planet = client.get(planetID, noUpdate=1)
            # skip non-planets
            try:
                count += sum((task.quantity for task in planet.prodQueue if (task.isShip and task.techID == designID)))
            except AttributeError:
                # this is either not a planet, or it's not planet with prodqueue useful for us
                continue
        # global queues
        for globalQueue in client.getPlayer().prodQueues:
            count += sum((task.quantity for task in globalQueue if (task.isShip and task.techID == designID)))
        return count

    def showDesigns(self):
        player = client.getPlayer()
        # check if highlighted ship design exists
        if self.highlightedDesignID not in player.shipDesigns:
            self.highlightedDesignID = None
        # designs
        highlighted = None
        items = []
        for designID in player.shipDesigns:
            spec = player.shipDesigns[designID]

            countInService = self._getNumberInFleets(designID)
            countInBuild = self._getNumberInBuild(designID)

            # ui list item
            hullTech = client.getFullTechInfo(spec.hullID)
            item = ui.Item(spec.name, tDesignID=designID,
                           tClass="%s/%s%d" % (_(gdata.shipClasses[spec.combatClass][:1].upper()),
                                               _("TL"),
                                               hullTech.level),
                           tNumber=countInService,
                           tInBuild=countInBuild)
            if spec.upgradeTo:
                item.foreground = gdata.sevColors[gdata.NONE]
            if designID == self.highlightedDesignID:
                highlighted = item
            items.append(item)
        self.win.vDesigns.items = items
        self.win.vDesigns.itemsChanged()
        self.win.vDesigns.highlightItem(highlighted, 0)

    def _setDetailButtons(self, player):
        if self.selectedDesignID:
            self.win.vScrap.enabled = 1
            if player.shipDesigns[self.selectedDesignID].upgradeTo == 0:
                self.win.vUpgrade.enabled = 1
                self.win.vUpgrade.text = _("Upgrade")
            else:
                self.win.vUpgrade.enabled = 1
                self.win.vUpgrade.text = _("Cancel Upgrd")

        if self.editMode:
            self.win.vName.enabled = 1
            self.win.vEnginesButton.enabled = 1
            self.win.vWeaponsButton.enabled = 1
            self.win.vEquipmentButton.enabled = 1
            self.win.vUpgrade.enabled = 0
            self.win.vUpgrade.text = _("Upgrade")
            self.win.vScrap.enabled = 0
        else:
            # view only mode?
            # let's reset highlights in design listboxes
            self.selectedEqID = None
            self.win.vName.enabled = 0
            self.win.vEngines.unselectAll()
            self.win.vWeapons.unselectAll()
            self.win.vEquipment.unselectAll()

            self.win.vDuplDesign.enabled = 1
            self.win.vConstruct.enabled = 0
            self.win.vEnginesButton.enabled = 0
            self.win.vWeaponsButton.enabled = 0
            self.win.vEquipmentButton.enabled = 0
            if not self.selectedDesignID:
                self.win.vScrap.enabled = 0
                self.win.vUpgrade.enabled = 0

    def _designRepresentation(self, player):
        if self.highlightedDesignID is None:
            if self.editMode:
                if self.ctrlID:
                    eqIDs = {self.ctrlID: 1}
                else:
                    eqIDs = {}
                for eqID in self.eqIDs:
                    eqIDs[eqID] = self.eqIDs[eqID]
                improvements = []
            else:
                self.hullID = self.ctrlID = None
                self.win.vName.text = ""
                self.eqIDs = {}
                eqIDs = {}
                improvements = []
        else:
            spec = player.shipDesigns[self.highlightedDesignID]
            self.hullID = spec.hullID
            eqIDs = spec.eqIDs
            improvements = spec.improvements
            self.win.vName.text = spec.name
            self.win.vHull.text = client.getTechInfo(self.hullID).name
            self.eqIDs = {}
            for eqID in eqIDs:
                tech = client.getTechInfo(eqID)
                if tech.subtype == "seq_ctrl":
                    self.ctrlID = eqID
                    self.win.vCtrl.text = tech.name
                else:
                    self.eqIDs[eqID] = eqIDs[eqID]
        try:
            result = ShipUtils.makeShipFullSpec(player, None, self.hullID, eqIDs, improvements)
            if self.editMode:
                self.win.vConstruct.enabled = 1
        except GameException, e:
            self.win.setStatus(e.args[0])
            self.win.vConstruct.enabled = 0
            try:
                result = ShipUtils.makeShipFullSpec(player, None, self.hullID, eqIDs,
                                                    improvements, raiseExs=False)
            except GameException:
                result = None
        else:
            self.win.setStatus(_("Ready."))
        return result

    def _detailEquipmentLists(self):
        # design info
        if self.hullID:
            tech = client.getTechInfo(self.hullID)
            self.win.vHull.text = tech.name  # TODO _(tech.name)
        elif self.editMode:
            self.win.vHull.text = _("[Click to select]")
        else:
            self.win.vHull.text = ""
        if self.ctrlID:
            tech = client.getTechInfo(self.ctrlID)
            self.win.vCtrl.text = tech.name  # TODO _(tech.name)
        elif self.editMode:
            self.win.vCtrl.text = _("[Click to select]")
        else:
            self.win.vCtrl.text = ""
        # equipments
        engines = []
        weapons = []
        equipment = []
        selected = None
        selected_type = None
        for eqID in self.eqIDs:
            tech = client.getTechInfo(eqID)
            short = sequip.getShortDescr(eqID)
            _long = sequip.getLongDescr(eqID)
            # cache has been introduced to let items preserve highlight information
            if eqID in self.itemCache:
                item = self.itemCache[eqID]
                item.tNumber = self.eqIDs[eqID]
            else:
                item = ui.Item(tech.name,
                               techID=eqID,
                               tNumber=self.eqIDs[eqID],
                               tData=short,
                               tooltipTitle=_("Details"),
                               tooltip=_long,
                               statustip=_long)
                self.itemCache[eqID] = item
            if eqID == self.selectedEqID:
                selected = item
                selected_type = tech.subtype
            if tech.subtype == "seq_eng":
                engines.append(item)
            elif tech.subtype == "seq_wpn":
                weapons.append(item)
            elif tech.subtype in ["seq_mod", "seq_struct"]:
                equipment.append(item)
        self.win.vEngines.items = engines
        self.win.vEngines.itemsChanged()
        if selected_type == "seq_eng":
            self.win.vEngines.selectItem(selected)
        else:
            self.win.vEngines.selectItem(None)
        self.win.vWeapons.items = weapons
        self.win.vWeapons.itemsChanged()
        if selected_type == "seq_wpn":
            self.win.vWeapons.selectItem(selected)
        else:
            self.win.vWeapons.selectItem(None)
        self.win.vEquipment.items = equipment
        self.win.vEquipment.itemsChanged()
        if selected_type == "seq_mod":
            self.win.vEquipment.selectItem(selected)
        else:
            self.win.vEquipment.selectItem(None)

    def _detailComputedAttributes(self, player, result):
        if result:
            hull = client.getTechInfo(result.hullID)
            self.win.vAClass.text = _(gdata.shipClasses[result.combatClass])
            self.win.vASignature.text = _("%d") % result.signature
            if result.speed == result.battleSpeed:
                self.win.vSpeed.text = _("Speed")
                self.win.vASpeed.text = _("%.2f") % result.speed
            else:
                self.win.vSpeed.text = _("Spd FTL (STL)")
                self.win.vASpeed.text = _("%.2f (%.2f)") % (result.speed, result.battleSpeed)
            self.win.vAHP.text = _("%d - %d") % (result.maxHP, result.shieldHP) if result.shieldHP > 0 else _("%d") % result.maxHP
            self.win.vAAttack.text = _("%d") % result.combatAtt
            self.win.vADefence.text = _("%d / %d") % (result.combatDef, result.missileDef)
            self.win.vAPayload.text = _("%d") % (hull.maxWeight - result.weight) if getattr(hull, "maxWeight", None) else _("N/A")
            self.win.vASlots.text = _("%d") % (hull.slots - result.slots) if hasattr(hull, "slots") else _("N/A")
            self.win.vATanks.text = _("%d") % result.storEn
            if result.speed > 0 and result.operEn > 0:
                support = result.storEn / result.operEn
                self.win.vARange.text = _("%.2f") % (support * result.speed / Rules.turnsPerDay)
            else:
                self.win.vARange.text = _("None")
            self.win.vACCPts.text = _("%d") % result.buildProd
            self.win.vACombatPwr.text = _("%d") % result.combatPwr
            if self.highlightedDesignID and player.shipDesigns[self.highlightedDesignID].upgradeTo:
                self.win.vAUpgrade.text = player.shipDesigns[player.shipDesigns[self.highlightedDesignID].upgradeTo].name
                self.win.vAUpgrade.font = "normal-italic"
            else:
                self.win.vAUpgrade.text = _("N/A")
                self.win.vAUpgrade.font = "normal"
        else:
            self.win.vAClass.text = _("N/A")
            self.win.vASignature.text = _("N/A")
            self.win.vASpeed.text = _("N/A")
            self.win.vAHP.text = _("N/A")
            self.win.vAAttack.text = _("N/A")
            self.win.vADefence.text = _("N/A")
            self.win.vAPayload.text = _("N/A")
            self.win.vASlots.text = _("N/A")
            self.win.vATanks.text = _("N/A")
            self.win.vARange.text = _("N/A")
            self.win.vACCPts.text = _("N/A")
            self.win.vACombatPwr.text = _("N/A")
            self.win.vAUpgrade.text = _("N/A")

    def showDetails(self):
        player = client.getPlayer()
        self._setDetailButtons(player)
        result = self._designRepresentation(player)
        self._detailEquipmentLists()
        self._detailComputedAttributes(player, result)

    def onConstruct(self, widget, action, data):
        name = self.win.vName.text
        if not name:
            self.win.setStatus(_("Enter name of the design."))
            return
        # compute
        player = client.getPlayer()
        if self.ctrlID:
            eqIDs = {self.ctrlID: 1}
        else:
            eqIDs = {}
        for eqID in self.eqIDs:
            if self.eqIDs[eqID]:
                eqIDs[eqID] = self.eqIDs[eqID]
        try:
            self.win.setStatus(_("Executing ADD SHIP DESIGN command..."))
            player = client.getPlayer()
            player.shipDesigns, self.selectedDesignID = \
                client.cmdProxy.addShipDesign(player.oid, name, self.hullID, eqIDs)
            self.win.vDuplDesign.enabled = 1
            self.win.setStatus(_('Command has been executed.'))
        except GameException, e:
            self.win.setStatus(_(e.args[0]))
            return
        self.editMode = False
        self.update()

    def onClose(self, widget, action, data):
        self.editMode = False
        self.hide()

    def onSelectHull(self, widget, action, data):
        if self.editMode:
            self.selTechDlg.display('isShipHull', [], self.onHullSelected, self.hullID, self.hullID)

    def onHullSelected(self, hullID):
        self.hullID = hullID
        self.showDetails()

    def onSelectCtrl(self, widget, action, data):
        if self.editMode:
            self.selTechDlg.display('isShipEquip', ["seq_ctrl"], self.onCtrlSelected, self.ctrlID, self.hullID)

    def onCtrlSelected(self, ctrlID):
        self.ctrlID = ctrlID
        self.showDetails()

    def onAddEngine(self, widget, action, data):
        self.selTechDlg.display('isShipEquip', ["seq_eng"], self.onEqSelected, hullID=self.hullID)

    def onAddWeapon(self, widget, action, data):
        self.selTechDlg.display('isShipEquip', ["seq_wpn"], self.onEqSelected, hullID=self.hullID)

    def onAddEquipment(self, widget, action, data):
        self.selTechDlg.display('isShipEquip', ["seq_mod", "seq_struct"], self.onEqSelected, hullID=self.hullID)

    def onEqSelected(self, eqID):
        self.eqIDs[eqID] = self.eqIDs.get(eqID, 0) + 1
        self.showDetails()

    def onSelectDesign(self, widget, action, data):
        item = self.win.vDesigns.selection[0]
        self.editMode = False
        self.selectedDesignID = self.highlightedDesignID = item.tDesignID
        self.showDetails()

    def onHighlightDesign(self, widget, action, data):
        if self.editMode:
            return
        if data is None and not self.win.vDesigns.selection:
            # unhighlight into non-selection
            self.highlightedDesignID = None
            self.win.vDuplDesign.enabled = 0
            self.showDetails()
            return
        if data is not None:
            item = self.win.vDesigns.highlight
        elif self.win.vDesigns.selection:
            item = self.win.vDesigns.selection[0]
        self.highlightedDesignID = item.tDesignID
        self.showDetails()

    def onNewDesign(self, widget, action, data):
        self.selectedDesignID = self.highlightedDesignID = None
        self.editMode = True
        self.win.vDesigns.selectItem(None)
        self.hullID = Const.OID_NONE
        self.ctrlID = Const.OID_NONE
        self.eqIDs = {}
        self.win.vName.text = _(" ")
        self.win.vDuplDesign.enabled = 0
        self.update()

    def onDuplDesign(self, widget, action, data):
        self.selectedDesignID = None
        self.highlightedDesignID = None
        self.editMode = True
        self.win.vDesigns.selectItem(None)
        self.win.vName.text = _(" ")
        self.win.vDuplDesign.enabled = 0
        self.update()

    def _getSelectedWidget(self):
        widgets = []
        if self.win.vEngines.selection:
            widgets.append(self.win.vEngines)
        if self.win.vWeapons.selection:
            widgets.append(self.win.vWeapons)
        if self.win.vEquipment.selection:
            widgets.append(self.win.vEquipment)
        return widgets

    def onEqSelectedInListInc(self, widget, action, data):
        if self.editMode:
            self._onEqSelectedInList(widget)
            if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self._onChangeEquipmentQty(1)
            else:
                self._onChangeEquipmentQty(5)

    def onEqSelectedInListDec(self, widget, action, data):
        if self.editMode:
            self._onEqSelectedInList(widget)
            if not pygame.key.get_mods() & pygame.KMOD_SHIFT:
                self._onChangeEquipmentQty(-1)
            else:
                self._onChangeEquipmentQty(-5)

    def _onEqSelectedInList(self, widget):
        for old_select_widget in self._getSelectedWidget():
            if old_select_widget is not widget:
                old_select_widget.unselectAll()
        self.selectedEqID = widget.selection[0].techID

    def _onChangeEquipmentQty(self, delta):
        for widget in self._getSelectedWidget():
            item = widget.selection[0]
            eqID = item.techID
            self.eqIDs[eqID] = max(self.eqIDs.get(eqID, 0) + delta, 0)
            self.showDetails()

    def onRemoveEquipment(self, widget, action, data):
        if self.win.vEquipment.selection:
            item = self.win.vEquipment.selection[0]
            eqID = item.techID
            del self.eqIDs[eqID]
            self.showDetails()

    def onScrap(self, widget, action, data):
        # count number of ships using this design
        count = 0
        for fleetID in client.getPlayer().fleets:
            fleet = client.get(fleetID)
            for designID, hp, shieldHP, exp in fleet.ships:
                if designID == self.selectedDesignID:
                    count += 1
        self.confirmDlg.display(_('Deletion of this design dismantle %d ship(s). Are you sure to scrap it?') % count,
                                _('Yes'),
                                _('No'),
                                confirmAction=self.onScrapConfirmed,
                                agreementNeeded=count != 0)

    def onScrapConfirmed(self):
        self.win.vDuplDesign.enabled = 0
        try:
            self.win.setStatus(_("Executing SCRAP SHIP DESIGN command..."))
            player = client.getPlayer()
            oldFleets = player.fleets
            player.shipDesigns, player.fleets, player.stratRes, player.prodQueues = \
                client.cmdProxy.scrapShipDesign(player.oid, self.selectedDesignID)
            self.selectedDesignID = None
            self.win.setStatus(_('Command has been executed.'))
        except GameException, e:
            self.win.setStatus(_(e.args[0]))
            return
        # reread information about fleets and planets
        oldFleets.extend(player.planets)
        client.updateIDs(oldFleets)

        gdata.mainGameDlg.update()
        self.update()

    def onUpgrade(self, widget, action, data):
        player = client.getPlayer()
        if player.shipDesigns[self.selectedDesignID].upgradeTo == 0:
            # upgrade
            self.upgradeDlg.display(self.selectedDesignID, self)
        else:
            # cancel upgrade
            try:
                self.win.setStatus(_("Executing CANCEL UPGRADE SHIP DESIGN command..."))
                player.shipDesigns = \
                    client.cmdProxy.cancelUpgradeShipDesign(player.oid, self.selectedDesignID)
                self.win.setStatus(_('Command has been executed.'))
            except GameException, e:
                self.win.setStatus(_(e.args[0]))
                return
            self.update()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             titleOnly=w == 800 and h == 600,
                             movable=0,
                             title=_('Construction Centre'),
                             rect=ui.Rect((w - 800 - 4 * (w != 800)) / 2,
                                          (h - 600 - 4 * (h != 600)) / 2,
                                          800 + 4 * (w != 800),
                                          580 + 4 * (h != 600)),
                             layoutManager=ui.SimpleGridLM())
        self.win.subscribeAction('*', self)
        # player listing
        ui.Title(self.win, layout=(0, 0, 15, 1), text=_('Ship Designs'),
                 font='normal-bold', align=ui.ALIGN_W)
        ui.Listbox(self.win, layout=(0, 1, 15, 25), id='vDesigns',
                   columns=((_('#'), 'tNumber', 2, ui.ALIGN_E),
                            (_('B'), 'tInBuild', 2, ui.ALIGN_E),
                            (_('Name'), 'text', 8, ui.ALIGN_W),
                            (_('Class'), 'tClass', 2, ui.ALIGN_W)),
                   columnLabels=1,
                   action="onSelectDesign",
                   hoverAction="onHighlightDesign")
        ui.Button(self.win, layout=(0, 26, 7, 1), text=_("New design"),
                  action="onNewDesign")
        ui.Button(self.win, layout=(7, 26, 7, 1), text=_("Dupl. design"),
                  action="onDuplDesign", enabled=0, id="vDuplDesign")
        # current design
        ui.Title(self.win, layout=(15, 0, 25, 1), text=_('Design'),
                 font='normal-bold', align=ui.ALIGN_W)
        # info
        ui.Label(self.win, layout=(15, 1, 5, 1), text=_("Name"),
                 align=ui.ALIGN_W)
        ui.Entry(self.win, layout=(20, 1, 10, 1), id="vName",
                 align=ui.ALIGN_E)
        ui.Label(self.win, layout=(15, 2, 5, 1), text=_("Hull type"),
                 align=ui.ALIGN_W)
        ui.ActiveLabel(self.win, layout=(20, 2, 10, 1), id="vHull",
                       align=ui.ALIGN_E, action="onSelectHull")
        ui.Label(self.win, layout=(15, 3, 5, 1), text=_("Control unit"),
                 align=ui.ALIGN_W)
        ui.ActiveLabel(self.win, layout=(20, 3, 10, 1), id="vCtrl",
                       align=ui.ALIGN_E, action="onSelectCtrl")
        ui.Button(self.win, layout=(15, 4, 6, 1), text=_('Engines'),
                  id="vEnginesButton", font='normal-bold', action="onAddEngine")
        ui.Title(self.win, layout=(21, 4, 19, 1),)
        ui.Listbox(self.win, layout=(15, 5, 25, 3), id='vEngines',
                   columns=((_('#'), 'tNumber', 2, ui.ALIGN_E),
                            (_('Name'), 'text', 8, ui.ALIGN_W),
                            (_('Data'), 'tData', 14, ui.ALIGN_W)),
                   columnLabels=0,
                   action="onEqSelectedInListInc",
                   rmbAction="onEqSelectedInListDec")
        ui.Button(self.win, layout=(15, 8, 6, 1), text=_('Weapons'),
                  id="vWeaponsButton", font='normal-bold', action="onAddWeapon")
        ui.Title(self.win, layout=(21, 8, 19, 1),)
        ui.Listbox(self.win, layout=(15, 9, 25, 4), id='vWeapons',
                   columns=((_('#'), 'tNumber', 2, ui.ALIGN_E),
                            (_('Name'), 'text', 8, ui.ALIGN_W),
                            (_('Data'), 'tData', 14, ui.ALIGN_W)),
                   columnLabels=0,
                   action="onEqSelectedInListInc",
                   rmbAction="onEqSelectedInListDec")
        ui.Button(self.win, layout=(15, 13, 6, 1), text=_('Equipment'),
                  id="vEquipmentButton", font='normal-bold', action="onAddEquipment")
        ui.Title(self.win, layout=(21, 13, 19, 1),)
        ui.Listbox(self.win, layout=(15, 14, 25, 5), id='vEquipment',
                   columns=((_('#'), 'tNumber', 2, ui.ALIGN_E),
                            (_('Name'), 'text', 8, ui.ALIGN_W),
                            (_('Data'), 'tData', 14, ui.ALIGN_W)),
                   columnLabels=0,
                   action="onEqSelectedInListInc",
                   rmbAction="onEqSelectedInListDec")

        ui.Button(self.win, layout=(15, 19, 6, 1), text=_("Upgrade to"),
                  id="vUpgrade", font='normal-bold', action="onUpgrade")
        ui.Label(self.win, layout=(21, 19, 6, 1), id="vAUpgrade", align=ui.ALIGN_E)
        ui.Title(self.win, layout=(27.5, 19, 12.5, 1))

        # ship's attrs
        ui.Label(self.win, layout=(30.5, 1, 4.5, 1), text=_("Class"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(35, 1, 4.75, 1), id="vAClass", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(30.5, 2, 6.5, 1), text=_("Free slots"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(37, 2, 2.75, 1), id="vASlots", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(30.5, 3, 6.5, 1), text=_("Unused payload"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(37, 3, 2.75, 1), id="vAPayload", align=ui.ALIGN_E)

        ui.Label(self.win, layout=(17, 21, 4, 1), text=_("HP"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(21, 21, 5, 1), id="vAHP", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(17, 22, 4, 1), text=_("Base attack"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(21, 22, 5, 1), id="vAAttack", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(17, 23, 3, 1), text=_("Base defence"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(20, 23, 6, 1), id="vADefence", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(17, 24, 5, 1), text=_("Military power"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(22, 24, 4, 1), id="vACombatPwr", align=ui.ALIGN_E)

        ui.Label(self.win, layout=(28, 20, 5, 1), text=_("Signature"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(33, 20, 5, 1), id="vASignature", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(28, 21, 5, 1), id="vSpeed", text=_("Speed"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(34, 21, 5, 1), id="vASpeed", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(28, 22, 5, 1), text=_("Tanks"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(33, 22, 5, 1), id="vATanks", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(28, 23, 5, 1), text=_("Max. range"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(33, 23, 5, 1), id="vARange", align=ui.ALIGN_E)
        ui.Label(self.win, layout=(28, 24, 5, 1), text=_("Constr. pts"), align=ui.ALIGN_W)
        ui.Label(self.win, layout=(33, 24, 5, 1), font='normal-bold', id="vACCPts", align=ui.ALIGN_E)

        # actions
        ui.Title(self.win, layout=(15, 25, 25, 1))
        ui.Button(self.win, layout=(15, 26, 5, 1), text=_("Scrap"),
                  id="vScrap", action="onScrap")
        ui.Button(self.win, layout=(35, 26, 5, 1), text=_("Construct"),
                  id="vConstruct", action="onConstruct", enabled=0)
        # status bar + submit/cancel
        ui.TitleButton(self.win, layout=(35, 27, 5, 1), text=_('Close'), action='onClose')
        ui.Title(self.win, id='vStatusBar', layout=(0, 27, 35, 1), align=ui.ALIGN_W)

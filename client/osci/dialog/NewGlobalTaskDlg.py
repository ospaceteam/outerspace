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

import pygameui as ui

from ige import GameException
from ige.ospace import Rules
import ige.ospace.Const as Const

from osci import gdata, client, res
from TechInfoDlg import TechInfoDlg
from ConstructionDlg import ConstructionDlg
import Utils

class NewGlobalTaskDlg:

    def __init__(self, app):
        self.app = app
        self.showShips = 1
        self.showOther = 0
        self.techID = 0
        self.showLevels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 99]
        self.techInfoDlg = TechInfoDlg(app)
        self.constructionDlg = ConstructionDlg(app)
        self.createUI()
        self.win.setTagAttr('ship', 'visible', 1)
        # set default sorting for technologies
        self.win.vTechs.setSort("text")

    def display(self, caller, queue, structToDemolish = Const.OID_NONE):
        if gdata.config.defaults.reportfinalization != None:
            val = gdata.config.defaults.reportfinalization
            self.win.vReportFin.checked = val == 'yes'

        self.caller = caller
        self.playerID = client.getPlayerID()
        self.maxTechLevel = 0
        self.quantity = 1
        self.queue = queue
        self.showTechs()
        self.win.show()
        gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)
        self.win.hide()

    def update(self):
        if self.win.visible:
            if self.showShips:
                self.win.vInfo.enabled = Utils.enableConstruction(client)
            self.showTechs()

    def _processProjects(self):
        items = []
        for techID in client.getPlayer().techs.keys():
            tech = client.getTechInfo(techID)

            if not tech.isProject or tech.globalDisabled or tech.level not in self.showLevels:
                continue

            item = ui.Item(tech.name,
                           tLevel=tech.level,
                           tProd=tech.buildProd,
                           techID=techID,
                           tIsShip=0)
            items.append(item)
        return items

    def _filterShipSize(self, tech):
        return ((self.win.vSmall.checked and tech.combatClass == 0)
                or (self.win.vMedium.checked and tech.combatClass == 1)
                or (self.win.vLarge.checked and tech.combatClass == 2))

    def _filterShipMilitary(self, tech):
        return ((self.win.vMilShip.checked and tech.isMilitary)
                or (self.win.vCivShip.checked and not tech.isMilitary))

    def _processShips(self):
        items = []

        player = client.getPlayer()
        for designID in player.shipDesigns.keys():
            tech = player.shipDesigns[designID]
            if not self._filterShipSize(tech) or not self._filterShipMilitary(tech) or tech.level not in self.showLevels:
                continue
            if tech.upgradeTo != Const.OID_NONE:
                # skip ships that are set to upgrade
                continue

            item = ui.Item(tech.name,
                           tLevel=tech.level,
                           tProd=tech.buildProd,
                           techID=designID,
                           tIsShip=1)
            items.append(item)
        return items

    def showTechs(self):
        # techs
        items = []
        select = None

        if self.showOther:
            items += self._processProjects()
        if self.showShips:
            items += self._processShips()

        # special handling for ships
        # sort it by level and then by name
        items.sort(key=lambda a: (100 - a.tLevel, a.text))
        self.win.vTechs.items = items
        self.win.vTechs.itemsChanged()
        for item in items:
            self.maxTechLevel = max(self.maxTechLevel, item.tLevel)
            if item.techID == self.techID:
                self.win.vTechs.selectItem(item)
        # filter
        for i in range(1, 10):
            widget = getattr(self.win, 'vLevel%d' % i)
            if i in self.showLevels and i <= self.maxTechLevel:
                widget.visible = 1
                widget.pressed = 1
            elif i not in self.showLevels and i <= self.maxTechLevel:
                widget.visible = 1
                widget.pressed = 0
            else:
                widget.visible = 0
        self.win.vShipsToggle.pressed = self.showShips
        self.win.vOtherToggle.pressed = self.showOther
        # quantity
        self.win.vQuantity.text = str(self.quantity)

    def showSlots(self):
        # techs
        items = []
        techs = {}
        if self.showStructures:
            player = client.getPlayer()
            target = client.get(self.targetID, noUpdate=1)
            if hasattr(target, 'slots') and target.owner == player.oid:
                if len(target.slots) < target.plSlots:
                    item = ui.Item(_("Free slot"), techID=0)
                    items.append(item)
                for struct in target.slots:
                    if not struct[Const.STRUCT_IDX_TECHID] in techs:
                        techs[struct[Const.STRUCT_IDX_TECHID]] = 1
                    else:
                        techs[struct[Const.STRUCT_IDX_TECHID]] += 1
                for tech in techs.keys():
                    techInfo = client.getTechInfo(tech)
                    item = ui.Item("%s (%d)" % (techInfo.name, techs[tech]), techID=tech)
                    items.append(item)

        self.win.vTSlots.items = items
        self.win.vTSlots.itemsChanged()
        self.structToDemolish = Const.OID_NONE


    def onSelectTech(self, widget, action, data):
        self.techID = data.techID

    def onToggleLevel(self, widget, action, data):
        i = widget.data
        if i in self.showLevels:
            self.showLevels.remove(i)
        else:
            self.showLevels.append(i)
        self.update()

    def onCancel(self, widget, action, data):
        self.hide()

    def onConstruct(self, widget, action, data):
        if not self.techID:
            self.win.setStatus(_('Select technology to construct.'))
            return
        try:
            self.quantity = int(self.win.vQuantity.text)
        except ValueError:
            self.win.setStatus(_('Specify quantity (1, 2, 3, ...).'))
            return
        try:
            self.win.setStatus(_('Executing START CONSTRUCTION command...'))
            player = client.getPlayer()

            player.prodQueues[self.queue], player.stratRes = client.cmdProxy.startGlobalConstruction(self.playerID, self.techID, self.quantity, self.techID < 1000, self.win.vReportFin.checked, self.queue)
            self.win.setStatus(_('Command has been executed.'))
        except GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.hide()
        self.caller.update()

    def onToggleShips(self, widget, action, data):
        self.quantity = int(self.win.vQuantity.text)
        self.showStructures = 0
        self.showShips = 1
        self.showOther = 0
        self.win.setTagAttr('struct', 'visible', 0)
        self.win.setTagAttr('ship', 'visible', 1)
        self.update()

    def onToggleOther(self, widget, action, data):
        self.quantity = int(self.win.vQuantity.text)
        self.showStructures = 0
        self.showShips = 0
        self.showOther = 1
        self.win.setTagAttr('struct', 'visible', 0)
        self.win.setTagAttr('ship', 'visible', 0)
        self.update()

    def onInfo(self, widget, action, data):
        if len(self.win.vTechs.selection) == 0:
            return
        task = self.win.vTechs.selection[0]
        if not task.tIsShip:
            self.techInfoDlg.display(task.techID)
        else:
            self.constructionDlg.selectedDesignID = task.techID;
            self.constructionDlg.display()

    def onFilter(self, widget, action, data):
        self.update()

    def createUI(self):
        w, h = gdata.scrnSize
        cols = 20
        rows = 25
        dlgWidth = cols * 20 + 4
        dlgHeight = rows * 20 + 4
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             movable=0,
                             title=_('Select new global task'),
                             rect=ui.Rect((w - dlgWidth) / 2, (h - dlgHeight) / 2, dlgWidth, dlgHeight),
                             layoutManager=ui.SimpleGridLM(),
                             tabChange=True)
        self.win.subscribeAction('*', self)
        ui.Title(self.win, layout=(0, 0, 20, 1), text=_('Technology'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Listbox(self.win, layout=(0, 1, 20, 19), id='vTechs',
                   columns=((_('Name'), 'text', 14, ui.ALIGN_W), (_('Lvl'), 'tLevel', 2, ui.ALIGN_E),
                   (_('Constr'), 'tProd', 3, ui.ALIGN_E)),
                   columnLabels=1, action='onSelectTech')
        # filter
        ui.Button(self.win, layout=(0, 20, 3, 1), text=_('Ships'), toggle=1,
                  id='vShipsToggle', action='onToggleShips')
        ui.Button(self.win, layout=(3, 20, 3, 1), text=_('Misc'), toggle=1,
                  id='vOtherToggle', action='onToggleOther')
        ui.Button(self.win, layout=(6, 20, 1, 1), text=_('1'), id='vLevel1',
                  toggle=1, action='onToggleLevel', data=1)
        ui.Button(self.win, layout=(7, 20, 1, 1), text=_('2'), id='vLevel2',
                  toggle=1, action='onToggleLevel', data=2)
        ui.Button(self.win, layout=(8, 20, 1, 1), text=_('3'), id='vLevel3',
                  toggle=1, action='onToggleLevel', data=3)
        ui.Button(self.win, layout=(9, 20, 1, 1), text=_('4'), id='vLevel4',
                  toggle=1, action='onToggleLevel', data=4)
        ui.Button(self.win, layout=(10, 20, 1, 1), text=_('5'), id='vLevel5',
                  toggle=1, action='onToggleLevel', data=5)
        ui.Button(self.win, layout=(11, 20, 1, 1), text=_('6'), id='vLevel6',
                  toggle=1, action='onToggleLevel', data=6)
        ui.Button(self.win, layout=(12, 20, 1, 1), text=_('7'), id='vLevel7',
                  toggle=1, action='onToggleLevel', data=7)
        ui.Button(self.win, layout=(13, 20, 1, 1), text=_('8'), id='vLevel8',
                  toggle=1, action='onToggleLevel', data=8)
        ui.Button(self.win, layout=(14, 20, 1, 1), text=_('9'), id='vLevel9',
                  toggle=1, action='onToggleLevel', data=9)
        ui.Button(self.win, layout=(15, 20, 4, 1), text=_('Info'), action='onInfo',
                  id='vInfo')
        # ship types
        ui.Check(self.win, layout=(0, 21, 4, 1), text=_('Small'), tags=['ship'],
                 id='vSmall', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(4, 21, 4, 1), text=_('Medium'), tags=['ship'],
                 id='vMedium', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(8, 21, 4, 1), text=_('Large'), tags=['ship'],
                 id='vLarge', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(12, 21, 4, 1), text=_('Civilian'), tags=['ship'],
                 id='vCivShip', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(16, 21, 4, 1), text=_('Military'), tags=['ship'],
                 id='vMilShip', checked=1, align=ui.ALIGN_W, action='onFilter')
        # build
        ui.Label(self.win, layout=(0, 22, 5, 1), text=_('Quantity'), align=ui.ALIGN_W)
        ui.Entry(self.win, layout=(5, 22, 6, 1), id='vQuantity', align=ui.ALIGN_E, orderNo=1)
        ui.Check(self.win, layout=(13, 22, 7, 1), id='vReportFin', text=_('Report finalization'))
        ui.Title(self.win, layout=(0, 23, 10, 1), id='vStatusBar', align=ui.ALIGN_W)
        ui.TitleButton(self.win, layout=(10, 23, 5, 1), text=_('Cancel'), action='onCancel')
        ui.TitleButton(self.win, layout=(15, 23, 5, 1), text=_('Construct'), action='onConstruct')

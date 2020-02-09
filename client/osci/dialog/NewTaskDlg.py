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
from ConfirmDlg import ConfirmDlg
import Utils


class NewTaskDlg:

    def __init__(self, app):
        self.app = app
        self.showStructures = 1
        self.showShips = 0
        self.showOther = 0
        self.techID = 0
        self.showLevels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 99]
        self.techInfoDlg = TechInfoDlg(app)
        self.constructionDlg = ConstructionDlg(app)
        self.confirmDlg = ConfirmDlg(app)
        self.createUI()
        self.win.setTagAttr('struct', 'visible', 1)
        self.win.setTagAttr('ship', 'visible', 0)
        # set default sorting for technologies
        self.win.vTechs.setSort("text")

    def display(self, caller, prodProd, structToDemolish=Const.OID_NONE):
        if gdata.config.defaults.reportfinalization != None:
            val = gdata.config.defaults.reportfinalization
            self.win.vReportFin.checked = val == 'yes'

        self.caller = caller
        self.systemID = caller.systemID
        self.planetID = caller.planetID
        self.playerID = client.getPlayerID()
        self.targetID = caller.planetID
        self.maxTechLevel = 0
        self.quantity = 1
        self.govTransferConfirm = False
        self.govTransferData = None
        self.prodProd = prodProd
        self.structToDemolish = structToDemolish
        self.showTechs()
        self.showSlots()
        self.win.show()
        gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)
        self.win.hide()

    def update(self):
        if self.win.visible:
            self.quantity = int(self.win.vQuantity.text)
            if self.showShips:
                self.win.vInfo.enabled = Utils.enableConstruction(client)
            self.showTechs()
            self.showSlots()

    def _processNonShips(self, tech):
        if self.prodProd > 0:
            etc = math.ceil(float(tech.buildProd) / self.prodProd)
            if self.targetID != self.planetID:
                etc *= Rules.buildOnAnotherPlanetMod
            etc = res.formatTime(etc)
        else:
            etc = _("N/A")

        item = ui.Item(tech.name,
                       tLevel=tech.level,
                       tProd=tech.buildProd,
                       techID=tech.id,
                       tIsShip=0,
                       tETC=etc)
        self.maxTechLevel = max(self.maxTechLevel, tech.level)

        return item

    def _filterStructure(self, tech):
        return ((self.win.vMilitary.checked and tech.isMilitary)
                or (self.win.vBioProduction.checked and (getattr(tech, "prodBio", 0) or getattr(tech, "prodEnv", 0) > 0))
                or (self.win.vEnProduction.checked and getattr(tech, "prodEn", 0))
                or (self.win.vCPProduction.checked and getattr(tech, "prodProd", 0))
                or (self.win.vRPProduction.checked and getattr(tech, "prodSci", 0))
                or (self.win.vMorale.checked and getattr(tech, "moraleTrgt", 0)))

    def _filterShipSize(self, tech):
        return ((self.win.vSmall.checked and tech.combatClass == 0)
                or (self.win.vMedium.checked and tech.combatClass == 1)
                or (self.win.vLarge.checked and tech.combatClass == 2))

    def _filterShipMilitary(self, tech):
        return ((self.win.vMilShip.checked and tech.isMilitary)
                or (self.win.vCivShip.checked and not tech.isMilitary))

    def _showStructures(self):
        items = []

        for techID in client.getPlayer().techs.keys():
            tech = client.getTechInfo(techID)
            if not tech.isStructure or tech.level not in self.showLevels or \
               (tech.isStructure and not self._filterStructure(tech)):
                continue
            items.append(self._processNonShips(tech))

        return items

    def _showProjects(self):
        items = []
        for techID in client.getPlayer().techs.keys():
            tech = client.getTechInfo(techID)
            if tech.level not in self.showLevels or not tech.isProject:
                continue
            items.append(self._processNonShips(tech))

        return items

    def _showShips(self):
        items = []
        player = client.getPlayer()

        for designID in player.shipDesigns.keys():
            tech = player.shipDesigns[designID]
            if not self._filterShipSize(tech) or not self._filterShipMilitary(tech):
                continue

            if tech.upgradeTo != Const.OID_NONE:
                # skip ships that are set to upgrade
                continue
            if self.prodProd > 0:
                etc = res.formatTime(math.ceil(float(tech.buildProd) / self.prodProd))
            else:
                etc = _("N/A")
            item = ui.Item(tech.name,
                           tLevel=tech.level,
                           tProd=tech.buildProd,
                           techID=designID,
                           tIsShip=1,
                           tETC=etc)
            items.append(item)
        return items

    def _processTarget(self, planet):
        ownerName = res.getUnknownName()
        ownerID = Const.OID_NONE
        if hasattr(planet, 'owner'):
            ownerID = planet.owner
            if planet.owner != Const.OID_NONE:
                ownerName = client.get(planet.owner, noUpdate=1).name
        if planet.plType in ("A", "G"):
            color = gdata.sevColors[gdata.DISABLED]
        else:
            color = res.getPlayerColor(ownerID)
        plname = getattr(planet, 'name', res.getUnknownName())
        item = ui.Item(plname,
                       text_raw=getattr(planet, 'plEn', plname),
                       planetID=planet.oid,
                       plOwner=ownerName,
                       foreground=color)
        return item

    def showTechs(self):
        # techs
        items = []

        if self.showStructures:
            items += self._showStructures()
        if self.showShips:
            items += self._showShips()
        if self.showOther:
            items += self._showProjects()

        # sort it by level and then by name
        items.sort(key=lambda a: (100 - a.tLevel, a.text))
        self.win.vTechs.items = items
        self.win.vTechs.itemsChanged()
        # preserve selection
        for item in items:
            if self.techID == item.techID:
                self.win.vTechs.selectItem(item)
                break
        # tech level filter
        for i in range(1, 7):
            widget = getattr(self.win, 'vLevel%d' % i)
            if i in self.showLevels and i <= self.maxTechLevel:
                widget.visible = 1
                widget.pressed = 1
            elif i not in self.showLevels and i <= self.maxTechLevel:
                widget.visible = 1
                widget.pressed = 0
            else:
                widget.visible = 0
        self.win.vStructuresToggle.pressed = self.showStructures
        self.win.vShipsToggle.pressed = self.showShips
        self.win.vOtherToggle.pressed = self.showOther
        # targets
        info = []
        system = client.get(self.systemID, noUpdate=1)
        for planetID in system.planets:
            planet = client.get(planetID, noUpdate=1)
            info.append(self._processTarget(planet))
        self.win.vTargets.items = info
        self.win.vTargets.itemsChanged()
        for item in info:
            if self.targetID == item.planetID:
                self.win.vTargets.selectItem(item)
                break
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

    def onSelectPlanet(self, widget, action, data):
        self.quantity = int(self.win.vQuantity.text)
        self.targetID = data.planetID
        self.showTechs()
        self.showSlots()

    def onSelectSlot(self, widget, action, data):
        self.structToDemolish = data.techID

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

    def onGovTransferConfirmed(self):
        # we assume player wants to build just one center - in opposite case, he may change quantity in the task itself
        self.win.vQuantity.text = str(1)
        self.govTransferConfirm = True
        self.onConstruct(*self.govTransferData)

    def onConstruct(self, widget, action, data):
        planet = client.get(self.planetID, noUpdate=1)
        player = client.getPlayer()
        if not self.techID:
            self.win.setStatus(_('Select technology to construct.'))
            return
        if not self.targetID:
            self.win.setStatus(_('Select planet to construct on.'))
            return
        try:
            self.quantity = int(self.win.vQuantity.text)
        except ValueError:
            self.win.setStatus(_('Specify quantity (1, 2, 3, ...).'))
            return
        # government centers have additional query and if confirmed, another round of this function is called
        if self.techID < 1000:
            tech = player.shipDesigns[self.techID]
        else:
            tech = client.getTechInfo(self.techID)
        if not getattr(tech, 'govPwr', 0) == 0 and not self.govTransferConfirm:
            # confirm dialog doesn't send through parameters, so we have to save them
            self.govTransferData = (widget, action, data)
            self.confirmDlg.display(_("Do you want to issue relocation of your government?"),
                _("Yes"), _("No"), self.onGovTransferConfirmed)
        else:
            try:
                self.win.setStatus(_('Executing START CONSTRUCTION command...'))
                planet.prodQueue, player.stratRes = client.cmdProxy.startConstruction(self.planetID,
                    self.techID, self.quantity, self.targetID, self.techID < 1000,
                    self.win.vReportFin.checked, self.structToDemolish)
                self.win.setStatus(_('Command has been executed.'))
            except GameException, e:
                self.win.setStatus(e.args[0])
                return
        self.hide()
        self.caller.update()

    def onToggleStructures(self, widget, action, data):
        self.showStructures = 1
        self.showShips = 0
        self.showOther = 0
        self.win.setTagAttr('struct', 'visible', 1)
        self.win.setTagAttr('ship', 'visible', 0)
        self.update()

    def onToggleShips(self, widget, action, data):
        self.showStructures = 0
        self.showShips = 1
        self.showOther = 0
        self.win.setTagAttr('struct', 'visible', 0)
        self.win.setTagAttr('ship', 'visible', 1)
        self.update()

    def onToggleOther(self, widget, action, data):
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
        cols = 38
        rows = 24 #was 23
        dlgWidth = cols * 20 + 4
        dlgHeight = rows * 20 + 4
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             movable=0,
                             title=_('Select new task'),
                             rect=ui.Rect((w - dlgWidth) / 2, (h - dlgHeight) / 2, dlgWidth, dlgHeight),
                             layoutManager=ui.SimpleGridLM(),
                             tabChange=True)
        self.win.subscribeAction('*', self)
        ui.Title(self.win, layout=(0, 0, 22, 1), text=_('Technology'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Listbox(self.win, layout=(0, 1, 22, 19), id='vTechs',
                   columns=((_('Name'), 'text', 13, ui.ALIGN_W), (_('Lvl'), 'tLevel', 2, ui.ALIGN_E),
                   (_('Constr'), 'tProd', 3, ui.ALIGN_E), (_('ETC'), 'tETC', 3, ui.ALIGN_E)),
                   columnLabels=1, action='onSelectTech')
        # filter
        ui.Button(self.win, layout=(0, 20, 3, 1), text=_('Stucts'), toggle=1,
                  id='vStructuresToggle', action='onToggleStructures')
        ui.Button(self.win, layout=(3, 20, 3, 1), text=_('Ships'), toggle=1,
                  id='vShipsToggle', action='onToggleShips')
        ui.Button(self.win, layout=(6, 20, 3, 1), text=_('Misc'), toggle=1,
                  id='vOtherToggle', action='onToggleOther')
        ui.Button(self.win, layout=(9, 20, 1, 1), text=_('1'), id='vLevel1',
                  toggle=1, action='onToggleLevel', data=1)
        ui.Button(self.win, layout=(10, 20, 1, 1), text=_('2'), id='vLevel2',
                  toggle=1, action='onToggleLevel', data=2)
        ui.Button(self.win, layout=(11, 20, 1, 1), text=_('3'), id='vLevel3',
                  toggle=1, action='onToggleLevel', data=3)
        ui.Button(self.win, layout=(12, 20, 1, 1), text=_('4'), id='vLevel4',
                  toggle=1, action='onToggleLevel', data=4)
        ui.Button(self.win, layout=(13, 20, 1, 1), text=_('5'), id='vLevel5',
                  toggle=1, action='onToggleLevel', data=5)
        ui.Button(self.win, layout=(14, 20, 1, 1), text=_('6'), id='vLevel6',
                  toggle=1, action='onToggleLevel', data=6)
        ui.Button(self.win, layout=(18, 20, 4, 1), text=_('Info'), action='onInfo',
                  id='vInfo')
        # targets
        ui.Title(self.win, layout=(22, 0, 16, 1), text=_('Target planet'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Listbox(self.win, layout=(22, 1, 16, 10), id='vTargets',
                   columns=((_('Planet'), 'text', 10, ui.ALIGN_W), (_('Owner'), 'plOwner', 5, ui.ALIGN_W)), columnLabels=1,
                   action='onSelectPlanet')
        ui.Listbox(self.win, layout=(22, 11, 16, 7), id='vTSlots',
                   columns=((_('Target slots'), 'text', 15, ui.ALIGN_W), ), columnLabels=1,
                   action='onSelectSlot')
        # prod types
        ui.Check(self.win, layout=(0, 21, 6, 1), text=_('Bio production'), tags=['struct'],
                 id='vBioProduction', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(6, 21, 6, 1), text=_('En production'), tags=['struct'],
                 id='vEnProduction', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(12, 21, 6, 1), text=_('CP production'), tags=['struct'],
                 id='vCPProduction', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(18, 21, 6, 1), text=_('RP production'), tags=['struct'],
                 id='vRPProduction', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(24, 21, 6, 1), text=_('Military'), tags=['struct'],
                 id='vMilitary', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(30, 21, 6, 1), text=_('Morale'), tags=['struct'],
                 id='vMorale', checked=1, align=ui.ALIGN_W, action='onFilter')
        # ship types
        ui.Check(self.win, layout=(0, 21, 6, 1), text=_('Small'), tags=['ship'],
                 id='vSmall', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(6, 21, 6, 1), text=_('Medium'), tags=['ship'],
                 id='vMedium', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(12, 21, 6, 1), text=_('Large'), tags=['ship'],
                 id='vLarge', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(18, 21, 6, 1), text=_('Civilian'), tags=['ship'],
                 id='vCivShip', checked=1, align=ui.ALIGN_W, action='onFilter')
        ui.Check(self.win, layout=(24, 21, 6, 1), text=_('Military'), tags=['ship'],
                 id='vMilShip', checked=1, align=ui.ALIGN_W, action='onFilter')
        # build
        ui.Title(self.win, layout=(22, 18, 16, 1), text=_('Options'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Label(self.win, layout=(22, 19, 10, 1), text=_('Quantity'), align=ui.ALIGN_W)
        ui.Entry(self.win, layout=(33, 19, 5, 1), id='vQuantity', align=ui.ALIGN_E, orderNo=1)
        ui.Check(self.win, layout=(31, 20, 7, 1), id='vReportFin', text=_('Report finalization'))
        ui.Title(self.win, layout=(0, 22, 28, 1), id='vStatusBar', align=ui.ALIGN_W)
        ui.TitleButton(self.win, layout=(28, 22, 5, 1), text=_('Cancel'), action='onCancel')
        ui.TitleButton(self.win, layout=(33, 22, 5, 1), text=_('Construct'), action='onConstruct')

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
from TechInfoDlg import TechInfoDlg
from ConstructionDlg import ConstructionDlg
from ConfirmDlg import ConfirmDlg
from ige.ospace.Const import *
from ige.ospace import Rules
from osci import gdata, client, res
from ige import GameException
import math
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

    def display(self, caller, prodProd, structToDemolish = OID_NONE):
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

    def showTechs(self):
        # techs
        items = []
        select = None

        showMilitary = self.win.vMilitary.checked
        showBio = self.win.vBioProduction.checked
        showEn = self.win.vEnProduction.checked
        showCP = self.win.vCPProduction.checked
        showRP = self.win.vRPProduction.checked
        showMorale = self.win.vMorale.checked

        showSmall = self.win.vSmall.checked
        showMed = self.win.vMedium.checked
        showLarge = self.win.vLarge.checked
        showCivShip = self.win.vCivShip.checked
        showMilShip = self.win.vMilShip.checked

        for techID in client.getPlayer().techs.keys():
            tech = client.getTechInfo(techID)

            # hide pirate techs from ships and miscs view
            if not self.showStructures and tech.level == 99:
                continue

            if tech.isStructure:
                if (tech.isMilitary or getattr(tech, "prodBio", 0) > 0 or getattr(tech, "prodEnv", 0) > 0 or \
                        getattr(tech, "prodEn", 0) > 0 or getattr(tech, "prodProd", 0) > 0 or \
                        getattr(tech, "prodSci", 0) > 0 or getattr(tech, "moraleTrgt", 0) > 0):
                    if not ((tech.isMilitary and showMilitary) or \
                           ((getattr(tech, "prodBio", 0) > 0 or getattr(tech, "prodEnv", 0) > 0) and showBio) or \
                            (getattr(tech, "prodEn", 0) > 0 and showEn) or \
                            (getattr(tech, "prodProd", 0) > 0 and showCP) or \
                            (getattr(tech, "prodSci", 0) > 0 and showRP) or \
                            (getattr(tech, "moraleTrgt", 0) > 0 and showMorale)):
                        continue

            if self.prodProd > 0:
                etc = math.ceil(float(tech.buildProd) / self.prodProd)
                if self.targetID != self.planetID:
                    etc *= Rules.buildOnAnotherPlanetMod
                etc = res.formatTime(etc)
            else:
                etc = _("N/A")
            item = ui.Item(tech.name,
                tLevel = tech.level,
                tProd = tech.buildProd,
                techID = techID,
                tIsShip = 0,
                tETC = etc,
            )
            if item.tLevel > self.maxTechLevel:
                self.maxTechLevel = item.tLevel

            if item.tLevel in self.showLevels and \
                ((self.showStructures and tech.isStructure) or \
                (self.showOther and (tech.isProject))):
                items.append(item)
                if techID == self.techID:
                    select = item

        # special handling for ships
        player = client.getPlayer()
        if self.showShips:
            for designID in player.shipDesigns.keys():
                tech = player.shipDesigns[designID]

                if not ((tech.combatClass == 0 and showSmall) or (tech.combatClass == 1 and showMed) or (tech.combatClass == 2 and showLarge)):
                    continue

                if not ((tech.isMilitary and showMilShip) or (not tech.isMilitary and showCivShip)):
                    continue

                if tech.upgradeTo != OID_NONE:
                    # skip ships that are set to upgrade
                    continue
                if self.prodProd > 0:
                    etc = res.formatTime(math.ceil(float(tech.buildProd) / self.prodProd))
                else:
                    etc = _("N/A")
                item = ui.Item(tech.name,
                    tLevel = tech.level,
                    tProd = tech.buildProd,
                    techID = designID,
                    tIsShip = 1,
                    tETC = etc,
                )
                items.append(item)
                if designID == self.techID:
                    select = item
        # sort it by level and then by name
        items.sort(lambda a, b: cmp((100 - a.tLevel, a.text), (100 - b.tLevel, b.text)))
        self.win.vTechs.items = items
        self.win.vTechs.itemsChanged()
        self.win.vTechs.selectItem(select)
        # filter
        for i in xrange(1, 10):
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
        system = client.get(self.systemID, noUpdate = 1)
        select = None
        if hasattr(system, 'planets'):
            for planetID in system.planets:
                planet = client.get(planetID, noUpdate = 1)
                owner = res.getUnknownName()
                #rel = REL_UNDEF
                ownerID = OID_NONE
                if hasattr(planet, 'owner'):
                    ownerID = planet.owner
                    if planet.owner != OID_NONE:
                        owner = client.get(planet.owner, noUpdate = 1).name
                        #rel = client.getRelationTo(planet.owner)
                    else:
                        owner = _('[Nobody]')
                if planet.plType in ("A", "G"):
                    color = gdata.sevColors[gdata.DISABLED]
                else:
                    #color = res.getFFColorCode(rel)
                    color = res.getPlayerColor(ownerID)
                plname = getattr(planet, 'name', res.getUnknownName())
                item = ui.Item(
                    plname,
                    text_raw = getattr(planet, 'plEn', plname),
                    planetID = planetID,
                    plOwner = owner,
                    foreground = color,
                )
                info.append(item)
                if planetID == self.targetID:
                    select = item
        self.win.vTargets.items = info
        self.win.vTargets.itemsChanged()
        self.win.vTargets.selectItem(select)
        # quantity
        self.win.vQuantity.text = str(self.quantity)

    def showSlots(self):
        # techs
        items = []
        techs = {}
        if self.showStructures:
            player = client.getPlayer()
            target = client.get(self.targetID, noUpdate = 1)
            if hasattr(target, 'slots') and target.owner == player.oid:
                if len(target.slots) < target.plSlots:
                    item = ui.Item(_("Free slot"), techID = 0)
                    items.append(item)
                for struct in target.slots:
                    if not struct[STRUCT_IDX_TECHID] in techs:
                        techs[struct[STRUCT_IDX_TECHID]] = 1
                    else:
                        techs[struct[STRUCT_IDX_TECHID]] += 1
                for tech in techs.keys():
                    techInfo = client.getTechInfo(tech)
                    item = ui.Item("%s (%d)" % (techInfo.name, techs[tech]), techID = tech)
                    items.append(item)

        self.win.vTSlots.items = items
        self.win.vTSlots.itemsChanged()
        self.structToDemolish = OID_NONE

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
        planet = client.get(self.planetID, noUpdate = 1)
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
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _('Select new task'),
            rect = ui.Rect((w - dlgWidth) / 2, (h - dlgHeight) / 2, dlgWidth, dlgHeight),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True
        )
        self.win.subscribeAction('*', self)
        ui.Title(self.win, layout = (0, 0, 22, 1), text = _('Technology'),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.Listbox(self.win, layout = (0, 1, 22, 19), id = 'vTechs',
            columns = ((_('Name'), 'text', 13, ui.ALIGN_W), (_('Lvl'), 'tLevel', 2, ui.ALIGN_E),
                (_('Constr'), 'tProd', 3, ui.ALIGN_E), (_('ETC'), 'tETC', 3, ui.ALIGN_E)),
            columnLabels = 1, action = 'onSelectTech')
        # filter
        ui.Button(self.win, layout = (0, 20, 3, 1), text = _('Stucts'), toggle = 1,
            id = 'vStructuresToggle', action = 'onToggleStructures')
        ui.Button(self.win, layout = (3, 20, 3, 1), text = _('Ships'), toggle = 1,
            id = 'vShipsToggle', action = 'onToggleShips')
        ui.Button(self.win, layout = (6, 20, 3, 1), text = _('Misc'), toggle = 1,
            id = 'vOtherToggle', action = 'onToggleOther')
        ui.Button(self.win, layout = (9, 20, 1, 1), text = _('1'), id = 'vLevel1',
            toggle = 1, action = 'onToggleLevel', data = 1)
        ui.Button(self.win, layout = (10, 20, 1, 1), text = _('2'), id = 'vLevel2',
            toggle = 1, action = 'onToggleLevel', data = 2)
        ui.Button(self.win, layout = (11, 20, 1, 1), text = _('3'), id = 'vLevel3',
            toggle = 1, action = 'onToggleLevel', data = 3)
        ui.Button(self.win, layout = (12, 20, 1, 1), text = _('4'), id = 'vLevel4',
            toggle = 1, action = 'onToggleLevel', data = 4)
        ui.Button(self.win, layout = (13, 20, 1, 1), text = _('5'), id = 'vLevel5',
            toggle = 1, action = 'onToggleLevel', data = 5)
        ui.Button(self.win, layout = (14, 20, 1, 1), text = _('6'), id = 'vLevel6',
            toggle = 1, action = 'onToggleLevel', data = 6)
        ui.Button(self.win, layout = (15, 20, 1, 1), text = _('7'), id = 'vLevel7',
            toggle = 1, action = 'onToggleLevel', data = 7)
        ui.Button(self.win, layout = (16, 20, 1, 1), text = _('8'), id = 'vLevel8',
            toggle = 1, action = 'onToggleLevel', data = 8)
        ui.Button(self.win, layout = (17, 20, 1, 1), text = _('9'), id = 'vLevel9',
            toggle = 1, action = 'onToggleLevel', data = 9)
        ui.Button(self.win, layout = (18, 20, 4, 1), text = _('Info'), action = 'onInfo',
            id = 'vInfo')
        # targets
        ui.Title(self.win, layout = (22, 0, 16, 1), text = _('Target planet'),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.Listbox(self.win, layout = (22, 1, 16, 10), id = 'vTargets',
            columns = ((_('Planet'), 'text', 10, ui.ALIGN_W), (_('Owner'), 'plOwner', 5, ui.ALIGN_W)), columnLabels = 1,
            action = 'onSelectPlanet')
        ui.Listbox(self.win, layout = (22, 11, 16, 7), id = 'vTSlots',
            columns = ((_('Target slots'), 'text', 15, ui.ALIGN_W), ), columnLabels = 1,
            action = 'onSelectSlot')
        # prod types
        ui.Check(self.win, layout = (0, 21, 6, 1), text = _('Bio production'), tags = ['struct'],
            id = 'vBioProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (6, 21, 6, 1), text = _('En production'), tags = ['struct'],
            id = 'vEnProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (12, 21, 6, 1), text = _('CP production'), tags = ['struct'],
            id = 'vCPProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (18, 21, 6, 1), text = _('RP production'), tags = ['struct'],
            id = 'vRPProduction', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (24, 21, 6, 1), text = _('Military'), tags = ['struct'],
            id = 'vMilitary', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (30, 21, 6, 1), text = _('Morale'), tags = ['struct'],
            id = 'vMorale', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        # ship types
        ui.Check(self.win, layout = (0, 21, 6, 1), text = _('Small'), tags = ['ship'],
            id = 'vSmall', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (6, 21, 6, 1), text = _('Medium'), tags = ['ship'],
            id = 'vMedium', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (12, 21, 6, 1), text = _('Large'), tags = ['ship'],
            id = 'vLarge', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (18, 21, 6, 1), text = _('Civilian'), tags = ['ship'],
            id = 'vCivShip', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        ui.Check(self.win, layout = (24, 21, 6, 1), text = _('Military'), tags = ['ship'],
            id = 'vMilShip', checked = 1, align = ui.ALIGN_W, action = 'onFilter')
        # build
        ui.Title(self.win, layout = (22, 18, 16, 1), text = _('Options'),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.Label(self.win, layout = (22, 19, 10, 1), text = _('Quantity'), align = ui.ALIGN_W)
        ui.Entry(self.win, layout = (33, 19, 5, 1), id = 'vQuantity', align = ui.ALIGN_E, orderNo = 1)
        ui.Check(self.win, layout = (31, 20, 7, 1), id = 'vReportFin', text = _('Report finalization'))
        ui.Title(self.win, layout = (0, 22, 28, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (28, 22, 5, 1), text = _('Cancel'), action = 'onCancel')
        ui.TitleButton(self.win, layout = (33, 22, 5, 1), text = _('Construct'), action = 'onConstruct')

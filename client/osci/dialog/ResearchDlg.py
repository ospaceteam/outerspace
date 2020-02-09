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

import ige
from ige.ospace import Rules, Utils, TechHandlers
import ige.ospace.Const as Const

from osci import client, res, gdata

from TechInfoDlg import TechInfoDlg
from ConfirmDlg import ConfirmDlg

class ResearchDlg:

    def __init__(self, app):
        self.app = app
        self.techInfoDlg = TechInfoDlg(app)
        self.confirmDlg = ConfirmDlg(app)
        self.showCompleted = 0
        self.showObsolete = 0
        self.createUI()

    def display(self):
        self.win.vUnObs.enabled = 0
        self.win.vObs.enabled = 0
        self.show()
        # show window
        if not self.win.visible:
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
        if self.win.visible:
            self.show()

    def _processResearchableTech(self, tech):
        player = client.getPlayer()

        item = ui.Item(tech.name, tLevel=tech.level, techID=tech.id)
        item.tStruct = '*' if getattr(tech, 'isStructure', None) else ''
        item.tShip = '*' if getattr(tech, 'isShipEquip', None) else ''

        neededSci = Utils.getTechRCost(player, tech.id)
        item.tETC = res.formatTime(float(neededSci) / player.effSciPoints) if player.effSciPoints > 0 else _("N/A")
        item.foreground = None

        if client.getFullTechInfo(tech.id).finishResearchHandler == TechHandlers.finishResTLAdvance:
            item.foreground = gdata.sevColors[gdata.CRI]
        elif getattr(tech, "researchDisables", None):
            item.foreground = (0xff, 0xff, 0x00)
        return item

    def _processResearchable(self, disabled, queued):
        player = client.getPlayer()

        items = []
        for techID in client.getAllTechIDs():
            if techID in player.techs or techID in queued or techID in disabled:
                continue
            tech = client.getTechInfo(techID)
            if not hasattr(tech, 'partialData') or not hasattr(tech, 'researchMod'):
                continue
            items.append(self._processResearchableTech(tech))
        self.win.vRTechs.items = items
        self.win.vRTechs.itemsChanged()

    def _processResearchQueueTask(self, task):
        player = client.getPlayer()
        tech = client.getTechInfo(task.techID)
        fulltech = client.getFullTechInfo(task.techID)
        researchSci = Utils.getTechRCost(player, task.techID, task.improvement)
        item = ui.Item(tech.name, techID=task.techID)
        item.tooltipTitle = _("Details")
        item.tooltip = _("Research points %d/%d, change %d pts/turn.") % (task.currSci, researchSci, task.changeSci)
        item.statustip = item.tooltip
        item.tImpToMax = "*" if task.improveToMax else ""
        item.tImproveToMax = task.improveToMax
        item.tProgress = _("%d %%") % int(task.currSci * 100 / researchSci) if task.currSci > 0 else _("-")
        totalSci = 0
        if task.changeSci > 0:
            etc = float(researchSci - task.currSci) / max(task.changeSci, player.effSciPoints)
            totalSci += researchSci - task.currSci
            if player.effSciPoints > 0:
                item.tETC = res.formatTime(etc)
            else:
                item.tETC = res.getNA()
        elif task.changeSci < 0:
            etc = - float(task.currSci) / min(task.changeSci, player.effSciPoints)
            item.tETC = _("[%s]") % res.formatTime(etc)
        elif player.effSciPoints > 0:
            etc = float(researchSci) / player.effSciPoints
            totalSci += researchSci
            item.tETC = res.formatTime(etc)
        else:
            item.tETC = res.getNA()

        if task.improveToMax:
            for impr in range(task.improvement + 1, fulltech.maxImprovement + 1):
                totalSci += Utils.getTechRCost(player, task.techID, impr)
        item.tLevel = _("%d-%d") % (tech.level, task.improvement)
        return item, totalSci

    def _processResearchQueue(self):
        player = client.getPlayer()

        items = []
        index = 0
        queued = []
        totalSci = 0
        for task in player.rsrchQueue:
            queued.append(task.techID)
            item, taskSci = self._processResearchQueueTask(task)
            item.index = index
            items.append(item)
            totalSci += taskSci
            index += 1
        totalSci = math.ceil(float(totalSci) / player.effSciPoints)
        self.win.vRQueue.items = items
        self.win.vRQueue.itemsChanged()
        self.win.vRQueueTop.enabled = 0
        self.win.vRQueueUp.enabled = 0
        self.win.vRQueueDown.enabled = 0
        self.win.vRQueueAbort.enabled = 0
        self.win.vRQueueRepat.enabled = 0
        self.win.vRQueueRepat.pressed = 0
        self.win.vRQueueInfo.enabled = 0
        self.win.vRTotal.text = res.formatTime(totalSci) if totalSci else _("N/A")
        return queued

    def _processImprovableTech(self, tech, scheduledIDs):
        player = client.getPlayer()

        item = ui.Item(tech.name,
                       techID=tech.id,
                       tLevel='%d-%d' % (tech.level, player.techs[tech.id]),
                       tStruct=(' ', '*')[tech.isStructure],
                       tShip=(' ', '*')[tech.isShipEquip])
        neededSci = Utils.getTechRCost(player, tech.id)
        item.tETC = res.formatTime(float(neededSci) / player.effSciPoints) if player.effSciPoints > 0 else _("N/A")
        item.foreground = (0xd0, 0xd0, 0xd0) if tech.id in scheduledIDs else None
        item.foreground = (0x80, 0x40, 0x40) if tech.id in player.obsoleteTechs else item.foreground
        return item

    def _processKnownTech(self):
        player = client.getPlayer()

        items = []
        disabled = []
        scheduledIDs = set([task.techID for task in player.rsrchQueue])
        for techID in player.techs.keys():
            if techID in player.obsoleteTechs and not self.showObsolete:
                continue
            tech = client.getTechInfo(techID)
            improvement = player.techs[techID]
            if improvement == tech.maxImprovement and not self.showCompleted:
                continue
            items.append(self._processImprovableTech(tech, scheduledIDs))
            disabled.extend(tech.researchDisables)
        self.win.vKTechs.items = items
        self.win.vKTechs.itemsChanged()
        return disabled

    def show(self):
        player = client.getPlayer()
        # title
        self.win.vRQueueTitle.text = _('Research queue [%d pts/turn]') % (
            player.effSciPoints,
        )
        self.win.title = _("Research [TL%d]") % player.techLevel

        disabled = self._processKnownTech()
        queued = self._processResearchQueue()
        self._processResearchable(disabled, queued)

    def onSelectKTech(self, widget, action, data):
        techID = self.win.vKTechs.selection[0].techID
        player = client.getPlayer()
        if techID in player.obsoleteTechs:
            self.win.vObs.enabled = 0
            self.win.vUnObs.enabled = 1
        else:
            self.win.vUnObs.enabled = 0
            self.win.vObs.enabled = 1

    def onKTechInfo(self, widget, action, data):
        if self.win.vKTechs.selection:
            self.techInfoDlg.display(self.win.vKTechs.selection[0].techID)

    def onSelectRTech(self, widget, action, data):
        # TODO implement
        pass

    def onRTechInfo(self, widget, action, data):
        if self.win.vRTechs.selection:
            self.techInfoDlg.display(self.win.vRTechs.selection[0].techID)

    def onSelectRQueueTech(self, widget, action, data):
        index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
        self.win.vRQueueTop.enabled = index > 0
        self.win.vRQueueUp.enabled = index > 0
        self.win.vRQueueDown.enabled = index < len(self.win.vRQueue.items) - 1
        self.win.vRQueueAbort.enabled = 1
        self.win.vRQueueRepat.enabled = 1
        self.win.vRQueueRepat.pressed = self.win.vRQueue.selection[0].tImproveToMax
        self.win.vRQueueInfo.enabled = 1

    def onRQueueTechInfo(self, widget, action, data):
        if self.win.vRQueue.selection:
            self.techInfoDlg.display(self.win.vRQueue.selection[0].techID)

    def onCloseDlg(self, widget, action, data):
        self.hide()

    def onStartResearch(self, widget, action, data):
        if not self.win.vRTechs.selection:
            self.win.setStatus(_('Select technology to research.'))
            return
        else:
            techID = self.win.vRTechs.selection[0].techID
        try:
            self.win.setStatus(_('Executing START RESEARCH command...'))
            player = client.getPlayer()
            player.rsrchQueue = client.cmdProxy.startResearch(player.oid, techID)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onStartImprovement(self, widget, action, data):
        if not self.win.vKTechs.selection:
            self.win.setStatus(_('Select technology to improve.'))
            return
        else:
            techID = self.win.vKTechs.selection[0].techID
        try:
            self.win.setStatus(_('Executing START RESEARCH command...'))
            player = client.getPlayer()
            player.rsrchQueue = client.cmdProxy.startResearch(player.oid, techID)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onRTaskMove(self, widget, action, data):
        self.win.setStatus(_('Executing MOVE RESEARCH command...'))
        player = client.getPlayer()
        index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
        # fix -9999 (move to top)
        amount = widget.data
        if index + amount < 0: amount = - index
        # execute command
        player.rsrchQueue = client.cmdProxy.moveResearch(player.oid, index, amount)
        self.update()
        index += amount
        self.win.vRQueue.selectItem(self.win.vRQueue.items[index])
        self.win.setStatus(_('Command has been executed.'))
        self.onSelectRQueueTech(widget, action, None)

    def onRTaskRepeat(self, widget, action, data):
        self.win.setStatus(_('Executing EDIT RESEARCH command...'))
        player = client.getPlayer()
        index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
        repeat = not self.win.vRQueue.selection[0].tImproveToMax
        # execute command
        player.rsrchQueue = client.cmdProxy.editResearch(player.oid, index, repeat)
        self.update()
        self.win.vRQueue.selectItem(self.win.vRQueue.items[index])
        self.win.setStatus(_('Command has been executed.'))
        self.onSelectRQueueTech(widget, action, None)

    def onToggleCompleted(self, widget, action, data):
        self.showCompleted = self.win.vSCompl.pressed
        self.update()

    def onRTaskAbort(self, widget, action, data):
        self.confirmDlg.display(_("Abort this research task?"),
            _("Yes"), _("No"), self.onRTaskAbortConfirmed)

    def onRTaskAbortConfirmed(self):
        self.win.setStatus(_('Executing ABORT RESEARCH command...'))
        player = client.getPlayer()
        index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
        player.rsrchQueue = client.cmdProxy.abortResearch(player.oid, index)
        self.update()
        self.win.setStatus(_('Command has been executed.'))

    def onSetObsolete(self, widget, action, data):
        if not self.win.vKTechs.selection:
            self.win.setStatus(_('Select technology to obsolete.'))
            return
        else:
            techID = self.win.vKTechs.selection[0].techID
        try:
            self.win.setStatus(_('Executing OBSOLETTE command...'))
            player = client.getPlayer()
            player.obsoleteTechs = client.cmdProxy.addObsoleteTechs(player.oid, techID)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onUnsetObsolete(self, widget, action, data):
        if not self.win.vKTechs.selection:
            self.win.setStatus(_('Select technology to un-obsolete.'))
            return
        else:
            techID = self.win.vKTechs.selection[0].techID
        try:
            self.win.setStatus(_('Executing UN-OBSOLETTE command...'))
            player = client.getPlayer()
            player.obsoleteTechs = client.cmdProxy.delObsoleteTechs(player.oid, techID)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onToggleObsolete(self, widget, action, data):
        self.showObsolete = self.win.vSObsl.pressed
        self.update()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             titleOnly=w == 800 and h == 600,
                             movable=0,
                             title=_('Research'),
                             rect=ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
                             layoutManager=ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        ui.Title(self.win, layout=(0, 27, 35, 1), id='vStatusBar',
                 align=ui.ALIGN_W)
        ui.TitleButton(self.win, layout=(35, 27, 5, 1), text=_('Close'),
                       action='onCloseDlg')
        # known techs
        ui.Title(self.win, layout=(0, 0, 20, 1), text=_('Known technologies'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Listbox(self.win, layout=(0, 1, 20, 24), id='vKTechs',
                   columns=((_('Name'), 'text', 10, ui.ALIGN_W), (_('Lvl'), 'tLevel', 1.5, 0),
                   (_('Str'), 'tStruct', 1, 0), (_('Sh'), 'tShip', 1, 0),
                   (_('ETC'), 'tETC', 0, ui.ALIGN_E)), columnLabels=1, action='onSelectKTech')
        ui.Button(self.win, layout=(0, 25, 5, 1), text=_('Improve'),
                  action='onStartImprovement')
        ui.Button(self.win, layout=(5, 25, 5, 1), id="vSCompl", text=_('Show completed'),
                  action='onToggleCompleted', toggle=1, pressed=0)
        ui.Button(self.win, layout=(15, 25, 5, 1), text=_('Info'),
                  action='onKTechInfo')
        ui.Button(self.win, layout=(0, 26, 5, 1), id='vUnObs', text=_('Un-Obsolete'),
                  action='onUnsetObsolete')
        ui.Button(self.win, layout=(0, 26, 5, 1), id='vObs', text=_('Obsolete'),
                  action='onSetObsolete')
        ui.Button(self.win, layout=(5, 26, 5, 1), id="vSObsl", text=_('Show obsolete'),
                  action='onToggleObsolete', toggle=1, pressed=0)
        # unknown techs
        ui.Title(self.win, layout=(20, 0, 20, 1), text=_('Researchable technologies'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Listbox(self.win, layout=(20, 1, 20, 12), id='vRTechs',
                   columns=((_('Name'), 'text', 10, ui.ALIGN_W), (_('Lvl'), 'tLevel', 1.5, 0),
                   (_('Str'), 'tStruct', 1, 0), (_('Sh'), 'tShip', 1, 0),
                   (_('ETC'), 'tETC', 0, ui.ALIGN_E)), columnLabels=1, action='onSelectRTech')
        ui.Button(self.win, layout=(20, 13, 5, 1), text=_('Research'),
                  action='onStartResearch')
        ui.Button(self.win, layout=(35, 13, 5, 1), text=_('Info'),
                  action='onRTechInfo')
        # research queue
        ui.Title(self.win, layout=(20, 14, 20, 1), text=_('Research queue'),
                 align=ui.ALIGN_W, id='vRQueueTitle', font='normal-bold')
        ui.Listbox(self.win, layout=(20, 15, 20, 11), id='vRQueue',
                   columns=((_('R'), 'tImpToMax', 1, ui.ALIGN_NONE),
                            (_('Name'), 'text', 10, ui.ALIGN_W),
                            (_('Lvl'), 'tLevel', 1.5, 0),
                            (_('Progress'), 'tProgress', 3.5, ui.ALIGN_E),
                            (_('ETC'), 'tETC', 0, ui.ALIGN_E)),
                   columnLabels=1, action='onSelectRQueueTech', sortable=False)
        ui.Button(self.win, layout=(20, 26, 2, 1), text=_("TOP"),
                  id='vRQueueTop', action='onRTaskMove', data=-9999,
                  tooltip=_("Move selected technology to the top of the queue."))
        ui.ArrowButton(self.win, layout=(22, 26, 1, 1), direction=ui.ALIGN_N,
                       id='vRQueueUp', action='onRTaskMove', data=-1)
        ui.ArrowButton(self.win, layout=(23, 26, 1, 1), direction=ui.ALIGN_S,
                       id='vRQueueDown', action='onRTaskMove', data=1)
        ui.Button(self.win, layout=(24, 26, 4, 1), text=_('Repeat'),
                  id='vRQueueRepat', action='onRTaskRepeat', toggle=1,
                  tooltip=_("Repeat research of this technology until the technology is fully improved."))
        ui.Button(self.win, layout=(28, 26, 3, 1), text=_('Abort'),
                  id='vRQueueAbort', action='onRTaskAbort')
        ui.Button(self.win, layout=(31, 26, 4, 1), text=_('Info'),
                  id='vRQueueInfo', action='onRQueueTechInfo')
        ui.Label(self.win, layout=(35, 26, 4, 1), id="vRTotal", align=ui.ALIGN_E,
                 tooltip=_("Total amount of time needed to research all technologies in the queue"))


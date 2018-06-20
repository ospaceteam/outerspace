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

# TODO rewrite it to support general number of queues, not just 5 and to make
# the code nicer

import pygameui as ui
from ChangeQtyDlg import ChangeQtyDlg
from NewGlobalTaskDlg import NewGlobalTaskDlg
from ConstructionDlg import ConstructionDlg
from TechInfoDlg import TechInfoDlg
from ConfirmDlg import ConfirmDlg
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client, sequip
import ige.ospace.Const as Const
from ige.ospace import ShipUtils, Rules
from ige import GameException
from ige import log
import math

class GlobalQueuesDlg:

    def __init__(self, app):
        self.app = app
        self.player = None
        self.vPQueues = None
        self.queueNo = 5
        self.activeQueue = 0
        self.activeIndex = None
        self.changeQtyDlg = ChangeQtyDlg(app)
        self.newGlobalTaskDlg = NewGlobalTaskDlg(self.app)
        self.constructionDlg = ConstructionDlg(app)
        self.techInfoDlg = TechInfoDlg(app)
        self.confirmDlg = ConfirmDlg(app)
        self.createUI()

    def display(self):
        self.playerID = client.getPlayerID()
        self.show()
        self.win.show()
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()
        if self.activeQueue is not None:
            # we don't want current selection to be visible next time we open the dialog
            self.vPQueues[self.activeQueue].selectItem(None)
            self.win.setTagAttr('data', 'visible', False)
        # unregister updates
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)

    def update(self):
        self.show()
        if self.activeQueue is not None:
            if self.activeIndex is not None:
                # restore selection, as the items are recreated in show routine
                self.vPQueues[self.activeQueue].selectItem(self.vPQueues[self.activeQueue].items[self.activeIndex])
            else:
                self.vPQueues[self.activeQueue].selectItem(None)

    def show(self):
        self.player = client.getPlayer()
        self.vPQueues = [self.win.vPQueue0, self.win.vPQueue1, self.win.vPQueue2, self.win.vPQueue3, self.win.vPQueue4]
        #
        for queueNo in xrange(self.queueNo):
            self.showProdQueue(queueNo)

    def showProdQueue(self, id):
        # construction queue
        prodQueue = self.player.prodQueues[id]
        items = []

        index = 0
        for task in prodQueue:
            if task.isShip:
                tech = self.player.shipDesigns[task.techID]
                icons = ((res.getShipImg(tech.combatClass, tech.isMilitary), ui.ALIGN_NONE),)
            else:
                tech = client.getFullTechInfo(task.techID)
                icons = ((res.getTechImg(task.techID), ui.ALIGN_NONE),)
            item = ui.Item(text = str(task.quantity), font = 'small', align = ui.ALIGN_NE, icons = icons, tooltipTitle = "", tooltip = tech.name, statustip = tech.name, index = index, const = tech.buildProd*task.quantity)
            if task.isShip:
                item.background = None
            else:
                item.background = (0x44, 0x44, 0x44)
            items.append(item)
            index += 1
        icons = ((res.getTechImg(1), ui.ALIGN_NONE),)
        item = ui.Item(_('New'), font = 'small-bold', align = ui.ALIGN_SW, icons = icons, index = None)
        items.append(item)
        self.vPQueues[id].items = items
        self.vPQueues[id].itemsChanged()

    def onQueueItemSelected(self, widget, action, data):
        if widget.orderNo != self.activeQueue:
            self.vPQueues[self.activeQueue].selectItem(None)
        self.activeQueue = widget.orderNo
        if not data:
            # unselected
            self.activeIndex = None
            self.win.setTagAttr('data', 'visible', False)
        elif data.index == None:
            # new task
            self.win.setTagAttr('data', 'visible', False)
            self.activeIndex = None
            self.newGlobalTaskDlg.display(self, self.activeQueue)
            self.vPQueues[self.activeQueue].selectItem(None)
        else:
            # info about task
            task = self.vPQueues[self.activeQueue].items[data.index]
            self.activeIndex = data.index
            self.win.setTagAttr('data', 'visible', True)
            self.win.vTaskName.text = task.tooltip
            self.win.vTaskQuantity.text = task.text
            self.win.vTaskConstPoints.text = task.const

    def onMoveTaskFirstLast(self, widget, action, data):
        if self.activeQueue == None or self.activeIndex == None:
            return

        if widget.data == -1:
            rel = -1 * self.activeIndex
            pos = 0
        else:
            rel = len(self.player.prodQueues[self.activeQueue]) - self.activeIndex - 1
            pos = len(self.player.prodQueues[self.activeQueue]) - 1

        try:
            self.win.setStatus(_('Executing MOVE TASK command...'))
            self.player.prodQueues[self.activeQueue] = client.cmdProxy.moveGlobalConstrItem(self.playerID, self.activeQueue, self.activeIndex, rel)
            self.win.setStatus(_('Command has been executed.'))
        except GameException, e:
            self.win.setStatus(e.args[0])
            return

        self.activeIndex = pos
        self.update()

    def onMoveTask(self, widget, action, data):
        if self.activeQueue == None or self.activeIndex == None:
            return
        try:
            self.win.setStatus(_('Executing MOVE TASK command...'))
            self.player.prodQueues[self.activeQueue] = client.cmdProxy.moveGlobalConstrItem(self.playerID, self.activeQueue, self.activeIndex, widget.data)
            self.win.setStatus(_('Command has been executed.'))
        except GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.activeIndex += widget.data
        self.update()

    def onQtyTask(self, widget, action, data):
        if self.activeQueue == None or self.activeIndex == None:
            return
        task = self.player.prodQueues[self.activeQueue][self.activeIndex]
        self.changeQtyDlg.display(task.quantity, self.onChangeQtyConfirmed)

    def onChangeQtyConfirmed(self):
        if self.changeQtyDlg.quantity != None:
            try:
                self.win.setStatus(_('Executing CHANGE TASK command...'))
                self.player.prodQueues[self.activeQueue], self.player.stratRes = client.cmdProxy.changeGlobalConstruction(self.playerID, self.activeQueue, self.activeIndex, self.changeQtyDlg.quantity)
                self.win.setStatus(_('Command has been executed.'))
            except GameException, e:
                self.win.setStatus(e.args[0])
                return
        self.win.vTaskQuantity.text = self.player.prodQueues[self.activeQueue][self.activeIndex].quantity
        self.win.vTaskConstPoints.text = self.player.prodQueues[self.activeQueue][self.activeIndex].const
        self.update()

    def onTaskInfo(self, widget, action, data):
        if self.activeQueue == None or self.activeIndex == None:
            return
        task = self.player.prodQueues[self.activeQueue][self.activeIndex]
        if not task.isShip:
            self.techInfoDlg.display(task.techID)
        else:
            log.debug("Show ship info")
            self.constructionDlg.selectedDesignID = task.techID;
            self.constructionDlg.display()

    def onAbortTask(self, widget, action, data):
        self.confirmDlg.display(_("Abort this construction task?"),
            _("Yes"), _("No"), self.onAbortTaskConfirmed)

    def onAbortTaskConfirmed(self):
        if self.activeQueue is not None and self.activeIndex is not None:
            try:
                self.win.setStatus(_('Executing ABORT CONSTRUCTION command...'))
                self.player.prodQueues[self.activeQueue], self.player.stratRes = client.cmdProxy.abortGlobalConstruction(self.playerID, self.activeQueue, self.activeIndex)
                self.win.setStatus(_('Command has been executed.'))
            except GameException, e:
                self.win.setStatus(e.args[0])
                return
            if len(self.player.prodQueues[self.activeQueue]) == self.activeIndex:
                if self.activeIndex == 0:
                    self.activeIndex = None
                else:
                    self.activeIndex -= 1

        self.update()
        if self.activeIndex is not None:
            task = self.vPQueues[self.activeQueue].items[self.activeIndex]
            self.win.vTaskName.text = task.tooltip
            self.win.vTaskQuantity.text = task.text
            self.win.vTaskConstPoints.text = task.const
        else:
            self.win.setTagAttr('data', 'visible', False)


    def onClose(self, widget, action, data):
        self.hide()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _('Global production queues'),
            rect = ui.Rect((w - 400 - 4 ) / 2, (h - 440 - 4 ) / 2, 400 + 4 , 420 + 4 ),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        ui.Title(self.win, layout = (0, 0, 20, 1), text = _('Default global queue'),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.ButtonArray(self.win, layout = (0, 1, 20, 2), id = 'vPQueue0',
            buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onQueueItemSelected', orderNo = 0)
        ui.Title(self.win, layout = (0, 3, 20, 1), text = _('Queue \"{0}\"'.format(res.globalQueueName(1))),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.ButtonArray(self.win, layout = (0, 4, 20, 2), id = 'vPQueue1',
            buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onQueueItemSelected', orderNo = 1)
        ui.Title(self.win, layout = (0, 6, 20, 1), text = _('Queue \"{0}\"'.format(res.globalQueueName(2))),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.ButtonArray(self.win, layout = (0, 7, 20, 2), id = 'vPQueue2',
            buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onQueueItemSelected', orderNo = 2)
        ui.Title(self.win, layout = (0, 9, 20, 1), text = _('Queue \"{0}\"'.format(res.globalQueueName(3))),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.ButtonArray(self.win, layout = (0, 10, 20, 2), id = 'vPQueue3',
            buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onQueueItemSelected', orderNo = 3)
        ui.Title(self.win, layout = (0, 12, 20, 1), text = _('Queue \"{0}\"'.format(res.globalQueueName(4))),
            align = ui.ALIGN_W, font = 'normal-bold')
        ui.ButtonArray(self.win, layout = (0, 13, 20, 2), id = 'vPQueue4',
            buttonSize = (2, 2), showSlider = 0, tags = ['pl'], action = 'onQueueItemSelected', orderNo = 4)
        ui.Label(self.win, layout = (0, 16, 20, 1), id = 'vTaskName', align = ui.ALIGN_W,
            font = 'normal-bold', tags = ['queue', 'data'])
        ui.Label(self.win, layout = (9, 17, 7, 1), text = _('Construction pts'),
            align = ui.ALIGN_W, tags = ['queue'])
        ui.Label(self.win, layout = (16, 17, 4, 1), id = 'vTaskConstPoints', align = ui.ALIGN_E,
            tags = ['queue', 'data'])
        ui.Label(self.win, layout = (0, 17, 5, 1), text = _('Quantity'),
            align = ui.ALIGN_W, tags = ['queue'])
        ui.Label(self.win, layout = (5, 17, 3, 1), id = 'vTaskQuantity', align = ui.ALIGN_E,
            tags = ['queue', 'data'])
        ui.Button(self.win, layout = (0, 18, 2, 1), id = 'vITFirst', text = _('<<'),
            tags = ['queue'], action = 'onMoveTaskFirstLast',
            tooltipTitle = _('Move task to first position in queue'), data = -1)
        ui.Button(self.win, layout = (2, 18, 2, 1), id = 'vITPrev', text = _('<'),
            tags = ['queue'], action = 'onMoveTask', data = -1,
            tooltipTitle = _('Move task to previous position in queue'))
        ui.Button(self.win, layout = (4, 18, 2, 1), id = 'vITNext', text = _('>'),
            tags = ['queue'], action = 'onMoveTask', data = 1,
            tooltipTitle = _('Move task to next position in queue'))
        ui.Button(self.win, layout = (6, 18, 2, 1), id = 'vITLast', text = _('>>'),
            tags = ['queue'], action = 'onMoveTaskFirstLast',
            tooltipTitle = _('Move task to last position in queue'), data = 1)
        ui.Button(self.win, layout = (8, 18, 4, 1), text = _('Quantity'),
            tags = ['queue'], action = 'onQtyTask',
            tooltipTitle = _('Change task quantity'))
        ui.Button(self.win, layout = (12, 18, 4, 1), text = _('Info'), id = "vITInfo",
            tags = ['queue'], action = 'onTaskInfo',
            tooltipTitle = _('Show task informations'))
        ui.Button(self.win, layout = (16, 18, 4, 1), text = _('Abort'),
            tags = ['queue'], action = 'onAbortTask',
            tooltipTitle = _('Abort task construction'))
        # status bar + submit/cancel
        ui.TitleButton(self.win, layout = (15, 19, 5, 1), text = _('Close'), action = 'onClose')
        ui.Title(self.win, id = 'vStatusBar', layout = (0, 19, 15, 1), align = ui.ALIGN_W)
        #self.win.statusBar = self.win.vStatusBar


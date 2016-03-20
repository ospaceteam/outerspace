#
#  Copyright 2001 - 2011 Ludek Smid [http://www.ospace.net/]
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
import time

import pygameui as ui
from osci import client, gdata, res
from ige.ospace.Const import *
import ige
from MainGameDlg import MainGameDlg

class GalaxerDlg:
    """ There you subscribe to the new galaxy."""

    def __init__(self, app):
        self.app = app
        self.createUI()
        self.galaxerInfo = client.getGalaxerData()

    def display(self, caller = None):
        self.caller = caller
        if self.show():
            self.win.show()

    def hide(self):
        self.win.hide()

    def show(self):
        items = []
        for galaxyType in self.galaxerInfo:
            info, tPos, tCur, rawTime, isSelected = self.galaxerInfo[galaxyType]
            if rawTime:
                tTime = time.strftime(_("%m-%d-%y %H:%M"), time.localtime(rawTime))
            else:
                tTime = _('N/A')
            if isSelected:
                tChoice = '*'
            else:
                tChoice = ''
            item = ui.Item(galaxyType, tPos = tPos, tCur = tCur, tTime = tTime,tChoice = tChoice)
            items.append(item)
        self.win.vGalaxer.items = items
        self.win.vGalaxer.itemsChanged()
        return True

    def onSelect(self, widget, action, data):
        self.win.vInfo.text = [self.galaxerInfo[data.text][0]]
        self.win.vInfo.offsetRow = 0
        self.win.vInfo.vertScrollbar.slider.position = 0
        return

    def onToggle(self, widget, action, data):
        selection = self.win.vGalaxer.selection
        try:
            selectedType = selection[0].text
        except IndexError:
            selectedType = None
        if selectedType:
            result = client.setPlayerPreference(selectedType)
            if not type(result) == type(True) and not result == True:
                self.galaxerInfo = result
                self.show()
            else:
                self.win.setStatus(_('Command has been executed.'))
                self.hide()
                if not gdata.mainGameDlg:
                    gdata.mainGameDlg = MainGameDlg(self.app)
                    gdata.mainGameDlg.display()
                client.updateDatabase(clearDB = 1)

    def onCancel(self, widget, action, data):
        self.win.hide()
        if self.caller:
            self.caller.display()
        else:
            self.app.exit()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            movable = 0,
            title = _('Select, which galaxy types do you want to play'),
            rect = ui.Rect((w - 424) / 2, (h - 264) / 2, 424, 264),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True
        )
        ui.Listbox(self.win, layout = (0, 0, 21, 6), id = 'vGalaxer',
            columns = (    (_('Galaxy type'), 'text', 5, ui.ALIGN_W),
                        (_('Capacity'), 'tPos', 3, ui.ALIGN_NONE),
                        (_('Queue'), 'tCur', 3, ui.ALIGN_NONE),
                        (_('Last start'), 'tTime', 8, ui.ALIGN_E),
                        (_(''), 'tChoice', 1, ui.ALIGN_NONE)),
                        columnLabels = 1, action = 'onSelect')
        self.win.subscribeAction('*', self)
        scrollBar = ui.Scrollbar(self.win, layout = (20, 6, 1, 4))
        textBox = ui.Text(self.win, layout = (0, 6, 20, 4), id = "vInfo", editable = 0)
        textBox.attachVScrollbar(scrollBar)
        ui.TitleButton(self.win, layout = (0, 10, 21, 1), text = _('Toggle booking'), action = 'onToggle')
        ui.Title(self.win, layout = (0, 11, 17, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (17, 11, 4, 1), text = _('Exit'), action = 'onCancel')
        self.win.statusBar = self.win.vStatusBar

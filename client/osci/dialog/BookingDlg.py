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
import time

import pygameui as ui
from osci import client, gdata, res
from ige.ospace.Const import *
import ige
from MainGameDlg import MainGameDlg

class BookingDlg:
    """ There you subscribe to the new galaxy."""

    def __init__(self, app):
        self.app = app
        self.createUI()
        self.displayGoal = False
        self.offering = client.cmdProxy.getBookingOffers()
        self.bookingInfo = client.cmdProxy.getBookingAnswers()
        self.selectionID = None

    def display(self, caller = None):
        self.caller = caller
        if self.show():
            self.win.show()

    def hide(self):
        self.win.hide()

    def show(self):
        self._showMenu()
        self._showSelection()
        return True

    def _showMenu(self):
        items = []
        for galaxyType in self.bookingInfo:
            if galaxyType is None:
                # this is helper value TODO: handle it different way
                continue
            booking = self.bookingInfo[galaxyType]
            tPos = self.offering[galaxyType].players
            tCur = booking.bookings
            rawTime = booking.last_creation
            tScenario = gdata.gameScenarios[self.offering[galaxyType].scenario]
            isSelected = booking.is_booked
            if rawTime:
                tTime = time.strftime(_("%m-%d-%y %H:%M"), time.localtime(rawTime))
            else:
                tTime = _('N/A')
            if isSelected:
                tChoice = '*'
            else:
                tChoice = ''
            item = ui.Item(galaxyType, tPos = tPos, tCur = tCur, tTime = tTime,tChoice = tChoice, tScenario = tScenario)
            items.append(item)
        self.win.vBooking.items = items
        self.win.vBooking.itemsChanged()

    def _showSelection(self):
        if self.selectionID:
            selection = self.offering[self.selectionID]
            self._displayText(self.selectionID, selection.scenario)
            self.win.vInfo.offsetRow = 0
            self.win.vInfo.vertScrollbar.slider.position = 0

            self.win.vPlanets.text = _('{0} - {1}'.format(selection.minPlanets, selection.maxPlanets))
            self.win.vRadius.text = selection.radius
            self.win.vPlayerGroup.text = selection.playerGroup
            self.win.vResources.text = [", ".join(map(lambda x: gdata.stratRes[x], selection.resources))]
            self.win.vResources.offsetRow = 0
            if selection.challenges:
                self.win.vChallenges.text = ", ".join(map(lambda x: gdata.gameChallenges[x], selection.challenges))
            else:
                self.win.vChallenges.text = ""

    def _displayText(self, selectionID, scenario):
        try:
            if self.displayGoal:
                self.win.vInfo.text = [gdata.gameScenarioDescriptions[scenario]]
            else:
                self.win.vInfo.text = [gdata.galaxyTypeDescriptions[selectionID]]
        except KeyError:
            # this shouldn't happen
            self.win.vInfo.text = [_("Description missing.")]

    def onSelect(self, widget, action, data):
        self.selectionID = data.text
        self._showSelection()

    def onToggle(self, widget, action, data):
        selection = self.win.vBooking.selection
        try:
            selectedType = selection[0].text
        except IndexError:
            selectedType = None
        if selectedType:
            result = client.cmdProxy.toggleBooking(selectedType)
            if not result[None]:
                # booking change is logged, no galaxy creation triggered
                self.bookingInfo = result
                self.show()
            else:
                # galaxy creation has been triggered
                self.hide()
                self.caller.display()
                self.caller.win.setStatus(_('New galaxy creation has been triggered.'))

    def onGoalToggle(self, widget, action, data):
        self.displayGoal = not self.displayGoal
        if self.displayGoal:
            self.win.vGoalToggle.text = _("Show galaxy info")
        else:
            self.win.vGoalToggle.text = _("Show goal info")
        self.show()

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
            rect = ui.Rect((w - 564) / 2, (h - 344) / 2, 564, 344),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True
        )
        ui.Listbox(self.win, layout = (0, 0, 28, 6), id = 'vBooking',
                             sortedBy = ('tPos', 1),
            columns = (
                        ('', 'tChoice', 1, ui.ALIGN_NONE),
                        (_('Galaxy type'), 'text', 6, ui.ALIGN_NONE),
                        (_('Scenario'), 'tScenario', 6, ui.ALIGN_NONE),
                        (_('Queue'), 'tCur', 3, ui.ALIGN_NONE),
                        (_('Capacity'), 'tPos', 3, ui.ALIGN_NONE),
                        (_('Last start'), 'tTime', 8, ui.ALIGN_E)
                        ),
                        columnLabels = 1, action = 'onSelect')
        self.win.subscribeAction('*', self)

        scrollBarInfo = ui.Scrollbar(self.win, layout = (27, 6, 1, 5))
        textBox = ui.Text(self.win, layout = (9, 6.3, 18, 4.7), id = "vInfo", editable = 0)
        textBox.attachVScrollbar(scrollBarInfo)

        ui.Button(self.win, layout = (0.5, 6.5, 8, 1), id = "vGoalToggle", text = _('Display Goals'), action = 'onGoalToggle')
        ui.Label(self.win, layout = (0, 8, 4, 1), text = _("Planets:"), align = ui.ALIGN_W,
                tooltipTitle = _("Planets"),
                tooltip = _("Range of number of planets. About half of them is not colonizable at the beginning.")
                )
        ui.Label(self.win, layout = (4, 8, 4.5, 1), id = "vPlanets", align = ui.ALIGN_E,
                tooltipTitle = _("Planets"),
                tooltip = _("Range of number of planets. About half of them is not colonizable at the beginning.")
                )
        ui.Label(self.win, layout = (0, 9, 4, 1), text = _("Radius:"), align = ui.ALIGN_W,
                tooltipTitle = _("Radius"),
                tooltip = _("Galaxy radius, implies speed of game.")
                )
        ui.Label(self.win, layout = (4, 9, 4.5, 1), id = "vRadius", align = ui.ALIGN_E,
                tooltipTitle = _("Radius"),
                tooltip = _("Galaxy radius, implies speed of game.")
                )
        ui.Label(self.win, layout = (0, 10, 4, 1), text = _("Grouping:"), align = ui.ALIGN_W,
                tooltipTitle = _("Grouping"),
                tooltip = _("How many starting positions are grouped together in vicinity.")
                )
        ui.Label(self.win, layout = (4, 10, 4.5, 1), id = "vPlayerGroup", align = ui.ALIGN_E,
                tooltipTitle = _("Grouping"),
                tooltip = _("How many starting positions are grouped together.")
                )

        ui.Label(self.win, layout = (0, 11.2, 4, 1), text = _("Resources:"), align = ui.ALIGN_W)
        ui.Text (self.win, layout = (4, 11.2, 23, 1.6), id = "vResources", editable = 0)
        ui.Label(self.win, layout = (0, 13, 4, 1), text = _("Challenges:"), align = ui.ALIGN_W)
        ui.Label(self.win, layout = (4, 13, 24, 1), id = "vChallenges", align = ui.ALIGN_W)

        ui.TitleButton(self.win, layout = (0, 14, 28, 1), text = _('Toggle booking'), action = 'onToggle')
        ui.Title(self.win, layout = (0, 15, 24, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (24, 15, 4, 1), text = _('Exit'), action = 'onCancel')
        self.win.statusBar = self.win.vStatusBar

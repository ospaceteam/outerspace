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

import ige
import ige.ospace.Const as Const
from osci import client
from osci import gdata
from PasswordDlg import PasswordDlg


class BookingDlg:
    """ There you subscribe to the new galaxy."""

    def __init__(self, app):
        self.app = app
        self.createUI()
        self.passwordDlg = PasswordDlg(app, hide = False)
        self.displayGoal = False
        self.displayPublic = True
        self.offering = client.cmdProxy.getBookingOffers()
        self.bookingInfo = client.cmdProxy.getBookingAnswers()
        self.selectionID = None

    def display(self, caller = None):
        self.selectionID = None
        self.caller = caller
        if self.show():
            self.win.show()

    def hide(self):
        self.win.hide()

    def show(self):
        self._setButtons()
        self._showMenu()
        self._showSelection()
        return True

    def _setButtons(self):
        self.win.vBookingPublic.visible = self.displayPublic
        self.win.vBookingPrivate.visible = not self.displayPublic
        self.win.vCreatePrivate.visible = self.displayPublic
        self.win.vDeletePrivate.visible = not self.displayPublic
        if self.displayPublic:
            self.win.vPublicToggle.text = _("Show private bookings")
        else:
            self.win.vPublicToggle.text = _("Show public bookings")
        if self.selectionID:
            book = self.bookingInfo[self.selectionID]
            scenario = self.offering[book.gal_type].scenario
            self.win.vCreatePrivate.enabled = scenario != Const.SCENARIO_SINGLE
            self.win.vDeletePrivate.enabled = book.owner_nick == client.account.nick
            self.win.vToggle.enabled = book.owner_nick != client.account.nick
        else:
            self.win.vCreatePrivate.enabled = False
            self.win.vDeletePrivate.enabled = False

    def _showMenu(self):
        itemsPublic = []
        itemsPrivate = []
        for bookID in self.bookingInfo:
            if bookID < Const.BID_FREESTART:
                continue
            book = self.bookingInfo[bookID]
            tPos = book.capacity
            tCur = book.bookings
            rawTime = book.last_creation
            tScenario = gdata.gameScenarios[self.offering[book.gal_type].scenario]
            isSelected = book.is_booked
            if rawTime:
                tTime = time.strftime(_("%m-%d-%y %H:%M"), time.localtime(rawTime))
            else:
                tTime = _('N/A')
            if isSelected:
                tChoice = '*'
            else:
                tChoice = ''
            item = ui.Item(book.gal_type, tPos = tPos, tCur = tCur, tTime = tTime,tChoice = tChoice, tScenario = tScenario, tOwner = book.owner_nick, tID = bookID)
            if book.owner_nick:
                itemsPrivate.append(item)
            else:
                itemsPublic.append(item)
        self.win.vBookingPublic.items = itemsPublic
        self.win.vBookingPublic.itemsChanged()
        self.win.vBookingPrivate.items = itemsPrivate
        self.win.vBookingPrivate.itemsChanged()

    def _showSelection(self):
        if self.selectionID:
            book = self.bookingInfo[self.selectionID]
            selection = self.offering[book.gal_type]
            self._displayText(book.gal_type, selection.scenario)
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

    def _displayText(self, gal_type, scenario):
        try:
            if self.displayGoal:
                self.win.vInfo.text = [gdata.gameScenarioDescriptions[scenario]]
            else:
                self.win.vInfo.text = [gdata.galaxyTypeDescriptions[gal_type]]
        except KeyError:
            # this shouldn't happen
            self.win.vInfo.text = [_("Description missing.")]

    def onSelect(self, widget, action, data):
        self.selectionID = data.tID
        self._setButtons()
        self._showSelection()

    def onToggleBooking(self, widget, action, data):
        if self.selectionID is None:
            self.win.setStatus(_('Select booking entry to toggle.'))
            return
        if self.displayPublic:
            self._onToggleBooking()
        else:
            self.passwordDlg.display(self._onToggleBooking)

    def _handleResult(self, result):
        triggerID = Const.BID_TRIGGERED
        if not triggerID in result or not result[triggerID]:
            # booking change is logged, no galaxy creation triggered
            self.bookingInfo = result
            self.show()
        else:
            # galaxy creation has been triggered
            self.hide()
            self.caller.display()
            self.caller.win.setStatus(_('New galaxy creation has been triggered.'))

    def _onToggleBooking(self, password = None):
        if self.selectionID:
            try:
                result = client.cmdProxy.toggleBooking(self.selectionID, password)
                self._handleResult(result)
            except ige.BookingMngrException:
                self.win.setStatus(_('Wrong password.'))

    def onPublicToggle(self, widget, action, data):
        self.selectionID = None
        self.displayPublic = not self.displayPublic
        self.show()

    def onGoalToggle(self, widget, action, data):
        self.displayGoal = not self.displayGoal
        if self.displayGoal:
            self.win.vGoalToggle.text = _("Show galaxy info")
        else:
            self.win.vGoalToggle.text = _("Show goal info")
        self.show()

    def onCreatePrivate(self, widget, action, data):
        if self.selectionID is None:
            self.win.setStatus(_('Select galaxy type to create private booking.'))
            return
        self.passwordDlg.display(self.onCreatePrivateConfirmed)

    def onCreatePrivateConfirmed(self, password):
        result = client.cmdProxy.createPrivateBooking(self.selectionID, password)
        self._handleResult(result)

    def onDeletePrivate(self, widget, action, data):
        if self.selectionID is None:
            self.win.setStatus(_('Select galaxy type to create private booking.'))
            return
        result = client.cmdProxy.deletePrivateBooking(self.selectionID)
        self.selectionID = None
        self._handleResult(result)

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
            rect = ui.Rect((w - 564) / 2, (h - 404) / 2, 564, 404),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True
        )
        ui.Listbox(self.win, layout = (0, 0, 28, 7), id = 'vBookingPublic',
                        sortedBy = ('text', 1),
                        columns = (
                                ('', 'tChoice', 1, ui.ALIGN_NONE),
                                (_('Galaxy type'), 'text', 6, ui.ALIGN_NONE),
                                (_('Scenario'), 'tScenario', 6, ui.ALIGN_NONE),
                                (_('Queue'), 'tCur', 3, ui.ALIGN_NONE),
                                (_('Capacity'), 'tPos', 3, ui.ALIGN_NONE),
                                (_('Last start'), 'tTime', 8, ui.ALIGN_E)
                                ),
                        columnLabels = 1,
                        action = 'onSelect',
                        )
        ui.Listbox(self.win, layout = (0, 0, 28, 7), id = 'vBookingPrivate',
                        sortedBy = ('tOwner', 1),
                        columns = (
                                ('', 'tChoice', 1, ui.ALIGN_NONE),
                                (_('Galaxy type'), 'text', 6, ui.ALIGN_NONE),
                                (_('Scenario'), 'tScenario', 6, ui.ALIGN_NONE),
                                (_('Queue'), 'tCur', 3, ui.ALIGN_NONE),
                                (_('Capacity'), 'tPos', 3, ui.ALIGN_NONE),
                                (_('Owner'), 'tOwner', 8, ui.ALIGN_E)
                                ),
                        columnLabels = 1,
                        action = 'onSelect',
                        )
        self.win.subscribeAction('*', self)

        ui.Button(self.win, layout = (0, 7, 8, 1), id = "vPublicToggle", text = _('Show personal bookings'), action = 'onPublicToggle',
            tooltipTitle = _("Booking types"),
            tooltip = _("Public Bookings\nPublic bookings are recommended way how to jump into new game.\nWhen queue is full, galaxy creation is triggered, and you can start adventure with group of strangers.\n\nPrivate Bookings\nPrivate bookings are the way to start game with group of your friends.\nEvery private booking requires password chosen by the owner.\nSingle player games cannot be privately booked (as they are private by definition).")
                )
        ui.Button(self.win, layout = (20, 7, 8, 1), id = "vCreatePrivate", text = _('Create private booking'), action = 'onCreatePrivate',
                tooltipTitle = _("Create Private Booking"),
                tooltip = _("Private bookings are way how to create games for group of friends.\n\
Every booking has to be created password protected, so you have to tell others\n\
what the password is.\n\n\
Account has limit of {0} private bookings at the time. Created galaxies\n\
no longers counts into the limit.".format(Const.BOOKING_PRIVATE_LIMIT))
                )

        ui.Button(self.win, layout = (20, 7, 8, 1), id = "vDeletePrivate", text = _('Delete private booking'), action = 'onDeletePrivate',
                tooltipTitle = _("Delete Private Booking"),
                tooltip = _("As the author of the booking, you can delete it at any time. No further warning will be issued.")
                )

        ui.Button(self.win, layout = (7, 8.5, 14, 1.5), id = "vToggle", text = _('Toggle booking'), action = 'onToggleBooking')
        scrollBarInfo = ui.Scrollbar(self.win, layout = (27, 10.3, 1, 4.7))
        textBox = ui.Text(self.win, layout = (9, 10.3, 18, 4.7), id = "vInfo", editable = 0)
        textBox.attachVScrollbar(scrollBarInfo)

        ui.Button(self.win, layout = (0.5, 10.5, 8, 1), id = "vGoalToggle", text = _('Display Goals'), action = 'onGoalToggle')
        ui.Label(self.win, layout = (0, 12, 4, 1), text = _("Planets:"), align = ui.ALIGN_W,
                tooltipTitle = _("Planets"),
                tooltip = _("Range of number of planets. About half of them is not colonizable at the beginning.")
                )
        ui.Label(self.win, layout = (4, 12, 4.5, 1), id = "vPlanets", align = ui.ALIGN_E,
                tooltipTitle = _("Planets"),
                tooltip = _("Range of number of planets. About half of them is not colonizable at the beginning.")
                )
        ui.Label(self.win, layout = (0, 13, 4, 1), text = _("Radius:"), align = ui.ALIGN_W,
                tooltipTitle = _("Radius"),
                tooltip = _("Galaxy radius, implies speed of game.")
                )
        ui.Label(self.win, layout = (4, 13, 4.5, 1), id = "vRadius", align = ui.ALIGN_E,
                tooltipTitle = _("Radius"),
                tooltip = _("Galaxy radius, implies speed of game.")
                )
        ui.Label(self.win, layout = (0, 14, 4, 1), text = _("Grouping:"), align = ui.ALIGN_W,
                tooltipTitle = _("Grouping"),
                tooltip = _("How many starting positions are grouped together in vicinity.")
                )
        ui.Label(self.win, layout = (4, 14, 4.5, 1), id = "vPlayerGroup", align = ui.ALIGN_E,
                tooltipTitle = _("Grouping"),
                tooltip = _("How many starting positions are grouped together.")
                )

        ui.Label(self.win, layout = (0, 15.2, 4, 1), text = _("Resources:"), align = ui.ALIGN_W)
        ui.Text (self.win, layout = (4, 15.2, 23, 1.6), id = "vResources", editable = 0)
        ui.Label(self.win, layout = (0, 17, 4, 1), text = _("Challenges:"), align = ui.ALIGN_W)
        ui.Label(self.win, layout = (4, 17, 24, 1), id = "vChallenges", align = ui.ALIGN_W)

        ui.Title(self.win, layout = (0, 18, 24, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (24, 18, 4, 1), text = _('Exit'), action = 'onCancel')
        self.win.statusBar = self.win.vStatusBar

#
#  Copyright 2001 - 2018 Ludek Smid [http://www.ospace.net/]
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

from osci import gdata

class PasswordDlg:

    def __init__(self, app, hide = True):
        self.app = app
        self.createUI()
        if hide:
            self.win.vPassword.showChar = '*'

    def display(self, confirmAction):
        self.confirmAction = confirmAction
        self.win.show()
        self.app.setFocus(self.win.vPassword)
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

    def onOK(self, widget, action, data):
        self.password = self.win.vPassword.text
        if not self.password:
            self.win.setStatus(_("Please enter password."))
            return
        self.hide()
        self.confirmAction(self.password)

    def onCancel(self, widget, action, data):
        self.password = ''
        self.hide()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _('Enter password'),
            rect = ui.Rect((w - 264) / 2, (h - 104) / 2, 264, 104),
            layoutManager = ui.SimpleGridLM(),
        )
        # creating dialog window
        self.win.subscribeAction('*', self)

        ui.Label(self.win,
            text = _("Password:"),
            align = ui.ALIGN_E,
            layout = (0, 1, 5, 1)
        )
        ui.Entry(self.win, id = 'vPassword',
            align = ui.ALIGN_W,
            layout = (5, 1, 5, 1),
        )
        ui.Title(self.win, layout = (0, 3, 3, 1))
        ui.TitleButton(self.win, layout = (3, 3, 5, 1), text = _("Cancel"), action = "onCancel")
        okBtn = ui.TitleButton(self.win, layout = (8, 3, 5, 1), text = _("OK"), action = 'onOK')
        self.win.acceptButton = okBtn

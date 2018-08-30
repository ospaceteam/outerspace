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
from osci import client, gdata, res
from ige import SecurityException

class ChangePasswordDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self, caller = None, message = None):
        self.caller = caller
        self.win.vOld.text = ""
        self.win.vNew.text = ""
        self.win.vConfirm.text = ""
        self.win.show()

    def hide(self):
        self.win.hide()

    def onChange(self, widget, action, data):
        oldPassword = self.win.vOld.text
        newPassword = self.win.vNew.text
        confirmPassword = self.win.vConfirm.text
        if newPassword != confirmPassword:
            self.win.vMessage.text = _("Passwords do not match.")
            self.win.vNew.text = ""
            self.win.vConfirm.text = ""
            return
        self.win.hide()
        try:
            client.cmdProxy.changePassword(oldPassword, newPassword)
        except SecurityException, e:
            # failed
            self.win.vMessage.text = _(e.args[0])
            self.win.show()
            return
        if self.caller:
            self.caller.display(message = _("The password has been changed."))

    def onCancel(self, widget, action, data):
        self.win.hide()
        if self.caller:
            self.caller.display()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            movable = 0,
            title = _('Change password'),
            rect = ui.Rect((w - 324) / 2, (h - 104) / 2, 324, 104),
            layoutManager = ui.SimpleGridLM(),
            tabChange = True
        )
        self.win.subscribeAction('*', self)
        ui.Label(self.win,
            text = _('Old password'),
            align = ui.ALIGN_E,
            layout = (0, 0, 6, 1)
        )
        ui.Entry(self.win, id = 'vOld',
            align = ui.ALIGN_W,
            showChar = '*',
            layout = (6, 0, 10, 1),
            orderNo = 1
        )
        ui.Label(self.win,
            text = _('New password'),
            align = ui.ALIGN_E,
            layout = (0, 1, 6, 1),
        )
        ui.Entry(self.win, id = 'vNew',
            align = ui.ALIGN_W,
            showChar = '*',
            layout = (6, 1, 10, 1),
            orderNo = 2
        )
        ui.Label(self.win,
            align = ui.ALIGN_E,
            text = _('Confirm'),
            layout = (0, 2, 6, 1),
        )
        ui.Entry(self.win, id = 'vConfirm',
            align = ui.ALIGN_W,
            layout = (6, 2, 10, 1),
            showChar = "*",
            orderNo = 3
        )
        ui.Title(self.win, layout = (0, 3, 8, 1), id = 'vMessage', align = ui.ALIGN_W)
        ui.TitleButton(self.win, layout = (8, 3, 4, 1), text = _('Cancel'), action = 'onCancel')
        ui.TitleButton(self.win, layout = (12, 3, 4, 1), text = _('Apply'), action = 'onChange')

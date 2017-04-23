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

import pygameui as ui, string
from osci import client, gdata, res
from ige import log
from ige.ospace.Const import *

class BuoyDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self, buoyText, buoyType, confirmAction = None):
        self.confirmAction = confirmAction
        self.win.vText.text = buoyText.split("\n")
        self.win.vAllied.checked = buoyType == BUOY_TO_ALLY
        self.win.vScanner.checked = buoyType == BUOY_TO_SCANNERSHARE
        self.win.show()
        self.app.setFocus(self.win.vText)
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
        self.win.show()

    def onOK(self, widget, action, data):
        self.buoyText = string.join(self.win.vText.text, "\n")
        if self.win.vAllied.checked:
            self.buoyType = BUOY_TO_ALLY
        elif self.win.vScanner.checked:
            self.buoyType = BUOY_TO_SCANNERSHARE
        else:
            self.buoyType = BUOY_PRIVATE
        self.hide()
        if self.confirmAction:
            self.confirmAction()

    def onCancel(self, widget, action, data):
        self.quantity = None
        self.hide()

    def turnOff(self, widget, action, data):
        if widget.data == "vAllied":
            self.win.vScanner.checked = 0
        if widget.data == "vScanner":
            self.win.vAllied.checked = 0

    def createUI(self):
        w, h = gdata.scrnSize
        cols = 22
        rows = 13
        width = cols * 20 + 4
        height = rows * 20 + 24
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _("Edit buoy"),
            rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
        )
        # creating dialog window
        self.win.subscribeAction('*', self)

        ui.Label(self.win,
            text = _("Buoy text:"),
            align = ui.ALIGN_W,
            layout = (0, 0, 4, 1)
        )
        ui.Label(self.win,
            text = _("Visible to:"),
            align = ui.ALIGN_W,
            layout = (6, 0, 4, 1)
        )
        ui.Check(self.win,
            text = _("Allies"),
            align = ui.ALIGN_W,
            layout = (10.5, 0, 4, 1),
            id = 'vAllied',
            action = "turnOff",
            data = "vAllied"
        )
        ui.Check(self.win,
            text = _("Scanner Share"),
            align = ui.ALIGN_W,
            layout = (15, 0, 6, 1),
            id = 'vScanner',
            action = "turnOff",
            data = "vScanner"
        )
        s = ui.Scrollbar(self.win, layout = (cols - 1, 1, 1, rows - 3))
        t = ui.Text(self.win, id = 'vText',
            align = ui.ALIGN_W,
            layout = (0, 1, cols - 1, rows - 2),
        )
        t.attachVScrollbar(s)

        ui.Title(self.win, layout = (0, rows - 1, cols - 10, 1))
        ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Cancel"), action = "onCancel")
        okBtn = ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("OK"), action = 'onOK')
        self.win.acceptButton = okBtn

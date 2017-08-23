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

from ConfirmDlg import ConfirmDlg
import pygameui as ui
import re
from osci import gdata, client

class GalaxyFinishDlg:
    def __init__(self, app):
        self.app = app
        self.confirmDlg = ConfirmDlg(self.app)
        self.createUI()

    def display(self, finishAction = None):
        # show window
        self.finishAction = finishAction
        if not self.win.visible:
            self.win.show()

    def update(self):
        if self.win.visible:
            self.show()

    def show(self):
        pass

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()

    def onFinish(self, widget, action, data):
        self.confirmDlg.display(_('Are you really really sure you want to finish this galaxy?'), _('No'),
            ('Yes'), cancelAction = self.onRealyFinish)

    def onRealyFinish(self):
        self.hide()
        if self.finishAction:
            self.finishAction(self.win.vMsg.text)

    def onClose(self, widget, action, data):
        self.hide()

    def createUI(self):
        screenWidth, screenHeight = gdata.scrnSize
        # size of dialog in layout metrics (for SimpleGridLM)
        cols = 25
        rows = 20
        # dialog width and height in pixels
        width = cols * 20 + 5
        height = rows * 20 + 4
        #creating dialog window
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _("Galaxy finish"),
            rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        # first row is window title
        rows -= 1

        ui.Label(self.win, layout = (0, 0, cols, 1), text = _("If you are sure to finish this galaxy, click on Finish button."), align = ui.ALIGN_W)
        ui.Label(self.win, layout = (0, 1, cols, 1), text = _("You can enter message visible in finish announcement below."), align = ui.ALIGN_W)

        s = ui.Scrollbar(self.win, layout = (cols - 1, 2, 1, rows - 3))
        t = ui.Text(self.win, layout = (0, 2, cols - 1, rows - 3), id = 'vMsg')
        t.attachVScrollbar(s)

        # dialog bottom line
        ui.Title(self.win, layout = (0, rows - 1, cols - 10, 1))
        ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Finish"), action = 'onFinish')
        ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Cancel"), action = 'onClose')

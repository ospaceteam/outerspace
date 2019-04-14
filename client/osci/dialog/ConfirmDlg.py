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
from osci import client, gdata, res

class ConfirmDlg:

    def __init__(self, app):
        self._agreement = None
        self.agreementNeeded = None
        self.app = app
        self.createUI()

    def display(self, message, okText, cancelText, confirmAction = None, cancelAction = None, agreementNeeded = False):
        self.win.vText.text = [message]
        self.win.vConfirm.text = okText
        if cancelText:
            self.win.vCancel.text = cancelText
            self.win.vCancel.enabled = True
        else:
            self.win.vCancel.text = ""
            self.win.vCancel.enabled = False
        self.agreementNeeded = agreementNeeded
        self.confirmAction = confirmAction
        self.cancelAction = cancelAction
        self.manageAgreement()
        self.win.show()

    def manageAgreement(self):
        if self.agreementNeeded:
            if self._agreement is None:
                self._agreement = False
            self.win.vAgree.enabled = True
            self.win.vAgree.visible = True
            self.win.vAgree.checked = False
        else:
            self.win.vAgree.enabled = False
            self.win.vAgree.visible = False
            self.win.vAgree.checked = True

    def hide(self):
        self.win.hide()

    def onAgree(self, widget, action, data):
        self._agreement = not self._agreement
        pass

    def onConfirm(self, widget, action, data):
        if not self.win.vAgree.checked:
            self.win.setStatus(_("You have to agree explicitly to proceed."))
            return
        self.hide()
        if self.confirmAction:
            self.confirmAction()

    def onCancel(self, widget, action, data):
        self.hide()
        if self.cancelAction:
            self.cancelAction()

    def setTitle(self, title):
        self.win.title = title

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            movable = 0,
            title = _('Question'),
            rect = ui.Rect((w - 424) / 2, (h - 124) / 2, 424, 124),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        ui.Text(self.win, layout = (5, 0, 16, 3), id = 'vText', background = self.win.app.theme.themeBackground, editable = 0)
        ui.Label(self.win, layout = (0, 0, 5, 4), icons = ((res.loginLogoImg, ui.ALIGN_W),))
        ui.Title(self.win, layout = (0, 4, 13, 1), id = 'vStatusBar', align = ui.ALIGN_W)
        ui.Check(self.win, layout = (17, 3, 4, 1), text = _('I agree'), id = 'vAgree', action = 'onAgree')
        ui.TitleButton(self.win, layout = (13, 4, 4, 1), id = 'vCancel', action = 'onCancel')
        ui.TitleButton(self.win, layout = (17, 4, 4, 1), id = 'vConfirm', action = 'onConfirm')

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
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
import ige.ospace.Const as Const
from ige import GameException

class LocateDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self, objID, caller):
        obj = client.get(objID, noUpdate = 1)
        self.caller = caller
        self.win.vStarMap.setPosition = 0
        self.win.vStarMap.control_modes['minimap'] = 0
        self.win.vStarMap.control_modes['hotbuttons'] = 0
        self.win.vStarMap.setPos(obj.x, obj.y)
        self.win.vStarMap.precompute()
        self.win.vStarMap.highlightPos = (obj.x, obj.y)
        self.show()
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
        self.win.vStarMap.precompute()

    def show(self):
        pass

    def onCancel(self, widget, action, data):
        self.hide()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
            modal = 1,
            escKeyClose = 1,
            movable = 0,
#            title = _('Redirect Fleets'),
            rect = ui.Rect(300 + (w - 800 - 4 * (w != 800)) / 2, 180 + (h - 600 - 4 * (h != 600)) / 2, 400 + 4 * (w != 800), 400 + 4 * (h != 600)),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        StarMapWidget(self.win, layout = (0, 0, 20, 19),
            id = 'vStarMap')

        ui.TitleButton(self.win, layout = (15, 19, 5, 1), text = _('Cancel'), action = 'onCancel')
        ui.Title(self.win, id = 'vStatusBar', layout = (0, 19, 15, 1), align = ui.ALIGN_W)

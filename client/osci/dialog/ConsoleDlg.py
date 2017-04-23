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

class ConsoleDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self):
        self.win.show()

    def hide(self):
        self.win.hide()

    def createUI(self):
        self.win = ui.Window(self.app,
            modal = 1,
            rect = ui.Rect(0, 20, 400, 600),
            layoutManager = ui.SimpleGridLM(),
        )

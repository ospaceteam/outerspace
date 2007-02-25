#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygameui as ui
import re
from osci import gdata, client
from ige.ospace.Const import *
from ige.ospace import Rules
import string, math, fnmatch

class SearchDlg:
	"""Displays Search for system dialog.

	"""
	def __init__(self, app):
		self.pattern = None
		self.founded = []
		self.app = app
		self.mapWidget = None
		self.createUI()

	def display(self):
		# show window
		if not self.win.visible:
			self.win.show()

	def update(self):
		if self.win.visible:
			self.show()

	def show(self):
		self.win.vSystemName.focus = 1

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()

	def onClose(self, widget, action, data):
		self.pattern = None
		self.founded = []
		self.hide()

	def onSearch(self, widget, action, data):
		self.pattern = string.lower(str(self.win.vSystemName.text))
		self.founded = []
		self.doSearch()

	def onNext(self, widget, action, data):
		if self.pattern and len(self.founded) > 0:
			self.doSearch()

	def doSearch(self):
		found = False
		for objID in client.db.keys():
			obj = client.get(objID, noUpdate = 1)
			if hasattr(obj, 'type') and obj.type in (T_SYSTEM, T_WORMHOLE):
				name = string.lower(getattr(obj, "name", ""))
				if len(name) > 0 and not name in self.founded and fnmatch.fnmatch(name, self.pattern):
					if hasattr(obj, "x") and hasattr(obj, "y") and self.mapWidget:
						self.mapWidget.highlightPos = (obj.x, obj.y)
						self.mapWidget.setPos(obj.x, obj.y)
						self.update()
					found = True
					self.founded.append(name)
					break
		if not found and self.mapWidget:
			self.mapWidget.highlightPos = None
			self.win.setStatus(_("No system found"))

	def createUI(self):
		screenWidth, screenHeight = gdata.scrnSize
		# size of dialog in layout metrics (for SimpleGridLM)
		cols = 20
		rows = 6
		# dialog width and height in pixels
		width = cols * 20 + 5
		height = rows * 20 + 4
		#creating dialog window
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Search for system"),
			rect = ui.Rect(10, 25, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# first row is window title
		rows -= 1

		ui.Label(self.win, layout = (0, 0, cols, 1), text = _("Use wildcard search as with files (*ese* finds Presere and Shesed)"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (0, 1, cols - 1, 1), text = _("* matches everything, ? matches any single character"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (0, 2, 6, 1), text = _("System name:"), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (6, 2, cols - 7, 1), id = "vSystemName", align = ui.ALIGN_W)

		# dialog bottom line
		ui.Title(self.win, layout = (0, rows - 1, cols - 15, 1))
		srchBtn = ui.TitleButton(self.win, layout = (cols - 15, rows - 1, 5, 1), text = _("Find"), action = 'onSearch', data = 1)
		ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Next"), action = 'onNext')
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Cancel"), action = 'onClose')
		self.win.acceptButton = srchBtn

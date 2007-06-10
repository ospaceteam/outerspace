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

class MapOverlayDlg:

	def __init__(self, app):
		self.app = app
		self.overlayMode = gdata.OVERLAY_OWNER
		self.lastOverlayMode = gdata.OVERLAY_OWNER
		self.mapWidget = None
		self.initCheck = False
		self.createUI()

	def display(self):
		if self.mapWidget:
			self.overlayMode = self.mapWidget.overlayMode
		if not self.initCheck:
			self.initCheck = True
			self.addChecks()
		if not self.win.visible:
			self.win.show()

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()

	def onClose(self, widget, action, data):
		self.hide()

	def onSelect(self, widget, action, data):
		if widget.checked: #only do this if it changed
			self.overlayMode = widget.data
			if self.mapWidget:
				self.mapWidget.overlayMode = self.overlayMode
				self.mapWidget.repaintMap = 1
			self.removeChecks()
		else:
			widget.checked = 1 #recheck it if they didn't change checks
		self.hide()

	def removeChecks(self):
		if gdata.OVERLAY_OWNER != self.overlayMode:
			self.win.vOVERLAY_OWNER.checked = 0
		if gdata.OVERLAY_DIPLO != self.overlayMode:
			self.win.vOVERLAY_DIPLO.checked = 0
		if gdata.OVERLAY_BIO != self.overlayMode:
			self.win.vOVERLAY_BIO.checked = 0
		if gdata.OVERLAY_FAME != self.overlayMode:
			self.win.vOVERLAY_FAME.checked = 0
		if gdata.OVERLAY_MIN != self.overlayMode:
			self.win.vOVERLAY_MIN.checked = 0
		if gdata.OVERLAY_SLOT != self.overlayMode:
			self.win.vOVERLAY_SLOT.checked = 0
		if gdata.OVERLAY_STARGATE != self.overlayMode:
			self.win.vOVERLAY_STARGATE.checked = 0
		if gdata.OVERLAY_DOCK != self.overlayMode:
			self.win.vOVERLAY_DOCK.checked = 0
		if gdata.OVERLAY_MORALE != self.overlayMode:
			self.win.vOVERLAY_MORALE.checked = 0

	def addChecks(self):
		if gdata.OVERLAY_OWNER == self.overlayMode:
			self.win.vOVERLAY_OWNER.checked = 1
		if gdata.OVERLAY_DIPLO == self.overlayMode:
			self.win.vOVERLAY_DIPLO.checked = 1
		if gdata.OVERLAY_BIO == self.overlayMode:
			self.win.vOVERLAY_BIO.checked = 1
		if gdata.OVERLAY_FAME == self.overlayMode:
			self.win.vOVERLAY_FAME.checked = 1
		if gdata.OVERLAY_MIN == self.overlayMode:
			self.win.vOVERLAY_MIN.checked = 1
		if gdata.OVERLAY_SLOT == self.overlayMode:
			self.win.vOVERLAY_SLOT.checked = 1
		if gdata.OVERLAY_STARGATE == self.overlayMode:
			self.win.vOVERLAY_STARGATE.checked = 1
		if gdata.OVERLAY_DOCK == self.overlayMode:
			self.win.vOVERLAY_DOCK.checked = 1
		if gdata.OVERLAY_MORALE == self.overlayMode:
			self.win.vOVERLAY_MORALE.checked = 1
		

	def createUI(self):
		w, h = gdata.scrnSize
		cols = 20
		rows = 10
		width = cols * 20 + 5
		height = rows * 20 + 4
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			title = _("Set Map Overlay:"),
			rect = ui.Rect(10, 25, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# overlay modes
		ui.Check(self.win, layout = (0, 0, 10, 1), id = "vOVERLAY_OWNER", text = _("Standard"),
			action = "onSelect", data = gdata.OVERLAY_OWNER)
		ui.Check(self.win, layout = (0, 1, 10, 1), id = "vOVERLAY_DIPLO", text = _("Diplomacy"),
			action = "onSelect", data = gdata.OVERLAY_DIPLO)
		ui.Check(self.win, layout = (0, 2, 10, 1), id = "vOVERLAY_BIO", text = _("Environment"),
			action = "onSelect", data = gdata.OVERLAY_BIO)
		ui.Check(self.win, layout = (0, 3, 10, 1), id = "vOVERLAY_MIN", text = _("Minerals"),
			action = "onSelect", data = gdata.OVERLAY_MIN)
		ui.Check(self.win, layout = (0, 4, 10, 1), id = "vOVERLAY_SLOT", text = _("Slots"),
			action = "onSelect", data = gdata.OVERLAY_SLOT)
		ui.Check(self.win, layout = (0, 5, 10, 1), id = "vOVERLAY_STARGATE", text = _("Fleet Acceleration"),
			action = "onSelect", data = gdata.OVERLAY_STARGATE)
		ui.Check(self.win, layout = (0, 6, 10, 1), id = "vOVERLAY_DOCK", text = _("Refuel and Upgrade"),
			action = "onSelect", data = gdata.OVERLAY_DOCK)
		ui.Check(self.win, layout = (0, 7, 10, 1), id = "vOVERLAY_MORALE", text = _("Morale"),
			action = "onSelect", data = gdata.OVERLAY_MORALE)
		ui.Check(self.win, layout = (0, 8, 10, 1), id = "vOVERLAY_FAME", text = _("Pirate Fame"),
			action = "onSelect", data = gdata.OVERLAY_FAME)
		
		ui.Title(self.win, layout = (0, rows - 1, cols - 15, 1))
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Close"), action = 'onClose')

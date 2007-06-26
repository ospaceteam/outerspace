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
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
from ige.ospace.Const import *
import ige

class RenameFleetDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, fleetID):
		self.fleetID = fleetID
		fleet = client.get(fleetID)
		if not hasattr(fleet,'customname'):
			return
		self.state = fleet.allowmerge
		if self.state == 0:
			self.win.vRetain.checked = 0
			self.win.vPrevent.checked = 1
		elif self.state == 2:
			self.win.vRetain.checked = 1
			self.win.vPrevent.checked = 0
		else:
			self.win.vRetain.checked = 0
			self.win.vPrevent.checked = 0
		if fleet.customname:
			self.win.vName.text = fleet.customname
		else:
			self.win.vName.text = ''
		self.win.show()
		self.app.setFocus(self.win.vName)
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
		pass

	def onRename(self, widget, action, data):
		# rename
		try:
			self.win.setStatus(_('Executing RENAME FLEET command...'))
			fleet = client.get(self.fleetID, noUpdate = 1)
			name = client.cmdProxy.renameFleet(self.fleetID, self.win.vName.text)
			state = client.cmdProxy.setMergeState(self.fleetID, self.state)
			fleet.customname = name
			fleet.allowmerge = state
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			for dialog in gdata.updateDlgs:
				dialog.update()
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))

	def onDelete(self, widget, action, data):
		try:
			self.win.setStatus(_('Executing DELETE CUSTOM FLEET NAME command...'))
			fleet = client.get(self.fleetID, noUpdate = 1)
			name = client.cmdProxy.removeFleetName(self.fleetID)
			state = client.cmdProxy.setMergeState(self.fleetID, 1) #reset to normal joins
			fleet.customname = None
			fleet.allowmerge = state
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			for dialog in gdata.updateDlgs:
				dialog.update()
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))

	def onCancel(self, widget, action, data):
		self.hide()

	def onSelect(self, widget, action, data):
		if widget.checked: #only do this if it is checked
			self.state = widget.data
			if self.state == 0:
				self.win.vRetain.checked = 0
			else:
				self.win.vPrevent.checked = 0
		else:
			self.state = 1

	def createUI(self):
		w, h = gdata.scrnSize
		cols = 15
		rows = 8
		width = cols * 20 + 5
		height = rows * 20 + 4
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Rename Fleet'),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# rename
		ui.Label(self.win, layout = (0, 0, 5, 1), text = _('Name'), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (5, 0, 10, 1), id = 'vName', align = ui.ALIGN_E)
		ui.Check(self.win, layout = (0, 1, 15, 1), id = "vRetain", text = _("Retain name during fleet joins"),
			action = "onSelect", data = 2)
		ui.Check(self.win, layout = (0, 2, 15, 1), id = "vPrevent", text = _("Prevent all fleet joins"),
			action = "onSelect", data = 0)
		ui.Label(self.win, layout = (0, 4, 15, 1), text = _(' Note: Retaining name will prevent two'), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (0, 5, 15, 1), text = _(' retain name fleets from joining.'), align = ui.ALIGN_W)
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (10, 6, 5, 1), text = _('Rename'), action = 'onRename')
		ui.TitleButton(self.win, layout = (5, 6, 5, 1), text = _('Delete Name'), action = 'onDelete')
		ui.TitleButton(self.win, layout = (0, 6, 5, 1), text = _('Cancel'), action = 'onCancel')
		#self.win.statusBar = self.win.vStatusBar

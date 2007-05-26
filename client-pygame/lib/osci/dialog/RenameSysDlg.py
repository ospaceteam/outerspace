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

class RenameSysDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, systemID):
		self.systemID = systemID
		self.show()
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

	def show(self):
		system = client.get(self.systemID, noUpdate = 1)
		self.win.vName.text = getattr(system, 'name', res.getUnknownName())
		items = [
			ui.Item(_('Alpha, Beta, ...'), tIndex = 1),
			ui.Item(_('I, II, III, ...'), tIndex = 2),
			ui.Item(_('Prime, Secundus, ...'), tIndex = 3),
			ui.Item(_('A, B, C, D, E, ...'), tIndex = 4),
			ui.Item(_('1, 2, 3, 4, 5, ...'), tIndex = 5),
		]
		self.win.vNumbers.items = items
		self.win.vNumbers.itemsChanged()

	def onClose(self, widget, action, data):
		if not self.win.vNumbers.selection:
			self.win.setStatus(_('Select planet numbering type, please.'))
			return
		item = self.win.vNumbers.selection[0]
		# rename
		try:
			self.win.setStatus(_('Executing RENAME SYSTEM command...'))
			system = client.get(self.systemID, noUpdate = 1)
			names = client.cmdProxy.rename(self.systemID, self.win.vName.text, item.tIndex)
			system.name = names[0]
			# update planets
			if hasattr(system, "planets"):
				index = 1
				for planetID in system.planets:
					client.get(planetID, noUpdate = 1).name = names[index]
					index += 1
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			for dialog in gdata.updateDlgs:
					dialog.update()
		except ige.GameException, e:
			self.win.setStatus(_(e.args[0]))

	def onCancel(self, widget, action, data):
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Rename system'),
			rect = ui.Rect((w - 404) / 2, (h - 164) / 2, 400 + 4, 164),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# rename
		ui.Title(self.win, layout = (0, 0, 10, 1), text = _('System name'),
			font = 'normal-bold', align = ui.ALIGN_W)
		ui.Label(self.win, layout = (0, 1, 5, 1), text = _('Name'), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (5, 1, 5, 1), id = 'vName', align = ui.ALIGN_E)
		ui.Title(self.win, layout = (10, 0, 10, 1), text = _('Planet numbering'),
			font = 'normal-bold', align = ui.ALIGN_W)
		ui.Listbox(self.win, layout = (10, 1, 10, 5), id = 'vNumbers', columnLabels = 0,
			columns = ((None, 'text', 0, ui.ALIGN_W),))
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (15, 6, 5, 1), text = _('Rename'), action = 'onClose')
		ui.TitleButton(self.win, layout = (10, 6, 5, 1), text = _('Cancel'), action = 'onCancel')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 6, 10, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar
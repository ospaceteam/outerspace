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
from ige import GameException

class FleetMassRedirectionDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.targetID = OID_NONE

	def display(self, systemID, caller):
		system = client.get(systemID, noUpdate = 1)
		self.caller = caller
		self.systemID = systemID
		self.win.vStarMap.currX = system.x
		self.win.vStarMap.currY = system.y
		self.win.vStarMap.setPosition = 0
		self.win.vStarMap.precompute()
		if self.targetID:
			target = client.get(self.targetID, noUpdate = 1)
			self.win.vStarMap.highlightPos = (target.x, target.y)
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

	def onSelectCommand(self, widget, action, data):
		self.command = widget.data
		self.showCommands()

	def onSelectMapObj(self, widget, action, data):
		target = client.get(data, noUpdate = 1)
		if target.type == T_PLANET:
			self.win.setStatus(_("Select systems, please."))
		elif target.type in (T_SYSTEM, T_WORMHOLE):
			self.targetID = target.oid
			self.win.vStarMap.highlightPos = (target.x, target.y)
			self.win.setStatus(_('Executing REDIRECT FLEETS command...'))
			player = client.getPlayer()
			if self.targetID == self.systemID:
				self.systemID = OID_NONE
			try:
				player.shipRedirections = client.cmdProxy.redirectShips(player.oid,
					self.targetID, self.systemID)
				self.win.setStatus(_('Command has been executed.'))
				self.win.vStarMap.precomputeRedirections(True)
			except GameException, e:
				self.win.setStatus(e.args[0])
		else:
			self.win.vStarMap.hightlightPos = None
		self.show()

	def onFinish(self, widget, action, data):
		gdata.mainGameDlg.update()
		self.caller.update()
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Mass Redirect Fleets to This System'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		StarMapWidget(self.win, layout = (0, 0, 40, 27),
			id = 'vStarMap', action = 'onSelectMapObj')
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Done'), action = 'onFinish')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

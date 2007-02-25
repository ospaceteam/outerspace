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
from osci import gdata, res, client, sequip
from ige.ospace.Const import *
from ige.ospace import *
from ige import GameException
from ConfirmDlg import ConfirmDlg

class ConstrUpgradeDlg:

	def __init__(self, app):
		self.app = app
		self.confirmDlg = ConfirmDlg(app)
		self.createUI()

	def display(self, designID, caller):
		self.designID = designID
		self.selected = None
		self.caller = caller
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
		self.show()

	def show(self):
		items = []
		player = client.getPlayer()
		origSpec = player.shipDesigns[self.designID]
		# count ships
		count = 0
		for fleetID in player.fleets:
			fleet = client.get(fleetID)
			for tmpDesignID, hp, shieldHP, exp in fleet.ships:
				if tmpDesignID == self.designID:
					count += 1
		# construct list
		selected = None
		for designID in player.shipDesigns:
			spec = player.shipDesigns[designID]
			if origSpec.combatClass != spec.combatClass:
				continue
			if spec.upgradeTo:
				continue
			if designID == self.designID:
				continue
			diff = max(
				Rules.shipMinUpgrade,
				int((spec.buildProd - origSpec.buildProd) * Rules.shipUpgradeMod),
			)
			item = ui.Item(
				spec.name,
				tDiff = diff,
				tTotal = diff * count,
				tDesignID = designID,
			)
			if designID == self.selected:
				selected = item
			items.append(item)
		self.win.vList.items = items
		self.win.vList.itemsChanged()
		self.win.vList.selectItem(selected)

	def onCancel(self, widget, action, data):
		self.hide()

	def onSelect(self, widget, action, data):
		if not self.win.vList.selection:
			self.win.setStatus(_("Select design to upgrade to"))
			return
		designID = self.win.vList.selection[0].tDesignID
		try:
			self.win.setStatus(_("Executing UPGRADE SHIP DESIGN command..."))
			player = client.getPlayer()
			player.shipDesigns, player.stratRes, tasksUpgraded = \
				client.cmdProxy.upgradeShipDesign(player.oid, self.designID, designID)
			self.win.setStatus(_('Command has been executed.'))
		except GameException, e:
			self.win.setStatus(e.args[0])
			return
		client.updateIDs(player.planets)
		self.caller.update()
		self.hide()
		if not tasksUpgraded:
			self.confirmDlg.display(_("Constructions queues on planets have not been updated, because new design uses different (amount of) strategic resources than old design. You have to fix them manually."), _("OK"), None)

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _('Select design to upgrade to'),
			rect = ui.Rect((w - 404) / 2, (h - 463) / 2, 404, 463),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# component list
		ui.Listbox(self.win, layout = (0, 0, 20, 21), id = "vList",
			columns = (
				(_('Name'), 'text', 11, ui.ALIGN_W),
				(_('Per ship'), 'tDiff', 4, ui.ALIGN_E),
				(_('Total'), 'tTotal', 4, ui.ALIGN_E),
			),
			columnLabels = 1
		)
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (15, 21, 5, 1), text = _('Select'), action = 'onSelect')
		ui.TitleButton(self.win, layout = (10, 21, 5, 1), text = _('Cancel'), action = 'onCancel')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 21, 10, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

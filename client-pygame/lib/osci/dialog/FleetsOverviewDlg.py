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
from ige.ospace import Rules
import math

class FleetsOverviewDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self):
		if gdata.config.defaults.showredirects != None:
			val = gdata.config.defaults.showredirects
			self.win.vRedirects.checked = val == 'yes'

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
		# get check box selections
		mine = self.win.vMine.checked
		enemy = self.win.vEnemy.checked
		unfriendly = self.win.vUnfriendy.checked
		neutral = self.win.vNeutral.checked
		friendly = self.win.vFriendly.checked
		allied = self.win.vAllied.checked
		redirects = self.win.vRedirects.checked

		player = client.getPlayer()
		#
		items = []
		for fleetID in client.db.keys():
			fleet = client.get(fleetID, noUpdate = 1)
			# skip non-fleets
			if not hasattr(fleet, "type") or (fleet.type != T_FLEET and fleet.type != T_ASTEROID):
				continue
			# shall be shown?
			fgColor = None

			ownerName = ""
			ownerNameTip = ""

			# check fleet color and if display fleet
			if hasattr(fleet, 'owner'):
				plRelation = client.getRelationTo(fleet.owner)
				fgColor = res.getPlayerColor(fleet.owner)
				ok = 0
				if mine and fleet.owner == player.oid:
					ok = 1
				elif enemy and plRelation >= REL_ENEMY_LO and plRelation < REL_ENEMY_HI:
					ok = 1
				elif unfriendly and plRelation >= REL_UNFRIENDLY_LO and plRelation < REL_UNFRIENDLY_HI:
					ok = 1
				elif neutral and plRelation >= REL_NEUTRAL_LO and plRelation < REL_NEUTRAL_HI:
					ok = 1
				elif friendly and plRelation >= REL_FRIENDLY_LO and plRelation < REL_FRIENDLY_HI:
					ok = 1
				elif allied and plRelation >= REL_ALLY_LO and plRelation < REL_ALLY_HI:
					ok = 1

				if not ok:
					continue

				if fleet.owner != player.oid:
					owner = getattr(client.get(fleet.owner, noUpdate = 1), "name", res.getUnknownName())
					ownerName = " (%s)" % owner
					ownerNameTip = owner
			else:
				# asteroids has no owner
				fgColor = res.getFFColorCode(0) #enemy
				if not enemy:
					continue

			# check position of fleet
			system = None
			systemName = "-"
			if hasattr(fleet, 'orbiting') and fleet.orbiting:
				system = client.get(fleet.orbiting, noUpdate = 1)
				systemName = getattr(system, "name", res.getUnknownName())
			elif hasattr(fleet, 'closeSystem'):
				system = client.get(fleet.closeSystem, noUpdate = 1)
				systemName = _("%s (dst)") % getattr(system, "name", res.getUnknownName())

			# get fleet current action and target of action
			order = "-"
			targetName = "-"
			if hasattr(fleet, 'actions'):
				if fleet.actionIndex < len(fleet.actions):
					action, target, data  = fleet.actions[fleet.actionIndex]
					if action == FLACTION_REDIRECT and not redirects:
						continue
					order = gdata.fleetActions[action]
					if target != OID_NONE:
						targetName = getattr(client.get(target, noUpdate = 1), 'name', res.getUnknownName())
						order = "%s %s" % (order, targetName)
			# eta
			if hasattr(fleet, "eta"): eta = res.formatTime(fleet.eta)
			else: eta = "?"

			# fuel
			if hasattr(fleet, "storEn"):
				if fleet.maxEn > 0: fuel = 100 * fleet.storEn / fleet.maxEn
				else: fuel = 0
			else:
				fuel = "?"

			# operational time
			if hasattr(fleet, 'storEn') and hasattr(fleet, 'operEn'):
				turns = 100000
				if fleet.operEn > 0: turns = fleet.storEn / fleet.operEn
				rawRange = turns * fleet.speed / Rules.turnsPerDay
				range = "%.2f" % rawRange
				opTime = res.formatTime(turns)
			else:
				rawRange = 0
				range = "?"
				opTime = "?"

			# last upgrade
			if hasattr(fleet, "lastUpgrade"):
				lastUpgrade = res.formatTime(fleet.lastUpgrade)
			else:
				lastUpgrade = "?"

			# create ListBox Item for fleet
			item = ui.Item(
				"%s %s" % (getattr(fleet, 'name', res.getUnknownName()), ownerName),
				tooltip = ownerNameTip,
				tLocation = systemName,
				tOrder = order,
				tMP = getattr(fleet, "combatPwr", "?"),
				tETA = eta,
				tETA_raw = getattr(fleet, "eta", 0),
				tSignature = getattr(fleet, "signature", "?"),
				tFuel = fuel,
				tOpTime = opTime,
				tRange = range,
				tRange_raw = rawRange,
				tLastUpgrade = lastUpgrade,
				tFleetID = fleetID,
				foreground = fgColor)
			items.append(item)

		self.win.vFleets.items = items
		self.win.vFleets.itemsChanged()

	def onSelectFleet(self, widget, action, data):
		item = self.win.vFleets.selection[0]
		fleet = client.get(item.tFleetID, noUpdate = 1)
		if hasattr(fleet, "owner") and fleet.owner == client.getPlayerID():
			# show dialog
			gdata.mainGameDlg.onSelectMapObj(None, None, item.tFleetID)
		else:
			# center fleet on map
			if hasattr(fleet, "x"):
				gdata.mainGameDlg.win.vStarMap.highlightPos = (fleet.x, fleet.y)
				gdata.mainGameDlg.win.vStarMap.setPos(fleet.x, fleet.y)
				self.hide()
				return
			self.win.setStatus(_("Cannot show location"))

	def onShowLocation(self, widget, action, data):
		item = self.win.vFleets.selection[0]
		fleet = client.get(item.tFleetID, noUpdate = 1)
		# center on map
		if hasattr(fleet, "x"):
			gdata.mainGameDlg.win.vStarMap.highlightPos = (fleet.x, fleet.y)
			gdata.mainGameDlg.win.vStarMap.setPos(fleet.x, fleet.y)
			self.hide()
			return
		self.win.setStatus(_("Cannot show location"))

	def onToggleCondition(self, widget, action, data):
		self.update()

	def onClose(self, widget, action, data):
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Fleets Overview'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# playets listbox
		ui.Listbox(self.win, layout = (0, 0, 40, 26), id = 'vFleets',
			columns = [
				(_('Fleet'), 'text', 5, ui.ALIGN_W),
				(_('Location'), 'tLocation', 6.5, ui.ALIGN_W),
				(_('Current order'), 'tOrder', 7, ui.ALIGN_W),
				(_('ETA'), 'tETA', 3, ui.ALIGN_E),
				(_('Fuel %'), 'tFuel', 3, ui.ALIGN_E),
				(_('Op. time'), 'tOpTime', 3, ui.ALIGN_E),
				(_('Range'), 'tRange', 3, ui.ALIGN_E),
				(_('MP'), 'tMP', 3, ui.ALIGN_E),
				(_('Sign'), 'tSignature', 2, ui.ALIGN_E),
				(_("Last upgr."), "tLastUpgrade", 3.5, ui.ALIGN_E),
			],
			columnLabels = 1, action = 'onSelectFleet', rmbAction = "onShowLocation")

		ui.Check(self.win, layout = (0, 26, 5, 1), text = _('Mine'), id = "vMine",
			checked = 1, action = "onToggleCondition")
		ui.Check(self.win, layout = (5, 26, 5, 1), text = _('Enemy'), id = "vEnemy",
			checked = 0, action = "onToggleCondition")
		ui.Check(self.win, layout = (10, 26, 5, 1), text = _('Unfriendly'), id = "vUnfriendy",
			checked = 0, action = "onToggleCondition")
		ui.Check(self.win, layout = (15, 26, 5, 1), text = _('Neutral'), id = "vNeutral",
			checked = 0, action = "onToggleCondition")
		ui.Check(self.win, layout = (20, 26, 5, 1), text = _('Friendly'), id = "vFriendly",
			checked = 0, action = "onToggleCondition")
		ui.Check(self.win, layout = (25, 26, 5, 1), text = _('Allied'), id = "vAllied",
			checked = 0, action = "onToggleCondition")
		ui.Check(self.win, layout = (34, 26, 6, 1), text = _('Show redirects'), id = "vRedirects",
			checked = 0, action = "onToggleCondition")
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

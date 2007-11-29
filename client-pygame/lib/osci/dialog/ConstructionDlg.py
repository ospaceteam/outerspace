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
from ige.ospace import ShipUtils, Rules
from ConstrSelTechDlg import ConstrSelTechDlg
from ConstrUpgradeDlg import ConstrUpgradeDlg
from ConfirmDlg import ConfirmDlg
from ige import GameException

class ConstructionDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.selTechDlg = ConstrSelTechDlg(app)
		self.upgradeDlg = ConstrUpgradeDlg(app)
		self.confirmDlg = ConfirmDlg(app)
		self.selectedDesignID = None

	def display(self):
		self.hullID = OID_NONE
		self.ctrlID = OID_NONE
		self.eqIDs = {}
		self.selectedEqID = None
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
		player = client.getPlayer()
		# check if selected ship design exists
		if self.selectedDesignID not in player.shipDesigns:
			self.selectedDesignID = None
		# designs
		items = []
		selected = None
		items = []
		for designID in player.shipDesigns:
			spec = player.shipDesigns[designID]
			# number of ships with this design in fleet
			countInService = 0
			for fleetID in player.fleets:
				fleet = client.get(fleetID)
				for tmpDesignID, hp, shieldHP, exp in fleet.ships:
					if tmpDesignID == designID:
						countInService += 1
			hullTech = client.getFullTechInfo(spec.hullID)
			# number of ships in build queue
			countInBuild = 0
			for planetID in client.db.keys():
				planet = client.get(planetID, noUpdate = 1)
				# skip non-planets
				if not hasattr(planet, "type") or planet.type != T_PLANET \
					or not hasattr(planet, 'owner') or not planet.owner == player.oid \
					or not planet.prodQueue:
					continue
				for task in planet.prodQueue:
					if task.isShip and task.techID == designID:
						countInBuild += task.quantity
			# ui list item
			item = ui.Item(spec.name, tDesignID = designID,
				tClass = "%s/%s%d" % (
					_(gdata.shipClasses[spec.combatClass][:1].upper()),_("TL"),
					hullTech.level,
				),
				tNumber = countInService,
				tInBuild = countInBuild
			)
			if spec.upgradeTo:
				item.foreground = gdata.sevColors[gdata.NONE]
			if designID == self.selectedDesignID:
				selected = item
			items.append(item)
		self.win.vDesigns.items = items
		self.win.vDesigns.itemsChanged()
		self.win.vDesigns.selectItem(selected)
		# compute
		if self.selectedDesignID == None:
			if self.ctrlID:
				eqIDs = {self.ctrlID : 1}
			else:
				eqIDs = {}
			for eqID in self.eqIDs:
				eqIDs[eqID] = self.eqIDs[eqID]
			improvements = []
			self.win.vUpgrade.enabled = 0
			self.win.vUpgrade.text = _("Upgrade")
			self.win.vScrap.enabled = 0
			self.win.vConstruct.enabled = 1
		else:
			spec = player.shipDesigns[self.selectedDesignID]
			self.hullID = spec.hullID
			eqIDs = spec.eqIDs
			improvements = spec.improvements
			self.win.vName.text = spec.name
			self.win.vHull.text = client.getTechInfo(self.hullID).name
			self.eqIDs = {}
			for eqID in eqIDs:
				tech = client.getTechInfo(eqID)
				if tech.subtype == "seq_ctrl":
					self.ctrlID = eqID
					self.win.vCtrl.text = tech.name
				else:
					self.eqIDs[eqID] = eqIDs[eqID]
			if player.shipDesigns[self.selectedDesignID].upgradeTo == 0:
				self.win.vUpgrade.enabled = 1
				self.win.vUpgrade.text = _("Upgrade")
			else:
				self.win.vUpgrade.enabled = 1
				self.win.vUpgrade.text = _("Cancel Upgrd")
			self.win.vScrap.enabled = 1
			self.win.vConstruct.enabled = 0
		try:
			result = ShipUtils.makeShipFullSpec(player, None, self.hullID, eqIDs, improvements)
		except GameException, e:
			self.win.setStatus(e.args[0])
			try:
				result = ShipUtils.makeShipFullSpec(player, None, self.hullID, eqIDs,
					improvements, raiseExs = False)
			except GameException:
				result = None
		else:
			self.win.setStatus(_("Ready."))
		# design info
		if self.hullID:
			tech = client.getTechInfo(self.hullID)
			self.win.vHull.text = tech.name # TODO _(tech.name)
		else:
			self.win.vHull.text = _("[Click to select]")
		if self.ctrlID:
			tech = client.getTechInfo(self.ctrlID)
			self.win.vCtrl.text = tech.name # TODO _(tech.name)
		else:
			self.win.vCtrl.text = _("[Click to select]")
		# equipments
		items = []
		selected = None
		for eqID in self.eqIDs:
			tech = client.getTechInfo(eqID)
			short = sequip.getShortDescr(eqID)
			long = sequip.getLongDescr(eqID)
			item = ui.Item(tech.name, techID = eqID, tNumber = self.eqIDs[eqID],
				tData = short, tooltip = long, statustip = long)
			if eqID == self.selectedEqID:
				selected = item
			items.append(item)
		self.win.vEquipment.items = items
		self.win.vEquipment.itemsChanged()
		self.win.vEquipment.selectItem(selected)
		# display computed attrs
		if result:
			hull = client.getTechInfo(result.hullID)
			self.win.vAClass.text = _(gdata.shipClasses[result.combatClass])
			self.win.vASignature.text = _("%d") % result.signature
			self.win.vASpeed.text = _("%.2f") % result.speed
			if result.shieldHP > 0:
				self.win.vAHP.text = _("%d - %d") % (result.maxHP, result.shieldHP)
			else:
				self.win.vAHP.text = _("%d") % result.maxHP
			self.win.vAAttack.text = _("%d") % result.combatAtt
			self.win.vADefence.text = _("%d / %d") % (result.combatDef, result.missileDef)
			if hasattr(hull, "maxWeight"):
				self.win.vAPayload.text = _("%d") % (hull.maxWeight - result.weight)
			else:
				self.win.vAPayload.text = _("N/A")
			if hasattr(hull, "slots"):
				self.win.vASlots.text = _("%d") % (hull.slots - result.slots)
			else:
				self.win.vASlots.text = _("N/A")
			self.win.vATanks.text = _("%d") % result.storEn
			self.win.vASupport.text = _("%d") % result.operEn
			if result.speed > 0:
				support = 10000000
				if result.operEn > 0: support = min(support, result.storEn / result.operEn)
				self.win.vARange.text = _("%.2f") % (support * result.speed / Rules.turnsPerDay)
			else:
				self.win.vARange.text = _("None")
			self.win.vACCPts.text = _("%d") % result.buildProd
			self.win.vACSup.text = _("%d") % (result.buildProd * Rules.operProdRatio)
			self.win.vABaseExp.text = _("%d") % result.baseExp
			self.win.vACombatPwr.text = _("%d") % result.combatPwr
			if self.selectedDesignID and player.shipDesigns[self.selectedDesignID].upgradeTo:
				self.win.vAUpgrade.text = player.shipDesigns[player.shipDesigns[self.selectedDesignID].upgradeTo].name
			else:
				self.win.vAUpgrade.text = _("N/A")
		else:
			self.win.vAClass.text = _("N/A")
			self.win.vASignature.text = _("N/A")
			self.win.vASpeed.text = _("N/A")
			self.win.vAHP.text = _("N/A")
			self.win.vAAttack.text = _("N/A")
			self.win.vADefence.text = _("N/A")
			self.win.vAPayload.text = _("N/A")
			self.win.vASlots.text = _("N/A")
			self.win.vATanks.text = _("N/A")
			self.win.vASupport.text = _("N/A")
			self.win.vARange.text = _("N/A")
			self.win.vACCPts.text = _("N/A")
			self.win.vACSup.text = _("N/A")
			self.win.vABaseExp.text = _("N/A")
			self.win.vACombatPwr.text = _("N/A")
			self.win.vAUpgrade.text = _("N/A")

	def onConstruct(self, widget, action, data):
		name = self.win.vName.text
		if not name:
			self.win.setStatus(_("Enter name of the design."))
			return
		# compute
		player = client.getPlayer()
		if self.ctrlID:
			eqIDs = {self.ctrlID: 1}
		else:
			eqIDs = {}
		for eqID in self.eqIDs:
			eqIDs[eqID] = self.eqIDs[eqID]
		try:
			self.win.setStatus(_("Executing ADD SHIP DESIGN command..."))
			player = client.getPlayer()
			player.shipDesigns, self.selectedDesignID = \
				client.cmdProxy.addShipDesign(player.oid, name, self.hullID, eqIDs)
			self.win.vDuplDesign.enabled = 1
			self.win.setStatus(_('Command has been executed.'))
		except GameException, e:
			self.win.setStatus(_(e.args[0]))
			return
		self.update()

	def onCancel(self, widget, action, data):
		self.hide()

	def onClose(self, widget, action, data):
		self.hide()

	def onSelectHull(self, widget, action, data):
		self.selTechDlg.display('isShipHull', [], self.onHullSelected, self.hullID, self.hullID)

	def onHullSelected(self, hullID):
		self.hullID = hullID
		self.show()

	def onSelectCtrl(self, widget, action, data):
		self.selTechDlg.display('isShipEquip', ["seq_ctrl"], self.onCtrlSelected, self.ctrlID, self.hullID)

	def onCtrlSelected(self, ctrlID):
		self.ctrlID = ctrlID
		self.show()

	def onAddEquipment(self, widget, action, data):
		self.selTechDlg.display('isShipEquip', ["seq_wpn", "seq_mod", "seq_struct",
			"seq_eng"], self.onEqSelected, hullID = self.hullID)

	def onEqSelected(self, eqID):
		self.eqIDs[eqID] = self.eqIDs.get(eqID, 0) + 1
		self.show()

	def onSelectDesign(self, widget, action, data):
		item = self.win.vDesigns.selection[0]
		self.selectedDesignID = item.tDesignID
		self.win.vDuplDesign.enabled = 1
		self.update()

	def onNewDesign(self, widget, action, data):
		self.selectedDesignID = None
		self.win.vDesigns.selectItem(None)
		self.hullID = OID_NONE
		self.ctrlID = OID_NONE
		self.eqIDs = {}
		self.win.vName.text = _(" ")
		self.win.vDuplDesign.enabled = 0
		self.update()

	def onDuplDesign(self, widget, action, data):
		self.selectedDesignID = None
		self.win.vDesigns.selectItem(None)
		self.win.vName.text = _(" ")
		self.win.vDuplDesign.enabled = 0
		self.update()

	def onEqSelectedInList(self, widget, action, data):
		self.selectedEqID = self.win.vEquipment.selection[0].techID

	def onChangeEquipmentQty(self, delta):
		if self.win.vEquipment.selection:
			item = self.win.vEquipment.selection[0]
			eqID = item.techID
			self.eqIDs[eqID] = self.eqIDs.get(eqID, 0) + delta
			self.update()

	def onIncrEquipment(self, widget, action, data):
		self.onChangeEquipmentQty(1)

	def onDecrEquipment(self, widget, action, data):
		self.onChangeEquipmentQty(-1)

	def onIncrEquipment5(self, widget, action, data):
		self.onChangeEquipmentQty(5)

	def onDecrEquipment5(self, widget, action, data):
		self.onChangeEquipmentQty(-5)

	def onIncrEquipment20(self, widget, action, data):
		self.onChangeEquipmentQty(20)

	def onDecrEquipment20(self, widget, action, data):
		self.onChangeEquipmentQty(-20)

	def onRemoveEquipment(self, widget, action, data):
		if self.win.vEquipment.selection:
			item = self.win.vEquipment.selection[0]
			eqID = item.techID
			del self.eqIDs[eqID]
			self.update()

	def onScrap(self, widget, action, data):
		# count number of ships using this design
		count = 0
		for fleetID in client.getPlayer().fleets:
			fleet = client.get(fleetID)
			for designID, hp, shieldHP, exp in fleet.ships:
				if designID == self.selectedDesignID:
					count += 1
		self.confirmDlg.display(_('Deletion of this design dismantle %d ship(s). Are you sure to scrap it?') % count, _('Yes'),
			_('No'), confirmAction = self.onScrapConfirmed)

	def onScrapConfirmed(self):
		self.win.vDuplDesign.enabled = 0
		try:
			self.win.setStatus(_("Executing SCRAP SHIP DESIGN command..."))
			player = client.getPlayer()
			oldFleets = player.fleets
			player.shipDesigns, player.fleets, player.stratRes = \
				client.cmdProxy.scrapShipDesign(player.oid, self.selectedDesignID)
			self.selectedDesignID = None
			self.win.setStatus(_('Command has been executed.'))
		except GameException, e:
			self.win.setStatus(_(e.args[0]))
			return
		# reread information about fleets and planets
		oldFleets.extend(player.planets)
		client.updateIDs(oldFleets)

		gdata.mainGameDlg.update()
		self.update()

	def onUpgrade(self, widget, action, data):
		player = client.getPlayer()
		if player.shipDesigns[self.selectedDesignID].upgradeTo == 0:
			# upgrade
			self.upgradeDlg.display(self.selectedDesignID, self)
		else:
			# cancel upgrade
			try:
				self.win.setStatus(_("Executing CANCEL UPGRADE SHIP DESIGN command..."))
				player.shipDesigns = \
					client.cmdProxy.cancelUpgradeShipDesign(player.oid, self.selectedDesignID)
				self.win.setStatus(_('Command has been executed.'))
			except GameException, e:
				self.win.setStatus(_(e.args[0]))
				return
			self.update()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Construction Centre'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# player listing
		ui.Title(self.win, layout = (0, 0, 15, 1), text = _('Ship Designs'),
			font = 'normal-bold', align = ui.ALIGN_W)
		ui.Listbox(self.win, layout = (0, 1, 15, 25), id = 'vDesigns',
			columns = (
				(_('#'), 'tNumber', 2, ui.ALIGN_E),
				(_('B'), 'tInBuild', 2, ui.ALIGN_E),
				(_('Name'), 'text', 8, ui.ALIGN_W),
				(_('Class'), 'tClass', 2, ui.ALIGN_W),
			),
			columnLabels = 1, action = "onSelectDesign",
		)
		ui.Button(self.win, layout = (0, 26, 7, 1), text = _("New design"),
			action = "onNewDesign")
		ui.Button(self.win, layout = (7, 26, 7, 1), text = _("Dupl. design"),
			action = "onDuplDesign", enabled = 0, id = "vDuplDesign")
		# current design
		ui.Title(self.win, layout = (15, 0, 25, 1), text = _('Design'),
			font = 'normal-bold', align = ui.ALIGN_W)
		# info
		ui.Label(self.win, layout = (15, 1, 5, 1), text = _("Name"),
			align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (20, 1, 10, 1), id = "vName",
			align = ui.ALIGN_E)
		ui.Label(self.win, layout = (15, 2, 5, 1), text = _("Hull type"),
			align = ui.ALIGN_W)
		ui.ActiveLabel(self.win, layout = (20, 2, 10, 1), id = "vHull",
			align = ui.ALIGN_E, action = "onSelectHull")
		ui.Label(self.win, layout = (15, 3, 5, 1), text = _("Control unit"),
			align = ui.ALIGN_W)
		ui.ActiveLabel(self.win, layout = (20, 3, 10, 1), id = "vCtrl",
			align = ui.ALIGN_E, action = "onSelectCtrl")
		ui.Title(self.win, layout = (15, 4, 15, 1), text = _('Equipment'),
			font = 'normal-bold', align = ui.ALIGN_W)
		ui.Listbox(self.win, layout = (15, 5, 15, 19), id = 'vEquipment',
			columns = (
				(_('#'), 'tNumber', 2, ui.ALIGN_E),
				(_('Name'), 'text', 8, ui.ALIGN_W),
				(_('Data'), 'tData', 4, ui.ALIGN_W),
			),
			columnLabels = 1, action = "onEqSelectedInList"
		)
		ui.Button(self.win, layout = (15, 24, 1.2, 1), text = _("++"),
			action = "onIncrEquipment5", rmbAction = "onIncrEquipment20")
		ui.Button(self.win, layout = (16.2, 24, 1.8, 1), text = _("+"),
			action = "onIncrEquipment")
		ui.Button(self.win, layout = (18, 24, 1.8, 1), text = _("-"),
			action = "onDecrEquipment")
		ui.Button(self.win, layout = (19.8, 24, 1.2, 1), text = _("--"),
			action = "onDecrEquipment5", rmbAction = "onDecrEquipment20")
		ui.Button(self.win, layout = (21, 24, 4.5, 1), text = _("Add"),
			action = "onAddEquipment")
		ui.Button(self.win, layout = (25.5, 24, 4.5, 1), text = _("Remove"),
			action = "onRemoveEquipment")
		# ship's attrs
		ui.Label(self.win, layout = (30, 1, 5, 1), text = _("Class"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 1, 5, 1), id = "vAClass", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 2, 5, 1), text = _("Signature"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 2, 5, 1), id = "vASignature", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 3, 5, 1), text = _("Speed"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 3, 5, 1), id = "vASpeed", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 4, 5, 1), text = _("HP"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 4, 5, 1), id = "vAHP", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 5, 5, 1), text = _("Base attack"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 5, 5, 1), id = "vAAttack", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 6, 5, 1), text = _("Base defence"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 6, 5, 1), id = "vADefence", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 7, 5, 1), text = _("Military power"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 7, 5, 1), id = "vACombatPwr", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 8, 5, 1), text = _("Base exp pts"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 8, 5, 1), id = "vABaseExp", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 10, 3, 1), text = _("Tanks"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (33, 10, 7, 1), id = "vATanks", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 11, 7, 1), text = _("Support (fuel)"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (37, 11, 3, 1), id = "vASupport", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 12, 7, 1), text = _("Support (const. pts)"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (37, 12, 3, 1), id = "vACSup", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 13, 5, 1), text = _("Max. range"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 13, 5, 1), id = "vARange", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 15, 5, 1), text = _("Unused payload"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 15, 5, 1), id = "vAPayload", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 16, 5, 1), text = _("Free slots"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 16, 5, 1), id = "vASlots", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 18, 5, 1), text = _("Constr. pts"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 18, 5, 1), id = "vACCPts", align = ui.ALIGN_E)
		ui.Label(self.win, layout = (30, 20, 5, 1), text = _("Upgrade to"), align = ui.ALIGN_W)
		ui.Label(self.win, layout = (35, 20, 5, 1), id = "vAUpgrade", align = ui.ALIGN_E)
		# actions
		ui.Title(self.win, layout = (15, 25, 25, 1), text = _('Design Actions'),
			font = 'normal-bold', align = ui.ALIGN_W)
		ui.Button(self.win, layout = (15, 26, 5, 1), text = _("Upgrade"),
			id = "vUpgrade", action = "onUpgrade")
		ui.Button(self.win, layout = (20, 26, 5, 1), text = _("Scrap"),
			id = "vScrap", action = "onScrap")
		ui.Button(self.win, layout = (35, 26, 5, 1), text = _("Construct"),
			id = "vConstruct", action = "onConstruct")
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

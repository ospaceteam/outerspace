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
from ige import GameException
import math

class FleetSpecsDlg:

	def __init__(self, app):
		self.app = app
		self.fleetID = OID_NONE
		self.designID = OID_NONE
		self.showInheritance = 0
		self.showOnlyShieldPiercing = 0 #todo - add button and calculation system
		self.showMaxHPs = 0
		self.setDefaults()
		self.createUI()

	def setDefaults(self):
		self.sm_min = {0:0,1:0,2:0,3:0}
		self.sm_max = {0:0,1:0,2:0,3:0}
		self.sm = {'num':0,'hp':0,'sh':0,'catt':0,'cdef':0,'mdef':0}
		self.med_min = {0:0,1:0,2:0,3:0}
		self.med_max = {0:0,1:0,2:0,3:0}
		self.med = {'num':0,'hp':0,'sh':0,'catt':0,'cdef':0,'mdef':0}
		self.lg_min = {0:0,1:0,2:0,3:0}
		self.lg_max = {0:0,1:0,2:0,3:0}
		self.lg = {'num':0,'hp':0,'sh':0,'catt':0,'cdef':0,'mdef':0}

	def displayDesign(self, designID):
		#todo - make used somewhere
		self.setDefaults()
		self.fleetID = OID_NONE
		self.designID = designID
		self.win.title = _('Design Details')
		self.calcDesign(self.designID)
		self.show()
		# show window
		if not self.win.visible:
			self.win.show()
		# register for updates
		if self not in gdata.updateDlgs:
			gdata.updateDlgs.append(self)

	def displayFleet(self, fleetID):
		self.setDefaults()
		self.designID = OID_NONE
		self.fleetID = fleetID
		self.fleet = client.get(fleetID, noUpdate = 1)
		self.win.title = _('Fleet Details: %s') % getattr(self.fleet, 'name', res.getUnknownName())
		if not hasattr(self.fleet, "ships"):
			return
		self.calcFleet(self.fleet)
		self.show()
		# show window
		if not self.win.visible:
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
		self.setDefaults()
		if self.fleetID != OID_NONE: #MaxHPs or Shield Piercing flag might have changed, so recalc fleet
			self.calcFleet(self.fleet)
		elif self.designID != OID_NONE:
			self.calcDesign(self.designID)
		self.show()

	def calcDesign(self,designID,count=1,addHP=True):
		player = client.getPlayer()
		spec = player.shipDesigns[designID]
		size = spec.combatClass
		eqIDs = spec.weaponIDs #equipment list
		for eqID in eqIDs:
			tech = client.getFullTechInfo(eqID)
			if tech.subtype == "seq_wpn":
				try:
					level = player.techs[eqID]
				except:
					level = 1 #tech not researched
				improvement = Rules.techImprEff[level]
				dmgMin = tech.weaponDmgMin * tech.weaponROF
				dmgMax = tech.weaponDmgMax * tech.weaponROF
				weaponclass = tech.weaponClass
				if self.showOnlyShieldPiercing and not tech.weaponIgnoreShield:
					continue
				if size==0:
					self.sm_min[weaponclass] += int(count * dmgMin * improvement)
					self.sm_max[weaponclass] += int(count * dmgMax * improvement)
				elif size==1:
					self.med_min[weaponclass] += int(count * dmgMin * improvement)
					self.med_max[weaponclass] += int(count * dmgMax * improvement)
				elif size==2:
					self.lg_min[weaponclass] += int(count * dmgMin * improvement)
					self.lg_max[weaponclass] += int(count * dmgMax * improvement)
		if addHP:
			if size==0:
				self.sm['num'] += count
				self.sm['hp'] += spec.maxHP*count
				self.sm['sh'] += spec.shieldHP*count
			elif size==1:
				self.med['num'] += count
				self.med['hp'] += spec.maxHP*count
				self.med['sh'] += spec.shieldHP*count
			elif size==2:
				self.lg['num'] += count
				self.lg['hp'] += spec.maxHP*count
				self.lg['sh'] += spec.shieldHP*count
		if size==0:
			self.sm['catt'] += spec.combatAtt*count
			self.sm['cdef'] += spec.combatDef*count
			self.sm['mdef'] += spec.missileDef*count
		elif size==1:
			self.med['catt'] += spec.combatAtt*count
			self.med['cdef'] += spec.combatDef*count
			self.med['mdef'] += spec.missileDef*count
		elif size==2:
			self.lg['catt'] += spec.combatAtt*count
			self.lg['cdef'] += spec.combatDef*count
			self.lg['mdef'] += spec.missileDef*count
		return size

	def calcFleet(self,fleet):
		if hasattr(fleet, 'ships'):
			designs = {}
			designHPs = {}
			designSHs = {}
			for designID, hp, shield, exp in fleet.ships:
				if designID in designs:
					designs[designID] += 1
					designHPs[designID] += hp
					designSHs[designID] += shield
				else:
					designs[designID] = 1
					designHPs[designID] = hp
					designSHs[designID] = shield
                        for designID in designs.keys():
				size = self.calcDesign(designID,designs[designID],self.showMaxHPs)
				if not self.showMaxHPs:
					if size==0:
						self.sm['num'] += designs[designID]
						self.sm['hp'] += designHPs[designID]
						self.sm['sh'] += designSHs[designID]
					elif size==1:
						self.med['num'] += designs[designID]
						self.med['hp'] += designHPs[designID]
						self.med['sh'] += designSHs[designID]
					elif size==2:
						self.lg['num'] += designs[designID]
						self.lg['hp'] += designHPs[designID]
						self.lg['sh'] += designSHs[designID]

	def show(self):
		items= []
		if self.showInheritance:
			items.append(ui.Item(_("Dmg vs Small (min)"), tSm = self.sm_min[0], tMed = self.med_min[0], tLg = self.lg_min[0]))
			items.append(ui.Item(_("Dmg vs Small (max)"), tSm = self.sm_max[0], tMed = self.med_max[0], tLg = self.lg_max[0]))
			items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
			items.append(ui.Item(_("Dmg vs Medium (min)"), tSm = int(self.sm_min[1]+self.sm_min[0]*Rules.weaponDmgDegrade[1]),
				tMed = int(self.med_min[1]+self.med_min[0]*Rules.weaponDmgDegrade[1]),
				tLg = int(self.lg_min[1]+self.lg_min[0]*Rules.weaponDmgDegrade[1])))
			items.append(ui.Item(_("Dmg vs Medium (max)"), tSm = int(self.sm_max[1]+self.sm_max[0]*Rules.weaponDmgDegrade[1]),
				tMed = int(self.med_max[1]+self.med_max[0]*Rules.weaponDmgDegrade[1]),
				tLg = int(self.lg_max[1]+self.lg_max[0]*Rules.weaponDmgDegrade[1])))
			items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
			items.append(ui.Item(_("Dmg vs Large (min)"), tSm = int(self.sm_min[2]+self.sm_min[1]*Rules.weaponDmgDegrade[1]+self.sm_min[0]*Rules.weaponDmgDegrade[2]),
				tMed = int(self.med_min[2]+self.med_min[1]*Rules.weaponDmgDegrade[1]+self.med_min[0]*Rules.weaponDmgDegrade[2]),
				tLg = int(self.lg_min[2]+self.lg_min[1]*Rules.weaponDmgDegrade[1]+self.lg_min[0]*Rules.weaponDmgDegrade[2])))
			items.append(ui.Item(_("Dmg vs Large (max)"), tSm = int(self.sm_max[2]+self.sm_max[1]*Rules.weaponDmgDegrade[1]+self.sm_max[0]*Rules.weaponDmgDegrade[2]),
				tMed = int(self.med_max[2]+self.med_max[1]*Rules.weaponDmgDegrade[1]+self.med_max[0]*Rules.weaponDmgDegrade[2]),
				tLg = int(self.lg_max[2]+self.lg_max[1]*Rules.weaponDmgDegrade[1]+self.lg_max[0]*Rules.weaponDmgDegrade[2])))
			items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
			items.append(ui.Item(_("Dmg vs Planet (min)"), tSm = int(self.sm_min[3]+self.sm_min[2]*Rules.weaponDmgDegrade[1]+self.sm_min[1]*Rules.weaponDmgDegrade[2]+self.sm_min[0]*Rules.weaponDmgDegrade[3]),
				tMed = int(self.med_min[3]+self.med_min[2]*Rules.weaponDmgDegrade[1]+self.med_min[1]*Rules.weaponDmgDegrade[2]+self.med_min[0]*Rules.weaponDmgDegrade[3]),
				tLg = int(self.lg_min[3]+self.lg_min[2]*Rules.weaponDmgDegrade[1]+self.lg_min[1]*Rules.weaponDmgDegrade[2]+self.lg_min[0]*Rules.weaponDmgDegrade[3])))
			items.append(ui.Item(_("Dmg vs Planet (max)"), tSm = int(self.sm_max[3]+self.sm_max[2]*Rules.weaponDmgDegrade[1]+self.sm_max[1]*Rules.weaponDmgDegrade[2]+self.sm_max[0]*Rules.weaponDmgDegrade[3]),
				tMed = int(self.med_max[3]+self.med_max[2]*Rules.weaponDmgDegrade[1]+self.med_max[1]*Rules.weaponDmgDegrade[2]+self.med_max[0]*Rules.weaponDmgDegrade[3]),
				tLg = int(self.lg_max[3]+self.lg_max[2]*Rules.weaponDmgDegrade[1]+self.lg_max[1]*Rules.weaponDmgDegrade[2]+self.lg_max[0]*Rules.weaponDmgDegrade[3])))
		else:
			items.append(ui.Item(_("Dmg vs Small (min)"), tSm = self.sm_min[0], tMed = self.med_min[0], tLg = self.lg_min[0]))
			items.append(ui.Item(_("Dmg vs Small (max)"), tSm = self.sm_max[0], tMed = self.med_max[0], tLg = self.lg_max[0]))
			items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
			items.append(ui.Item(_("Dmg vs Medium (min)"), tSm = self.sm_min[1], tMed = self.med_min[1], tLg = self.lg_min[1]))
			items.append(ui.Item(_("Dmg vs Medium (max)"), tSm = self.sm_max[1], tMed = self.med_max[1], tLg = self.lg_max[1]))
			items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
			items.append(ui.Item(_("Dmg vs Large (min)"), tSm = self.sm_min[2], tMed = self.med_min[2], tLg = self.lg_min[2]))
			items.append(ui.Item(_("Dmg vs Large (max)"), tSm = self.sm_max[2], tMed = self.med_max[2], tLg = self.lg_max[2]))
			items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
			items.append(ui.Item(_("Dmg vs Planet (min)"), tSm = self.sm_min[3], tMed = self.med_min[3], tLg = self.lg_min[3]))
			items.append(ui.Item(_("Dmg vs Planet (max)"), tSm = self.sm_max[3], tMed = self.med_max[3], tLg = self.lg_max[3]))
		items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
		items.append(ui.Item(_("Total Ships"), tSm = self.sm['num'], tMed = self.med['num'], tLg = self.lg['num']))
		items.append(ui.Item(_("Total HPs"), tSm = self.sm['hp'], tMed = self.med['hp'], tLg = self.lg['hp']))
		items.append(ui.Item(_("Total Shields"), tSm = self.sm['sh'], tMed = self.med['sh'], tLg = self.lg['sh']))
		items.append(ui.Item(_(" "), tSm = '', tMed = '', tLg = ''))
		smnum = max(self.sm['num'],1)
		mednum = max(self.med['num'],1)
		lgnum = max(self.lg['num'],1)
		items.append(ui.Item(_("Average ATT"), tSm = round(1.0*self.sm['catt']/smnum,1), tMed = round(1.0*self.med['catt']/mednum,1), tLg = round(1.0*self.lg['catt']/lgnum,1)))
		items.append(ui.Item(_("Average DEF"), tSm = round(1.0*self.sm['cdef']/smnum,1), tMed = round(1.0*self.med['cdef']/mednum,1), tLg = round(1.0*self.lg['cdef']/lgnum,1)))
		items.append(ui.Item(_("Average Missile DEF"), tSm = round(1.0*self.sm['mdef']/smnum,1), tMed = round(1.0*self.med['mdef']/mednum,1), tLg = round(1.0*self.lg['mdef']/lgnum,1)))
		self.win.vClassData.items = items
		self.win.vClassData.itemsChanged()

	def onToggleCondition(self, widget, action, data):
		setattr(self, widget.data, not getattr(self, widget.data))
		self.update()

	def onClose(self, widget, action, data):
		self.hide()

	def createUI(self):
		screenWidth, screenHeight = gdata.scrnSize
		# size of dialog in layout metrics (for SimpleGridLM)
		cols = 20
		rows = 24
		# dialog width and height in pixels
		width = cols * 20 + 5
		height = rows * 20 + 4
		#creating dialog window
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Fleet Details"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# playets listbox
		ui.Listbox(self.win, layout = (0, 0, cols, rows-3), id = 'vClassData',
			columns = [(_('Class'), 'text', 8, ui.ALIGN_W),
			(_('Small'), 'tSm', 4, ui.ALIGN_E),
			(_('Medium'), 'tMed', 4, ui.ALIGN_E),
			(_('Large'), 'tLg', 4, ui.ALIGN_E)],
			columnLabels = 1, sortable = 0)
		ui.Button(self.win, layout = (0, rows-3, 10, 1), text = _('Use Dmg Inheritance'), id = "vInherit",
			toggle = 1,	action = "onToggleCondition", data = "showInheritance")
		ui.Button(self.win, layout = (10, rows-3, 10, 1), text = _('Use Max HPs'), id = "vMaxHP",
			toggle = 1,	action = "onToggleCondition", data = "showMaxHPs")
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (cols-5, rows-2, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, rows-2, cols-5, 1), align = ui.ALIGN_W)
		#self.win.statusBar = self.win.vStatusBar

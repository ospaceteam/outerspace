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
from osci import client, res, gdata
from ige.ospace.Const import *
from ige.ospace import Rules, Utils, TechHandlers
from TechInfoDlg import TechInfoDlg
from ConfirmDlg import ConfirmDlg
import ige

class ResearchDlg:

	def __init__(self, app):
		self.app = app
		self.techInfoDlg = TechInfoDlg(app)
		self.confirmDlg = ConfirmDlg(app)
		self.showCompleted = 0
		self.createUI()

	def display(self):
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
		if self.win.visible:
			self.show()

	def show(self):
		player = client.getPlayer()
		# title
		self.win.vRQueueTitle.text = _('Research queue [%d pts/turn]') % (
			player.effSciPoints,
		)
		self.win.title = _("Research [TL%d]") % player.techLevel
		# Known techs
		items = []
		#~researchable = {}
		disabled = []
		taskIDs = {}
		for task in player.rsrchQueue:
			taskIDs[task.techID] = None
		for techID in player.techs.keys():
			tech = client.getTechInfo(techID)
			improvement = player.techs[techID]
			item = ui.Item(tech.name,
				techID = techID,
				tLevel = '%d-%d' % (tech.level, improvement),
				tStruct = (' ', '*')[tech.isStructure],
				tShip = (' ', '*')[tech.isShipEquip],
			)
			if improvement < Rules.techMaxImprovement and improvement < tech.maxImprovement:
				neededSci = Utils.getTechRCost(player, techID)
				if player.effSciPoints > 0:
					item.tETC = res.formatTime(float(neededSci) / player.effSciPoints)
				else:
					item.tETC = _("N/A")
				found = 0
				if taskIDs.has_key(techID):
					item.foreground = (0xd0, 0xd0, 0xd0)
				else:
					item.foreground = None
			else:
				item.tETC = res.getNA()
				item.foreground = (0x80, 0x80, 0x80)
				if not self.showCompleted:
					# skip this item
					continue
			items.append(item)
			disabled.extend(tech.researchDisables)
			#~for improvement in range(1, improvement + 1):
			#~	for techID in tech.researchEnables[improvement]:
			#~		researchable[techID] = 1
		self.win.vKTechs.items = items
		self.win.vKTechs.itemsChanged()
		# Research queue
		items = []
		index = 0
		queueTechs = []
		total = 0
		for task in player.rsrchQueue:
			tech = client.getTechInfo(task.techID)
			queueTechs.append(task.techID)
			item = ui.Item(tech.name, techID = task.techID, index = index)
			researchSci = Utils.getTechRCost(player, task.techID, task.improvement)
			item.tooltip = _("Research points %d/%d, change %d pts/turn.") % (task.currSci, researchSci, task.changeSci)
			item.statustip = item.tooltip
			item.tImpToMax = ["", "*"][task.improveToMax]
			item.tImproveToMax = task.improveToMax
			if task.currSci > 0:
				item.tProgress = _("%d %%") % int(task.currSci * 100 / researchSci)
			else:
				item.tProgress = _("-")
			if task.changeSci > 0:
				value = float(researchSci - task.currSci) / max(task.changeSci, player.effSciPoints)
				total += int(value + 1)
				item.tETC = res.formatTime(value)
			elif task.changeSci < 0:
				value = - float(task.currSci) / min(task.changeSci, player.effSciPoints)
				item.tETC = _("[%s]") % res.formatTime(value)
			elif player.effSciPoints > 0:
				value = float(researchSci) / player.effSciPoints
				total += int(value + 1)
				item.tETC = res.formatTime(value)
			else:
				item.tETC = res.getNA()
			item.tLevel = _("%d-%d") % (tech.level, task.improvement)
			items.append(item)
			index += 1
		self.win.vRQueue.items = items
		self.win.vRQueue.itemsChanged()
		self.win.vRQueueTop.enabled = 0
		self.win.vRQueueUp.enabled = 0
		self.win.vRQueueDown.enabled = 0
		self.win.vRQueueAbort.enabled = 0
		self.win.vRQueueRepat.enabled = 0
		self.win.vRQueueRepat.pressed = 0
		self.win.vRQueueInfo.enabled = 0
		self.win.vRTotal.text = res.formatTime(total)
		# Researchable techs
		items = []
		for techID in client.getAllTechIDs():
			if player.techs.has_key(techID)	or techID in queueTechs \
				or techID in disabled:
				continue
			# can check requirements
			tech = client.getTechInfo(techID)
			if not hasattr(tech, "partialData"):
				continue
			item = ui.Item(tech.name, tLevel = tech.level, techID = techID)
			if hasattr(tech, 'isStructure'): item.tStruct = ('', '*')[tech.isStructure]
			else: item.tStruct = ''
			if hasattr(tech, 'isShipEquip'): item.tShip = ('', '*')[tech.isShipEquip]
			else: item.tShip = ''
			if hasattr(tech, 'researchMod'):
				neededSci = Utils.getTechRCost(player, techID)
				if player.effSciPoints > 0:
					item.tETC = res.formatTime(float(neededSci) / player.effSciPoints)
				else:
					item.tETC = _("N/A")
				item.foreground = None
			else:
				item.tSci = res.getNA()
				item.foreground = (0xc0, 0xc0, 0xc0)
				# skip this item
				continue
			if hasattr(tech, "researchDisables") and tech.researchDisables:
				item.foreground = (0xff, 0xff, 0x00)
			if client.getFullTechInfo(techID).finishResearchHandler == TechHandlers.finishResTLAdvance:
					item.foreground = gdata.sevColors[gdata.CRI]
			items.append(item)
		self.win.vRTechs.items = items
		self.win.vRTechs.itemsChanged()

	def onSelectKTech(self, widget, action, data):
		# TODO implement
		pass

	def onKTechInfo(self, widget, action, data):
		if self.win.vKTechs.selection:
			self.techInfoDlg.display(self.win.vKTechs.selection[0].techID)

	def onSelectRTech(self, widget, action, data):
		# TODO implement
		pass

	def onRTechInfo(self, widget, action, data):
		if self.win.vRTechs.selection:
			self.techInfoDlg.display(self.win.vRTechs.selection[0].techID)

	def onSelectRQueueTech(self, widget, action, data):
		index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
		self.win.vRQueueTop.enabled = index > 0
		self.win.vRQueueUp.enabled = index > 0
		self.win.vRQueueDown.enabled = index < len(self.win.vRQueue.items) - 1
		self.win.vRQueueAbort.enabled = 1
		self.win.vRQueueRepat.enabled = 1
		self.win.vRQueueRepat.pressed = self.win.vRQueue.selection[0].tImproveToMax
		self.win.vRQueueInfo.enabled = 1

	def onRQueueTechInfo(self, widget, action, data):
		if self.win.vRQueue.selection:
			self.techInfoDlg.display(self.win.vRQueue.selection[0].techID)

	def onCloseDlg(self, widget, action, data):
		self.hide()

	def onStartResearch(self, widget, action, data):
		if not self.win.vRTechs.selection:
			self.win.setStatus(_('Select technology to research.'))
			return
		else:
			techID = self.win.vRTechs.selection[0].techID
		try:
			self.win.setStatus(_('Executing START RESEARCH command...'))
			player = client.getPlayer()
			player.rsrchQueue = client.cmdProxy.startResearch(player.oid, techID)
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return
		self.update()

	def onStartImprovement(self, widget, action, data):
		if not self.win.vKTechs.selection:
			self.win.setStatus(_('Select technology to improve.'))
			return
		else:
			techID = self.win.vKTechs.selection[0].techID
		try:
			self.win.setStatus(_('Executing START RESEARCH command...'))
			player = client.getPlayer()
			player.rsrchQueue = client.cmdProxy.startResearch(player.oid, techID)
			self.win.setStatus(_('Command has been executed.'))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return
		self.update()

	def onRTaskMove(self, widget, action, data):
		self.win.setStatus(_('Executing MOVE RESEARCH command...'))
		player = client.getPlayer()
		index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
		# fix -9999 (move to top)
		amount = widget.data
		if index + amount < 0: amount = - index
		# execute command
		player.rsrchQueue = client.cmdProxy.moveResearch(player.oid, index, amount)
		self.update()
		index += amount
		self.win.vRQueue.selectItem(self.win.vRQueue.items[index])
		self.win.setStatus(_('Command has been executed.'))
		self.onSelectRQueueTech(widget, action, None)

	def onRTaskRepeat(self, widget, action, data):
		self.win.setStatus(_('Executing EDIT RESEARCH command...'))
		player = client.getPlayer()
		index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
		repeat = not self.win.vRQueue.selection[0].tImproveToMax
		# execute command
		player.rsrchQueue = client.cmdProxy.editResearch(player.oid, index, repeat)
		self.update()
		self.win.vRQueue.selectItem(self.win.vRQueue.items[index])
		self.win.setStatus(_('Command has been executed.'))
		self.onSelectRQueueTech(widget, action, None)

	def onToggleComleted(self, widget, action, data):
		self.showCompleted = self.win.vSCompl.pressed
		self.update()

	def onRTaskAbort(self, widget, action, data):
		self.confirmDlg.display(_("Abort this research task?"),
			_("Yes"), _("No"), self.onRTaskAbortConfirmed)

	def onRTaskAbortConfirmed(self):
		self.win.setStatus(_('Executing ABORT RESEARCH command...'))
		player = client.getPlayer()
		index = self.win.vRQueue.items.index(self.win.vRQueue.selection[0])
		player.rsrchQueue = client.cmdProxy.abortResearch(player.oid, index)
		self.update()
		self.win.setStatus(_('Command has been executed.'))

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Research'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		ui.Title(self.win, layout = (0, 27, 35, 1), id = 'vStatusBar',
			align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'),
			action = 'onCloseDlg')
		# TODO self.win.statusBar = self.win.vStatusBar
		# known techs
		ui.Title(self.win, layout = (0, 0, 20, 1), text = _('Known technologies'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Listbox(self.win, layout = (0, 1, 20, 25), id = 'vKTechs',
			columns = ((_('Name'), 'text', 10, ui.ALIGN_W), (_('Lvl'), 'tLevel', 1.5, 0),
			(_('Str'), 'tStruct', 1, 0), (_('Sh'), 'tShip', 1, 0),
			(_('ETC'), 'tETC', 0, ui.ALIGN_E)), columnLabels = 1, action = 'onSelectKTech')
		ui.Button(self.win, layout = (0, 26, 5, 1), text = _('Improve'),
			action = 'onStartImprovement')
		ui.Button(self.win, layout = (5, 26, 5, 1), id = "vSCompl", text = _('Show completed'),
			action = 'onToggleComleted', toggle = 1, pressed = 0)
		ui.Button(self.win, layout = (15, 26, 5, 1), text = _('Info'),
			action = 'onKTechInfo')
		# unknown techs
		ui.Title(self.win, layout = (20, 0, 20, 1), text = _('Researchable technologies'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Listbox(self.win, layout = (20, 1, 20, 12), id = 'vRTechs',
			columns = ((_('Name'), 'text', 10, ui.ALIGN_W), (_('Lvl'), 'tLevel', 1.5, 0),
			(_('Str'), 'tStruct', 1, 0), (_('Sh'), 'tShip', 1, 0),
			(_('ETC'), 'tETC', 0, ui.ALIGN_E)), columnLabels = 1, action = 'onSelectRTech')
		ui.Button(self.win, layout = (20, 13, 5, 1), text = _('Research'),
			action = 'onStartResearch')
		ui.Button(self.win, layout = (35, 13, 5, 1), text = _('Info'),
			action = 'onRTechInfo')
		# research queue
		ui.Title(self.win, layout = (20, 14, 20, 1), text = _('Research queue'),
			align = ui.ALIGN_W, id = 'vRQueueTitle', font = 'normal-bold')
		ui.Listbox(self.win, layout = (20, 15, 20, 11), id = 'vRQueue',
			columns = (
				(_('R'), 'tImpToMax', 1, ui.ALIGN_NONE),
				(_('Name'), 'text', 10, ui.ALIGN_W),
				(_('Lvl'), 'tLevel', 1.5, 0),
				(_('Progress'), 'tProgress', 3.5, ui.ALIGN_E),
				(_('ETC'), 'tETC', 0, ui.ALIGN_E)
			),
			columnLabels = 1, action = 'onSelectRQueueTech', sortable = False)
		ui.Button(self.win, layout = (20, 26, 2, 1), text =_("TOP"),
			id = 'vRQueueTop', action = 'onRTaskMove', data = -9999,
			tooltip = _("Move selected technology to the top of the queue."))
		ui.ArrowButton(self.win, layout = (22, 26, 1, 1), direction = ui.ALIGN_N,
			id = 'vRQueueUp', action = 'onRTaskMove', data = -1)
		ui.ArrowButton(self.win, layout = (23, 26, 1, 1), direction = ui.ALIGN_S,
			id = 'vRQueueDown', action = 'onRTaskMove', data = 1)
		ui.Button(self.win, layout = (24, 26, 4, 1), text = _('Repeat'),
			id = 'vRQueueRepat', action = 'onRTaskRepeat', toggle = 1,
			tooltip = _("Repeat research of this technology until the technology is fully improved."))
		ui.Button(self.win, layout = (28, 26, 3, 1), text = _('Abort'),
			id = 'vRQueueAbort', action = 'onRTaskAbort')
		ui.Button(self.win, layout = (31, 26, 4, 1), text = _('Info'),
			id = 'vRQueueInfo', action = 'onRQueueTechInfo')
		ui.Label(self.win, layout = (35, 26, 4, 1), id = "vRTotal", align = ui.ALIGN_E,
			tooltip = _("Total amount of time needed to research all technologies in the queue"))

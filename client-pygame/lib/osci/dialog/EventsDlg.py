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
from osci import gdata, res, client, messages
from ige.ospace.Const import *
from ige import NoSuchObjectException

class EventsDlg:

	def __init__(self, app):
		self.showInfo = 1
		self.showMIN = 1
		self.app = app
		self.createUI()

	def display(self):
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
		items = []
		index = 0
		# copy
		msgs = player.messages[:]
		msgs.reverse()
		currTurn = client.getTurn()
		for sourceID, msgID, locationID, turn, data in msgs:
			item = ui.Item(None, index = index)
			item.tTime = res.formatTime(turn - currTurn)
			item.message = (sourceID, msgID, locationID, turn, data)
			item.tSourceID = sourceID
			if sourceID != OID_NONE and sourceID != player.oid:
				obj = client.get(sourceID, noUpdate = 1)
				if obj:
					item.tSource = getattr(obj, 'name', res.getUnknownName())
				else:
					item.tSource = _('N/A')
			else:
				item.tSource = _('-')
			item.tLocationID = locationID
			if locationID != OID_NONE:
				obj = client.get(locationID, noUpdate = 1)
				item.tLocation = getattr(obj, 'name', res.getUnknownName())
			else:
				item.tLocation = _('-')
			item.tMessage = messages.getMsgText(msgID, data)
			sev = messages.getMsgSeverity(msgID)
			if sev == messages.CRI:
				item.foreground = (0xd0, 0x20, 0x20)
			elif sev == messages.MAJ:
				item.foreground = (0xff, 0xff, 0x00)
			elif sev == messages.MIN:
				item.foreground = None
				if not self.showMIN:
					continue
			elif sev == messages.INFO:
				item.foreground = (0xc0, 0xc0, 0xc0)
				if not self.showInfo:
					continue
			index += 1
			items.append(item)
		self.win.vMessages.items = items
		self.win.vMessages.itemsChanged()
		self.win.vDelete.enabled = 0

	def onMessageSelect(self, widget, action, data):
		self.win.vDelete.enabled = len(self.win.vMessages.selection) > 0

	def onPostMenu(self, widget, action, data):
		self.win.vDelete.enabled = len(self.win.vMessages.selection) > 0
		self.popup.show()

	def onDelete(self, widget, action, data):
		messages = []
		for item in self.win.vMessages.selection:
			messages.append(item.message)
		self.win.setStatus(_('Executing DELETE MESSAGES command...'))
		player = client.getPlayer()
		messages = client.cmdProxy.deleteMessages(player.oid, messages)
		# update related objects
		player.messages = messages
		# update client
		self.win.setStatus(_('Command has been executed.'))
		self.update()

	def onDeleteAll(self, widget, action, data):
		self.win.setStatus(_('Executing DELETE ALL MESSAGES command...'))
		player = client.getPlayer()
		messages = client.cmdProxy.deleteAllMessages(player.oid)
		# update related objects
		player.messages = messages
		# update client
		self.win.setStatus(_('Command has been executed.'))
		self.update()

	def onShowInfo(self, widget, action, data):
		self.showInfo = self.win.vShowInfo.pressed
		self.showMIN = self.win.vShowMIN.pressed
		self.update()

	def onClose(self, widget, action, data):
		self.hide()

	def onShowLoc(self, widget, action, data):
		item = self.win.vMessages.selection[0]
		if item.tLocationID != OID_NONE:
			obj = client.get(item.tLocationID, noUpdate = 1)
			if hasattr(obj, "x"):
				gdata.mainGameDlg.win.vStarMap.highlightPos = (obj.x, obj.y)
				gdata.mainGameDlg.win.vStarMap.setPos(obj.x, obj.y)
				self.hide()
				return
		self.win.setStatus(_("Cannot show location"))

	def onShowLocDel(self, widget, action, data):
		self.onShowLoc(widget, action, data)
		self.onDelete(widget, action, data)

	def onShowSource(self, widget, action, data):
		item = self.win.vMessages.selection[0]
		if item.tSourceID != OID_NONE:
			gdata.mainGameDlg.onSelectMapObj(None, None, item.tSourceID)
			#self.hide()
			return
		self.win.setStatus(_("Cannot show location"))

	def onShowSourceDel(self, widget, action, data):
		self.onShowSource(widget, action, data)
		self.onDelete(widget, action, data)

	def createUI(self):
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = 1,
			movable = 0,
			title = _('Events'),
			rect = ui.Rect(0, 0, 800, 580),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# message box
		ui.Listbox(self.win, layout = (0, 0, 40, 26), id = 'vMessages',
			columns = ((_('Time'), 'tTime', 3, ui.ALIGN_E), (_('Source'), 'tSource', 8, ui.ALIGN_W),
				(_('Location'), 'tLocation', 8, ui.ALIGN_W), (_('Message'), 'tMessage', 0, ui.ALIGN_W)),
			columnLabels = 1, action = 'onMessageSelect', multiselection = 0,
			rmbAction = "onPostMenu")
		ui.Button(self.win, layout = (0, 26, 5, 1), text = _('Delete'), id = 'vDelete',
			action = 'onDelete')
		ui.Button(self.win, layout = (5, 26, 5, 1), text = _('Delete All'), id = 'vDeleteAll',
			action = 'onDeleteAll')
		ui.Button(self.win, layout = (30, 26, 5, 1), text = _('Minor msgs'), id = 'vShowMIN',
			action = 'onShowInfo', toggle = 1, pressed = 1)
		ui.Button(self.win, layout = (35, 26, 5, 1), text = _('Info msgs'), id = 'vShowInfo',
			action = 'onShowInfo', toggle = 1, pressed = 1, foreground = (0xc0, 0xc0, 0xc0))
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		# menu
		self.popup = ui.Menu(self.app, title = _("Message actions"),
			items = [
				ui.Item(_("Show location"), action = "onShowLoc"),
				ui.Item(_("Show source"), action = "onShowSource"),
				ui.Item(_("Show location and delete msg"), action = "onShowLocDel"),
				ui.Item(_("Show source and delete msg"), action = "onShowSourceDel"),
				ui.Item(_("Delete"), action = "onDelete"),
			]
		)
		self.popup.subscribeAction("*", self)
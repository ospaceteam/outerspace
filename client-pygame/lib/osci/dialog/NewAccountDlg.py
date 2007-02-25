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
from osci import client, gdata, res
from ige.ospace.Const import *
from MainGameDlg import MainGameDlg
from ConfirmDlg import ConfirmDlg
import ige

class NewAccountDlg:
	""" Called for a new player."""

	def __init__(self, app):
		self.app = app
		self.createUI()
		self.confirmDlg = ConfirmDlg(app)
		self.confirmDlg.setTitle(_("No free starting position"))

	def display(self, caller = None):
		self.caller = caller
		if self.show():
			self.win.show()

	def hide(self):
		self.win.hide()

	def show(self):
		positions = client.cmdProxy.getStartingPositions()
		if not positions:
			# there are no positions -- pop up a dialog
			self.confirmDlg.display(
				_("We are sorry, but there are no starting positions available at this moment. Please, try again later."),
				_("Refresh"), _("Exit"), self.display, self.app.exit
			)
			return False
		items = []
		for objID, name, posType in positions:
			item = ui.Item(name, tObjID = objID, tPosType = posType)
			if posType == STARTPOS_NEWPLAYER:
				item.tPos = _('Independent player')
			elif posType == STARTPOS_AIPLAYER:
				item.tPos = _("Rebel faction")
			elif posType == STARTPOS_PIRATE:
				item.tPos = _("Pirate faction [VIP password needed]")
			else:
				item.tPos = _('Unknown. You cannot use this.')
			items.append(item)
		self.win.vPos.setItems(items)
		return True

	def onSelect(self, widget, action, data):
		if not self.win.vPos.selection:
			self.win.setStatus(_('Select position.'))
			return
		item = self.win.vPos.selection[0]
		if item.tPosType == STARTPOS_NEWPLAYER:
			self.win.setStatus(_('Executing CREATE NEW PLAYER command...'))
			playerID = client.cmdProxy.createNewPlayer(item.tObjID)
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			if not gdata.mainGameDlg:
				gdata.mainGameDlg = MainGameDlg(self.app)
				gdata.mainGameDlg.display()
			client.updateDatabase(clearDB = 1)
		elif item.tPosType == STARTPOS_AIPLAYER:
			self.win.setStatus(_('Executing TAKE OVER REBEL FACTION command...'))
			playerID = client.cmdProxy.takeOverAIPlayer(item.tObjID)
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			if not gdata.mainGameDlg:
				gdata.mainGameDlg = MainGameDlg(self.app)
				gdata.mainGameDlg.display()
			client.updateDatabase(clearDB = 1)
		elif item.tPosType == STARTPOS_PIRATE:
			password = self.win.vPassword.text
			if not password:
				self.win.setStatus(_("Supply VIP password, please."))
				return
			self.win.setStatus(_('Executing TAKE OVER PIRATE FACTION command...'))
			try:
				playerID = client.cmdProxy.takeOverPirate(item.tObjID, password)
			except ige.SecurityException:
				self.win.setStatus(_("Supply valid VIP password."))
				return
			self.win.setStatus(_('Command has been executed.'))
			self.hide()
			if not gdata.mainGameDlg:
				gdata.mainGameDlg = MainGameDlg(self.app)
				gdata.mainGameDlg.display()
			client.updateDatabase(clearDB = 1)

	def onCancel(self, widget, action, data):
		self.win.hide()
		if self.caller:
			self.caller.display()
		else:
			self.app.exit()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			movable = 0,
			title = _('Select starting position'),
			rect = ui.Rect((w - 424) / 2, (h - 264) / 2, 424, 264),
			layoutManager = ui.SimpleGridLM(),
		)
		ui.Listbox(self.win, layout = (0, 0, 21, 10), id = 'vPos',
			columns = ((_('Galaxy'), 'text', 5, ui.ALIGN_W), (_('Position'), 'tPos', 0, ui.ALIGN_W)),
			columnLabels = 1)
		self.win.subscribeAction('*', self)
		ui.Label(self.win, layout = (0, 10, 5, 1), text = _("VIP Password:"))
		ui.Entry(self.win, layout = (5, 10, 5, 1), id = 'vPassword', align = ui.ALIGN_W, showChar = '*')
		ui.Title(self.win, layout = (0, 11, 13, 1), id = 'vStatusBar', align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (13, 11, 4, 1), text = _('Exit'), action = 'onCancel')
		ui.TitleButton(self.win, layout = (17, 11, 4, 1), text = _('Select'), action = 'onSelect')
		self.win.statusBar = self.win.vStatusBar

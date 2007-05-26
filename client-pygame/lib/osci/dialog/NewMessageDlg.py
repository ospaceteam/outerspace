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
from osci import gdata, res, client
from ige.ospace.Const import *
import ige, string

class NewMessageDlg:

	def __init__(self, app):
		self.app = app
		self.createUI()

	def display(self, caller, objID, objType, forum, msgID = None):
		self.caller = caller
		self.msgSpec = gdata.mailboxSpec[objType, forum]
		messages = client.get(objID)._messages
		if self.msgSpec[1] == None:
			# cannot reply
			return
		elif self.msgSpec[1] == "forum":
			self.recipientObjID = [objID]
			self.recipientForum = forum
			if msgID != None:
				self.topic = messages[msgID]["topic"]
			else:
				self.topic = ""
		elif self.msgSpec[1] == "sender" and msgID != None:
			message = messages[msgID]
			self.recipientObjID = [message["senderID"]]
			self.recipientForum = "INBOX"
			self.topic = message["topic"]
			if self.topic[:4] != "Re: ":
				self.topic = "Re: %s" % self.topic
		elif self.msgSpec[1]:
			self.recipientObjID = []
			self.recipientForum = "INBOX"
			self.topic = ""
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
		pass
		# self.show()

	def show(self):
		if len(self.recipientObjID) > 0:
			text = ""
			for objId in self.recipientObjID:
				recipient = client.get(objId)
				text = u"%s, %s" % (text, _("%s / %s") % (recipient.name, _(self.msgSpec[0])))
			self.win.vRecipient.text = text[2:]
			self.win.vRecipient.action = None
		else:
			self.win.vRecipient.text = _("[Click to select]")
			self.win.vRecipient.action = "onSelectContact"
		if self.topic:
			self.win.vTopic.text = self.topic
			self.win.vTopic.enabled = 0
		else:
			self.win.vTopic.text = ""
			self.win.vTopic.enabled = 1
		self.win.vText.text = [""]

	def onSelectContact(self, widget, action, data):
		player = client.getPlayer()
		items = []
		for contactID in player.diplomacyRels:
			contact = client.get(contactID)
			item = ui.Item(contact.name, tRecipientID = contactID)
			items.append(item)

		self.cwin.vContacts.items = items
		self.cwin.vContacts.itemsChanged()
		self.cwin.show()

	def onContactCancel(self, widget, action, data):
		self.cwin.hide()

	def onContactSelected(self, widget, action, data):
		self.recipientObjID = []
		text = ""
		for item in self.cwin.vContacts.selection:
			self.recipientObjID.append(item.tRecipientID)
			recipient = client.get(item.tRecipientID)
			text = u"%s, %s" % (text, _("%s / %s") % (recipient.name, _(self.msgSpec[0])))
		self.win.vRecipient.text = text[2:]
		self.cwin.hide()

	def onCancel(self, widget, action, data):
		self.hide()

	def onSend(self, widget, action, data):
		if not self.recipientObjID:
			self.win.setStatus(_("Select a recipient, please."))
			return
		if not self.win.vTopic.text:
			self.win.setStatus(_("Specify a topic, please."))
			return
		if self.win.vText.text == [""]:
			self.win.setStatus(_("Type a message, please."))
			return
		try:
			self.win.setStatus(_("Executing SEND MESSAGE command..."))
			message = {
				"forum": self.recipientForum,
				"topic": self.win.vTopic.text,
				"text": string.join(self.win.vText.text, "\n"),
			}
			# send message to all recipients
			for objID in self.recipientObjID:
				client.cmdProxy.sendMsg(objID, message)

			# put message into outbox if forum is INBOX
			if self.recipientForum == "INBOX":
				recipients = ""
				for objID in self.recipientObjID:
					recipient = client.get(objID)
					recipients = u"%s, %s" % (recipients, recipient.name)

				message = {
					"forum": "OUTBOX",
					"topic": "To %s - %s" % (
						recipients[2:],
						self.win.vTopic.text,
					),
					"text": _("To %s / %s:\n\n%s") % (
						recipients[2:],
						_(self.msgSpec[0]),
						"\n".join(self.win.vText.text),
					)
				}
				client.cmdProxy.sendMsg(client.getPlayerID(), message)
			self.win.setStatus(_("Command has been executed."))
		except ige.GameException, e:
			self.win.setStatus(e.args[0])
			return
		client.getMessages()
		self.hide()
		self.caller.update()

	def createUI(self):
		w, h = gdata.scrnSize
		width = 764  # 38 * 20 + 4
		height = 464 # 23 * 20 + 4
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("New message"),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
			tabChange = True
		)
		self.win.subscribeAction('*', self)
		# headers
		ui.Label(self.win, layout = (0, 0, 5, 1), text = _("Recipient"), align = ui.ALIGN_W)
		ui.ActiveLabel(self.win, layout = (5, 0, 33, 1), id = "vRecipient", align = ui.ALIGN_W)
		ui.Label(self.win, layout = (0, 1, 5, 1), text = _("Subject"), align = ui.ALIGN_W)
		ui.Entry(self.win, layout = (5, 1, 33, 1), id = "vTopic", align = ui.ALIGN_W, orderNo = 1)
		ui.Title(self.win, layout = (0, 2, 38, 1), text = _("Message"),
			font = "normal-bold", align = ui.ALIGN_W)
		s = ui.Scrollbar(self.win, layout = (37, 3, 1, 18))
		t = ui.Text(self.win, layout = (0, 3, 37, 18), id = "vText", orderNo = 2)
		t.attachVScrollbar(s)
		# info
		ui.Title(self.win, layout = (0, 21, 28, 1), id = 'vStatusBar', align = ui.ALIGN_W)
		ui.TitleButton(self.win, layout = (28, 21, 5, 1), text = _("Cancel"), action = 'onCancel')
		ui.TitleButton(self.win, layout = (33, 21, 5, 1), text = _("Send"), action = 'onSend')
		# status bar
		#self.win.statusBar = self.win.vStatusBar
		#
		# contact window
		#
		width = 304  # 15 * 20 + 4
		height = 264 # 13 * 20 + 4
		self.cwin = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = 0,
			movable = 0,
			title = _("Select recipient"),
			rect = ui.Rect((w - width) / 2, (h - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.cwin.subscribeAction('*', self)
		# rename
		ui.Listbox(self.cwin, layout = (0, 0, 15, 11), id = 'vContacts', columnLabels = 0,
			columns = ((None, 'text', 0, ui.ALIGN_W),), multiselection = 1, sortedBy=('text', 1))
		# status bar + submit/cancel
		ui.TitleButton(self.cwin, layout = (10, 11, 5, 1), text = _("Select"), action = 'onContactSelected')
		ui.TitleButton(self.cwin, layout = (5, 11, 5, 1), text = _("Cancel"), action = 'onContactCancel')
		ui.Title(self.cwin, id = 'vStatusBar', layout = (0, 11, 5, 1), align = ui.ALIGN_W)
		#self.cwin.statusBar = self.cwin.vStatusBar
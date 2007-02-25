import wx

from RecipientsDlg import RecipientsDlg
import client, gdata

import ige

class MessageDlg(wx.Dialog):
	def __init__(self, parent, id, title, params):
		wx.Dialog.__init__(self, parent, id, title, pos = wx.DefaultPosition, 
			size = (700, 500), style = wx.DEFAULT_DIALOG_STYLE)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		grid = wx.FlexGridSizer(2, 2, 1, 1)
		grid.AddGrowableCol(1)
		
		label = wx.StaticText(self, -1, _("Recipient:"))
		grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
		
		recipients = wx.BoxSizer(wx.HORIZONTAL)
		self.recipient = wx.StaticText(self, -1, _("Select recipients..."), wx.DefaultPosition, wx.DefaultSize)
		recipients.Add(self.recipient, 1, wx.ADJUST_MINSIZE | wx.ALIGN_CENTER | wx.ALL, 4)
		selectRecip = wx.Button(self, -1, _("&Select"))
		wx.EVT_BUTTON(selectRecip, selectRecip.GetId(), self.OnSelectRecipient)
		recipients.Add(selectRecip, 0, wx.ALL, 4)
		grid.AddSizer(recipients, 1, wx.ALIGN_CENTER_VERTICAL | wx.GROW, 0)
		
		label = wx.StaticText(self, -1, _("Subject:"))
		grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
		
		self.subject = wx.TextCtrl(self, -1, "")
		grid.Add(self.subject, 1, wx.GROW | wx.ALL, 4)
		
		sizer.AddSizer(grid, 0, wx.GROW | wx.ALIGN_CENTER | wx.ALL)
		
		label = wx.StaticText(self, -1, _("Message:"))
		sizer.Add(label, 0, wx.LEFT|wx.TOP, 4)
		
		self.message = wx.TextCtrl(self, -1, "", style = wx.TE_MULTILINE)
		sizer.Add(self.message, 1, wx.GROW | wx.ALL, 4)
		
		boxButtons = wx.BoxSizer(wx.HORIZONTAL)
		
		btn = wx.Button(self, wx.ID_OK, _("S&end"))
		btn.SetDefault()
		boxButtons.Add(btn, 0, wx.ALL, 4)
		wx.EVT_BUTTON(self, btn.GetId(), self.OnSend)
		
		btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
		boxButtons.Add(btn, 0, wx.ALL, 4)
		
		sizer.AddSizer(boxButtons, 0, wx.ALIGN_CENTER | wx.ALL, 4)

		accel = wx.AcceleratorTable([
			(wx.ACCEL_ALT, ord('S'), selectRecip.GetId()),
			(wx.ACCEL_ALT, ord('E'), wx.ID_OK),
			(wx.ACCEL_ALT, ord('C'), wx.ID_CANCEL),
			])
		self.SetAcceleratorTable(accel)

		self.selectedRecipients = {}

		forum, objID, objType, msgID = params
		self.msgSpec = gdata.mailboxSpec[objType, forum] 
		messages = client.get(objID)._messages 
		topic = ""
		text = ""
		if self.msgSpec[1] == None:
			# cannot reply
			self.Destroy()
		elif self.msgSpec[1] == "forum":
			# message to some global forum
			self.selectedRecipients[objID] = True
			self.recipientForum = forum
			selectRecip.Disable()
			if msgID != None:
				message = messages[msgID]
				topic = message["topic"]
				if topic[:4] != "Re: ":
					topic = "Re: %s" % topic
				text = "\nOriginal message:\n\n%s" % message["text"]
		elif self.msgSpec[1] == "sender" and msgID != None:
			# message to users inbox
			message = messages[msgID]
			self.selectedRecipients[message["senderID"]] = True
			self.recipientForum = "INBOX"
			topic = message["topic"]
			if topic[:4] != "Re: ":
				topic = "Re: %s" % topic

			text = "\n\nOriginal message:\n\n%s" % message["text"]
		elif self.msgSpec[1]:
			self.recipientForum = "INBOX"

		self.message.SetValue(text)
		self.subject.SetValue(topic)
		
		if len(self.selectedRecipients) > 0:
			text = ""
			for objId, checked in self.selectedRecipients.items():
				recipient = client.get(objId)
				text = u"%s, %s" % (text, _("%s / %s") % (recipient.name, _(self.msgSpec[0])))
			self.recipient.SetLabel(text[2:])

		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		

	def OnSelectRecipient(self, event):
		dlg = RecipientsDlg(self, -1, self.selectedRecipients)
		if dlg.ShowModal() == wx.ID_OK:
			self.selectedRecipients = dlg.selectedRecipients
			text = ""
			for recipientID, checked in self.selectedRecipients.items():
				recipient = client.get(recipientID)
				if checked:
					text = u"%s, %s" % (text, _("%s / %s") % (recipient.name, _(self.msgSpec[0])))

			if len(text) == 0:
				self.recipient.SetLabel(_("Select recipients..."))
			else:
				self.recipient.SetLabel(text[2:])
		
		dlg.Destroy()
	
	def OnSend(self, event):
		if len(self.selectedRecipients) == 0:
			self.GetParent().SetStatusText(_("Select a recipients, please"))
			return
		if len(self.subject.GetValue()) == 0:
			self.GetParent().SetStatusText(_("Specify a topic, please."))
			return
		if len(self.message.GetValue()) == 0:
			self.GetParent().SetStatusText(_("Type a message, please."))
			return
		try:
			self.GetParent().SetStatusText(_("Executing SEND MESSAGE command..."))
			message = {
				"forum": self.recipientForum,
				"topic": self.subject.GetValue(),
				"text": self.message.GetValue(),
			}
			# send message to all recipients
			for objID, checked in self.selectedRecipients.items():
				client.cmdProxy.sendMsg(objID, message)
			
			# put message into outbox if forum is INBOX
			if self.recipientForum == "INBOX":
				recipients = ""
				for objID, checked in self.selectedRecipients.items():
					recipient = client.get(objID)
					recipients = u"%s, %s" % (recipients, recipient.name)
				
				message = {
					"forum": "OUTBOX",
					"topic": "To %s - %s" % (
						recipients[2:],
						self.subject.GetValue(),
					),
					"text": _("To %s / %s:\n\n%s") % (
						recipients[2:],
						_(self.msgSpec[0]),
						"\n%s" % self.message.GetValue(),
					)
				}
				client.cmdProxy.sendMsg(client.getPlayerID(), message)
			self.GetParent().SetStatusText(_("Command has been executed."))
			event.Skip()
		except ige.GameException, e:
			self.GetParent().SetStatusText(e.args[0])

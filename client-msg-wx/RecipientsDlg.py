import wx

import client

class RecipientsDlg(wx.Dialog):
	def __init__(self, parent, id, selectedRecipients):
		wx.Dialog.__init__(self, parent, id, ("Select recipients"), pos = wx.DefaultPosition, 
			size = (300, 320), style = wx.DEFAULT_DIALOG_STYLE)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		player = client.getPlayer()

		self.recipients = wx.CheckListBox(self, -1)
		
		self.items = []
		for contactID in player.diplomacyRels:
			contact = client.get(contactID)
			self.items.append((contact.name, contactID))
			self.recipients.Append(contact.name)

		i = 0
		for name, recipientID in self.items:
			if selectedRecipients.has_key(recipientID):
				self.recipients.Check(i, selectedRecipients[recipientID])
			i += 1

		wx.EVT_CHECKLISTBOX(self.recipients, self.recipients.GetId(), self.OnRecipient)
		sizer.Add(self.recipients, 1, wx.GROW|wx.ALL, 4)
		
		boxButtons = wx.BoxSizer(wx.HORIZONTAL)
		
		btn = wx.Button(self, wx.ID_OK, _("&Select"))
		btn.SetDefault()
		boxButtons.Add(btn, 0, wx.ALL, 4)
		
		btn = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
		boxButtons.Add(btn, 0, wx.ALL, 4)
		
		sizer.AddSizer(boxButtons, 0, wx.ALIGN_CENTER, 0)

		accel = wx.AcceleratorTable([
			(wx.ACCEL_ALT, ord('S'), wx.ID_OK),
			(wx.ACCEL_ALT, ord('C'), wx.ID_CANCEL),
			])
		self.SetAcceleratorTable(accel)
 
 		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		
		self.selectedRecipients = selectedRecipients

	def OnRecipient(self, event):
		pos = event.GetInt()
		self.selectedRecipients[self.items[pos][1]] = self.recipients.IsChecked(pos)

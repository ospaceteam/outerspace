import wx, time
import gdata, client, messages, res
import log, handler
import os, os.path
from ige.ospace.Const import * 

from MessageDlg import MessageDlg
 
sevColors = {
	gdata.CRI: "INDIAN RED",
	gdata.MAJ: "BLUE",
	gdata.MIN: "BLACK",
	gdata.NONE: "FOREST GREEN",
	gdata.DISABLED: "DARK GRAY",
}

MENU_EXIT		= 101
MENU_REFRESH	= 102
MENU_FIND		= 103
MENU_FIND_NEXT	= 104
 
class Messager(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title, pos = wx.DefaultPosition, size = (800, 600))
		
		self.selected = None

		self.Centre(wx.BOTH)
		
		splitter = wx.SplitterWindow(self, -1, style = wx.SP_FULLSASH | wx.SP_NOBORDER | wx.NO_3D)
		splitter2 = wx.SplitterWindow(splitter, -1, style = wx.SP_3D | wx.NO_3D)
		
		def EmptyHandler(evt): pass
		wx.EVT_ERASE_BACKGROUND(splitter, EmptyHandler)
		wx.EVT_ERASE_BACKGROUND(splitter2, EmptyHandler)
		
		tID = wx.NewId()
		self.tree = wx.TreeCtrl(splitter, tID, style = wx.TR_NO_BUTTONS)
		
		wx.EVT_TREE_ITEM_EXPANDING(self.tree, tID, self.OnExpand) 
		wx.EVT_TREE_ITEM_COLLAPSING(self.tree, tID, self.OnExpand)
		wx.EVT_TREE_SEL_CHANGED(self.tree, tID, self.OnForumSelected)
		
		panel = wx.Panel(splitter2, -1, style = wx.SP_NOBORDER | wx.NO_3D)
		
		tID = wx.NewId()
		self.list = wx.ListCtrl(panel, tID, style = wx.LC_REPORT | wx.LC_SINGLE_SEL)
		self.list.InsertColumn(0, "")
		self.list.InsertColumn(1, "Date")
		self.list.InsertColumn(2, "Sender")
		self.list.InsertColumn(3, "Subject")
		wx.EVT_LIST_ITEM_SELECTED(self.list, tID, self.OnMessageSelected)
		self.list.SetColumnWidth(0, 20)
		#self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		self.list.SetColumnWidth(2, 190)
		self.list.SetColumnWidth(3, 295)
		
		btnBox = wx.BoxSizer(wx.HORIZONTAL)
		self.newSubject = wx.Button(panel, -1, _("&New subject"))
		self.reply = wx.Button(panel, -1, _("&Reply"))
		self.readAll = wx.Button(panel, -1, _("Read &all"))
		self.delete = wx.Button(panel, -1, _("&Delete"))
		self.deleteAll = wx.Button(panel, -1, _("D&elete all"))
		btnBox.Add(self.newSubject, 1, wx.EXPAND)
		btnBox.Add(self.reply, 1, wx.EXPAND)
		btnBox.Add(self.readAll, 1, wx.EXPAND)
		btnBox.Add(self.delete, 1, wx.EXPAND)
		btnBox.Add(self.deleteAll, 1, wx.EXPAND)
		
		accel = wx.AcceleratorTable([
			(wx.ACCEL_ALT, ord('N'), self.newSubject.GetId()),
			(wx.ACCEL_ALT, ord('R'), self.reply.GetId()),
			(wx.ACCEL_ALT, ord('A'), self.readAll.GetId()),
			(wx.ACCEL_ALT, ord('D'), self.delete.GetId()),
			(wx.ACCEL_ALT, ord('E'), self.deleteAll.GetId()),
			])
		panel.SetAcceleratorTable(accel)

		wx.EVT_BUTTON(self.newSubject, self.newSubject.GetId(), self.OnNewSubject)
		wx.EVT_BUTTON(self.reply, self.reply.GetId(), self.OnReply)
		wx.EVT_BUTTON(self.readAll, self.readAll.GetId(), self.OnReadAll)
		wx.EVT_BUTTON(self.delete, self.delete.GetId(), self.OnDelete)
		wx.EVT_BUTTON(self.deleteAll, self.deleteAll.GetId(), self.OnDeleteAll)
		self.newSubject.Disable()
		self.reply.Disable()
		self.readAll.Disable()
		self.delete.Disable()
		self.deleteAll.Disable()

		box = wx.BoxSizer(wx.VERTICAL)
		box.Add(self.list, 1, wx.EXPAND)
		box.Add(btnBox, 0, wx.EXPAND)

		panel.SetSizer(box)
		panel.SetAutoLayout(True)
 
 		self.message = wx.TextCtrl(splitter2, -1, "", style = wx.TE_MULTILINE | wx.NO_3D | wx.TE_READONLY)
		
		splitter2.SplitHorizontally(panel, self.message)
		splitter.SplitVertically(self.tree, splitter2, 180)
		splitter.SetMinimumPaneSize(20)
		splitter2.SetMinimumPaneSize(20)

		box.Fit(panel)

		self.finddata = wx.FindReplaceData()
		self.findidx = 0
		
		wx.EVT_COMMAND_FIND(self, -1, self.OnFind)
		wx.EVT_COMMAND_FIND_NEXT(self, -1, self.OnFind)
		wx.EVT_COMMAND_FIND_REPLACE(self, -1, self.OnFind)
		wx.EVT_COMMAND_FIND_REPLACE_ALL(self, -1, self.OnFind)
		wx.EVT_COMMAND_FIND_CLOSE(self, -1, self.OnFindClose)

		menuBar = wx.MenuBar()
		menu = wx.Menu()
		menu.Append(MENU_FIND, _("&Find\tCtrl+F"))
		menu.Append(MENU_FIND_NEXT, _("&Find next\tF3"))
		menu.AppendSeparator()
		menu.Append(MENU_REFRESH, _("&Refresh\tCtrl+R"))
		menu.AppendSeparator()
		menu.Append(MENU_EXIT, _("E&xit\tAlt+X"))

		menuBar.Append(menu, _("&File"))
		self.SetMenuBar(menuBar)

		wx.EVT_MENU(self, MENU_EXIT, self.OnQuitMenu)
		wx.EVT_MENU(self, MENU_REFRESH, self.OnRefreshMenu)
		wx.EVT_MENU(self, MENU_FIND, self.OnFindMenu)
		wx.EVT_MENU(self, MENU_FIND_NEXT, self.OnFindNext)
		wx.EVT_UPDATE_UI(self, MENU_FIND, self.OnUpdateMenuUI)
		wx.EVT_UPDATE_UI(self, MENU_FIND_NEXT, self.OnUpdateMenuUI)

		self.CreateStatusBar(1, wx.ST_SIZEGRIP)

		self.selectedItem = None
		self.showFind = True
		self.createTree()

	def OnUpdateMenuUI(self, evt):
		evt.Enable(self.showFind);

	def FilterForum(self, objMessages, forum, key):
		return objMessages[key]["forum"] == forum

	def OnFind(self, evt):
		forum, objID, type, neco = self.selected

		objMessages = client.get(objID)._messages
		ids = objMessages.keys()
		ids.sort()
		ids.reverse() 

		# limit key only to thes with corresponding forum
		ids = filter(lambda x: self.FilterForum(objMessages, forum, x), ids)

		found = False
		#i = self.findidx
		for i in range(self.findidx, len(ids)):
		#for messageID in ids:
			messageID = ids[i]
			message = objMessages[messageID]
			# regenerate topics for messages with data
			if message.has_key("data") and message["topic"] == "EVENT":
				sourceID, msgID, locationID, turn, data = message["data"]
				message["topic"] = messages.getMsgText(msgID, data).split("\n")[0]
			
			findstring = self.finddata.GetFindString().lower()
			topic = message["topic"].lower()
			if topic.find(findstring) > -1:
				self.findidx = i + 1
				self.SelectMessage(i)
				found = True
				break

			if message.has_key("text"):
				text = message["text"].lower()
				if text.find(findstring) > -1:
					self.findidx = i + 1
					self.SelectMessage(i)
					found = True
					break
			
			# if implement searching in automaticaly generated messages,
			# add searching here	
			#if message.has_key("data"):
			#	sourceID, msgID, locationID, turn, data = message["data"]
			
			i += 1
		
		if not found:
			dlg = wx.MessageDialog(self, _("Find String Not Found"),
					_("Find"), wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
			self.findidx = 0

		if self.finddlg:
			if not found:
				self.finddlg.SetFocus()
			else:
				self.finddlg.Destroy()

	def SelectMessage(self, idx):
		self.list.SetFocus()
		item = self.list.GetItem(idx)
		item.SetMask(wx.LIST_MASK_STATE)
		item.SetState(wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
		self.list.SetItem(item)
		self.list.EnsureVisible(idx)

	def OnFindNext(self, evt):
		if self.finddata.GetFindString():
			self.OnFind(evt)
		else:
			self.OnFindMenu(evt)

	def OnFindClose(self, evt):
		evt.GetDialog().Destroy()

	def OnRefreshMenu(self, event):
		client.getMessages()
		self.createTree()

	def OnFindMenu(self, event):
		self.finddlg = wx.FindReplaceDialog(
			self,
			self.finddata, 
			_("Find"), 
			wx.FR_NOUPDOWN | 
			wx.FR_NOMATCHCASE | 
			wx.FR_NOWHOLEWORD)

		self.findidx = 0
		self.finddlg.Show(True)

	def OnQuitMenu(self, event):
		self.Close(True)

	def OnExpand(self, event):
		if not self.constructingTree:
			event.Veto()

	def OnMessageSelected(self, event):
		objID, msgID1, forum, type = self.itemData[event.m_itemIndex];
		message = client.get(objID)._messages[msgID1]
		message["readed"] = 1		
	
		text = ""
		if message.has_key("data"):
			text = messages.getFullMessageText(message)
		elif message.has_key("text"):
			text = '%s%s\n' % (text, message["text"])

		self.selected = (forum, objID, type, msgID1)
		self.message.SetValue(text)
		self.createTree(False)
		self.list.SetStringItem(event.m_itemIndex, 0, "")
		item = self.list.GetItem(event.m_itemIndex)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.NORMAL)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.delete.Enable(True)
		self.reply.Enable(gdata.mailboxSpec[type, forum][1] != None)
	
	def OnForumSelected(self, event):
		item = event.GetItem()
		if self.tree.GetItemData(item).GetData() == None:
			self.list.DeleteAllItems()
			self.newSubject.Disable()
			self.readAll.Disable()
			self.deleteAll.Disable()
			self.delete.Disable()
			self.reply.Disable()
			self.showFind = False
			return

		self.showFind = True
		forum, objID, type = self.tree.GetItemData(item).GetData()
		self.fillMessages(forum, objID, type)
		self.selected = (forum, objID, type, None)
		
	def fillMessages(self, forum, objID, type):
		objMessages = client.get(objID)._messages
		ids = objMessages.keys()
		ids.sort()
		ids.reverse() 
	
		i = 0
		self.itemData = {}
		self.list.Freeze()
		self.list.DeleteAllItems()
		for messageID in ids:
			message = objMessages[messageID]
			if message["forum"] == forum:
				# regenerate topics for messages with data
				if message.has_key("data") and message["topic"] == "EVENT":
					sourceID, msgID, locationID, turn, data = message["data"]
					message["topic"] = messages.getMsgText(msgID, data).split("\n")[0]
				
				self.list.InsertStringItem(i, "")
				self.list.SetStringItem(i, 3, message["topic"])
				item = self.list.GetItem(i)
				itemFont = item.GetFont()
				if message.has_key("data"):
					sourceID, msgID, locationID, turn, data = message["data"]
					color = wx.NamedColor(sevColors[messages.getMsgSeverity(msgID)])
					item.SetTextColour(color)
					if message["readed"]:
						state = _(" ")
					else:
						state = _("N")
						itemFont.SetWeight(wx.BOLD)
				else:
					color = wx.NamedColor(sevColors[gdata.MIN])
					item.SetTextColour(color)
					if message["readed"]:
						if message["replied"]:
							state = _("R")
						else:
							state = _(" ")

						itemFont.SetWeight(wx.NORMAL)
					else:
						state = _("N")
						itemFont.SetWeight(wx.BOLD)
				
				item.SetFont(itemFont)
				self.list.SetItem(item)
				date = time.strftime(_("%m-%d %H:%M"), time.localtime(message["time"]))
				self.list.SetStringItem(i, 0, state)
				self.list.SetStringItem(i, 2, message["sender"])
				self.list.SetStringItem(i, 1, date)
				self.itemData[i] = (objID, messageID, forum, type)
				i += 1
		
		self.list.Thaw()
		self.delete.Disable()
		self.reply.Disable()
		self.newSubject.Enable(gdata.mailboxSpec[type, forum][1] != None)
		self.readAll.Enable(i > 0)
		self.deleteAll.Enable(i > 0)
		self.message.SetValue("")
	
	def getMsgsNumber(self, objID, forum):
		messages = client.get(objID)._messages
		new = 0
		msgs = 0
		for messageID in messages:
			message = messages[messageID]
			if message["forum"] == forum:
				if message["readed"] == 0:
					new += 1
				msgs += 1
		return msgs, new
 
 	def createTree(self, select = True):
		player = client.getPlayer()
		self.tree.Freeze()
		self.constructingTree = 1
		self.tree.DeleteAllItems()
		root = self.tree.AddRoot("Channels")

		self.addNode(root, "INBOX", player.oid, T_PLAYER)
		events = self.addNode(root, "EVENTS", player.oid, T_PLAYER)
		self.addNode(root, "OUTBOX", player.oid, T_PLAYER)

		for galaxyID in player.galaxies:
			galaxy = client.get(galaxyID)
			galaxyNode = self.tree.AppendItem(root, _("Galaxy %s") % galaxy.name)
			
			self.addNode(galaxyNode, "NEWS", galaxyID, T_GALAXY)
			self.addNode(galaxyNode, "PUBLIC", galaxyID, T_GALAXY)
			self.tree.Expand(galaxyNode)

		osNode = self.tree.AppendItem(root, _("Outer Space"))

		self.addNode(osNode, "NEWS", OID_UNIVERSE, T_UNIVERSE)
		self.addNode(osNode, "PUBLIC", OID_UNIVERSE, T_UNIVERSE)
		self.addNode(osNode, "QA", OID_UNIVERSE, T_UNIVERSE)
		self.addNode(osNode, "IDEAS", OID_UNIVERSE, T_UNIVERSE)
		self.addNode(osNode, "ISSUES", OID_UNIVERSE, T_UNIVERSE)

		if self.selectedItem == None:
			self.selectedItem = events

		self.tree.Expand(osNode)
		self.tree.Expand(root)
		self.constructingTree = 0
		self.tree.Thaw()
		if select:
			self.tree.SelectItem(self.selectedItem)

	def addNode(self, parentNode, forum, objID, type):
		msgs, new = self.getMsgsNumber(objID, forum)
		spec = gdata.mailboxSpec[type, forum]
		text = "%s (%d / %d)" % (_(spec[0]), new, msgs)
		dataObj = wx.TreeItemData((forum, objID, type))
		item = self.tree.AppendItem(parentNode, text, data = dataObj)
		self.tree.SetItemBold(item, new > 0)
		if self.selected != None and self.selected[0] == forum and self.selected[1] == objID:
			self.selectedItem = item
		return item

	def OnNewSubject(self, event):
		dlg = MessageDlg(self, -1, _("New message"), (self.selected[0], self.selected[1], self.selected[2], None))
		dlg.ShowModal()
		dlg.Destroy()
		
		self.OnRefreshMenu(None)
	
	def OnReply(self, event):
		dlg = MessageDlg(self, -1, _("Reply message"), self.selected)
		dlg.ShowModal()
		dlg.Destroy()

		self.OnRefreshMenu(None)

	def OnReadAll(self, event):
		forum, objID, type, msgID = self.selected
		
		obj = client.get(objID)
		for messageID in obj._messages:
			message = obj._messages[messageID]
			if message["forum"] == forum:
				message["readed"] = 1
		
		self.createTree()
		self.fillMessages(forum, objID, type)

	def OnDelete(self, event):
		forum, objID, type, msgID = self.selected
		del client.get(objID)._messages[msgID]
		self.createTree()
		self.fillMessages(forum, objID, type)

	def OnDeleteAll(self, event):
		dlg = wx.MessageDialog(self, _("Delete all messages in this mailbox?"),
				_("Question"), wx.YES_NO | wx.ICON_QUESTION)
		
		if dlg.ShowModal() == wx.ID_YES:
			forum, objID, type, msgID = self.selected
			
			obj = client.get(objID)
			for messageID in obj._messages.keys():
				message = obj._messages[messageID]
				if message["forum"] == forum:
					del obj._messages[messageID]
	
			self.createTree()
			self.fillMessages(forum, objID, type)

		dlg.Destroy()

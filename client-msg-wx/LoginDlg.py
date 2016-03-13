import wx

class LoginDlg(wx.Dialog):
    def __init__(self, parent, id, title, login, password, gameid):
		wx.Dialog.__init__(self, parent, id, title, pos = wx.DefaultPosition,size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE)
		
		grid = wx.FlexGridSizer(3, 2, 1, 1)
		grid.AddGrowableCol(1)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		label = wx.StaticText(self, -1, _("Login:"))
		grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 4)
		
		self.login = wx.TextCtrl(self, -1, login)
		grid.Add(self.login, 1, wx.ALL, 4)
		
		label = wx.StaticText(self, -1, _("Password:"))
		grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 4)
		
		self.password = wx.TextCtrl(self, -1, password, style = wx.TE_PASSWORD)
		grid.Add(self.password, 1, wx.ALL, 4)
		
#		label = wx.StaticText(self, -1, _("Game:"))
#		grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 4)
#		
#		self.game = wx.TextCtrl(self, -1, gameid)
#		grid.Add(self.game, 1, wx.ALL, 4)
		
		sizer.AddSizer(grid, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 4)
		
		line = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTRE, 4)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		
		btn = wx.Button(self, wx.ID_OK, _("OK"))
		btn.SetDefault()
		box.Add(btn, 0, wx.ALL, 4)
		
		btn = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
		box.Add(btn, 0, wx.ALL, 4)
		
		sizer.AddSizer(box, 0, wx.ALIGN_CENTER|wx.ALL, 4)
		
		self.SetSizer(sizer)
		self.SetAutoLayout(True)
		sizer.Fit(self)

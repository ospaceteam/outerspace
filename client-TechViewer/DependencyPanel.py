import wx
from Gauge import Gauge

class DependencyPanel(wx.Panel):
	def __init__(self, parent, text, gaugeColor, textColor, env = 0, mineral = 0, energy = 0, nothing = 0):
		wx.Panel.__init__(self, parent, -1)

		gaugeBorders = (5, 5, 1, 7)
		
		self.env = Gauge(self, gaugeColor, textColor, gaugeBorders, env)
		self.mineral = Gauge(self, gaugeColor, textColor, gaugeBorders, mineral)
		self.energy = Gauge(self, gaugeColor, textColor, gaugeBorders, energy)
		self.nothing = Gauge(self, gaugeColor, textColor, gaugeBorders, nothing)

		vertBox = wx.BoxSizer(wx.VERTICAL)
		panelCaption = wx.StaticText(self, -1, text)
		font = panelCaption.GetFont()
		font.SetWeight(wx.FONTWEIGHT_BOLD)
		panelCaption.SetFont(font)
		vertBox.Add(panelCaption, 0, wx.BOTTOM, 5)

		gbs = wx.GridBagSizer(4, 4)
		gbs.SetFlexibleDirection(wx.HORIZONTAL)
		gbs.SetCols(2)
		gbs.SetRows(4)
		gbs.AddGrowableCol(1)
		
		gbs.Add(wx.StaticText(self, -1, "Environment"), (0, 0), flag = wx.WEST, border = 4)
		gbs.Add(self.env, (0, 1), flag = wx.EXPAND)
		gbs.Add(wx.StaticText(self, -1, "Mineral"), (1, 0), flag = wx.WEST, border = 4)
		gbs.Add(self.mineral, (1, 1), flag = wx.EXPAND)
		gbs.Add(wx.StaticText(self, -1, "Energy"), (2, 0), flag = wx.WEST, border = 4)
		gbs.Add(self.energy, (2, 1), flag = wx.EXPAND)
		gbs.Add(wx.StaticText(self, -1, "Nothing"), (3, 0), flag = wx.WEST, border = 4)
		gbs.Add(self.nothing, (3, 1), flag = wx.EXPAND)
		
		vertBox.Add(gbs, 1, wx.EXPAND | wx.ALL)

		self.SetSizerAndFit(vertBox)

	def SetEnv(self, percent):
		self.env.percent = percent
		self.Refresh()

	def SetMineral(self, percent):
		self.mineral.percent = percent
		self.Refresh()

	def SetEnergy(self, percent):
		self.energy.percent = percent
		self.Refresh()

	def SetNothing(self, percent):
		self.nothing.percent = percent
		self.Refresh()

	def Clear(self):
		self.nothing.percent = 0
		self.mineral.percent = 0
		self.env.percent = 0
		self.energy.percent = 0
		self.Refresh()


import wx

class Gauge(wx.Panel):
	"""
	borders = (left, right, top, bottom)
	"""
	def __init__(self, parent, gaugeColor, textColor, borders = (5, 5, 5, 5), percent = 1):
		wx.Panel.__init__(self, parent, -1)
		
		self.percent = percent
		self.borders = borders
		self.gaugeColor = gaugeColor
		self.textColor = textColor
		
		wx.EVT_SIZE(self, self.OnSize)
		wx.EVT_PAINT(self, self.OnPaint)
	
	def OnSize(self, event):
		self.Refresh()

	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		size = self.GetClientSize()
		dc.SetPen(wx.Pen(self.gaugeColor, 1))
		dc.SetBrush(wx.Brush(self.gaugeColor))
		if self.percent > 0:
			gaugeRect = (
				self.borders[0],
				self.borders[2], 
				(size.width * self.percent) - (self.borders[0] + self.borders[1]),
				size.height - (self.borders[2] + self.borders[3])
			)

			dc.DrawRectangle(*gaugeRect)
			dc.SetTextBackground(self.gaugeColor)
			dc.SetTextForeground(self.textColor)
			dc.DrawLabel("%d%%" % int(self.percent * 100), gaugeRect, wx.ALIGN_CENTER)

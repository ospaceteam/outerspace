import wx
from wxPython.lib.mixins.listctrl import wxColumnSorterMixin, wxListCtrlAutoWidthMixin

class AttributesListCtrl(wx.ListCtrl, wxListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos = wx.DefaultPosition, size = wx.DefaultSize, style = 0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        wxListCtrlAutoWidthMixin.__init__(self)


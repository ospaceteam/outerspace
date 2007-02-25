import wx
import sequip
from ige.ospace.Const import *
from ige.ospace import Rules

from AttributesListCtrl import AttributesListCtrl

ENGINE = 1
SMALL = 2
MEDIUM = 4
LARGE = 8
PLANET = 16
OTHER = 32

typeText = {
	ENGINE: 'Engine',
	SMALL:  'Anti-small',
	MEDIUM: 'Anti-medium',
	LARGE:  'Anti-large',
	PLANET: 'Anti-planet',
	OTHER:  'Other',
}

class ConstrSelTechDlg(wx.Dialog):

	def __init__(self, parent, id, techType, techSubtype, selectCallback, selected = 0, hullID = 0):
		wx.Dialog.__init__(self, parent, id, "Select component", size = (600, 400), pos = wx.DefaultPosition, style = wx.DEFAULT_DIALOG_STYLE)
		self.Centre(wx.BOTH)

		main = wx.BoxSizer(wx.VERTICAL)

		self.lastEqID = None

		tID = wx.NewId()

		self.designs = AttributesListCtrl(self, tID, style = wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL)
		self.designs.InsertColumn(0, "Name")
		self.designs.InsertColumn(1, "Type")
		self.designs.InsertColumn(2, "Data")
		self.designs.SetColumnWidth(0, 150)
		self.designs.SetColumnWidth(1, 80)
		self.designs.SetColumnWidth(2, 150)

		wx.EVT_MOTION(self.designs, self.OnMouseMove)

		checks = wx.BoxSizer(wx.HORIZONTAL)

		if len(techSubtype) > 1:
			self.engineFilter = wx.CheckBox(self, -1, typeText[ENGINE])
			self.engineFilter.SetValue(True)
			wx.EVT_CHECKBOX(self.engineFilter, self.engineFilter.GetId(), self.OnFilter)
			wx.EVT_UPDATE_UI(self.engineFilter, self.engineFilter.GetId(), self.OnUpdateUIEngine)
			self.smallFilter = wx.CheckBox(self, -1, typeText[SMALL])
			self.smallFilter.SetValue(True)
			wx.EVT_CHECKBOX(self.smallFilter, self.smallFilter.GetId(), self.OnFilter)
			wx.EVT_UPDATE_UI(self.smallFilter, self.smallFilter.GetId(), self.OnUpdateUISmall)
			self.mediumFilter = wx.CheckBox(self, -1, typeText[MEDIUM])
			self.mediumFilter.SetValue(True)
			wx.EVT_CHECKBOX(self.mediumFilter, self.mediumFilter.GetId(), self.OnFilter)
			wx.EVT_UPDATE_UI(self.mediumFilter, self.mediumFilter.GetId(), self.OnUpdateUIMedium)
			self.largeFilter = wx.CheckBox(self, -1, typeText[LARGE])
			self.largeFilter.SetValue(True)
			wx.EVT_CHECKBOX(self.largeFilter, self.largeFilter.GetId(), self.OnFilter)
			wx.EVT_UPDATE_UI(self.largeFilter, self.largeFilter.GetId(), self.OnUpdateUILarge)
			self.planetFilter = wx.CheckBox(self, -1, typeText[PLANET])
			self.planetFilter.SetValue(True)
			wx.EVT_CHECKBOX(self.planetFilter, self.planetFilter.GetId(), self.OnFilter)
			wx.EVT_UPDATE_UI(self.planetFilter, self.planetFilter.GetId(), self.OnUpdateUIPlanet)
			self.otherFilter = wx.CheckBox(self, -1, typeText[OTHER])
			self.otherFilter.SetValue(True)
			wx.EVT_CHECKBOX(self.otherFilter, self.otherFilter.GetId(), self.OnFilter)
			wx.EVT_UPDATE_UI(self.otherFilter, self.otherFilter.GetId(), self.OnUpdateUIOther)

			checks.Add(self.engineFilter, 0, wx.ALL, 4)
			checks.Add(self.smallFilter, 0, wx.ALL, 4)
			checks.Add(self.mediumFilter, 0, wx.ALL, 4)
			checks.Add(self.largeFilter, 0, wx.ALL, 4)
			checks.Add(self.planetFilter, 0, wx.ALL, 4)
			checks.Add(self.otherFilter, 0, wx.ALL, 4)

		buttons = wx.BoxSizer(wx.HORIZONTAL)

		okBtn = wx.Button(self, wx.ID_OK, "OK")
		wx.EVT_UPDATE_UI(okBtn, okBtn.GetId(), self.OnUpdateUIOK)

		okBtn.SetDefault()
		cancelBtn = wx.Button(self, wx.ID_CANCEL, "Cancel")

		buttons.Add(okBtn, 0, wx.ALL | wx.ALIGN_CENTER, 4)
		buttons.Add(cancelBtn, 0, wx.ALL | wx.ALIGN_CENTER, 4)

		main.Add(self.designs, 10, wx.GROW | wx.ALL, 4)
		main.AddSizer(checks, 0, wx.GROW | wx.ALL, 0)
		main.AddSizer(buttons, 0, wx.GROW | wx.ALL | wx.ALIGN_CENTER, 0)

		self.SetSizer(main)
		self.SetAutoLayout(True)

		self.techID = OID_NONE
		self.techType = techType
		self.techSubtype = techSubtype
		self.selected = selected

		if hullID:
			self.hullType = Rules.techs[hullID].combatClass
		else:
			self.hullType = 0

		self.typeFilter = ENGINE | SMALL | MEDIUM | LARGE | PLANET | OTHER

		self.showItems()

	def getTechType(self, tech):
		if getattr(tech, "engPwr") > 0:
			return ENGINE
		if getattr(tech, "weaponClass") == 0 and getattr(tech, "weaponDmgMin") > 0:
			return SMALL
		if getattr(tech, "weaponClass") == 1:
			return MEDIUM
		if getattr(tech, "weaponClass") == 2:
			return LARGE
		if getattr(tech, "weaponClass") == 3:
			return PLANET
		return OTHER

	def showItems(self):
		items = []
		selected = None
		self.designs.Freeze()
		self.designs.DeleteAllItems()
		i = 0
		for tech in Rules.techs.itervalues():
			if getattr(tech, self.techType) == 0:
				continue

			if self.techSubtype and tech.subtype not in self.techSubtype:
				continue

			# skip equipment not suitable for this hull
			if tech.minHull > self.hullType:
				continue

			techType = self.getTechType(tech)
			if self.typeFilter & techType == 0:
				continue

			self.designs.InsertStringItem(i, tech.name)
			self.designs.SetStringItem(i, 1, typeText[techType])
			self.designs.SetStringItem(i, 2, sequip.getLongDescr(tech.id))
			self.designs.SetItemData(i, tech.id)

			if tech.id == self.selected:
				self.designs.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

			i += 1

		self.designs.Thaw()

	def OnMouseMove(self, event):
		itemID, flag = self.designs.HitTest((event.GetX(), event.GetY()))
		if flag & wx.LIST_HITTEST_ONITEM:
			longDscr = sequip.getLongDescr(self.designs.GetItemData(itemID))
			if self.lastEqID != itemID:
				self.designs.SetToolTipString(longDscr)
			self.lastEqID = itemID
		else:
			self.designs.SetToolTipString("")
			self.lastEqID = None

	def OnUpdateUIEngine(self, event):
		event.Check(self.typeFilter & ENGINE)

	def OnUpdateUISmall(self, event):
		event.Check(self.typeFilter & SMALL)

	def OnUpdateUIMedium(self, event):
		event.Check(self.typeFilter & MEDIUM)

	def OnUpdateUILarge(self, event):
		event.Check(self.typeFilter & LARGE)

	def OnUpdateUIPlanet(self, event):
		event.Check(self.typeFilter & PLANET)

	def OnUpdateUIOther(self, event):
		event.Check(self.typeFilter & OTHER)

	def OnUpdateUIOK(self, event):
		itemID = self.designs.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		event.Enable(itemID != -1)

	def OnFilter(self, event):
		self.typeFilter = 0
		self.typeFilter += (self.engineFilter.GetValue() * ENGINE)
		self.typeFilter += (self.smallFilter.GetValue() * SMALL)
		self.typeFilter += (self.mediumFilter.GetValue() * MEDIUM)
		self.typeFilter += (self.largeFilter.GetValue() * LARGE)
		self.typeFilter += (self.planetFilter.GetValue() * PLANET)
		self.typeFilter += (self.otherFilter.GetValue() * OTHER)
		self.showItems()

	def getSelectedTech(self):
		itemID = self.designs.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		techID = None
		if itemID > -1:
			techID = self.designs.GetItemData(itemID)
		return techID

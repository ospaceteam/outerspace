import wx
import string

import sequip
	
from ige.ospace import Rules

from AttributesListCtrl import AttributesListCtrl
from Design import Design
from ConstrSelTechDlg import ConstrSelTechDlg

class ConstructionDlg(wx.Dialog):
	def __init__(self, parent, id, config, improvement):
		wx.Dialog.__init__(self, parent, id, "Construction centre", size = (850, 500), pos = wx.DefaultPosition, style = wx.DEFAULT_DIALOG_STYLE)

		self.config = config

		self.Centre(wx.BOTH)
		
		self.improvement = improvement
		
		tID = wx.NewId()

		leftBorder = wx.StaticBox(self, -1, " Ship designs ")
		
		self.designs = AttributesListCtrl(self, tID, style = wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL)
		self.designs.InsertColumn(0, "Name")
		self.designs.InsertColumn(1, "Class")
		self.designs.SetColumnWidth(0, 120)
		self.designs.SetColumnWidth(1, 50)
		
		wx.EVT_LIST_ITEM_SELECTED(self.designs, tID, self.OnDesignSelected)
		
		bottomLeft = wx.BoxSizer(wx.HORIZONTAL)
		
		newDesignID = wx.NewId()
		newDesign = wx.Button(self, newDesignID, "New")
		wx.EVT_BUTTON(newDesign, newDesignID, self.OnNewDesign) 		
		
		duplDesignID = wx.NewId()
		self.duplDesign = wx.Button(self, duplDesignID, "Duplicate")
		wx.EVT_UPDATE_UI(self.duplDesign, duplDesignID, self.OnUpdateUIDesign)
		
		scrapDesignID = wx.NewId()
		self.scrapDesign = wx.Button(self, scrapDesignID, "Scrap")
		wx.EVT_UPDATE_UI(self.scrapDesign, scrapDesignID, self.OnUpdateUIDesign)

		bottomLeft.Add(newDesign, 1, wx.ALL, 0)
		bottomLeft.Add(self.duplDesign, 1, wx.ALL, 0)
		bottomLeft.Add(self.scrapDesign, 1, wx.ALL, 0)
		
		left = wx.BoxSizer(wx.VERTICAL)
		left.Add(self.designs, 1, wx.GROW | wx.BOTTOM, 4)
		left.AddSizer(bottomLeft, 0, wx.GROW, 0)
		
		leftBorderSizer = wx.StaticBoxSizer(leftBorder, wx.VERTICAL)
		leftBorderSizer.AddSizer(left, 1, wx.GROW | wx.ALIGN_CENTRE | wx.TOP, 4)
		
		####### CENTER ######
		rightBorder = wx.StaticBox(self, -1, " Design ")
		
		lblName = wx.StaticText(self, -1, "Name")
		self.designName = wx.TextCtrl(self, -1, "")
		wx.EVT_TEXT(self.designName, self.designName.GetId(), self.OnNameChanged) 
		
		centerName = wx.BoxSizer(wx.HORIZONTAL)
		centerName.Add(lblName, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		centerName.Add(self.designName, 1, wx.ALIGN_RIGHT, 0)

		lblHull = wx.StaticText(self, -1, "Hull")
		self.hullBtn = wx.Button(self, -1, "[Click to select]")
		wx.EVT_BUTTON(self.hullBtn, self.hullBtn.GetId(), self.OnHull) 		
		
		centerHull = wx.BoxSizer(wx.HORIZONTAL)
		centerHull.Add(lblHull, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		centerHull.Add(self.hullBtn, 1, wx.ALIGN_RIGHT, 0)

		lblControl = wx.StaticText(self, -1, "Control unit")
		self.controlBtn = wx.Button(self, -1, "[Click to select]")
		wx.EVT_BUTTON(self.controlBtn, self.controlBtn.GetId(), self.OnCockpit) 		
		
		centerControl = wx.BoxSizer(wx.HORIZONTAL)
		centerControl.Add(lblControl, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		centerControl.Add(self.controlBtn, 1, wx.ALIGN_RIGHT, 0)

		equipBorder = wx.StaticBox(self, -1, " Equipment ")

		self.equipment = wx.ListCtrl(self, tID, style = wx.LC_REPORT | wx.SUNKEN_BORDER)
		self.equipment.InsertColumn(0, "#")
		self.equipment.InsertColumn(1, "Name")
		self.equipment.InsertColumn(2, "Data")
		self.equipment.SetColumnWidth(0, 20)
		self.equipment.SetColumnWidth(1, 120)
		self.equipment.SetColumnWidth(2, wx.LIST_AUTOSIZE_USEHEADER)
		
		wx.EVT_MOTION(self.equipment, self.OnMouseMove)
		
		self.lastEqID = None

		plusBtnID = wx.NewId()
		self.plusBtn = wx.Button(self, plusBtnID, "+")
		wx.EVT_BUTTON(self.plusBtn, plusBtnID, self.OnPlusBtn)
		wx.EVT_UPDATE_UI(self.plusBtn, plusBtnID, self.OnUpdateUIEquipment)

		minusBtnID = wx.NewId()
		self.minusBtn = wx.Button(self, minusBtnID, "-")
		wx.EVT_BUTTON(self.minusBtn, minusBtnID, self.OnMinusBtn)
		wx.EVT_UPDATE_UI(self.minusBtn, minusBtnID, self.OnUpdateUIEquipment)

		addBtnID = wx.NewId()
		self.addBtn = wx.Button(self, addBtnID, "Add")
		wx.EVT_BUTTON(self.addBtn, addBtnID, self.OnAddBtn)

		remBtnID = wx.NewId()
		self.remBtn = wx.Button(self, remBtnID, "Remove")
		wx.EVT_BUTTON(self.remBtn, remBtnID, self.OnRemoveBtn)
		wx.EVT_UPDATE_UI(self.remBtn, remBtnID, self.OnUpdateUIEquipment)

		equipBtnSizer = wx.BoxSizer(wx.HORIZONTAL)
		equipBtnSizer.Add(self.plusBtn, 0, wx.ALL, 0)
		equipBtnSizer.Add(self.minusBtn, 0, wx.ALL, 0)
		equipBtnSizer.Add(self.addBtn, 0, wx.ALL, 0)
		equipBtnSizer.Add(self.remBtn, 0, wx.ALL, 0)
		
		equipBorderSizer = wx.StaticBoxSizer(equipBorder, wx.VERTICAL)
		equipBorderSizer.Add(self.equipment, 1, wx.GROW | wx.TOP, 4)
		equipBorderSizer.AddSizer(equipBtnSizer, 0, wx.TOP, 4)

		center = wx.BoxSizer(wx.VERTICAL)
		center.AddSizer(centerName, 0, wx.GROW | wx.TOP, 4)
		center.AddSizer(centerHull, 0, wx.GROW | wx.TOP, 4)
		center.AddSizer(centerControl, 0, wx.GROW | wx.TOP, 4)
		center.AddSizer(equipBorderSizer, 1, wx.GROW, 0)

		####### RIGHT ######

		right = wx.BoxSizer(wx.VERTICAL)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Class")
		self.lblClass = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblClass, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW, 0)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Signature")
		self.lblSignature = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblSignature, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Speed")
		self.lblSpeed = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblSpeed, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)
		
		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "HP")
		self.lblHP = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblHP, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Base attack")
		self.lblAttack = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblAttack, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Base defence")
		self.lblDefence = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblDefence, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Military power")
		self.lblMP = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 1, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblMP, 1, wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Base experience points")
		self.lblBaseExp = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblBaseExp, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		right.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Tanks")
		self.lblTanks = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblTanks, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW, 0)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Support (fuel)")
		self.lblSuppFuel = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblSuppFuel, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Support (construction points)")
		self.lblSuppConstr = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblSuppConstr, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Maximum range")
		self.lblRange = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblRange, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		right.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Unused payload")
		self.lblPayload = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblPayload, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW, 0)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Free slots")
		self.lblFreeSlots = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblFreeSlots, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW | wx.TOP, 4)

		right.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)

		box = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(self, -1, "Construction points cost")
		self.lblConstrPts = wx.StaticText(self, -1, "", style = wx.ALIGN_RIGHT)
		box.Add(label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
		box.Add(self.lblConstrPts, 1, wx.GROW | wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 0, wx.GROW, 0)

		box = wx.BoxSizer(wx.VERTICAL)
		constrBtnID = wx.NewId()
		self.constrBtn = wx.Button(self, constrBtnID, "Construct")
		wx.EVT_BUTTON(self.constrBtn, constrBtnID, self.OnConstructBtn)

		pnl = wx.Panel(self, -1)
		box.Add(pnl, 1, wx.GROW | wx.ALIGN_TOP, 0)
		box.Add(self.constrBtn, 0, wx.ALIGN_BOTTOM| wx.ALIGN_RIGHT, 0)
		right.AddSizer(box, 1, wx.GROW , 0)

		rightGrid = wx.FlexGridSizer(1, 2, 0, 0)
		rightGrid.AddGrowableRow(0)
		rightGrid.AddGrowableCol(1)

		rightGrid.AddSizer(center, 1, wx.GROW | wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, 4)
		rightGrid.AddSizer(right, 1, wx.GROW | wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, 4)

		rightBorderSizer = wx.StaticBoxSizer(rightBorder, wx.VERTICAL)
		rightBorderSizer.AddSizer(rightGrid, 1, wx.GROW | wx.ALIGN_CENTRE, 0)
		
		mainSizer = wx.FlexGridSizer(1, 2, 0, 0)
		mainSizer.AddGrowableRow(0)
		mainSizer.AddGrowableCol(0)
		mainSizer.AddGrowableCol(1)
		mainSizer.AddSizer(leftBorderSizer, 0, wx.ALL | wx.GROW, 4)
		mainSizer.AddSizer(rightBorderSizer, 0, wx.ALL | wx.GROW, 4)

		self.storedDesigns = self.ReadDesigns()
		self.PopulateDesigns()
		
		self.selectedDesign = Design(None, self.improvement)
		self.selectedDesign.empty = True
		
		self.EnableButtons()
		self.FillValues()
		
		self.SetSizer(mainSizer)
		self.SetAutoLayout(True)

	def OnMouseMove(self, event):
		itemID, flag = self.equipment.HitTest((event.GetX(), event.GetY()))
		if flag & wx.LIST_HITTEST_ONITEM:
			longDscr = sequip.getLongDescr(self.equipment.GetItemData(itemID), self.improvement)
			if self.lastEqID != itemID:
				self.equipment.SetToolTipString(longDscr)
			self.lastEqID = itemID
		else:
			self.equipment.SetToolTipString("")
			self.lastEqID = None

	def OnUpdateUIEquipment(self, event):
		itemID = self.equipment.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		event.Enable(self.equipment.GetItemCount() > 0 and itemID > -1)
	
	def OnUpdateUIDesign(self, event):
		event.Enable(self.designs.GetItemCount() > 0 and not self.selectedDesign.empty)

	def OnNameChanged(self, event):
		self.selectedDesign.name = self.designName.GetValue()
	
	def OnConstructBtn(self, event):
		self.PopulateDesigns()
		self.SaveDesigns()

	def OnPlusBtn(self, event):
		itemID = self.equipment.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if itemID > -1:
			eqID = self.equipment.GetItemData(itemID)
			self.selectedDesign.eqIDs[eqID] = self.selectedDesign.eqIDs[eqID] + 1
			self.selectedDesign.makeFullSpec()
			self.FillValues()
			self.equipment.SetItemState(itemID, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

	def OnMinusBtn(self, event):
		itemID = self.equipment.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if itemID > -1:
			eqID = self.equipment.GetItemData(itemID)
			if self.selectedDesign.eqIDs[eqID] > 0:
				self.selectedDesign.eqIDs[eqID] = self.selectedDesign.eqIDs[eqID] - 1
				self.selectedDesign.makeFullSpec()
				self.FillValues()
				self.equipment.SetItemState(itemID, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

	def OnHull(self, event):
		if not self.selectedDesign.empty:
			hull = self.selectedDesign.hull
		else:
			hull = None
		
		selTechDlg = ConstrSelTechDlg(self, -1, 'isShipHull', [], None, hull, hull)
		if selTechDlg.ShowModal() == wx.ID_OK:
			self.selectedDesign.hull = selTechDlg.getSelectedTech()
		selTechDlg.Destroy()
		self.selectedDesign.makeFullSpec()
		self.FillValues()

	def OnCockpit(self, event):
		oldCockpit = self.selectedDesign.cockpit
		selTechDlg = ConstrSelTechDlg(self, -1, 'isShipEquip', ["seq_ctrl"], None, oldCockpit, self.selectedDesign.hull)
		if selTechDlg.ShowModal() == wx.ID_OK:
			self.selectedDesign.eqIDs[selTechDlg.getSelectedTech()] = 1
			if oldCockpit in self.selectedDesign.eqIDs:
				del self.selectedDesign.eqIDs[oldCockpit]
		selTechDlg.Destroy()
		self.selectedDesign.makeFullSpec()
		self.FillValues()

	def OnAddBtn(self, event):
		selTechDlg = ConstrSelTechDlg(self, -1, 'isShipEquip', ["seq_wpn", "seq_mod", "seq_struct",
			"seq_eng"], None, None, self.selectedDesign.hull)
		if selTechDlg.ShowModal() == wx.ID_OK:
			self.selectedDesign.eqIDs[selTechDlg.getSelectedTech()] = 1
		selTechDlg.Destroy()
		self.selectedDesign.makeFullSpec()
		self.FillValues()

	def OnRemoveBtn(self, event):
		itemID = self.equipment.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
		if itemID > -1:
			eqID = self.equipment.GetItemData(itemID)
			del self.selectedDesign.eqIDs[eqID]
			self.selectedDesign.makeFullSpec()
			self.FillValues()

	def ReadDesigns(self):
		ret = []
		if self.config.Designs.design1 == None:
			return ret
		designs = self.config._config.items("Designs")
		for name, value in designs:
			ret.append(Design(value, self.improvement))

		return ret
	
	def SaveDesigns(self):
		designs = self.config._config.items("Designs")
		for name, value in designs:
			self.config._config.remove_option("Designs", name)
		i = 1
		for design in self.storedDesigns:
			self.config._config.set("Designs", "design%d" % i, design.getConfigText())
			i += 1
	
	def PopulateDesigns(self):
		i = 0
		self.designs.Freeze()
		self.designs.DeleteAllItems()
		for design in self.storedDesigns:
			self.designs.InsertStringItem(i, design.name)
			self.designs.SetStringItem(i, 1, "%s / TL%d" % (sequip.cclass2Text(design.combatClass), design.level))
			i += 1
		self.designs.Thaw() 

	def OnDesignSelected(self, event):
		self.selectedDesign = self.storedDesigns[event.m_itemIndex]
		self.EnableButtons()
		self.FillValues()
	
	def OnNewDesign(self, event):
		self.selectedDesign = Design(None, self.improvement)
		self.storedDesigns.append(self.selectedDesign)
		self.PopulateDesigns()
		self.equipment.DeleteAllItems()
		self.EnableButtons(True)
		self.FillValues()
		self.designName.SetValue("New Design")

	def EnableButtons(self, newBtn = False):
		enable = not self.selectedDesign.empty
		self.designName.Enable(enable or newBtn)
		self.hullBtn.Enable(enable or newBtn)
		self.controlBtn.Enable(enable or newBtn)
		self.constrBtn.Enable(enable or newBtn)
		
	def FillValues(self):
		if not self.selectedDesign.empty:
			if self.selectedDesign.hullName != None:
				self.hullBtn.SetLabel(self.selectedDesign.hullName)
			else:
				self.hullBtn.SetLabel("[Click to select]")
			if self.selectedDesign.cockpitName != None:
				self.controlBtn.SetLabel(self.selectedDesign.cockpitName)
			else:
				self.controlBtn.SetLabel("[Click to select]")
			self.lblClass.SetLabel(sequip.cclass2Text(self.selectedDesign.combatClass))
			self.lblSignature.SetLabel("%d" % self.selectedDesign.signature)
			self.lblSpeed.SetLabel("%.2f" % self.selectedDesign.speed)
			if self.selectedDesign.shieldHP > 0:
				self.lblHP.SetLabel("%d - %d" % (self.selectedDesign.maxHP, self.selectedDesign.shieldHP))
			else:
				self.lblHP.SetLabel("%d" % self.selectedDesign.maxHP)
			self.lblAttack.SetLabel("%d" % self.selectedDesign.combatAtt)
			self.lblDefence.SetLabel("%d / %d" % (self.selectedDesign.combatDef, self.selectedDesign.missileDef))
			self.lblPayload.SetLabel("%d" % self.selectedDesign.payload)
			self.lblFreeSlots.SetLabel("%d" % self.selectedDesign.freeSlots)
			self.lblTanks.SetLabel("%d" % self.selectedDesign.storEn)
			self.lblSuppFuel.SetLabel("%d" % self.selectedDesign.operEn)
			if self.selectedDesign.speed > 0:
				support = 999999
				if self.selectedDesign.operEn > 0:
					support = min(support, self.selectedDesign.storEn / self.selectedDesign.operEn)
				self.lblRange.SetLabel("%.2f" % (support * self.selectedDesign.speed / Rules.turnsPerDay))
			else:
				self.lblRange.SetLabel("none")
			
			self.lblConstrPts.SetLabel("%d" % self.selectedDesign.buildProd)
			self.lblSuppConstr.SetLabel("%d" % (self.selectedDesign.buildProd * Rules.operProdRatio))
			self.lblBaseExp.SetLabel("%d" % self.selectedDesign.baseExp)
			self.lblMP.SetLabel("%d" % self.selectedDesign.combatPwr)
			self.designName.SetLabel(self.selectedDesign.name)
			i = 0
			self.equipment.Freeze()
			self.equipment.DeleteAllItems()
			for eqID in self.selectedDesign.eqIDs:
				eqTech = Rules.techs[int(eqID)]
				if eqTech.subtype in ["seq_wpn", "seq_mod", "seq_struct", "seq_eng"]:
					shortDscr = sequip.getShortDescr(int(eqID), self.improvement)
					self.equipment.InsertStringItem(i, str(self.selectedDesign.eqIDs[eqID]))
					self.equipment.SetStringItem(i, 1, eqTech.name)
					self.equipment.SetStringItem(i, 2, shortDscr)
					self.equipment.SetItemData(i, int(eqID))
					i += 1
			self.equipment.Thaw()
			self.equipment.SetColumnWidth(2, wx.LIST_AUTOSIZE)
		else:
			self.hullBtn.SetLabel("[Click to select]")
			self.controlBtn.SetLabel("[Click to select]")
			na = "N/A"
			self.lblClass.SetLabel(na)
			self.lblSignature.SetLabel(na)
			self.lblSpeed.SetLabel(na)
			self.lblHP.SetLabel(na)
			self.lblAttack.SetLabel(na)
			self.lblDefence.SetLabel(na)
			self.lblPayload.SetLabel(na)
			self.lblFreeSlots.SetLabel(na)
			self.lblTanks.SetLabel(na)
			self.lblSuppFuel.SetLabel(na)
			self.lblRange.SetLabel(na)
			self.lblConstrPts.SetLabel(na)
			self.lblSuppConstr.SetLabel(na)
			self.lblBaseExp.SetLabel(na)
			self.lblMP.SetLabel(na)
			self.designName.SetLabel("")

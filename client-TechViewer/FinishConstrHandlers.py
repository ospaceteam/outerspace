import wx
import sys

from ige.ospace import Rules

class FinishConstrHandlers:
	def __init__(self, attrList, improvement):
		self.list = attrList
		self.improvement = improvement

	def finishProjectADDSLOT3(self, i, tech):
		self.list.InsertStringItem(i, "Slots added on target planet (up to pl. max)")
		self.list.SetStringItem(i, 1, "1")
		return i + 1

	def finishProjectDEEPSPACESCAN(self, i, tech):
		self.list.InsertStringItem(i, "Temporarily improves scanner power of target by factor")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(Rules.techImprEff[self.improvement] * float(tech.data)))
		return i + 1

	def finishProjectIMPRENV(self, i, tech):
		self.list.InsertStringItem(i, "Add amount of points to planet enviroment")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(int(round(Rules.techImprEff[self.improvement] * float(tech.data)))))
		return i + 1

	def finishProjectREPAIRSHIPS2(self, i, tech):
		maxRepaired, repairHP = tech.data.split(",")
		eff = Rules.techImprEff[self.improvement]
		maxRepaired = int(int(maxRepaired) * eff)
		repairHP = int(int(repairHP) * eff)
		self.list.InsertStringItem(i, "Max number of ships to repair per turn")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(maxRepaired))
		i += 1
		self.list.InsertStringItem(i, "Amount of HP added per ship")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(repairHP))
		return i + 1

	def finishProjectNF(self, i, tech):
		self.list.InsertStringItem(i, "Units of strat.res. produced")
		self.list.SetStringItem(i, 1, str(int(tech.data)))
		return i + 1

	def finishProjectShiftPlDown(self, i, tech):
		self.list.InsertStringItem(i, "Adds amount of points to target pl. energy abundance")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(int(round(Rules.techImprEff[self.improvement] * int(tech.data)))))
		return i + 1

	def finishProjectShiftPlUp(self, i, tech):
		self.list.InsertStringItem(i, "Substracts amount of points from target pl. energy abundance")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(int(round(Rules.techImprEff[self.improvement] * int(tech.data)))))
		return i + 1

	def finishProjectBioEnrich(self, i, tech):
		self.list.InsertStringItem(i, "Set target planet environment to")
		self.list.SetStringItem(i, 1, str(200))
		self.list.InsertStringItem(i, "Set population on target planet to")
		self.list.SetStringItem(i, 1, str(1000))
		self.list.InsertStringItem(i, "Set target planet type to")
		self.list.SetStringItem(i, 1, "Gaia")
		return i + 3

	def finishProjectAsteroidMining(self, i, tech):
		self.list.InsertStringItem(i, "Adds amount of points to source pl. min. abundance")
		self.list.SetStringItem(i, 1, tech.data)
		self.list.InsertStringItem(i, "Substracts amount of points from target pl. min. abundance")
		self.list.SetStringItem(i, 1, tech.data)
		return i + 2

	def finishProjectTERRAFORMALIGNMENT6(self, i, tech):
		self.list.InsertStringItem(i, "Changes target pl. energy abundance towards best position by")
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		delta = int(float(tech.data) * Rules.techImprEff[self.improvement])
		self.list.SetStringItem(i, 1, str(delta))
		i += 1
		self.list.InsertStringItem(i, "Improves pl. environment (up to max %d) by" % Rules.envMax)
		item = self.list.GetItem(i)
		itemFont = item.GetFont()
		itemFont.SetWeight(wx.BOLD)
		item.SetFont(itemFont)
		self.list.SetItem(item)
		self.list.SetStringItem(i, 1, str(delta / 2))
		i += 1
		self.list.InsertStringItem(i, "Planet is upgraded if suitable for better type")
		return i + 1

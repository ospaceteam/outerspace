import wx
import sys
sys.path.append("../server/lib")

import sequip

from FinishConstrHandlers import FinishConstrHandlers
from DependencyPanel import DependencyPanel
from config import Config
 
from ige.ospace import Rules

from ConstructionDlg import ConstructionDlg
from AttributesListCtrl import AttributesListCtrl

stratRes = {
    0: "None",
    1: "Uranium",
    2: "Titanium",
    3: "Chromium",
    4: "Silicium",
    5: "Carboneum",
    6: "Antimatter",
    7: "Plutonium",
    8: "Wolframium",
    100: "Mutagen",
    1000: "Unnilseptium"
}

MENU_EXIT             = 101
MENU_SHOW_B           = 102
MENU_SHOW_C           = 103
MENU_SHOW_H           = 104
MENU_IMPROVEMENT_1    = 105
MENU_IMPROVEMENT_2    = 106
MENU_IMPROVEMENT_3    = 107
MENU_IMPROVEMENT_4    = 108
MENU_IMPROVEMENT_5    = 109
MENU_LEVEL_1          = 110
MENU_LEVEL_2          = 111
MENU_LEVEL_3          = 112
MENU_LEVEL_4          = 113
MENU_LEVEL_5          = 114
MENU_LEVEL_99         = 115
MENU_VIEW_LEVEL       = 116
MENU_VIEW_RACE        = 117
MENU_VIEW_REQ_LEVEL   = 118
MENU_CONSTRUCTION_DLG = 119

def bool2Text(value):
	if value:
		return "Yes"
	else:
		return "No"

V_NONE = 0x00
V_STRUCT = 0x01
V_HULL = 0x02
V_SEQUIP = 0x04
V_PROJECT = 0x08
V_EFF = 0x10
V_ALL = V_STRUCT|V_HULL|V_SEQUIP|V_PROJECT

techAttrs = {}

defaultAttr = ('Not specified', V_NONE, True, None, int)

def addAttr(attr, descr, props, showIfDefault, default = 0, convertor = str):
    global techAttrs
    techAttrs[attr] = (descr, props, showIfDefault, default, convertor)

addAttr('buildProd', 'Constr. reqs - construction points', V_ALL, 0)
addAttr('operBio', 'Operational reqs - biomatter', V_ALL, 0)
addAttr('operMin', 'Operational reqs - minerals', V_ALL, 0)
addAttr('operEn', 'Operational reqs - energy', V_ALL, 0)
addAttr('operWorkers', 'Operational reqs - workers', V_ALL, 0)
addAttr('prodBio', 'Production - biomatter', V_STRUCT|V_EFF, 0)
addAttr('prodMin', 'Production - minerals', V_STRUCT|V_EFF, 0)
addAttr('prodEn', 'Production - energy', V_STRUCT|V_EFF, 0)
addAttr('prodPop', 'Production - population', V_STRUCT|V_EFF, 0)
addAttr('prodProd', 'Production - constr. points', V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('prodSci', 'Production - research points', V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('prodEnv', 'Production - env. effect', V_STRUCT|V_EFF, 0)
addAttr('storBio', 'Storage - biomatter', V_STRUCT|V_EFF, 0)
addAttr('storMin', 'Storage - minerals', V_STRUCT|V_EFF, 0)
addAttr('storEn', 'Storage - energy', V_ALL|V_EFF, 0)
addAttr('storPop', 'Accommodate population', V_STRUCT|V_EFF, 0)
addAttr('revoltThr', 'Lowers revolt threshold by', V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('moraleTrgt', 'Increases max morale by', V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('govPwr', 'Government power', V_STRUCT|V_EFF, 0)
addAttr('maxHP', 'Hit points', V_STRUCT|V_HULL|V_SEQUIP|V_EFF, 0)
addAttr('scannerPwr', 'Scanner power', V_STRUCT|V_SEQUIP|V_EFF, 0)
addAttr('weaponClass', 'Target class', V_SEQUIP, True, convertor = sequip.cclass2Text)
addAttr('weaponDmgMin', 'Weapon minimum damage', V_SEQUIP|V_EFF, 0)
addAttr('weaponDmgMax', 'Weapon maximum damage', V_SEQUIP|V_EFF, 0)
addAttr('weaponAtt', 'Weapon attack', V_SEQUIP|V_EFF, 0)
addAttr('weaponROF', 'Weapon Rate Of Fire', V_SEQUIP, 0, convertor = float)
addAttr('minHull', 'Minimum required hull', V_SEQUIP|V_HULL, 0, convertor = sequip.cclass2Text)
addAttr('weight', 'Weight', V_SEQUIP|V_HULL, 0)
addAttr('slots', 'Slots', V_SEQUIP|V_HULL, 0)
addAttr('signature', 'Scan signature', V_SEQUIP|V_HULL, 0)
addAttr('combatDef', 'Combat defence', V_SEQUIP|V_HULL|V_EFF, 0)
addAttr('combatAtt', 'Combat attack', V_SEQUIP|V_HULL|V_EFF, 0)
addAttr('maxWeight', 'Maximum payload', V_HULL|V_EFF, 0)
addAttr('engPwr', 'Engine power', V_SEQUIP|V_EFF, 0)
addAttr('missileDef', 'Missile defence', V_SEQUIP|V_EFF, 0)
addAttr('refuelMax', 'Maximum refuel percent', V_STRUCT|V_EFF, 0)
addAttr('refuelInc', 'Refuel increase percent', V_STRUCT|V_EFF, 0)
addAttr('trainShipInc', 'Exp. points per turn', V_STRUCT|V_EFF, 0, convertor = float)
addAttr('trainShipMax', 'Exp. cap (base exp multiple)', V_STRUCT|V_EFF, 0)
addAttr('fleetSpeedBoost', 'Boost speed of fleets', V_STRUCT|V_EFF, 0, convertor = float)
addAttr('shieldRechargeFix', 'Shield recharge fixed', V_SEQUIP|V_HULL|V_EFF, 0)
addAttr('shieldRechargePerc', 'Shield recharge percent', V_SEQUIP|V_HULL|V_EFF, 0, convertor = float)
addAttr('weaponIgnoreShield', 'Weapon ignore shield', V_SEQUIP|V_HULL, 0, convertor = bool2Text)
addAttr('weaponIsMissile', 'Missile weapon (ECM counts)', V_SEQUIP|V_HULL, 0, convertor = bool2Text)

def getChildren(tech):
    return tech.researchEnables[1] + tech.researchEnables[2] + tech.researchEnables[3] + \
        tech.researchEnables[4] + tech.researchEnables[5]
 
def getParent(tech):
    if tech.researchRequires:
        return Rules.techs[tech.researchRequires[0][0]]
    else:
        return None

class App(wx.App):
    """Application class."""

    def OnInit(self):
        self.frame = TechViewer(None, -1, "OuterSpace Technology viewer")
        self.frame.Show()
        self.SetTopWindow(self.frame)  
        return True

class TechViewer(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, pos = wx.DefaultPosition, size = (800, 600))

        wx.EVT_CLOSE(self, self.OnClose)
        
        self.selected = None
        
        global config

        if config.Races.Bionic == None:
            config.Races.Bionic = 1

        if config.Races.Human == None:
            config.Races.Human = 1

        if config.Races.Cyborg == None:
            config.Races.Cyborg = 1

        if config.View.Improvement == None:
            config.View.Improvement = 3

        if config.View.Level == None:
            config.View.Level = 1
        
        if config.View.Race == None:
            config.View.Race = 1

        if config.Levels.Level1 == None:
            config.Levels.Level1 = 1

        if config.Levels.Level2 == None:
            config.Levels.Level2 = 1

        if config.Levels.Level3 == None:
            config.Levels.Level3 = 1

        if config.Levels.Level4 == None:
            config.Levels.Level4 = 1

        if config.Levels.Level5 == None:
            config.Levels.Level5 = 1

        if config.Levels.Level99 == None:
            config.Levels.Level99 = 1

        self.showBionic = config.Races.Bionic == "1"
        self.showHuman = config.Races.Human == "1"
        self.showCyborg = config.Races.Cyborg == "1"
        
        self.improvement = int(config.View.Improvement)

        self.levels = { 1: config.Levels.Level1 == "1", 
                        2: config.Levels.Level2 == "1", 
                        3: config.Levels.Level3 == "1", 
                        4: config.Levels.Level4 == "1", 
                        5: config.Levels.Level5 == "1", 
                        99: config.Levels.Level99 == "1"
                      }
        
        self.viewLevel = config.View.Level == "1"
        self.viewRace = config.View.Race == "1"
        self.viewReqLevel = config.View.ReqLevel == "1"

        self.currentTech = None

        self.Centre(wx.BOTH)
        
        splitter = wx.SplitterWindow(self, -1, style = wx.SP_3D)# | wx.SP_NOBORDER | wx.NO_3D)
        
        def EmptyHandler(evt): pass
        wx.EVT_ERASE_BACKGROUND(splitter, EmptyHandler)
        
        tID = wx.NewId()
        self.tree = wx.TreeCtrl(splitter, tID, style = wx.TR_HAS_BUTTONS)
        wx.EVT_TREE_SEL_CHANGED(self, tID, self.OnSelChanged)
        self.rightPanel = wx.Panel(splitter, -1, style = wx.SP_NOBORDER | wx.NO_3D)
        box = wx.BoxSizer(wx.VERTICAL)

        tID = wx.NewId()
        self.list = AttributesListCtrl(self.rightPanel, tID, style = wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.list.InsertColumn(0, "Name")
        self.list.InsertColumn(1, "Value")
        self.list.SetColumnWidth(0, 350)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        self.finishHandlers = FinishConstrHandlers(self.list, self.improvement)

        self.prodBio = DependencyPanel(self.rightPanel, "Bio production depends on:", wx.GREEN, wx.BLACK)
        self.prodEn = DependencyPanel(self.rightPanel, "Energy production depends on:", wx.BLUE, wx.WHITE)
        self.prodCon = DependencyPanel(self.rightPanel, "Construction points production depends on:", wx.BLACK, wx.WHITE)

        box.Add(self.list, 1, wx.EXPAND)
        box.Add(wx.StaticLine(self.rightPanel, -1), 0, wx.EXPAND | wx.ALL, 4)
        box.Add(self.prodBio, 0, wx.EXPAND | wx.WEST, 4)
        box.Add(wx.StaticLine(self.rightPanel, -1), 0, wx.EXPAND | wx.ALL, 4)
        box.Add(self.prodEn, 0, wx.EXPAND | wx.WEST, 4)
        box.Add(wx.StaticLine(self.rightPanel, -1), 0, wx.EXPAND | wx.ALL, 4)
        box.Add(self.prodCon, 0, wx.EXPAND | wx.WEST, 4)
        box.Fit(self.rightPanel)
        self.rightPanel.SetSizer(box)
        
        splitter.SplitVertically(self.tree, self.rightPanel, 360)
        splitter.SetMinimumPaneSize(20)

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.AppendCheckItem(MENU_SHOW_B, "Show &Bionic")
        menu.Check(MENU_SHOW_B, self.showBionic)
        menu.AppendCheckItem(MENU_SHOW_C, "Show &Cyborg")
        menu.Check(MENU_SHOW_C, self.showCyborg)
        menu.AppendCheckItem(MENU_SHOW_H, "Show &Human")
        menu.Check(MENU_SHOW_H, self.showHuman)
        menu.AppendSeparator()
        menu.Append(MENU_EXIT, "E&xit")
        
        menuBar.Append(menu, "&Race")
        
        menu = wx.Menu()
        menu.AppendRadioItem(MENU_IMPROVEMENT_1, "Improvement 1")
        menu.AppendRadioItem(MENU_IMPROVEMENT_2, "Improvement 2")
        menu.AppendRadioItem(MENU_IMPROVEMENT_3, "Improvement 3")
        menu.AppendRadioItem(MENU_IMPROVEMENT_4, "Improvement 4")
        menu.AppendRadioItem(MENU_IMPROVEMENT_5, "Improvement 5")
        
        menuBar.Append(menu, "&Improvement")
        
        menu = wx.Menu()
        menu.AppendCheckItem(MENU_LEVEL_1, "Level 1")
        menu.AppendCheckItem(MENU_LEVEL_2, "Level 2")
        menu.AppendCheckItem(MENU_LEVEL_3, "Level 3")
        menu.AppendCheckItem(MENU_LEVEL_4, "Level 4")
        menu.AppendCheckItem(MENU_LEVEL_5, "Level 5")
        menu.AppendSeparator()
        menu.AppendCheckItem(MENU_LEVEL_99, "Additional")
        
        menuBar.Append(menu, "&Level")

        menu = wx.Menu()
        menu.AppendCheckItem(MENU_VIEW_LEVEL, "Level")
        menu.AppendCheckItem(MENU_VIEW_RACE, "Race")
        menu.AppendCheckItem(MENU_VIEW_REQ_LEVEL, "Required parent tech level")
        
        menuBar.Append(menu, "&View")
        
        menu = wx.Menu()
        menu.Append(MENU_CONSTRUCTION_DLG, "Show construction dialog")
        
        menuBar.Append(menu, "Ship &construction")

        self.SetMenuBar(menuBar)

        wx.EVT_MENU(self, MENU_EXIT, self.OnQuitMenu)
        wx.EVT_MENU(self, MENU_SHOW_B, self.OnShowBionic)
        wx.EVT_MENU(self, MENU_SHOW_C, self.OnShowCyborg)
        wx.EVT_MENU(self, MENU_SHOW_H, self.OnShowHuman)
        wx.EVT_MENU(self, MENU_IMPROVEMENT_1, self.OnImprovement1)
        wx.EVT_MENU(self, MENU_IMPROVEMENT_2, self.OnImprovement2)
        wx.EVT_MENU(self, MENU_IMPROVEMENT_3, self.OnImprovement3)
        wx.EVT_MENU(self, MENU_IMPROVEMENT_4, self.OnImprovement4)
        wx.EVT_MENU(self, MENU_IMPROVEMENT_5, self.OnImprovement5)
        wx.EVT_UPDATE_UI(self, MENU_IMPROVEMENT_1, self.OnImprovement1Update)
        wx.EVT_UPDATE_UI(self, MENU_IMPROVEMENT_2, self.OnImprovement2Update)
        wx.EVT_UPDATE_UI(self, MENU_IMPROVEMENT_3, self.OnImprovement3Update)
        wx.EVT_UPDATE_UI(self, MENU_IMPROVEMENT_4, self.OnImprovement4Update)
        wx.EVT_UPDATE_UI(self, MENU_IMPROVEMENT_5, self.OnImprovement5Update)
        wx.EVT_MENU(self, MENU_LEVEL_1, self.OnLevel1)
        wx.EVT_MENU(self, MENU_LEVEL_2, self.OnLevel2)
        wx.EVT_MENU(self, MENU_LEVEL_3, self.OnLevel3)
        wx.EVT_MENU(self, MENU_LEVEL_4, self.OnLevel4)
        wx.EVT_MENU(self, MENU_LEVEL_5, self.OnLevel5)
        wx.EVT_MENU(self, MENU_LEVEL_99, self.OnLevel99)
        wx.EVT_UPDATE_UI(self, MENU_LEVEL_1, self.OnLevel1Update)
        wx.EVT_UPDATE_UI(self, MENU_LEVEL_2, self.OnLevel2Update)
        wx.EVT_UPDATE_UI(self, MENU_LEVEL_3, self.OnLevel3Update)
        wx.EVT_UPDATE_UI(self, MENU_LEVEL_4, self.OnLevel4Update)
        wx.EVT_UPDATE_UI(self, MENU_LEVEL_5, self.OnLevel5Update)
        wx.EVT_UPDATE_UI(self, MENU_LEVEL_99, self.OnLevel99Update)
        wx.EVT_MENU(self, MENU_VIEW_LEVEL, self.OnViewLevel)
        wx.EVT_MENU(self, MENU_VIEW_RACE, self.OnViewRace)
        wx.EVT_MENU(self, MENU_VIEW_REQ_LEVEL, self.OnViewReqLevel)
        wx.EVT_UPDATE_UI(self, MENU_VIEW_LEVEL, self.OnViewLevelUpdate)
        wx.EVT_UPDATE_UI(self, MENU_VIEW_RACE, self.OnViewRaceUpdate)
        wx.EVT_UPDATE_UI(self, MENU_VIEW_REQ_LEVEL, self.OnViewReqLevelUpdate)
        wx.EVT_MENU(self, MENU_CONSTRUCTION_DLG, self.OnConstruction)

        self.PopulateTree()

        return None

    def OnClose(self, event):
        global config
        config.Races.Bionic = int(self.showBionic)
        config.Races.Human = int(self.showHuman)
        config.Races.Cyborg = int(self.showCyborg)
        config.View.Improvement = self.improvement
        config.View.Level = int(self.viewLevel)
        config.View.Race = int(self.viewRace)
        config.View.ReqLevel = int(self.viewReqLevel)
        config.Levels.Level1 = int(self.levels[1])
        config.Levels.Level2 = int(self.levels[2])
        config.Levels.Level3 = int(self.levels[3])
        config.Levels.Level4 = int(self.levels[4])
        config.Levels.Level5 = int(self.levels[5])
        config.Levels.Level99 = int(self.levels[99])

        self.Destroy()

    def OnSelChanged(self, event):
        item = event.GetItem()
        tech = self.tree.GetItemData(item).GetData()
        self.DisplayTech(tech)
        self.currentTech = tech

    def OnQuitMenu(self, event):
        self.Close(True)
 
    def OnConstruction(self, event):
    	global config
        constrDlg = ConstructionDlg(None, -1, config, self.improvement)
        constrDlg.ShowModal()
    	constrDlg.Destroy()

    def OnImprovement1(self, event):
        self.SetImprovement(1)

    def OnImprovement2(self, event):
        self.SetImprovement(2)

    def OnImprovement3(self, event):
        self.SetImprovement(3)

    def OnImprovement4(self, event):
        self.SetImprovement(4)

    def OnImprovement5(self, event):
        self.SetImprovement(5)

    def SetImprovement(self, number):
        self.improvement = number
        self.finishHandlers.improvement = number
        self.DisplayTech(self.currentTech)

    def OnImprovement1Update(self, event):
        event.Check(self.improvement == 1)

    def OnImprovement2Update(self, event):
        event.Check(self.improvement == 2)

    def OnImprovement3Update(self, event):
        event.Check(self.improvement == 3)

    def OnImprovement4Update(self, event):
        event.Check(self.improvement == 4)

    def OnImprovement5Update(self, event):
        event.Check(self.improvement == 5)

    def OnLevel1(self, event):
        if self.levels[1]:
            self.levels[1] = False
            self.levels[2] = False
            self.levels[3] = False
            self.levels[4] = False
            self.levels[5] = False
        else:
            self.levels[1] = True
        self.PopulateTree()

    def OnLevel2(self, event):
        if self.levels[2]:
            self.levels[2] = False
            self.levels[3] = False
            self.levels[4] = False
            self.levels[5] = False
        else:
            self.levels[1] = True
            self.levels[2] = True
        self.PopulateTree()

    def OnLevel3(self, event):
        if self.levels[3]:
            self.levels[3] = False
            self.levels[4] = False
            self.levels[5] = False
        else:
            self.levels[1] = True
            self.levels[2] = True
            self.levels[3] = True
        self.PopulateTree()

    def OnLevel4(self, event):
        if self.levels[4]:
            self.levels[4] = False
            self.levels[5] = False
        else:
            self.levels[1] = True
            self.levels[2] = True
            self.levels[3] = True
            self.levels[4] = True
        self.PopulateTree()

    def OnLevel5(self, event):
        if self.levels[5]:
            self.levels[5] = False
        else:
            self.levels[1] = True
            self.levels[2] = True
            self.levels[3] = True
            self.levels[4] = True
            self.levels[5] = True
        self.PopulateTree()

    def OnLevel99(self, event):
        self.levels[99] = not self.levels[99]
        self.PopulateTree()

    def OnLevel1Update(self, event):
        event.Check(self.levels[1])

    def OnLevel2Update(self, event):
        event.Check(self.levels[2])

    def OnLevel3Update(self, event):
        event.Check(self.levels[3])

    def OnLevel4Update(self, event):
        event.Check(self.levels[4])

    def OnLevel5Update(self, event):
        event.Check(self.levels[5])

    def OnLevel99Update(self, event):
        event.Check(self.levels[99])

    def OnViewLevel(self, event):
        self.viewLevel = not self.viewLevel
        self.PopulateTree()

    def OnViewLevelUpdate(self, event):
        event.Check(self.viewLevel)

    def OnViewRace(self, event):
        self.viewRace = not self.viewRace
        self.PopulateTree()

    def OnViewRaceUpdate(self, event):
        event.Check(self.viewRace)

    def OnViewReqLevel(self, event):
        self.viewReqLevel = not self.viewReqLevel
        self.PopulateTree()

    def OnViewReqLevelUpdate(self, event):
        event.Check(self.viewReqLevel)

    def OnShowBionic(self, event):
        self.showBionic = event.IsChecked()
        self.PopulateTree()

    def OnShowCyborg(self, event):
        self.showCyborg = event.IsChecked()
        self.PopulateTree()

    def OnShowHuman(self, event):
        self.showHuman = event.IsChecked()
        self.PopulateTree()

    def PopulateTree(self):
        self.tree.Freeze()
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("Technologies")
        self.techs = {}
        self.AppendRootTechs(root)
        self.AppendChildTechs(root)
        self.tree.Expand(root)
        self.tree.SetScrollPos(wx.VERTICAL, 0)
        self.tree.Thaw()

    def DisplayTech(self, tech):
        self.list.DeleteAllItems()

        self.prodBio.Clear()
        self.prodEn.Clear()
        self.prodCon.Clear()

        if tech == None:
            return
        i = 0
        techType = V_NONE & (
            getattr(tech ,'isStructure', 0) * V_STRUCT |
            getattr(tech ,'isShipHull', 0) * V_HULL |
            getattr(tech ,'isShipEquip', 0) * V_SEQUIP |
            getattr(tech ,'isProject', 0) * V_PROJECT
        )
        if techType == V_NONE:
            if getattr(tech ,'isStructure', 0): techType = V_STRUCT
            elif getattr(tech ,'isShipHull', 0): techType = V_HULL
            elif getattr(tech ,'isShipEquip', 0): techType = V_SEQUIP
            elif getattr(tech ,'isProject', 0): techType = V_PROJECT

        for attribute in dir(tech):
            value = getattr(tech, attribute)
            descr, props, showIfDef, default, convertor = techAttrs.get(attribute, defaultAttr)
            if techType & props and (value != default or showIfDef):
                self.list.InsertStringItem(i, descr)
                if V_EFF & props:
                    item = self.list.GetItem(i)
                    itemFont = item.GetFont()
                    itemFont.SetWeight(wx.BOLD)
                    item.SetFont(itemFont)
                    self.list.SetItem(item)
                    if convertor != str:
                    	value = Rules.techImprEff[self.improvement] * value
                    else:
                    	value = int(round(Rules.techImprEff[self.improvement] * value))
                self.list.SetStringItem(i, 1, str(convertor(value)))
                i = i + 1
        
        text = ""
        for res in getattr(tech, "researchReqSRes", [0]):
            text += stratRes[res]
            text += ", "

        text = text[:-2]
        if len(text) > 0:
            self.list.InsertStringItem(i, "Strategic resource")
            self.list.SetStringItem(i, 1, text)
            
        if getattr(tech, "finishConstrHandler", None) != None:
            fce = tech.finishConstrHandler.__name__
            if fce in dir(self.finishHandlers):
                i = getattr(self.finishHandlers, fce)(i, tech)
                
        if getattr(tech, "prodProdMod", None) != None:
        	b, m, e, d = tech.prodProdMod
        	self.prodCon.SetEnv(b)
        	self.prodCon.SetMineral(m)
        	self.prodCon.SetEnergy(e)
        	self.prodCon.SetNothing(d)
        	
        if getattr(tech, "prodBioMod", None) != None:
        	b, m, e, d = tech.prodBioMod
        	self.prodBio.SetEnv(b)
        	self.prodBio.SetMineral(m)
        	self.prodBio.SetEnergy(e)
        	self.prodBio.SetNothing(d)

        if getattr(tech, "prodEnMod", None) != None:
        	b, m, e, d = tech.prodEnMod
        	self.prodEn.SetEnv(b)
        	self.prodEn.SetMineral(m)
        	self.prodEn.SetEnergy(e)
        	self.prodEn.SetNothing(d)

    def addNode(self, parentNode, tech):
        raceColours = {
            "C": wx.RED, 
            "B": wx.NamedColour("MEDIUM FOREST GREEN"),
            "H": wx.BLUE,
            "HC": wx.NamedColour("BROWN"),
            "CH": wx.NamedColour("BROWN"),
            "BH": wx.NamedColour("GOLD"),
            "HB": wx.NamedColour("GOLD"),
            "BC": wx.NamedColour("LIGHT MAGENTA"),
            "CB": wx.NamedColour("LIGHT MAGENTA")
        }

        dataItem = wx.TreeItemData(tech)
        title = tech.name
        colour = wx.BLACK
        if len(tech.researchRaces) < 3 and self.viewRace:
            title += " - " + tech.researchRaces
        
        appendByRace = False
        if self.showBionic and "B" in tech.researchRaces:
            appendByRace |= True
        if self.showHuman and "H" in tech.researchRaces:
            appendByRace |= True
        if self.showCyborg and "C" in tech.researchRaces:
            appendByRace |= True

        appendByLevel = False
        if self.levels[tech.level]:
            appendByLevel |= True

        treeItem = None
        parent = getParent(tech)
        reqlvl = 0
        if parent != None:
            for lvl in range (1,6):
                todo = parent.researchEnables[lvl]
                for current in todo:
                    if 1000 in Rules.techs[current].researchReqSRes:
                        continue
                    if tech.id == Rules.techs[current].id:
                        reqlvl = lvl
                        break
                if reqlvl == lvl:
                    break

        if appendByRace and appendByLevel and parentNode != None:
            if self.viewReqLevel:
                itemText = "[%d]--" % reqlvl
            else:
                itemText = ""
            
            if self.viewLevel:
                itemText = "%s%s (%d)" % (itemText, title, tech.level)
            else:
                itemText = "%s%s" % (itemText, title)

            treeItem = self.tree.AppendItem(parentNode, itemText, data = dataItem)
            if tech.researchRaces in raceColours:
                self.tree.SetItemTextColour(treeItem, raceColours[tech.researchRaces])

        return treeItem

    def AppendRootTechs(self, root):
        for tl in range(1, 10):
            for tech in Rules.techs.itervalues():
                if tech.researchRequires or tl != tech.level or 1000 in tech.researchReqSRes:
                    continue
                self.techs[tech] = self.addNode(root, tech)

        if self.levels[99]:
            self.level99Root = self.tree.AppendItem(root, "Level 99", data = None)
            for tech in Rules.techs.itervalues():
                if tech.researchRequires or 99 != tech.level or 1000 in tech.researchReqSRes:
                    continue
                self.techs[tech] = self.addNode(self.level99Root, tech)
            self.tree.SortChildren(self.level99Root)
            self.tree.Expand(self.level99Root)

    def AppendChildTechs(self, root):
        for tech in Rules.techs.itervalues():
            if tech.researchRequires:
                continue

            todo = getChildren(tech)
            while todo:
                current = Rules.techs[todo.pop(0)]
                if 1000 in current.researchReqSRes:
                    continue
                self.AppendChild(root, current)
                todo.extend(getChildren(current))

    def AppendChild(self, root, child):
        parent = getParent(child)

        self.techs[child] = self.addNode(self.techs[parent], child)
        if self.techs[parent] != None:
            self.tree.Expand(self.techs[parent])
            self.tree.SortChildren(self.techs[parent])

config = Config("config.ini")

app = App(False)
app.MainLoop()

config.save("config.ini")

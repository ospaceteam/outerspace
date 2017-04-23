#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygameui as ui
from osci import gdata, client, res
from osci.StarMapWidget import StarMapWidget
from StarSystemDlg import StarSystemDlg
from FleetDlg import FleetDlg
from ResearchDlg import ResearchDlg
from MessagesDlg import MessagesDlg
from ConstructionDlg import ConstructionDlg
from PlanetsOverviewDlg import PlanetsOverviewDlg
from SystemOverviewDlg import SystemOverviewDlg
from GlobalQueuesDlg import GlobalQueuesDlg
from FleetsOverviewDlg import FleetsOverviewDlg
from PlanetsAnalysisDlg import PlanetsAnalysisDlg
from FleetsAnalysisDlg import FleetsAnalysisDlg
from GalaxyRestartDlg import GalaxyRestartDlg
from ConfirmDlg import ConfirmDlg
from OptionsDlg import OptionsDlg
from SearchDlg import SearchDlg
import ProblemsDlg
import DiplomacyDlg
import EmpireOverviewDlg
from ige.ospace.Const import *
from ige.Const import *
from ige import log
import resources
import webbrowser, pygame
from pygame.locals import *
import time
import Utils

class MainGameDlg:

    def __init__(self, app):
        self.app = app
        self.starSystemDlg = StarSystemDlg(self.app)
        self.fleetDlg = FleetDlg(self.app)
        self.researchDlg = ResearchDlg(self.app)
        self.confirmDlg = ConfirmDlg(self.app)
        self.diplomacyDlg = DiplomacyDlg.DiplomacyDlg(self.app)
        self.constructionDlg = ConstructionDlg(self.app)
        self.messagesDlg = MessagesDlg(self.app)
        self.planetsOverviewDlg = PlanetsOverviewDlg(self.app)
        self.globalQueuesDlg = GlobalQueuesDlg(self.app)
        self.systemOverviewDlg = SystemOverviewDlg(self.app)
        self.fleetsOverviewDlg = FleetsOverviewDlg(self.app)
        self.optionsDlg = OptionsDlg(self.app)
        self.searchDlg = SearchDlg(self.app)
        self.problemsDlg = ProblemsDlg.ProblemsDlg(self.app)
        self.empireOverviewDlg = EmpireOverviewDlg.EmpireOverviewDlg(self.app)
        self.galaxyRestartDlg = GalaxyRestartDlg(self.app)
        self.planetsAnalysisDlg = PlanetsAnalysisDlg(app)
        self.fleetsAnalysisDlg = FleetsAnalysisDlg(app)
        self.mapWidget = None
        self.createUI()
        self.centered = 0

    def display(self):
        gdata.showBackground = 0
        gdata.mainGameDlg = self
        self.win.show()
        # register for updates
        gdata.updateDlgs.append(self)
        #self.refocus()

    def refocus(self):
        #log.debug("refocusing")
        self.app.setFocus(self.mapWidget)

    def onCmdInProgress(self, inProgress):
        if inProgress:
            self.win.vTurn.background = (0xff, 0xff, 0x00)
        else:
            self.win.vTurn.background = None

    def hide(self):
        gdata.showBackground = 1
        self.win.hide()
        gdata.mainGameDlg = None
        # unregister updates
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)

    def onQuit(self, widget, action, data):
        self.app.setStatus(_('Logging out and exitting...'))
        self.app.exit()

    def onSelectMapObj(self, widget, action, data):
        self.win.vStarMap.highlightPos = None
        obj = client.get(data, noUpdate = 1)
        if obj == None:
            self.app.setStatus(_('Cannot select object on map'))
            return
        if obj.type in (T_PLANET, T_SYSTEM, T_WORMHOLE):
            self.starSystemDlg.display(data)
        elif obj.type == T_FLEET:
            self.fleetDlg.display(data)

    def onResearch(self, widget, action, data):
        self.researchDlg.display()

    def onDiplomacy(self, widget, action, data):
        self.diplomacyDlg.display()

    def onMessages(self, widget, action, data):
        self.messagesDlg.display()

    def onConstruction(self, widget, action, data):
        self.constructionDlg.display()

    def onPlanetsMenu(self, widget, action, data):
        self.systemPlanetMenu.show((16*20, 0))

    def onPlanets(self, widget, action, data):
        self.planetsOverviewDlg.display()

    def onSystems(self, widget, action, data):
        self.systemOverviewDlg.display()

    def onPlanetAnalysis(self, widget, action, data):
        self.planetsAnalysisDlg.display()

    def onGlobalQueues(self, widget, action, data):
        self.globalQueuesDlg.display()

    def onFleetsMenu(self, widget, action, data):
        self.systemFleetMenu.show((20*20, 0))

    def onFleets(self, widget, action, data):
        self.fleetsOverviewDlg.display()

    def onFleetAnalysis(self, widget, action, data):
        self.fleetsAnalysisDlg.display()

    def onOptions(self, widget, action, data):
        self.optionsDlg.display()

    def onProblems(self, widget, action, data):
        self.problemsDlg.display()

    def onOverview(self, widget, action, data):
        self.empireOverviewDlg.display()

    def onSearch(self, widget, action, data):
        self.searchDlg.display()

    def onStats(self, widget, action, data):
        for galaxyID in client.getPlayer().galaxies:
            url = 'http://%s/%s/galaxy%d.html' % (
                gdata.config.game.server,
                gdata.config.game.lastgameid,
                galaxyID,
            )
            webbrowser.open(url, new = 1)

    def onSponsor(self, widget, action, data):
        webbrowser.open("http://www.k2.cz/", new = 1)

    def onResign(self, widget, action, data):
        # swap yes and no
        self.confirmDlg.display(_('Are you sure to resign current game?'), _('No'),
            _('Yes'), cancelAction = self.onResignConfirmed)

    def onSaveStarmap(self, widget, action, data):
        self.confirmDlg.display(_('Save the current starmap view as an image?'), _('Yes'),
            _('No'), confirmAction = self.onSaveStarmapConfirm)

    def onSaveStarmapConfirm(self):
        turn = client.getTurn()
        name = res.formatTime(turn,'_')
        savedas = self.mapWidget.save(name)
        self.confirmDlg.display(_('File saved as %s' % savedas), _('OK'), False)

    def onMenu(self, widget, action, data):
        w, h = gdata.scrnSize
        self.systemMenu.show((w - self.systemMenu.width * 20 - 4, 0))

    def onResignConfirmed(self):
        client.cmdProxy.resign(client.getPlayerID())
        client.db.clear()
        self.app.exit()

    def onRestartConfirmed(self, imperatorMsg):
        self.win.setStatus(_('Galaxy restart in progress...'))
        oldMsgHandler = client.cmdProxy.msgHandler
        client.cmdProxy.msgHandler = None
        client.cmdProxy.keepAliveTime = 60 * 60 # do not try to connect to server (one hour)
        client.cmdProxy.restartGalaxy(OID_UNIVERSE, client.getPlayer().galaxies[0], imperatorMsg)
        client.db.clear()
        client.cmdProxy.msgHandler = oldMsgHandler
        self.hide()
        self.app.exit()

    def update(self,configUpdated=False):
        self.galaxyRestart(None, None, False)
        player = client.getPlayer()
        turn = client.getTurn()
        self.win.vTurn.text = res.formatTime(turn)
        if configUpdated:
            self.win.vStarMap.updateConfigModes()
        self.win.vStarMap.precompute()
        # center of 1st player star
        if not self.centered:
            player = client.getPlayer()
            if player.planets:
                planet = client.get(player.planets[0])
                self.win.vStarMap.setPos(planet.x, planet.y)
            elif player.fleets:
                fleet = client.get(player.fleets[0])
                self.win.vStarMap.setPos(fleet.x, fleet.y)
            self.centered = 1
            self.refocus() #only fire off when dialog first updated
        # enable/disable construction
        self.win.vConstruction.enabled = Utils.enableConstruction(client)
        # enable/disable diplomacy
        #if player.diplomacyRels:
        self.win.vDiplomacy.enabled = 1
        #else:
        #    self.win.vDiplomacy.enabled = 0
        # highlight messages button?
        self.messagesDlg.update()
        if self.messagesDlg.newMsgs > 0:
            self.win.vMessages.foreground = gdata.sevColors[gdata.MAJ]
        else:
            self.win.vMessages.foreground = None

    def galaxyRestart(self, widget, action, data):
        shownFromMenu = bool(data)
        if client.db != None:
            player = client.getPlayer()
            if player.imperator > 2:
                self.systemMenu.items[3].enabled = True
                lastGalaxyRestartShown = gdata.config.game.lastGalaxyRestartShown
                if lastGalaxyRestartShown != None:
                    localTime = time.time()
                    storedTime = float(lastGalaxyRestartShown)
                    if localTime - storedTime > 60 * 60 * 24 or shownFromMenu == True:
                        gdata.config.game.lastGalaxyRestartShown = str(localTime)
                        self.galaxyRestartDlg.display(restartAction = self.onRestartConfirmed)
                else:
                    gdata.config.game.lastGalaxyRestartShown = str(time.time())
                    self.galaxyRestartDlg.display(restartAction = self.onRestartConfirmed)
            else:
                self.systemMenu.items[3].enabled = False
                if shownFromMenu == True:
                    self.win.setStatus(_("Only imperator elected three times and more can restart galaxy."))

    def updateMsgButton(self):
        if self.messagesDlg.newMsgs > 0:
            self.win.vMessages.foreground = gdata.sevColors[gdata.MAJ]
        else:
            self.win.vMessages.foreground = None

    def processKeyUp(self, evt):
        return ui.NoEvent


    def processKeyDown(self, evt):
        # Alt+M - Messages
        if evt.unicode == u'\x6D' and pygame.key.get_mods() & KMOD_ALT:
            self.messagesDlg.display()
        # Alt+R - Research
        elif evt.unicode == u'\x72' and pygame.key.get_mods() & KMOD_ALT:
            self.researchDlg.display()
        # Alt+D - Diplomacy
        elif evt.unicode == u'\x64' and pygame.key.get_mods() & KMOD_ALT:
            self.diplomacyDlg.display()
        # Alt+C - Constr
        elif evt.unicode == u'\x63' and pygame.key.get_mods() & KMOD_ALT:
            self.constructionDlg.display()
        # Alt+P - Planets
        elif evt.unicode == u'\x70' and pygame.key.get_mods() & KMOD_ALT:
            self.onPlanetsMenu(False,False,False) # use onPlanetsMenu rather than direct control
        # Alt+F - Fleets
        elif evt.unicode == u'\x66' and pygame.key.get_mods() & KMOD_ALT:
            self.onFleetsMenu(False,False,False) # use onFleetsMenu rather than direct control
        # Alt+O - Overview
        elif evt.unicode == u'\x6F' and pygame.key.get_mods() & KMOD_ALT:
            self.empireOverviewDlg.display()
        # Alt+B - Pro'b'lems
        elif evt.unicode == u'\x62' and pygame.key.get_mods() & KMOD_ALT:
            self.problemsDlg.display()
        # Alt+N - Me'n'u
        elif evt.unicode == u'\x6E' and pygame.key.get_mods() & KMOD_ALT:
            self.onMenu(False,False,False) # use onMenu rather than direct control

    def createUI(self):
        w, h = gdata.scrnSize
        lw, lh = w / 20, h / 20
        self.win = ui.Window(self.app,
            modal = 1,
            decorated = 0,
            alwaysInBackground = 1,
            movable = 0,
            rect = ui.Rect(0, 0, w, h),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        # map
        self.mapWidget = StarMapWidget(self.win,
            id = 'vStarMap',
            action = 'onSelectMapObj',
            layout = (0, 1, lw, lh - 2)
        )
        self.searchDlg.mapWidget = self.mapWidget
        self.win.callEventHandler = self.mapWidget
        self.mapWidget.callEventHandler = self
        # bottom
        ui.Label(self.win,
            id = 'vStatus',
            align = ui.ALIGN_W,
            layout = (0, lh - 1, lw - 16, 1),
        )
        ui.ActiveLabel(self.win,
            id = "vSponsor",
            align = ui.ALIGN_W,
            icons = [(pygame.image.load(resources.get("sponsor_logo_small.png")), ui.ALIGN_E)],
            layout = (lw - 12, lh - 1, 8, 1),
            action = "onSponsor",
            statustip = _("Server sponsored by K2 Software"),
        )
        ui.Label(self.win,
            id = 'vTurn',
            align = ui.ALIGN_E,
            text = '????.??',
            font = 'normal-bold',
            layout = (lw - 4, lh - 1, 4, 1),
        )
        # top
        ui.Button(self.win, layout = (0, 0, 4, 1), text = _('Messages'),
            action = 'onMessages', id = "vMessages")
        ui.Button(self.win, layout = (4, 0, 4, 1), text = _('Research'),
            action = 'onResearch')
        ui.Button(self.win, layout = (8, 0, 4, 1), text = _('Diplomacy'),
            id = "vDiplomacy", action = 'onDiplomacy', enabled = 0)
        ui.Button(self.win, layout = (12, 0, 4, 1), text = _('Constr'),
            id = "vConstruction", action = 'onConstruction', enabled = 0)
        ui.Button(self.win, layout = (16, 0, 4, 1), text = _('Planets'),
            id = "vPlanetsMenu", action = 'onPlanetsMenu', enabled = 1)
        ui.Button(self.win, layout = (20, 0, 4, 1), text = _('Fleets'),
            id = "vFleetsMenu", action = 'onFleetsMenu', enabled = 1)
        ui.Button(self.win, layout = (24, 0, 4, 1), text = _('Overview'),
            id = "vOverview", action = 'onOverview', enabled = 1)
        ui.Title(self.win, layout = (28, 0, lw - 37, 1))
        ui.Button(self.win, layout = (lw - 9, 0, 4, 1), text = _('Problems'),
            action = 'onProblems')
        ui.Button(self.win, layout = (lw - 5, 0, 5, 1), text = _('Menu'),
            action = 'onMenu')
        self.app.statusBar = self.win.vStatus
        self.app.setStatus(_('Ready.'))
        # system menu
        self.systemMenu = ui.Menu(self.app, title = _("Menu"),
            width = 5,
            items = [
                ui.Item(_("Find system"), action = "onSearch", hotkey = u'\x66'), # F
                ui.Item(_("Statistics"), action = "onStats", hotkey = u'\x73'), # S
                ui.Item(_("Save Starmap"), action = "onSaveStarmap", hotkey = u'\x76'), # V
                ui.Item(_("Galaxy restart"), action = "galaxyRestart", enabled = False, data = True), # no hotkey; if this position moved, you need to update restartGalaxy's "self.systemMenu.items" lines to reference new index position
                ui.Item(_("Options"), action = "onOptions", hotkey = u'\x6F'), # O
                ui.Item(_("--------"), enabled = False),
                ui.Item(_("Resign"), action = "onResign"), # no hotkey
                ui.Item(_("--------"), enabled = False),
                ui.Item(_("Quit"), action = "onQuit", hotkey = u'\x71'), # Q
            ]
        )
        self.systemMenu.subscribeAction("*", self)
        self.systemFleetMenu = ui.Menu(self.app, title = _("Fleets"),
            width = 4,
            items = [
                ui.Item(_("Fleet List"), action = "onFleets", hotkey = u'\x66'), # F
                ui.Item(_("Analysis"), action = "onFleetAnalysis", hotkey = u'\x61'), # A
            ]
        )
        self.systemFleetMenu.subscribeAction("*", self)
        self.systemPlanetMenu = ui.Menu(self.app, title = _("Planets"),
            width = 5,
            items = [
                ui.Item(_("Planet List"), action = "onPlanets", hotkey = u'\x70'), # P
                ui.Item(_("System List"), action = "onSystems", hotkey = u'\x73'), # S
                ui.Item(_("Global queues"), action = "onGlobalQueues"),
                ui.Item(_("Analysis"), action = "onPlanetAnalysis", hotkey = u'\x61'), #A
            ]
        )
        self.systemPlanetMenu.subscribeAction("*", self)

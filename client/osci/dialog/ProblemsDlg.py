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
import bisect
import copy
import math
import re
import string

import pygameui as ui
from osci import gdata, client, res
import ige.ospace.Const as Const
from ige.ospace import Utils, Rules

class ProblemsDlg:
    """Displays 'Problem locator' dialog.

    """
    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self):
        self.show()
        self.win.show()
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()
        # unregister updates
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)

    def update(self):
        self.show()

    class Problems:
        def __init__(self, win):
            self.items = []
            self.checkboxes = {gdata.CRI: win.vCritical.checked,
                               gdata.MAJ: win.vMajor.checked,
                               gdata.MIN: win.vMinor.checked,
                               gdata.INFO: win.vInfo.checked}

        def append(self, severity, item):
            if self.checkboxes[severity]:
                item.foreground = gdata.sevColors[severity]
                self.items.append(item)

    def _addProblemsStructStatus(self, problems, struct, planet):
        player = client.getPlayer()
        status = struct[Const.STRUCT_IDX_STATUS]
        tech = client.getFullTechInfo(struct[Const.STRUCT_IDX_TECHID])

        if hasattr(player, 'techs'):
            techEff = Rules.techImprEff[player.techs.get(struct[Const.STRUCT_IDX_TECHID], Rules.techBaseImprovement)]
        else:
            techEff = Rules.techImprEff[Rules.techBaseImprovement]

        HPturn = max(1, int(0.02 * tech.maxHP * techEff))
        turnsToDestroy = math.ceil(struct[Const.STRUCT_IDX_HP] / HPturn)

        if turnsToDestroy < Rules.turnsPerDay * 2:
            severity = gdata.MAJ
            if turnsToDestroy < Rules.turnsPerDay:
                severity = gdata.CRI
        else:
            severity = gdata.MIN

        if not status & Const.STRUCT_STATUS_ON:
            # structure is off
            problems.append(severity,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Structure (%s) is off and will be destroyed in %s turns.') % (tech.name, res.formatTime(turnsToDestroy))))

        if status & Const.STRUCT_STATUS_DETER:
            problems.append(gdata.MAJ,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Structure (%s) is deteriorating.') % (tech.name,)))
        if status & Const.STRUCT_STATUS_NOBIO:
            problems.append(gdata.INFO,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Structure (%s) has insufficient supply of biomatter.') % (tech.name,)))
        if status & Const.STRUCT_STATUS_NOEN:
            problems.append(gdata.INFO,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Structure (%s) has insufficient supply of energy.') % (tech.name,)))
        if status & Const.STRUCT_STATUS_NOPOP:
            problems.append(gdata.INFO,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Structure (%s) has insufficient supply of workers.') % (tech.name,)))
        if status & Const.STRUCT_STATUS_REPAIRING:
            problems.append(gdata.INFO,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Structure (%s) is repairing.') % (tech.name,)))

    def _getSystemRefuel(self, system):
        player = client.getPlayer()
        maxRefuelMax = 0
        hasRefuel = False
        for planetID in system.planets:
            planet = client.get(planetID, noUpdate=1)
            if hasattr(planet, 'owner'):
                if hasattr(planet, 'hasRefuel'):
                    hasRefuel = hasRefuel or planet.hasRefuel
                if hasattr(planet, 'refuelMax'):
                    if planet.owner == player.oid:
                        maxRefuelMax = max(maxRefuelMax, planet.refuelMax)
                    elif planet.owner in player.diplomacyRels:
                        dipl = client.getDiplomacyWith(planet.owner)
                        if Const.PACT_ALLOW_TANKING in dipl.pacts and dipl.pacts[Const.PACT_ALLOW_TANKING][0] == Const.PACT_ACTIVE:
                            maxRefuelMax = max(maxRefuelMax, planet.refuelMax)
                elif hasattr(planet, 'hasRefuel'):
                    maxRefuelMax
        return hasRefuel, maxRefuelMax

    def _addProblemsFleets(self, problems, fleet):
        if not fleet.orbiting:
            # we do not report fleets in flight
            return
        fleetName = fleet.customname if fleet.customname else fleet.name
        energyReserve = fleet.storEn * 100 / fleet.maxEn
        system = client.get(fleet.orbiting, noUpdate=1)
        systemName = getattr(system, "name", res.getUnknownName())
        hasRefuel, maxRefuelMax = self._getSystemRefuel(system)

        if energyReserve == 100:
            problems.append(gdata.INFO,
                            ui.Item(systemName, tOID=fleet.oid, tType=Const.T_FLEET,
                                    vDescription=_('Fleet "%s" has full fuel tanks.') % (fleetName)))
            return

        if 0 < maxRefuelMax <= energyReserve:
            severity = gdata.INFO
            if maxRefuelMax <= energyReserve:
                note = _(' and CAN refuel, but reached planet maximum refuel amount')
            else:
                note = _(' and IS refueling')
        elif hasRefuel:
            severity = gdata.INFO
            note = _(' and utilizes unknown refueling capacities')
        else:
            note = _(' and is NOT refueling')
            severity = [gdata.CRI, gdata.MAJ, gdata.MIN][bisect.bisect([25, 50], energyReserve)]
        problems.append(severity,
                        ui.Item(systemName, tOID=fleet.oid, tType=Const.T_FLEET,
                                vDescription=_('Fleet "%s" is low on fuel [%d %%]%s.') % (fleetName, energyReserve, note)))

    def _addProblemsMaterial(self, problems, system, mat, totalMat, material):
        if mat >= 0:
            return
        surplusTurns = totalMat / (-mat)
        if surplusTurns < Rules.turnsPerDay * 7:
            severity = gdata.MAJ
        elif surplusTurns < Rules.turnsPerDay * 2:
            severity = gdata.CRI
        else:
            severity = gdata.MIN

        if totalMat > 0:
            note = _(' surplus %d (%s)' % (totalMat, res.formatTime(surplusTurns)))
        else:
            note = _(' with no surplus left!')
        problems.append(severity,
                        ui.Item(system.name, tOID=system.oid, tType=Const.T_SYSTEM,
                                vDescription=_('%s decreasing - last turn change %d, %s.') % (material, mat, note)))

    def _getTaskSciValue(self, task):
        player = client.getPlayer()
        fulltech = client.getFullTechInfo(task.techID)
        researchSci = Utils.getTechRCost(player, task.techID, task.improvement)
        maxImprovement = min(Rules.techMaxImprovement, fulltech.maxImprovement)

        if task.improveToMax:
            # account next levels
            for impr in range(task.improvement + 1, maxImprovement + 1):
                researchSci += Utils.getTechRCost(player, task.techID, impr)
        return researchSci - task.currSci

    def _addProblemsResearch(self, problems):
        player = client.getPlayer()
        if player.effSciPoints < 0:
            problems.append(gdata.CRI,
                            ui.Item(_('Research'), tType=Const.T_TECHNOLOGY,
                                    vDescription=_('We are losing our researched knowledge by %d pts per turn!') % (player.effSciPoints,)))
            return
        elif player.effSciPoints == 0:
            return
        elif len(player.rsrchQueue) == 0:
            problems.append(gdata.CRI,
                            ui.Item(_('Research'), tType=Const.T_TECHNOLOGY,
                                    vDescription=_('Research queue is empty.')))
            return

        queueValue = sum(self._getTaskSciValue(task) for task in player.rsrchQueue)
        totalEtc = math.ceil(float(queueValue) / player.effSciPoints)

        # check short reseach queue
        if totalEtc < Rules.turnsPerDay * 2:
            severity = gdata.MIN
            if totalEtc < Rules.turnsPerDay:
                severity = gdata.MAJ
            problems.append(severity,
                            ui.Item(_('Research'), tType=Const.T_TECHNOLOGY,
                                    vDescription=_('Research queue ends in %s turns, %d item(s) on list.') % (res.formatTime(totalEtc), len(player.rsrchQueue))))

    def _addProblemsGlobalQueues(self, problems):
        # go through all planets to understand the state of global queues
        player = client.getPlayer()
        # holder for (number , eff production) of planets set to each queue
        globalQueueStats = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
        queConstValues = [0, 0, 0, 0, 0]
        queEtc = [0, 0, 0, 0, 0]

        for planetID in player.planets:
            planet = client.get(planetID, noUpdate=1)
            globalQueueStats[planet.globalQueue] = tuple([sum(x) for x in zip(globalQueueStats[planet.globalQueue], (1, planet.effProdProd))])

        # evaluate depletion rate of the global queue
        for queue in range(5):
            quePlanets, queEffProd = globalQueueStats[queue]
            for task in player.prodQueues[queue]:
                if task.isShip:
                    tech = player.shipDesigns[task.techID]
                else:
                    tech = client.getFullTechInfo(task.techID)
                queConstValues[queue] += task.quantity * tech.buildProd
            if queEffProd > 0:
                queEtc[queue] = math.ceil(float(queConstValues[queue])/queEffProd)
            else:
                queEtc[queue] = 99999

        # creation of items with global queue problems
        for queue in range(1, 5):
            queName = res.globalQueueName(queue)
            quePlanets = globalQueueStats[queue][0]
            # check empty global production queue with at least one planet [so its relevant]
            if queConstValues[queue] == 0 and quePlanets > 0:
                problems.append(gdata.CRI,
                                ui.Item(_('Global queue ' + queName), tType=Const.T_QUEUE,
                                        vDescription=_('Global production queue {0} used by {1} planet(s) is empty.'.format(queName, quePlanets))))
            # check end of global production queue
            elif queEtc[queue] < Rules.turnsPerDay * 2:
                severity = gdata.MIN
                if queEtc[queue] < Rules.turnsPerDay:
                    severity = gdata.MAJ
                problems.append(severity,
                                ui.Item(_('Global queue ' + queName), tType=Const.T_QUEUE,
                                        vDescription=_('Global production queue {0} used by {1} planet(s) runs out in {2} turns.'.format(queName, quePlanets, res.formatTime(queEtc[queue])))))
        return queEtc[0]  # time of depletion of the default queue will be reused later

    def _getTargetSlotDict(self, planetID):
        assert planetID in client.getPlayer().planets
        targets = {}
        planet = client.get(planetID, noUpdate=1)
        if planet.effProdProd <= 0:
            return targets

        nonShipTasks = (task for task in planet.prodQueue if not task.isShip)
        for task in nonShipTasks:
            tech = client.getFullTechInfo(task.techID)
            if tech.isStructure and task.demolishStruct == 0:
                quantity = task.quantity
            elif tech.isProject and tech.id == 3802:
                # we are constructing Habitable Surface Expansion
                # so after construction we will have new slot on the planet
                quantity = -1
            else:
                continue
            assert quantity != 0

            try:
                targets[task.targetID] += quantity
            except KeyError:
                targets[task.targetID] = quantity
        return targets

    def _addProblemsSlots(self, problems, system):
        player = client.getPlayer()
        playerPlanets = set(system.planets) & set(player.planets)
        freeSlots = {}
        structSources = dict.fromkeys(system.planets)
        for planetID in system.planets:
            planet = client.get(planetID, noUpdate=1)
            freeSlots[planetID] = planet.plSlots - len(planet.slots)

        for planetID in playerPlanets:
            for targetID, quantity in self._getTargetSlotDict(planetID).items():
                freeSlots[targetID] -= quantity
                if quantity > 0:
                    try:
                        structSources[targetID].add(planetID)
                    except AttributeError:
                        structSources[targetID] = set([planetID])

        for planetID, free in freeSlots.items():
            if free < 0:
                # not enough space, report for every planet that builds on this one
                planet = client.get(planetID, noUpdate=1)
                for sourceID in structSources[planetID]:
                    source = client.get(sourceID, noUpdate=1)
                    problems.append(gdata.MAJ,
                                    ui.Item(source.name, tOID=sourceID, tType=Const.T_PLANET,
                                            vDescription=_('There is no space for all constructed buildings on %s.') % (planet.name)))

    def _addProblemsDefaultQueue(self, problems, planet, defaultQueueEtc):
        player = client.getPlayer()
        if not planet.effProdProd > 0:
            return
        planetEtc = 0
        # compute length of production queue
        for task in planet.prodQueue:
            if task.isShip:
                tech = player.shipDesigns[task.techID]
            else:
                tech = client.getFullTechInfo(task.techID)
            modifier = Rules.buildOnAnotherPlanetMod if task.targetID != planet.oid else 1
            planetEtc += math.ceil(float(task.quantity * tech.buildProd * modifier - task.currProd) / planet.effProdProd)

        etc = planetEtc + defaultQueueEtc
        # check empty production queue
        if not etc:
            problems.append(gdata.CRI,
                            ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                    vDescription=_('Production queue is empty.')))
            return
        if etc < Rules.turnsPerDay:
            severity = gdata.MAJ
        elif etc < Rules.turnsPerDay * 2:
            severity = gdata.MIN
        else:
            severity = gdata.INFO

        problems.append(severity,
                        ui.Item(planet.name, tOID=planet.oid, tType=Const.T_PLANET,
                                vDescription=_('Production queue may end in {0} turns ({1} directly in planet queue).'.format(res.formatTime(etc), res.formatTime(planetEtc)))))

    def show(self):
        critical = self.win.vCritical.checked
        major = self.win.vMajor.checked
        minor = self.win.vMinor.checked
        info = self.win.vInfo.checked

        disp = 1

        player = client.getPlayer()
        problems = self.Problems(self.win)
        systems = set([])
        for planetID in player.planets:
            planet = client.get(planetID, noUpdate=1)
            systems.add(planet.compOf)

        defaultQueueEtc = self._addProblemsGlobalQueues(problems)

        for systemID in systems:
            system = client.get(systemID, noUpdate=1)
            bio = 0
            totalBio = 0
            en = 0
            totalEn = 0
            # holds modified planets
            planetCopies = {}

            for planetID in system.planets:
                planet = client.get(planetID, noUpdate=1)
                # copy of planet to change plSlots count
                if hasattr(planet, 'owner') and planet.owner == player.oid:
                    # add planet to the global queue stats
                    # compute bio and en for system
                    bio += planet.changeBio
                    totalBio += max(0, planet.storBio - planet.minBio)
                    en += planet.changeEn
                    totalEn += max(0, planet.storEn - planet.minEn)
                    # the planet needs to have global queue 0 - the default one - to have its queue reported
                    if self.win.vPlanets.checked:
                        if not planet.globalQueue:
                            self._addProblemsDefaultQueue(problems, planet, defaultQueueEtc)
                        for struct in planet.slots:
                            self._addProblemsStructStatus(problems, struct, planet)

            # free slots within the system
            self._addProblemsSlots(problems, system)
            # check bio for system
            if self.win.vSystems.checked:
                self._addProblemsMaterial(problems, system, bio, totalBio, 'Bio')
                self._addProblemsMaterial(problems, system, en, totalEn, 'En')

        # check fleets
        if self.win.vFleets.checked:
            for fleetID in player.fleets:
                fleet = client.get(fleetID, noUpdate=1)
                self._addProblemsFleets(problems, fleet)

        # check research queue
        if self.win.vResearch.checked:
            self._addProblemsResearch(problems)

        self.win.vProblems.items = problems.items
        self.win.vProblems.itemsChanged()

    def onClose(self, widget, action, data):
        self.hide()

    def onShowSource(self, widget, action, data):
        item = self.win.vProblems.selection[0]
        if item.tType == Const.T_FLEET:
            object = client.get(item.tOID, noUpdate=1)
            # center on map
            if hasattr(object, "x"):
                gdata.mainGameDlg.win.vStarMap.highlightPos = (object.x, object.y)
                gdata.mainGameDlg.win.vStarMap.setPos(object.x, object.y)
                self.hide()
                return
        elif item.tType in (Const.T_SYSTEM, Const.T_PLANET):
            if item.tOID != Const.OID_NONE:
                gdata.mainGameDlg.onSelectMapObj(None, None, item.tOID)
                return
        elif item.tType == Const.T_TECHNOLOGY:
            gdata.mainGameDlg.researchDlg.display()
            return
        elif item.tType == Const.T_QUEUE:
            gdata.mainGameDlg.globalQueuesDlg.display()
        self.win.setStatus(_("Cannot show location."))

    def onShowLocation(self, widget, action, data):
        item = self.win.vProblems.selection[0]
        if item.tType in (Const.T_SYSTEM, Const.T_PLANET, Const.T_FLEET):
            object = client.get(item.tOID, noUpdate=1)
            # center on map
            if hasattr(object, "x"):
                gdata.mainGameDlg.win.vStarMap.highlightPos = (object.x, object.y)
                gdata.mainGameDlg.win.vStarMap.setPos(object.x, object.y)
                self.hide()
                return
        self.win.setStatus(_("Cannot show location."))

    def onToggleCondition(self, widget, action, data):
        self.update()

    def createUI(self):
        screenWidth, screenHeight = gdata.scrnSize
        # size of dialog in layout metrics (for SimpleGridLM)
        cols = 40
        rows = 29
        # dialog width and height in pixels
        isSmallWin = screenHeight == 600 and screenWidth == 800
        width = cols * 20 + 4 * (not isSmallWin)
        height = rows * 20 + 4 * (not isSmallWin)
        #creating dialog window
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             movable=0,
                             title=_("Problems Locator"),
                             titleOnly=isSmallWin,
                             rect=ui.Rect((screenWidth - 800 - 4 * (not isSmallWin)) / 2,
                                          (screenHeight - 600 - 4 * (not isSmallWin)) / 2,
                                          width,
                                          height),
                             layoutManager=ui.SimpleGridLM())
        self.win.subscribeAction('*', self)
        # first row is window title
        rows -= 1

        ui.Listbox(self.win, layout=(0, 0, cols, rows - 2), id='vProblems',
                   columns=[(_('Location'), 'text', 10, ui.ALIGN_W),
                   (_('Problem description'), 'vDescription', 30, ui.ALIGN_W)],
                   columnLabels=1, action='onShowSource', rmbAction='onShowLocation')

        btnWidth = 4
        ui.Check(self.win, layout=(btnWidth * 0, rows - 2, btnWidth, 1), id='vSystems',
                 text=_('Systems'), action='onToggleCondition', checked=1)
        ui.Check(self.win, layout=(btnWidth * 1, rows - 2, btnWidth, 1), id='vPlanets',
                 text=_('Planets'), action='onToggleCondition', checked=1)
        ui.Check(self.win, layout=(btnWidth * 2, rows - 2, btnWidth, 1), id='vFleets',
                 text=_('Fleets'), action='onToggleCondition', checked=1)
        ui.Check(self.win, layout=(btnWidth * 3, rows - 2, btnWidth, 1), id='vResearch',
                 text=_('Research'), action='onToggleCondition', checked=1)

        ui.Check(self.win, layout=(btnWidth * 6, rows - 2, btnWidth, 1), id='vCritical',
                 text=_('Critical'), action='onToggleCondition', checked=1)
        ui.Check(self.win, layout=(btnWidth * 7, rows - 2, btnWidth, 1), id='vMajor',
                 text=_('Major'), action='onToggleCondition', checked=1)
        ui.Check(self.win, layout=(btnWidth * 8, rows - 2, btnWidth, 1), id='vMinor',
                 text=_('Minor'), action='onToggleCondition', checked=1)
        ui.Check(self.win, layout=(btnWidth * 9, rows - 2, btnWidth, 1), id='vInfo',
                 text=_('Info'), action='onToggleCondition', checked=0)

        # dialog bottom line
        ui.Title(self.win, layout=(0, rows - 1, cols - 5, 1))
        ui.TitleButton(self.win, layout=(cols - 5, rows - 1, 5, 1), text=_("Close"), action='onClose')

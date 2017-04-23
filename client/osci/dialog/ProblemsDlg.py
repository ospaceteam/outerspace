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
import re
from osci import gdata, client, res
from ige.ospace.Const import *
from ige.ospace import Utils, Rules
import string, math, copy

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

    def show(self):
        critical = self.win.vCritical.checked
        major = self.win.vMajor.checked
        minor = self.win.vMinor.checked
        info = self.win.vInfo.checked

        disp = 1

        player = client.getPlayer()
        items = []
        # object list (all player's objects + systems)
        objects = player.fleets[:]
        objects += player.planets[:]
        systems = {}
        for planetID in player.planets:
            planet = client.get(planetID)
            if planet.compOf not in systems:
                systems[planet.compOf] = None
        objects += systems.keys()

        # counting construction points value of each global production queue
        # holder for (number , eff production) of planets set to each queue
        globalQueueStats=[(0,0), (0,0), (0,0), (0,0), (0,0)]
        prodQueueProblems = []


        # go through all objects
        for objID in objects:
            if objID < OID_FREESTART:
                continue
            obj = client.get(objID, noUpdate = 1)
            if not hasattr(obj, "type"):
                continue
            if obj.type == T_SYSTEM:
                if not hasattr(obj, 'planets'):
                    continue
                bio = 0
                totalBio = 0
                en = 0
                totalEn = 0
                buildingQuantity = {}
                buildingInfo = {}
                # holds modified planets
                planetCopies = {}

                for planetID in obj.planets:
                    planet = client.get(planetID, noUpdate = 1)
                    # copy of planet to change plSlots count
                    if not planetID in planetCopies:
                        cPlanet = copy.deepcopy(planet)
                        planetCopies[planetID] = cPlanet
                    else:
                        cPlanet = planetCopies[planetID]
                    if hasattr(planet, 'owner') and planet.owner == player.oid:
                        queuePlanetNumber, queueEffProd = globalQueueStats[planet.globalQueue]
                        queuePlanetNumber += 1
                        queueEffProd += planet.effProdProd
                        globalQueueStats[planet.globalQueue] = (queuePlanetNumber, queueEffProd)
                        # compute bio and en for system
                        bio += planet.changeBio
                        totalBio += max(0, planet.storBio - planet.minBio)
                        en  += planet.changeEn
                        totalEn += max(0, planet.storEn - planet.minEn)
                        # the planet needs to have global queue 0 - the default one - to have its queue reported
                        if hasattr(planet, 'prodQueue') and self.win.vPlanets.checked and not planet.globalQueue:
                            totalEtc = 0
                            # compute length of production queue
                            if cPlanet.prodQueue and cPlanet.effProdProd > 0:
                                for task in cPlanet.prodQueue:
                                    if task.isShip:
                                        tech = client.getPlayer().shipDesigns[task.techID]
                                    else:
                                        tech = client.getFullTechInfo(task.techID)
                                        if tech.isStructure and hasattr(task, "demolishStruct") and task.demolishStruct == 0:
                                            # total count of constructing buildings on target
                                            if buildingQuantity.has_key(task.targetID):
                                                buildingQuantity[task.targetID] += task.quantity
                                            else:
                                                buildingQuantity[task.targetID] = task.quantity

                                            # information about source and target of constructing
                                            if buildingInfo.has_key((planetID, task.targetID)):
                                                buildingInfo[(planetID, task.targetID)] += task.quantity
                                            else:
                                                buildingInfo[(planetID, task.targetID)] = task.quantity
                                        elif tech.isProject and tech.id == 3802:
                                            # we are constructing Habitable Surface Expansion
                                            # so after construction we got some new slots on planet
                                            if not task.targetID in planetCopies:
                                                targetPlanet = client.get(task.targetID, noUpdate = 1)
                                                cPlanet = copy.deepcopy(targetPlanet)
                                                planetCopies[task.targetID] = cPlanet

                                            planetCopies[task.targetID].plSlots += task.quantity

                                    if task.targetID != planetID:
                                        totalEtc += math.ceil(float(tech.buildProd * Rules.buildOnAnotherPlanetMod - task.currProd) / planet.effProdProd)
                                        totalEtc += math.ceil((task.quantity - 1) * float(tech.buildProd * Rules.buildOnAnotherPlanetMod) / planet.effProdProd)
                                    else:
                                        totalEtc += math.ceil(task.quantity * float(tech.buildProd - task.currProd) / planet.effProdProd)
                                        totalEtc += math.ceil((task.quantity - 1) * float(tech.buildProd) / planet.effProdProd)
                            else:
                                totalEtc = 99999

                            prodQueueProblems.append((planetID, totalEtc, len(planet.prodQueue)))


                        # check for structures status
                        if hasattr(planet, 'slots') and self.win.vPlanets.checked:
                            for struct in planet.slots:
                                status = struct[STRUCT_IDX_STATUS]
                                problem = None
                                tech = client.getFullTechInfo(struct[STRUCT_IDX_TECHID])

                                if hasattr(player, 'techs'):
                                    techEff = Rules.techImprEff[player.techs.get(struct[STRUCT_IDX_TECHID], Rules.techBaseImprovement)]
                                else:
                                    techEff = Rules.techImprEff[Rules.techBaseImprovement]

                                HPturn = max(1, int(0.02 * tech.maxHP * techEff))
                                turnsToDestroy = math.ceil(struct[STRUCT_IDX_HP] / HPturn)

                                if turnsToDestroy < 48:
                                    dispDestr = major
                                    fgColorDestr = gdata.sevColors[gdata.MAJ]
                                    if turnsToDestroy < 24:
                                        dispDestr = critical
                                        fgColorDestr = gdata.sevColors[gdata.CRI]
                                else:
                                    dispDestr = minor
                                    fgColorDestr = None

                                if not status & STRUCT_STATUS_ON:
                                    # structure is off
                                    if dispDestr:
                                        items.append(ui.Item(planet.name, tOID = planetID, tType = T_PLANET, foreground = fgColorDestr,
                                            vDescription = _('Structure (%s) is off and will be destroyed in %s turns.') % (tech.name, res.formatTime(turnsToDestroy))))

                                elif status & STRUCT_STATUS_DETER:
                                    problem = _('is deteriorating and will be destroyed in %s turns') % res.formatTime(turnsToDestroy)
                                    disp = major
                                    fgColor = gdata.sevColors[gdata.MAJ]
                                elif status & STRUCT_STATUS_NOBIO:
                                    problem = _('has insufficient supply of biomatter')
                                    disp = info
                                    fgColor = gdata.sevColors[gdata.INFO]
                                elif status & STRUCT_STATUS_NOEN:
                                    problem = _('has insufficient supply of energy')
                                    disp = info
                                    fgColor = gdata.sevColors[gdata.INFO]
                                elif status & STRUCT_STATUS_NOPOP:
                                    problem = _('has insufficient supply of workers')
                                    disp = info
                                    fgColor = gdata.sevColors[gdata.INFO]
                                elif status & STRUCT_STATUS_REPAIRING:
                                    problem = _('is repairing')
                                    disp = info
                                    fgColor = gdata.sevColors[gdata.INFO]

                                if problem and disp:
                                    items.append(ui.Item(planet.name, tOID = planetID, tType = T_PLANET, foreground = fgColor,
                                        vDescription = _('Structure (%s) %s.') % (tech.name, problem)))

                for planetID, quantity in buildingQuantity.items():
                    planet = planetCopies[planetID]
                    # test, if there is total quantity of building as target for this planet
                    if planet.plSlots < len(planet.slots) + quantity and major:
                        # walk infos and search for all planets, that are building
                        # on planet founded above
                        for (sourceID, targetID), quantity in buildingInfo.items():
                            if planetID == targetID:
                                source = client.get(sourceID, noUpdate = 1)
                                items.append(ui.Item(source.name, tOID = sourceID, tType = T_PLANET, foreground = gdata.sevColors[gdata.MAJ],
                                            vDescription = _('There is no space for all constructed buildings on %s.') % (planet.name)))

                # check bio for system
                if bio < 0 and self.win.vSystems.checked:
                    disp = minor
                    fgColor = None
                    surplusTurns = totalBio / (-bio)
                    if surplusTurns < 168:
                        disp = major
                        fgColor = gdata.sevColors[gdata.MAJ]
                    if surplusTurns < 48:
                        disp = critical
                        fgColor = gdata.sevColors[gdata.CRI]

                    if disp:
                        if totalBio > 0:
                            items.append(ui.Item(obj.name, tOID = obj.oid, tType = T_SYSTEM, foreground = fgColor,
                                         vDescription = _('Bio decreasing - last turn change %d, surplus %d (%s).') % (bio, totalBio,res.formatTime(surplusTurns))))
                        else:
                            items.append(ui.Item(obj.name, tOID = obj.oid, tType = T_SYSTEM, foreground = fgColor,
                                         vDescription = _('Bio decreasing - last turn change %d, surplus %d.') % (bio, totalBio)))

                #check en for system
                if en < 0 and self.win.vSystems.checked:
                    disp = minor
                    fgColor = None
                    surplusTurns = totalEn / (-en)
                    if surplusTurns < 168:
                        disp = major
                        fgColor = gdata.sevColors[gdata.MAJ]
                    if surplusTurns < 48:
                        disp = critical
                        fgColor = gdata.sevColors[gdata.CRI]

                    if disp:
                        if totalEn > 0:
                            items.append(ui.Item(obj.name, tOID = obj.oid, tType = T_SYSTEM, foreground = fgColor,
                                        vDescription = _('Energy decreasing - last turn change %d, surplus %d (%s).') % (en, totalEn,res.formatTime(surplusTurns))))
                        else:
                            items.append(ui.Item(obj.name, tOID = obj.oid, tType = T_SYSTEM, foreground = fgColor,
                                         vDescription = _('Energy decreasing - last turn change %d, surplus %d.') % (en, totalEn)))

            # check fleets
            elif obj.type == T_FLEET and self.win.vFleets.checked:
                if hasattr(obj, 'owner') and obj.owner == player.oid:
                    energyReserve = obj.storEn  * 100 / obj.maxEn
                    system = None
                    disp = major
                    fgColor = gdata.sevColors[gdata.MAJ]
                    note = _(' and IS NOT refueling')

                    maxRefuelMax = 0
                    if hasattr(obj, 'orbiting') and obj.orbiting:
                        system = client.get(obj.orbiting, noUpdate = 1)
                        if hasattr(system, 'planets'):
                            for planetID in system.planets:
                                planet = client.get(planetID, noUpdate = 1)
                                if hasattr(planet, 'owner') and hasattr(planet, 'refuelMax'):
                                    if player.diplomacyRels.has_key(planet.owner):
                                        dipl = client.getDiplomacyWith(planet.owner)
                                        if dipl.pacts.has_key(PACT_ALLOW_TANKING) and dipl.pacts[PACT_ALLOW_TANKING][0] == PACT_ACTIVE:
                                            maxRefuelMax = max(maxRefuelMax, planet.refuelMax)
                                    else:
                                        if planet.owner == player.oid:
                                            maxRefuelMax = max(maxRefuelMax, planet.refuelMax)

                            if maxRefuelMax > 0:
                                disp = info
                                fgColor = gdata.sevColors[gdata.INFO]
                                note = _(' and IS refueling')
                                if maxRefuelMax <= energyReserve:
                                    note = _(' and CAN refuel, but reach planet maximum refuel amount')

                    else:
                        continue

                    systemName = res.getUnknownName()
                    if system and hasattr(system, "name"):
                        systemName = system.name

                    # check fleets energy reserve
                    if energyReserve < 50 and maxRefuelMax == 0:
                        disp = major
                        fgColor = gdata.sevColors[gdata.MAJ]
                        if energyReserve < 25 and maxRefuelMax == 0:
                            disp = critical
                            fgColor = gdata.sevColors[gdata.CRI]
                    else:
                        fgColor = gdata.sevColors[gdata.INFO]
                        disp = info

                    # is fleet named?
                    if hasattr(obj,'customname') and obj.customname:
                        name = obj.customname
                    else:
                        name = getattr(obj, "name", None)

                    if energyReserve == 100 and info and disp:
                        items.append(ui.Item(systemName, tOID = obj.oid, tType = T_FLEET,foreground = gdata.sevColors[gdata.INFO],
                                    vDescription = _('Fleet "%s" has full fuel tanks.') % (name)))
                    elif disp:
                        items.append(ui.Item(systemName, tOID = obj.oid, tType = T_FLEET,foreground = fgColor,
                                    vDescription = _('Fleet "%s" is low on fuel [%d %%]%s.') % (name, energyReserve, note)))


        queConstValues = [0, 0, 0, 0, 0]
        queEtc = [0, 0, 0, 0, 0]
        for queue in xrange(5):
            quePlanets, queEffProd = globalQueueStats[queue]
            for task in player.prodQueues[queue]:
                if task.isShip:
                    tech = client.getPlayer().shipDesigns[task.techID]
                else:
                    tech = client.getFullTechInfo(task.techID)
                queConstValues[queue] += task.quantity * tech.buildProd
            if queEffProd > 0:
                queEtc[queue] = math.ceil(float(queConstValues[queue])/queEffProd)
            else:
                queEtc[queue] = 99999

        # creation of items with production queue [default one] problems
        for planetID, totalEtc, queueLen in prodQueueProblems:
            planet = client.get(planetID, noUpdate = 1)

            # check empty production queue
            if queueLen == 0 and planet.effProdProd > 0 and queConstValues[0] == 0 and critical:
                items.append(ui.Item(planet.name, tOID = planetID, tType = T_PLANET,
                    foreground = gdata.sevColors[gdata.CRI],
                    vDescription = _('Production queue is empty.')))

            # check end of production queue
            if totalEtc+queEtc[0] < 48:
                fgColor = None
                disp = minor
                if totalEtc+queEtc[0] < 24:
                    disp = major
                    fgColor = gdata.sevColors[gdata.MAJ]
                    if disp:
                        items.append(ui.Item(planet.name, tOID = planetID, tType = T_PLANET, foreground = fgColor,
                            vDescription = _('Production queue may end in {0} turns ({1} directly in planet queue), {2} item(s) on list.'.format(res.formatTime(totalEtc+queEtc[0]), res.formatTime(totalEtc), queueLen))))

        # creation of items with global queue problems
        for queue in xrange(1, 5):
            queName = res.globalQueueName(queue)
            quePlanets = globalQueueStats[queue][0]
            # check empty global production queue with at least one planet [so its relevant]
            if queConstValues[queue] == 0 and  quePlanets > 0 and critical:
                items.append(ui.Item(_('Global queue ' + queName), tType = T_QUEUE,
                    foreground = gdata.sevColors[gdata.CRI],
                    vDescription = _('Global production queue {0} used by {1} planet(s) is empty.'.format(queName, quePlanets))))

            # check end of global production queue
            elif queEtc[queue] < 48:
                fgColor = None
                disp = minor
                if queEtc[queue] < 24:
                    disp = major
                    fgColor = gdata.sevColors[gdata.MAJ]
                if disp:
                    items.append(ui.Item(_('Global queue ' + queName), tType = T_QUEUE, foreground = fgColor,
                        vDescription = _('Global production queue {0} used by {1} planet(s) runs out in {2} turns.'.format(queName, quePlanets, res.formatTime(queEtc[queue])))))

        # check research queue
        if self.win.vResearch.checked:
            totalEtc = 0
            # compute length of research queue
            for task in player.rsrchQueue:
                tech = client.getTechInfo(task.techID)
                fulltech = client.getFullTechInfo(task.techID)
                researchSci = Utils.getTechRCost(player, task.techID, task.improvement)
                maxImprovement = min(Rules.techMaxImprovement,fulltech.maxImprovement)
                maxImpTotalSci = 0
                if task.improveToMax and task.improvement < maxImprovement:
                    for impr in range(task.improvement+1,maxImprovement+1):
                        maxImpTotalSci += Utils.getTechRCost(player, task.techID, impr)
                if task.changeSci > 0:
                    value = float(researchSci - task.currSci) / max(task.changeSci, player.effSciPoints)
                    totalEtc += int(value + 1)
                    if player.effSciPoints != 0:
                        totalEtc += float(maxImpTotalSci) / player.effSciPoints
                elif task.changeSci < 0:
                    totalEtc -= float(task.currSci) / min(task.changeSci, player.effSciPoints)
                elif player.effSciPoints > 0:
                    value = float(researchSci) / player.effSciPoints
                    totalEtc += int(value + 1)
                    totalEtc += float(maxImpTotalSci) / player.effSciPoints
                else:
                    totalEtc = 99999
                    break

            # check empty research queue
            if totalEtc == 0 and len(player.rsrchQueue) == 0 and player.effSciPoints > 0 and major:
                items.append(ui.Item(_('Research'), tType = T_TECHNOLOGY, foreground = gdata.sevColors[gdata.MAJ],
                    vDescription = _('Research queue is empty.')))
            # check short reseach queue
            elif totalEtc < 48:
                disp = minor
                fgColor = None
                if totalEtc < 24:
                    disp = major
                    fgColor = gdata.sevColors[gdata.MAJ]

                if disp:
                    items.append(ui.Item(_('Research'), tType = T_TECHNOLOGY, foreground = fgColor,
                                vDescription = _('Research queue ends in %s turns, %d item(s) on list.') % (res.formatTime(totalEtc), len(player.rsrchQueue))))

        self.win.vProblems.items = items
        self.win.vProblems.itemsChanged()

    def onClose(self, widget, action, data):
        self.hide()

    def onShowSource(self, widget, action, data):
        item = self.win.vProblems.selection[0]
        if item.tType == T_FLEET:
            object = client.get(item.tOID, noUpdate = 1)
            # center on map
            if hasattr(object, "x"):
                gdata.mainGameDlg.win.vStarMap.highlightPos = (object.x, object.y)
                gdata.mainGameDlg.win.vStarMap.setPos(object.x, object.y)
                self.hide()
                return
        elif item.tType in (T_SYSTEM, T_PLANET):
            if item.tOID != OID_NONE:
                gdata.mainGameDlg.onSelectMapObj(None, None, item.tOID)
                return
        elif item.tType == T_TECHNOLOGY:
            gdata.mainGameDlg.researchDlg.display()
            return
        elif item.tType == T_QUEUE:
            gdata.mainGameDlg.globalQueuesDlg.display()
        self.win.setStatus(_("Cannot show location."))

    def onShowLocation(self, widget, action, data):
        item = self.win.vProblems.selection[0]
        if item.tType in (T_SYSTEM, T_PLANET, T_FLEET):
            object = client.get(item.tOID, noUpdate = 1)
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
            modal = 1,
            escKeyClose = 1,
            movable = 0,
            title = _("Problems Locator"),
            titleOnly = isSmallWin,
            #rect = ui.Rect((screenWidth - width) / 2, ((screenHeight - height) / 2) * (not isSmallWin), width, height),
            rect = ui.Rect((screenWidth - 800 - 4 * (not isSmallWin)) / 2, (screenHeight - 600 - 4 * (not isSmallWin)) / 2, width, height),
            layoutManager = ui.SimpleGridLM(),
        )
        self.win.subscribeAction('*', self)
        # first row is window title
        rows -= 1

        ui.Listbox(self.win, layout = (0, 0, cols, rows - 2), id = 'vProblems',
            columns = [(_('System'), 'text', 10, ui.ALIGN_W),
            (_('Problem description'), 'vDescription', 30, ui.ALIGN_W)],
            columnLabels = 1, action='onShowSource', rmbAction='onShowLocation')

        btnWidth = 4
        ui.Check(self.win, layout = (btnWidth * 0, rows - 2, btnWidth, 1), id = 'vSystems',
            text = _('Systems'), action = 'onToggleCondition', checked = 1)
        ui.Check(self.win, layout = (btnWidth * 1, rows - 2, btnWidth, 1), id = 'vPlanets',
            text = _('Planets'), action = 'onToggleCondition', checked = 1)
        ui.Check(self.win, layout = (btnWidth * 2, rows - 2, btnWidth, 1), id = 'vFleets',
            text = _('Fleets'), action = 'onToggleCondition', checked = 1)
        ui.Check(self.win, layout = (btnWidth * 3, rows - 2, btnWidth, 1), id = 'vResearch',
            text = _('Research'), action = 'onToggleCondition', checked = 1)

        ui.Check(self.win, layout = (btnWidth * 6, rows - 2, btnWidth, 1), id = 'vCritical',
            text = _('Critical'), action = 'onToggleCondition', checked = 1)
        ui.Check(self.win, layout = (btnWidth * 7, rows - 2, btnWidth, 1), id = 'vMajor',
            text = _('Major'), action = 'onToggleCondition', checked = 1)
        ui.Check(self.win, layout = (btnWidth * 8, rows - 2, btnWidth, 1), id = 'vMinor',
            text = _('Minor'), action = 'onToggleCondition', checked = 1)
        ui.Check(self.win, layout = (btnWidth * 9, rows - 2, btnWidth, 1), id = 'vInfo',
            text = _('Info'), action = 'onToggleCondition', checked = 0)

        # dialog bottom line
        ui.Title(self.win, layout = (0, rows - 1, cols - 5, 1))
        ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Close"), action = 'onClose')

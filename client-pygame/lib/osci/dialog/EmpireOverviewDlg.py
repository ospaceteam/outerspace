#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of IGE - Outer Space.
#
#  IGE - Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  IGE - Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with IGE - Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import pygameui as ui
import re
from osci import gdata, client
from ige.ospace.Const import *
from ige.ospace import Rules
import string, math
from PlanetsAnalysisDlg import PlanetsAnalysisDlg
from FleetsAnalysisDlg import FleetsAnalysisDlg

class EmpireOverviewDlg:
	"""Displays Empire overview dialog.

	Dialog displays curent users statistics
	and amount of each strategic resource.
	"""
	def __init__(self, app):
		self._textRows = 0
		self.app = app
		self.planetsAnalysisDlg = PlanetsAnalysisDlg(app)
		self.fleetsAnalysisDlg = FleetsAnalysisDlg(app)
		self.createUI()

	def display(self):
		self.show()
		# show window
		if not self.win.visible:
			self.win.show()

	def hide(self):
		self.win.setStatus(_("Ready."))
		self.win.hide()

	def update(self):
		if self.win.visible:
			self.show()

	def show(self):
		player = client.getPlayer()
		if not hasattr(player.stats, "prodProd"):
			self.win.vText.text = [_("No data available")]
			self.win.vText.offsetRow = 0
			self.win.vText.vertScrollbar.slider.position = 0
			self.win.vText.vertScrollbar.slider.max = 1
			return
			
		text = []
		# imperator or leader
		if player.imperator == 1:
			text.append(_("You are LEADER of the galaxy."))
			text.append("")
		elif player.imperator == 2:
			text.append(_("You are IMPERATOR of the galaxy."))
			text.append("")
		elif player.imperator >= 3:
			text.append(_("You are IMPERATOR of the galaxy."))
			text.append(_("You have the right to end this galaxy."))
			text.append("")

		# strategic resources
		# check ownership of the strat. resources
		srChange = {}
		for planetID in player.planets:
			planet = client.get(planetID)
			if planet.plStratRes:
				sr = planet.plStratRes
				srChange[sr] = srChange.get(sr, 0) + 1

		if player.stratRes or srChange:
			text.append(_("Strategic resources:"))
			# merge owned and change
			srList = player.stratRes.keys()
			for sr in srChange:
				if sr not in srList:
					srList.append(sr)
			srList.sort()
			for sr in srList:
				text.append(u'    %s: %s (+%d)' % (
					gdata.stratRes[sr],
					player.stratRes.get(sr, 0),
					srChange.get(sr, 0),
				))
			text.append('')
		# statistics
		# compute some stats
		realProd = 0
		realSci = 0
		for planetID in player.planets:
			planet = client.get(planetID)
			realProd += planet.effProdProd
			realSci += planet.effProdSci
		for fleetID in player.fleets:
			fleet = client.get(fleetID)
		# display data
		text.append(_("Statistics:"))
		text.append(u'    %s: %s' % (_("Population"), getattr(player.stats, "storPop", "?")))
		if hasattr(player.stats, "storPop") and player.govPwr > player.stats.storPop and player.stats.storPop > 0:
			text.append(u'    %s: %s (%d %% unused)' % (_("Gov. power"), player.govPwr, 100 * (player.govPwr - player.stats.storPop) / player.govPwr))
		else:
			text.append(u'    %s: %s' % (_("Gov. power"), player.govPwr))
		text.append(u'    %s: %s' % (_("Planets"), getattr(player.stats, "planets", "?")))
		text.append(u'    %s: %s' % (_("Structures"), getattr(player.stats, "structs", "?")))
		text.append(u'    %s: %s' % (_("Raw production"), getattr(player.stats, "prodProd", "?")))
		text.append(u'    %s: %d' % (_("Total production"), realProd))
		text.append(u'    %s: %s' % (_("Raw research"), getattr(player.stats, "prodSci", "?")))
		text.append(u'    %s: %s' % (_("Total reseach"), player.effSciPoints))
		text.append(u'    %s: %s' % (_("Military power"), getattr(player.stats, "fleetPwr", "?")))
		if hasattr(player, "pirateFame"):
			text.append(_(u'    %s: %s (%+d %% production eff.)') % (
				_("Fame"),
				player.pirateFame,
				player.pirateFame,
			))
			text.append(u'    %s: %s fame' % (
				_("New colony cost"),
				int(Rules.pirateColonyCostMod * len(player.planets)),
			))
			text.append(u'    %s: %s fame' % (
				_("New colony on planet with TL3 resouce cost"),
				int(Rules.pirateTL3StratResColonyCostMod * Rules.pirateColonyCostMod * len(player.planets)),
			))
		text.append("")
		# Production
		text.append(_("Production:"))
		text.append(u'    %s: %s' % (_("Raw production"), getattr(player.stats, "prodProd", "?")))
		if player.prodIncreasePool > 0:
			ratio = (Rules.unusedProdMod * player.prodIncreasePool) / player.stats.prodProd
			text.append(u'    %s: %d (%+d %% effectivity)' % (
				_("Unused production"), player.prodIncreasePool, min(ratio * 100, math.sqrt(ratio) * 100)
			))
		# fleet support
		total = getattr(player.stats, 'fleetSupportProd', 0) + player.fleetUpgradePool * Rules.operProdRatio
		if total > player.stats.prodProd / 10:
			effectivity = - 100 * (total - player.stats.prodProd / 10) / max(player.stats.prodProd, 1)
		else:
			effectivity = 0
		text.append(u'    %s: %+d (first %d CP is free, %+d %% effectivity)' % (
			_("Fleet support"),
			- total,
			player.stats.prodProd / 10,
			effectivity,
		))
		text.append(u"    %s: %d %%" % (_("Empire effectivity"), int(100 * player.prodEff)))
		text.append(u'    %s: %d' % (_("Total production"), realProd))
		text.append("")
		# Research
		text.append(_("Research:"))
		text.append(u"    %s: %d %%" % (_("Empire effectivity"), int(100 * player.sciEff)))
		if hasattr(player.stats, "prodSci"):
			text.append(u"    %s: %s" % (_("Raw production"), getattr(player.stats, "prodSci", "?")))
		text.append(u'    %s: %s' % (_("Real production"), realSci))
		if player.techLevel < 7:
			popSupp = int(player.stats.storPop * Rules.sciPtsPerCitizen[player.techLevel])
		else:
			popSupp = 0
		text.append(u'    %s: %+d' % (_("Population support"), -popSupp))
		text.append(u'    %s: %+d' % (_("From pacts"), player.effSciPoints + popSupp - player.sciPoints))
		text.append(u'    %s: %d' % (_("Total research"), player.effSciPoints))
		text.append("")
		# Fleet
		civ = [0, 0, 0, 0]
		mil = [0, 0, 0, 0]
		mp = [0, 0, 0, 0]
		for fleetID in player.fleets:
			fleet = client.get(fleetID)
			for designID, hp, shield, exp in fleet.ships:
				tech = player.shipDesigns[designID]
				if tech.isMilitary:
					mil[tech.combatClass] += 1
				else:
					civ[tech.combatClass] += 1
				mp[tech.combatClass] += int(tech.combatPwr * float(hp + shield) / (tech.maxHP + tech.shieldHP))
		text.append(_("Fleet:"))
		text.append(u'    %s: %d (%d CP to support)' % (_("Upgrade Pool"), player.fleetUpgradePool, - player.fleetUpgradePool * Rules.operProdRatio))
		text.append(u'    %s: %d civ + %d mil, %d MP' % (_("Small ships"), civ[0], mil[0], mp[0]))
		text.append(u'    %s: %d civ + %d mil, %d MP' % (_("Medium ships"), civ[1], mil[1], mp[1]))
		text.append(u'    %s: %d civ + %d mil, %d MP' % (_("Large ships"), civ[2], mil[2], mp[2]))
		self.win.vText.text = text
		self.win.vText.offsetRow = 0
		self.win.vText.vertScrollbar.slider.position = 0
		self.win.vText.vertScrollbar.slider.max = len(text)

	def onClose(self, widget, action, data):
		self.hide()

	def onOK(self, widget, action, data):
		self.hide()

	def onPlanetsAnalysis(self, widget, action, data):
		self.planetsAnalysisDlg.display()

	def onFleetsAnalysis(self, widget, action, data):
		self.fleetsAnalysisDlg.display()

	def onMenu(self, widget, action, data):
		r = widget.rect
		self.analysisMenu.show((self.win.rect.left + r.left, self.win.rect.bottom - 4 * r.height))

	def createUI(self):
		screenWidth, screenHeight = gdata.scrnSize
		# size of dialog in layout metrics (for SimpleGridLM)
		cols = 23
		rows = 27
		# dialog width and height in pixels
		width = cols * 20 + 5
		height = rows * 20 + 4
		#creating dialog window
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			movable = 0,
			title = _("Empire Overview"),
			rect = ui.Rect((screenWidth - width) / 2, (screenHeight - height) / 2, width, height),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# first row is window title
		rows -= 1

		s = ui.Scrollbar(self.win, layout = (cols - 1, 0, 1, rows - 1))
		t = ui.Text(self.win, layout = (0, 0, cols - 1, rows - 1), id = "vText", editable = 0)
		self._textRows = rows - 1
		t.attachVScrollbar(s)

		# dialog bottom line
		ui.Title(self.win, layout = (0, rows - 1, cols - 10, 1))
		ui.TitleButton(self.win, layout = (cols - 10, rows - 1, 5, 1), text = _("Analysis"), action = "onMenu")
		ui.TitleButton(self.win, layout = (cols - 5, rows - 1, 5, 1), text = _("Close"), action = "onClose")

		# analysis menu
		self.analysisMenu = ui.Menu(self.app, title = _("Field of analysis"),
			width = 5,
			items = [
				ui.Item(_("Planets"), action = "onPlanetsAnalysis"),
				ui.Item(_("Fleets"), action = "onFleetsAnalysis"),
			]
		)
		self.analysisMenu.subscribeAction("*", self)

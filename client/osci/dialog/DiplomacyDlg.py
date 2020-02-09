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
from osci.StarMapWidget import StarMapWidget
from osci import gdata, res, client
import ige.ospace.Const as Const
from ige.ospace import Rules
from ColorDefinitionDlg import ColorDefinitionDlg
import ige

# pact actions
ACTION_NONE = 0
ACTION_CANCEL = 1
ACTION_CONFIRM = 3
ACTION_OFFER = 4

class DiplomacyDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()
        self.selectedPartyID = Const.OID_NONE
        self.selectedPactID = Const.OID_NONE
        self.galaxyScenario = None
        self.cDlg = ColorDefinitionDlg(self.app)

    def display(self):
        self.show()
        self.win.show()
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)

    def hide(self):
        self.win.setStatus(_("Ready."))
        self.win.hide()
        self.galaxyScenario = None
        # unregister updates
        if self in gdata.updateDlgs:
            gdata.updateDlgs.remove(self)

    def update(self):
        if not self.galaxyScenario:
            galaxyID = client.getPlayer().galaxy
            galaxy = client.get(galaxyID)
            self.galaxyScenario = galaxy.scenario
        self.show()

    def _getContactEntry(self, contactID):
        contact = client.get(contactID, publicOnly=1)
        dipl = client.getDiplomacyWith(contactID)
        if dipl.relChng > 0:
            suffix = _(" +")
        elif dipl.relChng < 0:
            suffix = _(" -")
        else:
            suffix = _("")
        relation = _("%s%s") % (_(gdata.relationNames[int(dipl.relation / 125)]), suffix)
        contactName = _("%s [elect]") % contact.name if client.getPlayer().voteFor == contactID else contact.name
        if getattr(dipl, "stats", None):
            return ui.Item(contactName,
                           tContactID=contactID,
                           tRelation=relation,
                           tRelation_raw=dipl.relation,
                           tPopulation=dipl.stats.storPop,
                           tPlanets=dipl.stats.planets,
                           tStructures=dipl.stats.structs,
                           tProduction=dipl.stats.prodProd,
                           tScience=dipl.stats.prodSci,
                           tFleetPwr=dipl.stats.fleetPwr,
                           tContact=(_("-"), _("Mobile"), _("Static"))[dipl.contactType],
                           foreground=res.getPlayerColor(contactID),
                           tooltipTitle=_("Relation"),
                           tooltip=_("Relation %d, change %+d") % (dipl.relation, dipl.relChng),
                           statustip=_("Relation %d, change %+d") % (dipl.relation, dipl.relChng))
        else:
            return ui.Item(contactName,
                           tContactID=contactID,
                           tRelation=relation,
                           tRelation_raw=dipl.relation,
                           tPopulation="-",
                           tPlanets="-",
                           tStructures="-",
                           tProduction="-",
                           tScience="-",
                           tFleetPwr="-",
                           tContact=(_("None"), _("Mobile"), _("Static"))[dipl.contactType],
                           foreground=res.getPlayerColor(contactID))

    def _getPlayerEntry(self):
        player = client.getPlayer()

        contactName = _("%s [elect]") % player.name if player.voteFor == player.oid else player.name
        return ui.Item(contactName,
                       tContactID=player.oid,
                       tRelation="-",
                       tRelation_raw=10000,
                       tPopulation=getattr(player.stats, "storPop", "?"),
                       tPlanets=getattr(player.stats, "planets", "?"),
                       tStructures=getattr(player.stats, "structs", "?"),
                       tProduction=getattr(player.stats, "prodProd", "?"),
                       tScience=getattr(player.stats, "prodSci", "?"),
                       tFleetPwr=getattr(player.stats, "fleetPwr", "?"),
                       tContact="-",
                       foreground=res.getFFColorCode(Const.REL_UNITY))

    def _buildContactList(self):
        player = client.getPlayer()

        items = []
        selected = None
        for contactID in player.diplomacyRels:
            item = self._getContactEntry(contactID)
            items.append(item)
            if self.selectedPartyID == contactID:
                selected = item
        # player
        item = self._getPlayerEntry()
        items.append(item)
        if self.selectedPartyID == player.oid:
            selected = item
        self.win.vContacts.items = items
        self.win.vContacts.selectItem(selected)
        self.win.vContacts.itemsChanged()
        return selected

    def _processVoting(self, selected):
        player = client.getPlayer()

        if self.galaxyScenario == Const.SCENARIO_OUTERSPACE:
            # this is just in case we reloged
            self.win.vAbstain.visible = 1
            self.win.vVoteFor.visible = 1
            self.win.vAbstain.enabled = player.voteFor != Const.OID_NONE
            if selected:
                self.win.vVoteFor.enabled = selected.tContactID != player.voteFor
            else:
                self.win.vVoteFor.enabled = 0
        else:
            self.win.vAbstain.visible = 0
            self.win.vVoteFor.visible = 0

    def _getPactsEntry(self, pactID, dipl):
        pactSpec = Rules.pactDescrs[pactID]

        if pactID in dipl.pacts:
            pactState1 = dipl.pacts[pactID][0]
            if self.partyDipl:
                pactState2 = self.partyDipl.pacts.get(pactID, [Const.PACT_OFF])[0]
                pactState2Text = _(gdata.pactStates[pactState2])
            else:
                pactState2 = Const.PACT_OFF
                pactState2Text = _("N/A")
            item = ui.Item(_(gdata.pactNames[pactID]),
                           tState1=_(gdata.pactStates[pactState1]),
                           tState2=pactState2Text,
                           tPactState=pactState1,
                           foreground=gdata.sevColors[(gdata.DISABLED, gdata.INFO, gdata.MIN)[min(pactState1, pactState2)]])
        else:
            if self.partyDipl:
                pactState2 = self.partyDipl.pacts.get(pactID, [Const.PACT_OFF])[0]
                pactState2Text = _(gdata.pactStates[pactState2])
            else:
                pactState2 = Const.PACT_OFF
                pactState2Text = _("N/A")
            item = ui.Item(_(gdata.pactNames[pactID]),
                           tState1=_(gdata.pactStates[Const.PACT_OFF]),
                           tState2=pactState2Text,
                           tPactState=Const.PACT_OFF,
                           foreground=gdata.sevColors[gdata.DISABLED])
        item.tPactID = pactID
        return item

    def _processPacts(self):
        player = client.getPlayer()

        items = []
        selected = None
        if self.selectedPartyID and self.selectedPartyID != player.oid:
            dipl = client.cmdProxy.getPartyDiplomacyRels(player.oid, self.selectedPartyID)[0]
            if not dipl:
                dipl = client.getDiplomacyWith(self.selectedPartyID)
            for pactID in gdata.pacts:
                pactSpec = Rules.pactDescrs[pactID]
                if not pactSpec.validityInterval[0] < dipl.relation < pactSpec.validityInterval[1]:
                    continue
                items.append(self._getPactsEntry(pactID, dipl))
        self.win.vPacts.items = items
        self.win.vPacts.selectItem(selected)
        self.win.vPacts.itemsChanged()

    def show(self):
        selected = self._buildContactList()
        self._processVoting(selected)
        self._processPacts()

        # Highlight buttons
        self.win.vHighlight.enabled = 1 - int(gdata.config.defaults.highlights == 'yes')
        self.win.vUHighlight.enabled = int(gdata.config.defaults.highlights == 'yes')

    def onContactSelected(self, widget, action, data):
        if self.win.vContacts.selection:
            self.selectedPartyID = self.win.vContacts.selection[0].tContactID
        else:
            self.selectedPartyID = None
        self.partyDipl = client.cmdProxy.getPartyDiplomacyRels(client.getPlayerID(), self.selectedPartyID)[1]
        self.update()
        self.onPactSelected(None, None, None)

    def onPactSelected(self, widget, action, data):
        if self.win.vPacts.selection:
            self.selectedPactID = self.win.vPacts.selection[0].tPactID
        else:
            self.selectedPactID = None
            self.win.vChangePactState.enabled = 0
            self.win.vPactConditions.enabled = 0
            self.win.vPactCondReset.enabled = 0
            self.win.vConditions.items = []
            self.win.vConditions.itemsChanged()
            return
        self.win.vChangePactState.enabled = 1
        self.win.vPactConditions.enabled = 1
        self.win.vPactCondReset.enabled = 1
        item = self.win.vPacts.selection[0]
        if item.tPactState == Const.PACT_OFF:
            self.win.vChangePactState.text = _("Enable")
            self.win.vChangePactState.data = "ENABLE"
        else:
            self.win.vChangePactState.text = _("Disable")
            self.win.vChangePactState.data = "DISABLE"
        # show conditions
        items = []
        selected = []
        dipl = client.getDiplomacyWith(self.selectedPartyID)
        conditions = dipl.pacts.get(item.tPactID, [0, item.tPactID])[1:]
        if self.partyDipl:
            partnerConditions = self.partyDipl.pacts.get(item.tPactID, [0])[1:]
        else:
            partnerConditions = []
        states = (_(" "), _("Required"))
        self.win.vCondTitle.text = _('Conditions for pact: %s') % _(gdata.pactNames[item.tPactID])
        for pactID in gdata.pacts:
            item = ui.Item(_(gdata.pactNames[pactID]),
                           tState1=states[pactID in conditions],
                           tState2=states[pactID in partnerConditions],
                           tPactID=pactID,
                           foreground=gdata.sevColors[(gdata.NONE, gdata.MAJ, gdata.MIN)[(pactID in conditions) + (pactID in partnerConditions)]])
            items.append(item)
            if pactID in conditions:
                selected.append(item)
        self.win.vConditions.items = items
        for item in selected:
            self.win.vConditions.selectItem(item)
        self.win.vConditions.itemsChanged()

    def onPactChange(self, widget, action, data):
        citem = self.win.vContacts.selection[0]
        pitem = self.win.vPacts.selection[0]
        pactState = pitem.tPactState
        if widget.data == "ENABLE":
            pactState = Const.PACT_INACTIVE
        elif widget.data == "DISABLE":
            pactState = Const.PACT_OFF
        if widget.data == "CONDSRESET":
            conditions = [pitem.tPactID]
        else:
            conditions = []
            for item in self.win.vConditions.selection:
                conditions.append(item.tPactID)
        try:
            self.win.setStatus(_('Executing CHANGE PACT CONDITIONS command...'))
            player = client.getPlayer()
            player.diplomacyRels = client.cmdProxy.changePactCond(player.oid,
                citem.tContactID, pitem.tPactID, pactState, conditions)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onVoteFor(self, widget, action, data):
        citem = self.win.vContacts.selection[0]
        try:
            self.win.setStatus(_('Executing ELECT command...'))
            player = client.getPlayer()
            player.voteFor = client.cmdProxy.setVoteFor(player.oid,
                citem.tContactID)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onAbstain(self, widget, action, data):
        try:
            self.win.setStatus(_('Executing ELECT command...'))
            player = client.getPlayer()
            player.voteFor = client.cmdProxy.setVoteFor(player.oid, Const.OID_NONE)
            self.win.setStatus(_('Command has been executed.'))
        except ige.GameException, e:
            self.win.setStatus(e.args[0])
            return
        self.update()

    def onHighlight(self, widget, action, data):
        gdata.config.defaults.highlights = 'yes'
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)
        gdata.mainGameDlg.update()
        self.update()

    def onUHighlight(self, widget, action, data):
        gdata.config.defaults.highlights = 'no'
        # register for updates
        if self not in gdata.updateDlgs:
            gdata.updateDlgs.append(self)
        gdata.mainGameDlg.update()
        self.update()

    def onDeleteHighlight(self, widget, action, data):
        playerID = self.win.vContacts.selection[0].tContactID
        if gdata.playersHighlightColors.has_key(playerID):
            del gdata.playersHighlightColors[playerID]
        self.update()
        gdata.mainGameDlg.update()

    def onColorDefinition(self, widget, action, data):
        playerID = self.win.vContacts.selection[0].tContactID
        if gdata.playersHighlightColors.has_key(playerID):
            self.cDlg.display(color = gdata.playersHighlightColors[playerID], confirmAction = self.onColorDefinitionConfirmed)
        else:
            self.cDlg.display(confirmAction = self.onColorDefinitionConfirmed)

    def onColorDefinitionConfirmed(self):
        playerID = self.win.vContacts.selection[0].tContactID
        gdata.playersHighlightColors[playerID] = self.cDlg.color
        self.update()
        gdata.mainGameDlg.update()

    def onClose(self, widget, action, data):
        self.hide()

    def onHighlightMenu(self, widget, action, data):
        self.eventPopup.show()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             titleOnly=(w == 800 and h == 600),
                             movable=0,
                             title=_('Diplomacy'),
                             rect=ui.Rect((w - 800 - 4 * (w != 800)) / 2,
                                          (h - 600 - 4 * (h != 600)) / 2,
                                          800 + 4 * (w != 800),
                                          580 + 4 * (h != 600)),
                             layoutManager=ui.SimpleGridLM())
        self.win.subscribeAction('*', self)
        # player listing
        ui.Listbox(self.win, layout=(0, 0, 40, 14), id='vContacts',
                   columns=((_('Name'), 'text', 8, ui.ALIGN_W),
                            (_('Relation'), 'tRelation', 4, ui.ALIGN_E),
                            (_('Population'), 'tPopulation', 4, ui.ALIGN_E),
                            (_('Planets'), 'tPlanets', 4, ui.ALIGN_E),
                            (_('Structures'), 'tStructures', 4, ui.ALIGN_E),
                            (_('Production'), 'tProduction', 4, ui.ALIGN_E),
                            (_('Research'), 'tScience', 4, ui.ALIGN_E),
                            (_('Military pwr'), 'tFleetPwr', 4, ui.ALIGN_E),
                            (_("Contact"), "tContact", 4, ui.ALIGN_E)),
                   columnLabels=1, action="onContactSelected", rmbAction="onHighlightMenu")
        # Voting
        ui.Button(self.win, layout=(0, 14, 5, 1), text=_("Elect"),
                  id="vVoteFor", action="onVoteFor")
        ui.Button(self.win, layout=(5, 14, 5, 1), text=_("Abstain"),
                  id="vAbstain", action="onAbstain")
        # Highlights
        ui.Button(self.win, layout=(24, 14, 8, 1), text=_("Highlights On"),
                  id="vHighlight", action="onHighlight")
        ui.Button(self.win, layout=(32, 14, 8, 1), text=_("Highligh Off"),
                  id="vUHighlight", action="onUHighlight")
        # pacts
        ui.Title(self.win, layout=(0, 15, 20, 1), text=_('Pacts'),
                 font='normal-bold', align=ui.ALIGN_W)
        ui.Listbox(self.win, layout=(0, 16, 20, 10), id='vPacts',
                   columns=((_('I'), 'tState1', 3, ui.ALIGN_W),
                            (_('Partner'), 'tState2', 3, ui.ALIGN_W),
                            (_('Pact'), 'text', 13, ui.ALIGN_W)),
                   columnLabels=1, action="onPactSelected")
        ui.Button(self.win, layout=(0, 26, 20, 1), text=_("On"),
                  id="vChangePactState", action="onPactChange", enabled=0)
        # conditions
        ui.Title(self.win, layout=(20, 15, 20, 1), text=_('Conditions'),
                 id="vCondTitle", font='normal-bold', align=ui.ALIGN_W)
        ui.Listbox(self.win, layout=(20, 16, 20, 10), id='vConditions',
                   columns=((_('I'), 'tState1', 3, ui.ALIGN_W),
                            (_('Partner'), 'tState2', 3, ui.ALIGN_W),
                            (_('Pact'), 'text', 13, ui.ALIGN_W)),
                   columnLabels=1, multiselection=1)
        ui.Button(self.win, layout=(20, 26, 15, 1), text=_("Change"),
                  id="vPactConditions", action="onPactChange", enabled=0, data="CONDS")
        ui.Button(self.win, layout=(35, 26, 5, 1), text=_("Reset"),
                  id="vPactCondReset", action="onPactChange", enabled=0, data="CONDSRESET")
        # status bar + submit/cancel
        ui.TitleButton(self.win, layout=(35, 27, 5, 1), text=_('Close'), action='onClose')
        ui.Title(self.win, id='vStatusBar', layout=(0, 27, 35, 1), align=ui.ALIGN_W)
        # highlight menu
        self.eventPopup = ui.Menu(self.app, title=_("Highligh actions"),
                                  items=[ui.Item(_("Define color"), action="onColorDefinition"),
                                         ui.Item(_("Disable highlight"), action="onDeleteHighlight")])
        self.eventPopup.subscribeAction("*", self)

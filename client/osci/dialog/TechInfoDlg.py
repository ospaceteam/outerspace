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
import string

import pygameui as ui

from ige.ospace import Rules, Utils
import ige.ospace.Const as Const

from osci import gdata, res, client


def cclass2Text(cclass):
    return [_("small"), _("medium"), _("large"), _("planet")][cclass]


def structWeapons2Text(array):
    string = ''
    i = 0
    j = 0
    for weaponNum in array:
        if i>3:
            break
        if weaponNum > 0:
            if j > 0:
                string += _(', ')
            string += _('%d') % ( weaponNum )
            string += [_("S"), _("M"), _("L"), _("P"), _("?"), _("?"), _("?"), _("?"), _("?"), _("?")][i]
            j+=1
        i+=1
    return string


def bool2Text(value):
    return _("Yes") if value else _("No")


def perc2Text(value):
    return _('%d%%') % (value * 100)


def percBase1_2Text(value):
    return _('%+d%%') % ((value - 1) * 100)


def perc100_2Text(value):
    return _('%d%%') % (value)


def getTechName(techID):
    try:
        return client.getFullTechInfo(techID).name
    except:
        return _('Unknown')


def getTechShortname(techID):
    tech = client.getFullTechInfo(techID)
    try:
        return tech.shortname if tech.shortname else tech.name
    except:
        return _('Unknown')


def getRateName(rate):
    return _('%d Turns') % (int(rate))


V_NONE = 0x00
V_STRUCT = 0x01
V_HULL = 0x02
V_SEQUIP = 0x04
V_PROJECT = 0x08
V_EFF = 0x10 # attr * techEff
V_EFF_REV = 0x20 # attr / techEff
V_ALL = V_STRUCT|V_HULL|V_SEQUIP|V_PROJECT

techAttrs = {}

defaultAttr = (_('Not specified'), V_NONE, True, None, int)


def addAttr(attr, descr, props, showIfDefault, default=0, convertor=int):
    global techAttrs
    techAttrs[attr] = (descr, props, showIfDefault, default, convertor)


addAttr('buildProd', _('Constr. reqs - construction points'), V_ALL, 0)

addAttr('operBio', _('Operational reqs - biomatter'), V_ALL, 0)
addAttr('operMin', _('Operational reqs - minerals'), V_ALL, 0)
addAttr('operEn', _('Operational reqs - energy'), V_ALL, 0)
addAttr('operWorkers', _('Operational reqs - workers'), V_ALL, 0)

addAttr('prodBio', _('Production - biomatter'), V_STRUCT | V_EFF, 0)
addAttr('prodMin', _('Production - minerals'), V_STRUCT | V_EFF, 0)
addAttr('prodEn', _('Production - energy'), V_STRUCT | V_EFF, 0)
addAttr('prodPop', _('Production - population'), V_STRUCT | V_EFF, 0)
addAttr('prodProd', _('Production - constr. points'), V_STRUCT | V_PROJECT | V_EFF, 0)
addAttr('prodSci', _('Production - research points'), V_STRUCT | V_PROJECT | V_EFF, 0)
addAttr('prodEnv', _('Production - env. effect'), V_STRUCT | V_EFF, 0)

addAttr('solarMod', _('Orbital Shift Effect'), V_STRUCT | V_EFF, 0)

addAttr('storBio', _('Storage - biomatter'), V_STRUCT | V_EFF, 0)
addAttr('storMin', _('Storage - minerals'), V_STRUCT | V_EFF, 0)
addAttr('storEn', _('Storage - energy'), V_ALL | V_EFF, 0)
addAttr('storPop', _('Accommodate population'), V_STRUCT | V_EFF, 0)

addAttr('revoltThr', _('Lowers revolt threshold by'), V_STRUCT | V_PROJECT | V_EFF, 0)
addAttr('moraleTrgt', _('Increases max morale by'), V_STRUCT | V_PROJECT | V_EFF, 0)
addAttr('govPwr', _('Government power'), V_STRUCT | V_EFF, 0)
addAttr('maxHP', _('Hit points'), V_STRUCT | V_HULL | V_SEQUIP | V_EFF, 0)

addAttr('scannerPwr', _('Scanner power'), V_STRUCT | V_SEQUIP | V_EFF, 0)
addAttr('planetShield', _('Planetary shield'), V_STRUCT | V_EFF, 0)
addAttr('systemAtt', _('Fleet attack (bonus)'), V_STRUCT | V_EFF, 0)
addAttr('systemDef', _('Fleet defense (bonus)'), V_STRUCT | V_EFF, 0)
addAttr('refuelMax', _('Maximum refuel percent'), V_STRUCT | V_EFF, 0, convertor=perc100_2Text)
addAttr('refuelInc', _('Refuel increase percent'), V_STRUCT | V_EFF, 0, convertor=perc100_2Text)
addAttr('repairShip', _('Ship repair percent'), V_STRUCT | V_EFF, 0, convertor=perc100_2Text)
addAttr('upgradeShip', _('Ship upgrade capacity'), V_STRUCT | V_EFF, 0)
addAttr('trainShipInc', _('Exp. points per turn'), V_STRUCT | V_EFF, 0, convertor=float)
addAttr('trainShipMax', _('Exp. cap (base exp multiple)'), V_STRUCT | V_EFF, 0)
addAttr('fleetSpeedBoost', _('Boost speed of fleets'), V_STRUCT | V_EFF, 0, convertor=float)
addAttr('structWeapons', _('Weapons'), V_STRUCT, 0, convertor=structWeapons2Text)

addAttr('weaponClass', _('Target class'), V_SEQUIP, True, convertor=cclass2Text)
addAttr('weaponDmgMin', _('Weapon minimum damage'), V_SEQUIP | V_EFF, 0)
addAttr('weaponDmgMax', _('Weapon maximum damage'), V_SEQUIP | V_EFF, 0)
addAttr('weaponIsMissile', _('Missile weapon (ECM counts)'), V_SEQUIP | V_HULL, 0, convertor=bool2Text)
addAttr('weaponIgnoreShield', _('Weapon ignore shield'), V_SEQUIP | V_HULL, 0, convertor=bool2Text)
addAttr('weaponAtt', _('Weapon attack'), V_SEQUIP | V_EFF, 0)
addAttr('weaponROF', _('Weapon Rate Of Fire'), V_SEQUIP, 0, convertor=float)

addAttr('mineclass', _('Mine Class Deployed'), V_STRUCT, 0, convertor=getTechShortname)
addAttr('minenum', _('Maximum Supported Mines'), V_STRUCT | V_EFF, 0, convertor=int)
addAttr('minerate', _('Mine Rate of Deploy'), V_STRUCT | V_EFF_REV, 0, convertor=getRateName)

addAttr('minHull', _('Minimum required hull'), V_SEQUIP | V_HULL, 0, convertor=cclass2Text)
addAttr('weight', _('Weight'), V_SEQUIP | V_HULL, 0)
addAttr('slots', _('Slots'), V_SEQUIP | V_HULL, 0)
addAttr('maxWeight', _('Maximum payload'), V_HULL, 0)
addAttr('engPwr', _('Engine power'), V_SEQUIP | V_EFF, 0)
addAttr('engStlPwr', _('Engine sub-light speed power'), V_SEQUIP | V_EFF, 0)

addAttr('signature', _('Scan signature'), V_SEQUIP | V_HULL, 0)
addAttr('signatureCloak', _('Signature visibility'), V_SEQUIP | V_HULL, 0)
addAttr('signatureDecloak', _('Signature visibility'), V_SEQUIP | V_HULL, 0)
addAttr('minSignature', _('Min. signature'), V_SEQUIP | V_HULL, 0)

addAttr('combatDef', _('Combat defence'), V_SEQUIP | V_HULL | V_EFF, 0)
addAttr('combatAtt', _('Combat attack'), V_SEQUIP | V_HULL | V_EFF, 0)
addAttr('missileDef', _('Missile defence'), V_SEQUIP | V_EFF, 0)
addAttr('combatAttPerc', _('Combat defense (extra)'), V_SEQUIP | V_HULL | V_EFF, 0, default=1, convertor=percBase1_2Text)
addAttr('combatDefPerc', _('Combat attack (extra)'), V_SEQUIP | V_HULL | V_EFF, 0, default=1, convertor=percBase1_2Text)
addAttr('missileDefPerc', _('Missile defence (extra)'), V_SEQUIP | V_EFF, 0, default=1, convertor=percBase1_2Text)

addAttr('shieldPerc', _('Shield strength'), V_SEQUIP | V_HULL | V_EFF, 0, convertor=perc2Text)
addAttr('shieldRechargeFix', _('Shield recharge fixed'), V_SEQUIP | V_HULL | V_EFF, 0)
addAttr('shieldRechargePerc', _('Shield recharge percent'), V_SEQUIP | V_HULL | V_EFF, 0, convertor=perc2Text)
addAttr('damageAbsorb', _('Armor damage absorbstion'), V_SEQUIP | V_HULL, 0)

addAttr('addMP', _('Device MP'), V_SEQUIP | V_HULL, 0)


class TechInfoDlg:

    def __init__(self, app):
        self.app = app
        self.createUI()

    def display(self, techID):
        self.techID = techID
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

    def _getGranularDependency(self, techMod):
        descr = []
        if techMod[0]:
            descr.append(_(" - %d %% on planet's environment") % (techMod[0] * 100))
        if techMod[1]:
            descr.append(_(" - %d %% on planet's min. abundance") % (techMod[1] * 100))
        if techMod[2]:
            descr.append(_(" - %d %% on planet's en. abundance") % (techMod[2] * 100))
        if techMod[3]:
            descr.append(_(" - %d %% is not dependent on any planet's attribute") % (techMod[3] * 100))
        return descr

    def _productionDependency(self, tech):
        descr = []
        for techModName, text in [('prodBioMod', _('Bio')),
                                  ('prodEnMod', _('Energy')),
                                  ('prodProdMod', _('Constr. point')),
                                  ('prodSciMod', _('Research point'))]:
            techMod = getattr(tech, techModName)
            if techMod not in ([0, 0, 0, 0], [0, 0, 0, 1]):
                descr.append(_("%s production depends:" % text))
                descr.extend(self._getGranularDependency(techMod))
                descr.append("")
        return descr

    def _getStratResText(self, tech, attr):
        try:
            resourceDict = getattr(tech, attr)
        except AttributeError:
            return ""
        requiredStratRes = []
        for res in resourceDict:
            try:
                amount = resourceDict[res] / float(Rules.stratResAmountBig)
            except IndexError:
                # this is case of research resources - it's pure list, not a dictionary
                requiredStratRes += [gdata.stratRes[res]]
            else:
                # continuation of build resources
                requiredStratRes += ['{0} ({1})'.format(gdata.stratRes[res], amount)]
        return ', '.join(requiredStratRes)

    def _researchContext(self, tech):
        player = client.getPlayer()

        descr = []
        improvement = player.techs.get(self.techID, 0)
        if hasattr(tech, 'researchMod'):
            prefix = _('Improvement') if improvement else _('Research')
            descr.append(_('%s costs: %d') % (prefix, Utils.getTechRCost(player, self.techID)))
            descr.append('')
        # requires
        if tech.researchRequires and improvement == 0:
            descr.append(_('Research requires:'))
            for tmpTechID, improvement in tech.researchRequires:
                tmpTech = client.getTechInfo(tmpTechID)
                descr.append(_(' - %s improvement %d (TL%d)') % (tmpTech.name, improvement, tmpTech.level))
            if hasattr(tech, "researchReqSRes"):
                for stratRes in tech.researchReqSRes:
                    descr.append(_(" - %s (strategic resource)") % (gdata.stratRes[stratRes]))
            descr.append('')
        if hasattr(tech, "researchDisables") and tech.researchDisables:
            descr.append(_("Research disables:"))
            for tmpTechID in tech.researchDisables:
                tmpTech = client.getTechInfo(tmpTechID)
                descr.append(_(" - %s (TL%d)") % (tmpTech.name, tmpTech.level))
            descr.append('')
        return descr

    def _preResearch(self, tech):
        descr = []
        descr.append(_('Estimated use:'))
        descr.extend(tech.textPreRsrch.split('\n'))
        descr.append('')
        return descr

    def _getTechType(self, tech):
        techType = V_NONE
        if getattr(tech, 'isStructure', 0):
            techType = V_STRUCT
        elif getattr(tech, 'isShipHull', 0):
            techType = V_HULL
        elif getattr(tech, 'isShipEquip', 0):
            techType = V_SEQUIP
        elif getattr(tech, 'isProject', 0):
            techType = V_PROJECT
        return techType

    def _prepareTypeButtons(self, tech):
        techType = self._getTechType(tech)

        self.win.vStruct.pressed = techType == V_STRUCT
        self.win.vStruct.enabled = getattr(tech, 'isStructure', 0)
        self.win.vHull.pressed = techType == V_HULL
        self.win.vHull.enabled = getattr(tech, 'isShipHull', 0)
        self.win.vSEquip.pressed = techType == V_SEQUIP
        self.win.vSEquip.enabled = getattr(tech, 'isShipEquip', 0)
        self.win.vProject.pressed = techType == V_PROJECT
        self.win.vProject.enabled = getattr(tech, 'isProject', 0)

    def _processAttributes(self, tech):
        techEff = Rules.techImprEff[client.getPlayer().techs.get(self.techID, Rules.techBaseImprovement)]
        items = []
        techType = self._getTechType(tech)

        for attr in dir(tech):
            value = getattr(tech, attr)
            descr, props, showIfDef, default, convertor = techAttrs.get(attr, defaultAttr)
            if techType & props and (value != default or showIfDef):
                item = ui.Item(descr, tValue=convertor(value))
                if V_EFF & props:
                    item.font = 'normal-bold'
                    item.tValue = convertor(value * techEff)
                elif V_EFF_REV & props:
                    item.font = 'normal-bold'
                    item.tValue = convertor(value / techEff)
                items.append(item)
        return items

    def _getPlayerRace(self):
        player = client.getPlayer()
        raceChoosen = None
        if player.techLevel == 1:
            techID = set(player.techs).intersection(set([1990, 1991, 1992])).pop()  # these are the race-selecting techs
            raceChoosen = client.getTechInfo(techID).data
        else:
            raceChoosen = player.race
        return raceChoosen

    def _researchEnablement(self, tech):
        descr = []
        tmp = []
        raceChoosen = self._getPlayerRace()

        for improvement in range(1, 6):
            for tmpTechID in tech.researchEnables[improvement]:
                tmpTech = client.getTechInfo(tmpTechID)
                racesDispl = ""
                if 0 < len(tmpTech.researchRaces) < 3 and not raceChoosen:
                    racesDispl = _(", only for %s") % tmpTech.researchRaces
                if not raceChoosen or not tmpTech.researchRaces or raceChoosen in tmpTech.researchRaces:
                    tmp.append(_(' - %s (with improvement %d, on TL%d%s)') % (tmpTech.name, improvement, tmpTech.level, racesDispl))
        if tmp:
            descr.append(_('Research/Improvement enables:'))
            descr.extend(tmp)
            descr.append('')
        return descr

    def _stratResources(self, tech):
        descr = []

        requiredStratResForBuilding = self._getStratResText(tech, "buildSRes")
        requiredStratResForResearch = self._getStratResText(tech, "researchReqSRes")
        if len(requiredStratResForBuilding) > 0 or len(requiredStratResForResearch) > 0:
            descr.append(_("Required strategic resources:"))
            if len(requiredStratResForBuilding) > 0:
                descr.append(_(" - for building: %s") % requiredStratResForBuilding)
            if len(requiredStratResForResearch) > 0:
                descr.append(_(" - for research: %s") % requiredStratResForResearch)

            descr.append("")
        return descr

    def _descriptionFlavor(self, tech):
        descr = []

        # description
        descr.append(_('Description:'))
        if tech.textDescr != u'Not specified':
            descr.extend(tech.textDescr.split('\n'))
        else:
            descr.extend(tech.textPreRsrch.split('\n'))
        descr.append('')
        # flavor
        descr.append(_('Rumours:'))
        descr.extend(tech.textFlavor.split('\n'))
        descr.append('')
        return descr

    def show(self):
        tech = client.getTechInfo(self.techID)
        self.win.title = _('Technology: %s (TL%d)') % (tech.name, tech.level)
        # fill data
        # fill description
        descr = []
        descr.extend(self._researchContext(tech))
        if hasattr(tech, 'partialData') and hasattr(tech, 'textPreRsrch'):
            # preresearch info
            descr.extend(self._preResearch(tech))
        elif not hasattr(tech, 'partialData'):
            descr.extend(self._researchEnablement(tech))
            descr.extend(self._productionDependency(tech))
            descr.extend(self._stratResources(tech))
            descr.extend(self._descriptionFlavor(tech))

        if not len(descr):
            descr.append(_('No information available'))
        #
        self.win.vDescr.text = descr

        self._prepareTypeButtons(tech)

        self.win.vData.items = self._processAttributes(tech)
        self.win.vData.itemsChanged()

    def onCancel(self, widget, action, data):
        self.hide()

    def onClose(self, widget, action, data):
        self.hide()

    def createUI(self):
        w, h = gdata.scrnSize
        self.win = ui.Window(self.app,
                             modal=1,
                             escKeyClose=1,
                             titleOnly=w == 800 and h == 600,
                             movable=0,
                             title=_('Split Fleet'),
                             rect=ui.Rect((w - 800 - 4 * (w != 800)) / 2,
                                          (h - 600 - 4 * (h != 600)) / 2,
                                          800 + 4 * (w != 800),
                                          580 + 4 * (h != 600)),
                             layoutManager=ui.SimpleGridLM())
        self.win.subscribeAction('*', self)
        # tech data
        ui.Title(self.win, layout=(0, 0, 18, 1), text=_('Data'),
                 align=ui.ALIGN_W, font='normal-bold')
        ui.Listbox(self.win, layout=(0, 1, 18, 25), id='vData',
                   columns=((_('Property'), 'text', 11, ui.ALIGN_W),
                   (_('Value'), 'tValue', 7, ui.ALIGN_E)),
                   columnLabels=0)
        ui.Button(self.win, layout=(1, 26, 4, 1), text=_('Structure'),
                  id='vStruct', toggle=0, data=V_STRUCT)
        ui.Button(self.win, layout=(5, 26, 4, 1), text=_('Ship Hull'),
                  id='vHull', toggle=0, data=V_HULL)
        ui.Button(self.win, layout=(9, 26, 4, 1), text=_('Ship Eq.'),
                  id='vSEquip', toggle=0, data=V_SEQUIP)
        ui.Button(self.win, layout=(13, 26, 4, 1), text=_('Project'),
                  id='vProject', toggle=0, data=V_PROJECT)
        ui.Button(self.win, layout=(17, 26, 1, 1), text='',
                  id='vEmpty1', toggle=0)
        ui.Button(self.win, layout=(0, 26, 1, 1), text='',
                  id='vEmpty2', toggle=0)
        # text field
        ui.Title(self.win, layout=(18, 0, 22, 1), text=_('Description'),
                 align=ui.ALIGN_W, font='normal-bold')
        s = ui.Scrollbar(self.win, layout=(39, 1, 1, 26))
        t = ui.Text(self.win, layout=(18, 1, 21, 26), id='vDescr', editable=0)
        t.attachVScrollbar(s)
        # status bar + submit/cancel
        ui.TitleButton(self.win, layout=(35, 27, 5, 1), text=_('Close'), action='onClose')
        ui.Title(self.win, id='vStatusBar', layout=(0, 27, 35, 1), align=ui.ALIGN_W)

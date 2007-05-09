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
from osci import gdata, res, client
from ige.ospace.Const import *
from ige.ospace import Rules, Utils
import string

def cclass2Text(cclass):
	return [_("small"), _("medium"), _("large"), _("planet")][cclass]

def structWeapons2Text(array):
    string = _('')
    i = 0
    j = 0
    for weaponNum in array:
        if i>3:
            break
        if weaponNum > 0:
            if j > 0:
                string += _(', ')
            string += _('%d') % ( weaponNum )
            string += [_("S"), _("M"), _("L"), _("P"), _("?"),_("?"),_("?"),_("?"),_("?"),_("?")][i]
            j+=1
        i+=1
    return string

def bool2Text(value):
	if value:
		return _("Yes")
	else:
		return _("No")

def perc2Text(value):
    string = _('%d%%') % (value * 100)
    return string

def perc100_2Text(value):
    string = _('%d%%') % (value)
    return string


V_NONE = 0x00
V_STRUCT = 0x01
V_HULL = 0x02
V_SEQUIP = 0x04
V_PROJECT = 0x08
V_EFF = 0x10
V_ALL = V_STRUCT|V_HULL|V_SEQUIP|V_PROJECT

techAttrs = {}

defaultAttr = (_('Not specified'), V_NONE, True, None, int)

def addAttr(attr, descr, props, showIfDefault, default = 0, convertor = int):
	global techAttrs
	techAttrs[attr] = (descr, props, showIfDefault, default, convertor)


addAttr('buildProd', _('Constr. reqs - construction points'), V_ALL, 0)

addAttr('operBio', _('Operational reqs - biomatter'), V_ALL, 0)
addAttr('operMin', _('Operational reqs - minerals'), V_ALL, 0)
addAttr('operEn', _('Operational reqs - energy'), V_ALL, 0)
addAttr('operWorkers', _('Operational reqs - workers'), V_ALL, 0)

addAttr('prodBio', _('Production - biomatter'), V_STRUCT|V_EFF, 0)
addAttr('prodMin', _('Production - minerals'), V_STRUCT|V_EFF, 0)
addAttr('prodEn', _('Production - energy'), V_STRUCT|V_EFF, 0)
addAttr('prodPop', _('Production - population'), V_STRUCT|V_EFF, 0)
addAttr('prodProd', _('Production - constr. points'), V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('prodSci', _('Production - research points'), V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('prodEnv', _('Production - env. effect'), V_STRUCT|V_EFF, 0)

addAttr('storBio', _('Storage - biomatter'), V_STRUCT|V_EFF, 0)
addAttr('storMin', _('Storage - minerals'), V_STRUCT|V_EFF, 0)
addAttr('storEn', _('Storage - energy'), V_ALL|V_EFF, 0)
addAttr('storPop', _('Accommodate population'), V_STRUCT|V_EFF, 0)

addAttr('revoltThr', _('Lowers revolt threshold by'), V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('moraleTrgt', _('Increases max morale by'), V_STRUCT|V_PROJECT|V_EFF, 0)
addAttr('govPwr', _('Government power'), V_STRUCT|V_EFF, 0)
addAttr('maxHP', _('Hit points'), V_STRUCT|V_HULL|V_SEQUIP|V_EFF, 0)

addAttr('scannerPwr', _('Scanner power'), V_STRUCT|V_SEQUIP|V_EFF, 0)
addAttr('planetShield',_('Planetary shield'), V_STRUCT|V_EFF, 0)
addAttr('systemAtt',_('Fleet attack (bonus)'), V_STRUCT|V_EFF, 0)
addAttr('systemDef',_('Fleet defense (bonus)'), V_STRUCT|V_EFF, 0)
addAttr('refuelMax', _('Maximum refuel percent'), V_STRUCT|V_EFF, 0, convertor = perc100_2Text)
addAttr('refuelInc', _('Refuel increase percent'), V_STRUCT|V_EFF, 0, convertor = perc100_2Text)
addAttr('trainShipInc', _('Exp. points per turn'), V_STRUCT|V_EFF, 0, convertor = float)
addAttr('trainShipMax', _('Exp. cap (base exp multiple)'), V_STRUCT|V_EFF, 0)
addAttr('fleetSpeedBoost', _('Boost speed of fleets'), V_STRUCT|V_EFF, 0, convertor = float)
addAttr('structWeapons', _('Weapons'), V_STRUCT, 0, convertor = structWeapons2Text)

addAttr('weaponClass', _('Target class'), V_SEQUIP, True, convertor = cclass2Text)
addAttr('weaponDmgMin', _('Weapon minimum damage'), V_SEQUIP|V_EFF, 0)
addAttr('weaponDmgMax', _('Weapon maximum damage'), V_SEQUIP|V_EFF, 0)
addAttr('weaponIsMissile', _('Missile weapon (ECM counts)'), V_SEQUIP|V_HULL, 0, convertor = bool2Text)
addAttr('weaponIgnoreShield', _('Weapon ignore shield'), V_SEQUIP|V_HULL, 0, convertor = bool2Text)
addAttr('weaponAtt', _('Weapon attack'), V_SEQUIP|V_EFF, 0)
addAttr('weaponROF', _('Weapon Rate Of Fire'), V_SEQUIP, 0, convertor = float)

addAttr('minHull', _('Minimum required hull'), V_SEQUIP|V_HULL, 0, convertor = cclass2Text)
addAttr('weight', _('Weight'), V_SEQUIP|V_HULL, 0)
addAttr('slots', _('Slots'), V_SEQUIP|V_HULL, 0)
addAttr('maxWeight', _('Maximum payload'), V_HULL, 0)
addAttr('engPwr', _('Engine power'), V_SEQUIP|V_EFF, 0)

addAttr('signature', _('Scan signature'), V_SEQUIP|V_HULL, 0)
addAttr('signatureCloak', _('Signature visibility'), V_SEQUIP|V_HULL, 0)
addAttr('signatureDecloak', _('Signature visibility'), V_SEQUIP|V_HULL, 0)
addAttr('minSignature', _('Min. signature'), V_SEQUIP|V_HULL, 0)

addAttr('combatDef', _('Combat defence'), V_SEQUIP|V_HULL|V_EFF, 0)
addAttr('combatAtt', _('Combat attack'), V_SEQUIP|V_HULL|V_EFF, 0)
addAttr('missileDef', _('Missile defence'), V_SEQUIP|V_EFF, 0)
addAttr('combatAttPerc', _('Combat defense (extra)'), V_SEQUIP|V_HULL|V_EFF, 0, convertor = perc2Text)
addAttr('combatDefPerc', _('Combat attack (extra)'), V_SEQUIP|V_HULL|V_EFF, 0, convertor = perc2Text)
addAttr('missileDefPerc', _('Missile defence (extra)'), V_SEQUIP|V_EFF, 0, convertor = perc2Text)

addAttr('shieldPerc', _('Shield strength'), V_SEQUIP|V_HULL|V_EFF, 0, convertor = perc2Text)
addAttr('shieldRechargeFix', _('Shield recharge fixed'), V_SEQUIP|V_HULL|V_EFF, 0)
addAttr('shieldRechargePerc', _('Shield recharge percent'), V_SEQUIP|V_HULL|V_EFF, 0, convertor = perc2Text)
addAttr('damageAbsorb', _('Armor damage absorbstion'), V_SEQUIP|V_HULL, 0)

addAttr('addMP', _('Device MP'), V_SEQUIP|V_HULL, 0)


class TechInfoDlg:

	def __init__(self, app):
		self.app = app
		self.techType = V_NONE
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

	def show(self):
		tech = client.getTechInfo(self.techID)
		player = client.getPlayer()
		techEff = Rules.techImprEff[player.techs.get(self.techID, Rules.techBaseImprovement)]
		self.win.title = _('Technology: %s (TL%d)') % (tech.name, tech.level)
		# fill data
		# fill description
		descr = []
		improvement = player.techs.get(self.techID, 0)
		if hasattr(tech, 'researchMod'):
			if improvement == 0:
				descr.append(_('Research costs: %d') % Utils.getTechRCost(player, self.techID))
				descr.append('')
			elif improvement < Rules.techMaxImprovement:
				descr.append(_('Improvement costs: %d') % Utils.getTechRCost(player, self.techID))
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
		if hasattr(tech, 'partialData') and hasattr(tech, 'textPreRsrch'):
			# preresearch info
			descr.append(_('Estimated use:'))
			descr.extend(tech.textPreRsrch.split('\n'))
			descr.append('')
		elif not hasattr(tech, 'partialData'):
			tmp = []
			for improvement in range(1, 6):
				for tmpTechID in tech.researchEnables[improvement]:
					tmpTech = client.getTechInfo(tmpTechID)
					racesDispl = ""
					raceChoosen = None
					if player.techLevel == 1:
						for techID in player.techs.keys():
							if techID in (1990, 1991, 1992):
								raceChoosen = client.getTechInfo(techID).data
					else:
						raceChoosen = player.race
					if len(tmpTech.researchRaces) > 0 and len(tmpTech.researchRaces) < 3 and not raceChoosen:
						racesDispl = _(", only for %s") % tmpTech.researchRaces
					if not raceChoosen or len(tmpTech.researchRaces) == 0 or raceChoosen in tmpTech.researchRaces:
						tmp.append(_(' - %s (with improvement %d, on TL%d%s)') % (tmpTech.name, improvement, tmpTech.level, racesDispl))
			if tmp:
				descr.append(_('Research/Improvement enables:'))
				descr.extend(tmp)
				descr.append('')
			# production dependency
			if tech.prodBioMod != [0, 0, 0, 0]:
				descr.append(_("Bio production depends:"))
				if tech.prodBioMod[0]: descr.append(_(" - %d %% on planet's environment") % (tech.prodBioMod[0] * 100))
				if tech.prodBioMod[1]: descr.append(_(" - %d %% on planet's min. abundance") % (tech.prodBioMod[1] * 100))
				if tech.prodBioMod[2]: descr.append(_(" - %d %% on planet's en. abundance") % (tech.prodBioMod[2] * 100))
				if tech.prodBioMod[3]: descr.append(_(" - %d %% is not dependent on any planet's attribute") % (tech.prodBioMod[3] * 100))
				descr.append("")
			if tech.prodEnMod != [0, 0, 0, 0]:
				descr.append(_("Energy production depends:"))
				if tech.prodEnMod[0]: descr.append(_(" - %d %% on planet's environment") % (tech.prodEnMod[0] * 100))
				if tech.prodEnMod[1]: descr.append(_(" - %d %% on planet's min. abundance") % (tech.prodEnMod[1] * 100))
				if tech.prodEnMod[2]: descr.append(_(" - %d %% on planet's en. abundance") % (tech.prodEnMod[2] * 100))
				if tech.prodEnMod[3]: descr.append(_(" - %d %% is not dependent on any planet's attribute") % (tech.prodEnMod[3] * 100))
				descr.append("")
			if tech.prodProdMod != [0, 0, 0, 0]:
				descr.append(_("Constr. points production depends:"))
				if tech.prodProdMod[0]: descr.append(_(" - %d %% on planet's environment") % (tech.prodProdMod[0] * 100))
				if tech.prodProdMod[1]: descr.append(_(" - %d %% on planet's min. abundance") % (tech.prodProdMod[1] * 100))
				if tech.prodProdMod[2]: descr.append(_(" - %d %% on planet's en. abundance") % (tech.prodProdMod[2] * 100))
				if tech.prodProdMod[3]: descr.append(_(" - %d %% is not dependent on any planet's attribute") % (tech.prodProdMod[3] * 100))
				descr.append("")
			# decription
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
		#
		self.win.vDescr.text = descr
		# re-set techType if neccessary
		self.techType = self.techType & (
			getattr(tech ,'isStructure', 0) * V_STRUCT |
			getattr(tech ,'isShipHull', 0) * V_HULL |
			getattr(tech ,'isShipEquip', 0) * V_SEQUIP |
			getattr(tech ,'isProject', 0) * V_PROJECT
		)
		if self.techType == V_NONE:
			if getattr(tech ,'isStructure', 0): self.techType = V_STRUCT
			elif getattr(tech ,'isShipHull', 0): self.techType = V_HULL
			elif getattr(tech ,'isShipEquip', 0): self.techType = V_SEQUIP
			elif getattr(tech ,'isProject', 0): self.techType = V_PROJECT
		# set type buttons
		self.win.vStruct.pressed = self.techType == V_STRUCT
		self.win.vStruct.enabled = getattr(tech ,'isStructure', 0)
		self.win.vHull.pressed = self.techType == V_HULL
		self.win.vHull.enabled = getattr(tech, 'isShipHull', 0)
		self.win.vSEquip.pressed = self.techType == V_SEQUIP
		self.win.vSEquip.enabled = getattr(tech, 'isShipEquip', 0)
		self.win.vProject.pressed = self.techType == V_PROJECT
		self.win.vProject.enabled = getattr(tech, 'isProject', 0)
		# fill data
		items = []
		for attr in dir(tech):
			value = getattr(tech, attr)
			descr, props, showIfDef, default, convertor = techAttrs.get(attr, defaultAttr)
			if self.techType & props and (value != default or showIfDef):
				item = ui.Item(descr, tValue = convertor(value))
				if V_EFF & props:
					item.font = 'normal-bold'
					item.tValue = convertor(value * techEff)
				items.append(item)
		self.win.vData.items = items
		self.win.vData.itemsChanged()

	def onShowType(self, widget, action, data):
		self.techType = widget.data
		self.update()

	def onCancel(self, widget, action, data):
		self.hide()

	def onClose(self, widget, action, data):
		self.hide()

	def createUI(self):
		w, h = gdata.scrnSize
		self.win = ui.Window(self.app,
			modal = 1,
			escKeyClose = 1,
			titleOnly = w == 800 and h == 600,
			movable = 0,
			title = _('Split Fleet'),
			rect = ui.Rect((w - 800 - 4 * (w != 800)) / 2, (h - 600 - 4 * (h != 600)) / 2, 800 + 4 * (w != 800), 580 + 4 * (h != 600)),
			layoutManager = ui.SimpleGridLM(),
		)
		self.win.subscribeAction('*', self)
		# tech data
		ui.Title(self.win, layout = (0, 0, 18, 1), text = _('Data'),
			align = ui.ALIGN_W, font = 'normal-bold')
		ui.Listbox(self.win, layout = (0, 1, 18, 25), id = 'vData',
			columns = ((_('Property'), 'text', 11, ui.ALIGN_W),
			(_('Value'), 'tValue', 7, ui.ALIGN_E)),
			columnLabels = 0)
		ui.Button(self.win, layout = (1, 26, 4, 1), text = _('Structure'),
			id = 'vStruct', toggle = 1, action = 'onShowType', data = V_STRUCT)
		ui.Button(self.win, layout = (5, 26, 4, 1), text = _('Ship Hull'),
			id = 'vHull', toggle = 1, action = 'onShowType', data = V_HULL)
		ui.Button(self.win, layout = (9, 26, 4, 1), text = _('Ship Eq.'),
			id = 'vSEquip', toggle = 1, action = 'onShowType', data = V_SEQUIP)
		ui.Button(self.win, layout = (13, 26, 4, 1), text = _('Project'),
			id = 'vProject', toggle = 1, action = 'onShowType', data = V_PROJECT)
		ui.Button(self.win, layout = (17, 26, 1, 1), text = _(''),
			id = 'vEmpty1', toggle = 0)
		ui.Button(self.win, layout = (0, 26, 1, 1), text = _(''),
			id = 'vEmpty2', toggle = 0)
		# text field
		ui.Title(self.win, layout = (18, 0, 22, 1), text = _('Description'),
			align = ui.ALIGN_W, font = 'normal-bold')
		s = ui.Scrollbar(self.win, layout = (39, 1, 1, 26))
		t = ui.Text(self.win, layout = (18, 1, 21, 26), id = 'vDescr', editable = 0)
		t.attachVScrollbar(s)
		# status bar + submit/cancel
		ui.TitleButton(self.win, layout = (35, 27, 5, 1), text = _('Close'), action = 'onClose')
		ui.Title(self.win, id = 'vStatusBar', layout = (0, 27, 35, 1), align = ui.ALIGN_W)
		#@self.win.statusBar = self.win.vStatusBar

import string

from ige.ospace import Rules
from ige.ospace import Const

class Design:
	def __init__(self, configText, improvement):
		self.__dict__["empty"] = True
		self.improvement = improvement
		self.hull = None
		self.hullName = None
		self.cockpitName = None
		self.name = "New Design"
		self.eqIDs = {}
		if configText != None:
			self.empty = False
			mainParts = string.split(configText, ";")
			self.name = mainParts[0]
			self.hull = int(mainParts[1])
			self.eqIDs = {}
			components = string.split(mainParts[2], ",")
			for component in components:
				componentParts = string.split(component, ":")
				self.eqIDs[int(componentParts[0])] = int(componentParts[1])
			
		self.makeFullSpec()

	def __setattr__(self, name, value):
		if self.empty and value != None:
			self.__dict__["empty"] = False
		self.__dict__[name] = value

	def getConfigText(self):
		eqIDs = ""
		for eqID in self.eqIDs:
			eqIDs = "%s,%d:%d" % (eqIDs, eqID, self.eqIDs[eqID])
		# eqIDs starts with comma
		return "%s;%d;%s" % (self.name, self.hull, eqIDs[1:])

	def makeFullSpec(self, improvements = []):
		hull = None
		self.combatAtt = 0
		self.combatDef = 0
		self.missileDef = 0
		self.storEn = 0
		self.operEn = 0
		self.maxHP = 0
		self.scannerPwr = 0
		self.engPwr = 0
		self.signature = 0
		self.minSignature = 0
		self.baseExp = 0
		self.freeSlots = 0
		self.shieldHP = 0
		self.payload = 0
		self.buildProd = 0
		self.level = 0
		self.combatClass = 0
		if self.hull != None:
			hull = Rules.techs[self.hull]
	
			# initial values
			techEff = Rules.techImprEff[self.improvement]
			self.hullName = hull.name
			self.cockpit = None
			self.cockpitName = ""
			self.level = hull.level
			self.combatClass = hull.combatClass
			self.improvements = improvements
			self.buildProd = hull.buildProd
			self.buildSRes = hull.buildSRes[:] # we need copy
			self.operEn = hull.operEn
			self.storEn = hull.storEn * techEff
			self.weight = hull.weight
			self.signature = hull.signature
			self.minSignature = hull.minSignature
			self.combatAtt = hull.combatAtt * techEff
			self.combatDef = hull.combatDef * techEff
			self.missileDef = hull.missileDef * techEff
			self.scannerPwr = max(hull.scannerPwr * techEff, Rules.scannerMinPwr)
			self.autoRepairFix = hull.autoRepairFix
			self.autoRepairPerc = hull.autoRepairPerc
			self.shieldRechargeFix = hull.shieldRechargeFix
			self.shieldRechargePerc = hull.shieldRechargePerc
			self.maxHP = int(hull.maxHP * techEff)
	
		self.engPwr = 0
		self.slots = 0
		self.upgradeTo = 0
		self.shieldHP = 0
		self.weaponIDs = []
		self.deployStructs = []
		self.isMilitary = 0
		self.baseExp = 0
		self.weight = 1
		shieldPerc = 0.0
		# add equipment
		counter = {}
		installations = {}
		errors = []
		for techID in self.eqIDs:
			tech = Rules.techs[techID]
			techEff = Rules.techImprEff[self.improvement]
			for i in xrange(0, self.eqIDs[techID]):
				counter[tech.subtype] = 1 + counter.get(tech.subtype, 0)
				installations[techID] = 1 + installations.get(techID, 0)
				# check min hull req
				if tech.minHull > self.combatClass:
					errors.append("Minimum hull requirement not satisfied.")
				# check maximum installations
				if tech.maxInstallations and installations[tech.id] > tech.maxInstallations:
					errors.append("Maximum number of equipment installations exceeded.")
				# add values
				self.level = max(self.level, tech.level)
				self.buildProd += tech.buildProd
				self.buildSRes.extend(tech.buildSRes)
				self.storEn += tech.storEn * techEff
				self.weight += tech.weight
				self.signature += tech.signature
				self.minSignature = max(self.minSignature, tech.minSignature)
				self.combatDef += tech.combatDef * techEff
				self.missileDef += tech.missileDef * techEff
				self.slots += tech.slots
				self.engPwr += tech.engPwr * techEff
				self.maxHP += tech.maxHP * techEff
				shieldPerc += tech.shieldPerc * techEff
				self.scannerPwr = max(self.scannerPwr, tech.scannerPwr * techEff)
				self.combatAtt += tech.combatAtt * techEff
				self.operEn += tech.operEn
				self.autoRepairFix = max(self.autoRepairFix, tech.autoRepairFix * techEff)
				self.autoRepairPerc = max(self.autoRepairPerc, tech.autoRepairPerc * techEff)
				self.shieldRechargeFix = max(self.shieldRechargeFix, tech.shieldRechargeFix * techEff)
				self.shieldRechargePerc = max(self.shieldRechargePerc, tech.shieldRechargePerc * techEff)
				# if weapon - register only
				if tech.subtype == "seq_wpn":
					self.weaponIDs.append(techID)
					self.isMilitary = 1
					weapon = Rules.techs[techID]
					self.baseExp += (weapon.weaponDmgMin + weapon.weaponDmgMax) / 2 * weapon.weaponROF
				if tech.subtype == "seq_ctrl":
					self.cockpit = techID
					self.cockpitName = tech.name

		# check various conditions
		if counter.get("seq_ctrl", 0) == 0:
			errors.append("No control module in the self.")
		if counter.get("seq_ctrl", 0) > 1:
			errors.append("Only one control module in the self. allowed.")
		if hull != None and self.slots > hull.slots:
			errors.append("Hull does not have so many slots to hold all equipment.")
		if hull != None and self.weight > hull.maxWeight:
			errors.append("self. is too heavy.")
		# compute secondary paramaters
		self.speed = float(self.engPwr) / self.weight
		self.baseExp = int(self.baseExp * Rules.shipBaseExpMod) + Rules.shipBaseExp[self.combatClass]
		# compute base attack/defence
		self.combatAtt += int(self.speed)
		self.combatDef += int(self.speed)
		self.missileDef += int(self.speed / 2.0)
		# improvements
		if len(improvements) > Rules.shipMaxImprovements:
			errors.append("Too many improvements.")
		for i in improvements:
			if i == SI_SPEED:
				self.speed *= Rules.shipImprovementMod
			elif i == SI_TANKS:
				self.storEn *= Rules.shipImprovementMod
			elif i == SI_ATT:
				self.combatAtt *= Rules.shipImprovementMod
			elif i == SI_DEF:
				self.combatDef *= Rules.shipImprovementMod
				self.missileDef *= Rules.shipImprovementMod
			elif i == SI_HP:
				self.maxHP *= Rules.shipImprovementMod
			elif i == SI_SHIELDS:
				self.shieldHP *= Rules.shipImprovementMod
		# round values down
		self.storEn = int(self.storEn)
		self.combatAtt = int(self.combatAtt / (self.combatClass + 1.0))
		self.combatDef = int(self.combatDef / (self.combatClass + 1.0))
		self.missileDef = int(self.missileDef / (self.combatClass + 1.0))
		self.maxHP = int(self.maxHP)
		self.shieldHP = int(self.maxHP * shieldPerc)
		self.scannerPwr = int(self.scannerPwr)
		self.engPwr = int(self.engPwr)
		self.signature = int(self.signature)
		self.baseExp = int(self.baseExp)
		if hull != None:
			self.freeSlots = hull.slots - self.slots
			self.payload = hull.maxWeight - self.weight
		# compute attack power
		attackPwr = 0.0
		refDefence = 10.0
		refAttack = 10.0
		refDmg = 10.0
		for weaponID in self.weaponIDs:
			weapon = Rules.techs[weaponID]
			dmg = (weapon.weaponDmgMin + weapon.weaponDmgMax) / 2 * weapon.weaponROF
			att = self.combatAtt + weapon.weaponAtt
			attackPwr += (att / float(att + refDefence) * dmg)
		# defence
		self.combatPwr = int(attackPwr * (self.maxHP + self.shieldHP) / (refAttack / (refAttack + self.combatDef) * refDmg))
		# fix signature
		self.signature = max(1, self.signature, self.minSignature)

		return errors
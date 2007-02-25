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

import sys, copy
from ige import log
from ige.ospace import Const
import sha, os.path
import cPickle as pickle
import types
from ige.ospace import TechHandlers
from xml.sax.handler import ContentHandler
from ige.IDataHolder import IDataHolder
import xml.sax

def noop(*args, **kwargs):
	return 1

attrs = {
	# types of technologies
	'isDiscovery' : 0,
	'isStructure' : 0,
	'isProject': 0,
	'isShipEquip' : 0,
	'isShipHull' : 0,
	'isStarting' : 0,
	"subtype": "techSubtype",
	"level": 0, 
	"maxImprovement": 5, #Rules.techMaxImprovement,
	"isMilitary": 0,
	# construction costs & conditions
	'buildProd' : 0,
	'buildTurns' : 1,
	'buildSRes': ['resource'],
	# operation costs
	'operBio' : 0,
	'operEn' : 0,
	"operWorkers": 0,
	# production
	'prodBio' : 0, # bio
	'prodEn' : 0, # energy
	'prodProd' : 0, # production
	'prodSci' : 0, # science
	'prodEnv': 0, # enviromental effect
	'prodPop': 0, # produce population
	'prodBioMod': [0.0, 0.0, 0.0, 0.0], # tuple of (plBio, plMin, plEn, default)
	'prodEnMod': [0.0, 0.0, 0.0, 0.0], # dtto
	'prodProdMod': [0.0, 0.0, 0.0, 0.0], # dtto
	# storage
	'storBio' : 0,
	'storProd' : 0,
	'storEn' : 0,
	'storPop' : 0,
	# morale affecting
	'revoltThr': 0,
	'moraleTrgt': 0,
	'govPwr': 0,
	# misc
	"unpackPop": 0,
	'envDmg' : 0,
	'maxHP' : 0,
	'scannerPwr': 0,
	"structWeapons": [0],
        "planetShield": 0, #planetary shield; when structure built, shield = 0; shield will regenerate at 2% per turn until equal to this value. Structures do not add shield strength; strongest shield = planet shield
        "systemAtt": 0,
        "systemDef": 0,
	"refuelMax": 0,
	"refuelInc": 0,
	"repairShip": 0.0,
	"upgradeShip": 0,
	"trainShipInc": 0.0, # how many exp/turn
	"trainShipMax": 0, # exp. cap (in base exps), not affected by techEff
	"fleetSpeedBoost": 0.0, # speed boost for stargates
	"fullInfo": 0, # if True, show full tech info even player not own tech
	# ship equipment
        "addMP" : 0, #for extra MP to be added to ship equipment
	'combatClass' : 0,
	'combatAtt': 0, #not cumulative for equipment; cumulative for hull, drives, cockpits, etc
	'combatDef': 0, #not cumulative for equipment; cumulative for hull, drives, cockpits, etc
	"missileDef": 0, #not cumulative for equipment; cumulative for hull, drives, cockpits, etc
        "combatAttPerc": 1.0, #multiplier of ATT; min of 100%; not cumulative
        "combatDefPerc": 1.0, #multiplier of DEF; min of 100%; not cumulative
        "missileDefPerc": 1.0, #multiplier of missile DEF; min of 100%; not cumulative
	'unpackStruct': '',
        'deployHandlerID' : '', #technology ID of tech to find deployHandlerFunction & deployHandlerValidator (this can be the deployable device OR a project)
        'deployHandlerFunction' : noop, #function name of TechHandler
        'deployHandlerValidator' : noop, #function name of TechHandler Validator
	'signature': 0, #cumulative
        'signatureCloak': 1.0, #max of 1.0 is effective; not cumulative
        'signatureDecloak': 1.0, #min of 1.0 is effective; not cumulative
	"minSignature": 0,
	"slots": 0,
	"weight": 0,
	"maxWeight": 0,
	"engPwr": 0,
	"shieldPerc": 0.0, # how many percent of maxHP have shields
	"minHull": 0,
        "maxHull": 10, #just make this higher than the largest hull so we know it doesn't break anything
	"maxInstallations": 0,
	"shieldRechargeFix": 0, # fixed amount of HP/turn to recharge
	"shieldRechargePerc": 0.0, # how many percent of shieldHP/turn is recharged
        "hardShield": 0.0, #shield penetrating weapons will penetrate at 100%; use as 1-hardShield for penentration level (hardShield percent = %damage absorbed by shield)
	"autoRepairFix": 0, # fixed amount of HP/turn to repair
	"autoRepairPerc": 0.0, # how many percent of maxHP/turn is repaired
	"autoRepairMaxHP": 0.0, # default is 100% in the engine, but leave at 0% here for proper calculation; out of total ship HPs
        "damageAbsorb": 0, #amount of damage absorbed by the hull (not shield!); max sum is 5 damage (set in Rules)
	# weapons
	'weaponDmgMin': 0,
	'weaponDmgMax': 0,
	'weaponAtt': 0,
	'weaponClass': 0,
	"weaponROF": 0.0,
	"weaponIgnoreShield": 0,
	"weaponIsMissile": 0,
	"weaponGoodForFlak": 1,
	# research
	'researchRequires': ['technology'],
	'researchEnables': ['technology'],
	'researchDisables': ['technology'],
	'researchReqSRes': ['resource'],
	"researchMod": "expr",
	'researchTurns': 1,
	"researchRaces": "BCH",
	# misc
	"data": "none",
	"recheckWhenTechLost": 0,
	"deprecated": 0, # this tech is no longer active
	# before build handler
	'validateConstrHandler' : noop,
	# after build handler
	'finishConstrHandler' : noop,
	# after research handler
	'finishResearchHandler' : noop,
	# names
	'name' : u'Unspecified',
	# textual description
	'textPreRsrch': u'Not specified',
	'textDescr': u'Not specified',
	'textFlavor': u'Not specified',
}

# class representing technologies
class Technology:

	def __init__(self, id, symbol, reg):
		self.id = id
		self.symbol = symbol
		if id in reg:
			raise KeyError("%s is already registered" % id)
		reg[id] = self

	def set(self, key, value):
		if attrs.has_key(key):
			attrType = type(attrs[key])
			if attrType == types.IntType:
				value = int(value)
			elif attrType == types.FloatType:
				value = float(value)
			elif attrType == types.UnicodeType:
				pass
			elif attrType == types.StringType:
				value = str(value)
			elif attrType == types.FunctionType:
				value = getattr(TechHandlers, value)
			elif attrType == types.ListType:
				itemType = type(attrs[key][0])
				if itemType == types.IntType:
					convertFunc = int
				elif itemType == types.StringType:
					convertFunc = str
				elif itemType == types.FloatType:
					convertFunc = float
				else:
					raise 'Unsupported attribute type %s' % repr(attrType)
				result = []
				for item in value.split(','):
					if item:
						result.append(convertFunc(item))
				value = result
			else:
				raise 'Unsupported attribute type %s' % repr(attrType)
			setattr(self, key, value)
		else:
			raise AttributeError('Cannot create %s - unsupported attribute.' % key)

	def __getattr__(self, attr):
		if attrs.has_key(attr):
			# optimalization
			setattr(self, attr, attrs[attr])
			return attrs[attr]
		else:
			raise AttributeError('No attribute %s' % attr)

	def isDefault(self, attr):
		if hasattr(self, attr):
			return getattr(self, attr) == attrs[attr]
		else:
			return 1

	def __repr__(self):
		result = '(Technology '
		for key, value in self.__dict__.items():
			result += '%s : %s, ' % (repr(key), repr(value))
		result += ')'
		return result

# holder for all technologies
techs = {}

# parse TechTree.xml and create all tech objects
class TechTreeContentHandler(ContentHandler):
	def startDocument(self):
		#@log.message('Parsing tech tree...')
		self.state = 1
		self.text = ''

	def endDocument(self):
		#@log.message('Tech tree created')
		if self.state != 1:
			raise 'Wrong TechTree specification'

	def startElement(self, name, attrs):
		if self.state == 1 and name == 'techtree':
			self.state = 2
		elif self.state == 2 and name == 'technology':
			log.debug('Tech %s [%s]' % (attrs['name'], attrs['id']))
			self.state = 3
			self.tech = Technology(int(attrs['id']), attrs['symbol'], techs)
			setattr(Tech, attrs['symbol'], int(attrs['id']))
			self.tech.set('name', attrs['name'])
		elif self.state == 3 and name == 'structure':
			self.tech.set('isStructure', 1)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'discovery':
			self.tech.set('isDiscovery', 1)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'notdiscovery':
			self.tech.set('isDiscovery', 0)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'starting':
			self.tech.set('isStarting', 1)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'notstarting':
			self.tech.set('isStarting', 0)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'shipequip':
			self.tech.set('isShipEquip', 1)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'project':
			self.tech.set('isProject', 1)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'shiphull':
			self.tech.set('isShipHull', 1)
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'data':
			for key in attrs.keys():
				self.tech.set(key, attrs[key])
		elif self.state == 3 and name == 'preresearch':
			self.state = 4
			self.text = ''
		elif self.state == 3 and name == 'description':
			self.state = 4
			self.text = ''
		elif self.state == 3 and name == 'flavor':
			self.state = 4
			self.text = ''
		else:
			raise 'Unsupported tag %s' % str(name)

	def endElement(self, name):
		if self.state == 2 and name == 'techtree':
			self.state = 1
		elif self.state == 3 and name == 'technology':
			self.state = 2
			#log.debug(repr(self.tech))
		elif self.state == 4 and name == 'preresearch':
			self.tech.textPreRsrch = self.text
			self.state = 3
		elif self.state == 4 and name == 'description':
			self.tech.textDescr = self.text
			self.state = 3
		elif self.state == 4 and name == 'flavor':
			self.tech.textFlavor = self.text
			self.state = 3

	def characters(self, text):
		self.text += text

Tech = IDataHolder()

## check, if anything has been changed

def chsumDir(chsum, dirname, names):
	names.sort()
	for filename in names:
		if os.path.splitext(filename)[1] in ('.xml',):
			log.debug('Checking file', filename)
			# read file
			fh = open(os.path.join(dirname, filename), 'rb')
			chsum.update(fh.read())
			fh.close()

# compute checksum
file = sys.modules[__name__].__file__
forceLoad = 0
if os.path.exists(file):
	# regular module
	directory = os.path.dirname(file)
	chsum = sha.new()
	os.path.walk(directory, chsumDir, chsum)
else:
	# packed, cannot access xml specifications
	directory = os.path.join('res', 'techspec')
	forceLoad = 1

# read old checksum
try:
	fh = open(os.path.join(directory, 'checksum'), 'rb')
	oldChsum = fh.read()
	fh.close()
except IOError:
	oldChsum = ''

# compare
if forceLoad or chsum.hexdigest() == oldChsum:
	# load old definitions
	log.message('Loading stored specifications from', directory)
	techs = pickle.load(open(os.path.join(directory, 'techs.spf'), 'rb'))
	Tech = pickle.load(open(os.path.join(directory, 'Tech.spf'), 'rb'))

	log.message("There is %d technologies" % len(techs))

	# clean up 'type' in lists
	for key in attrs.keys():
		if type(attrs[key]) == types.ListType and len(attrs[key]) == 1:
			log.debug("Cleaning up", key)
			attrs[key] = []

else:
	# create new ones
	## load technologies definitions

	def processDir(arg, dirname, names):
		if dirname.find(".svn") >= 0:
			log.message("Skipping directory", dirname)
			return
		log.message('Loading XML files from', dirname)
		names.sort()
		for filename in names:
			if os.path.splitext(filename)[1] == '.xml':
				log.message('Parsing XML file', filename)
				xml.sax.parse(os.path.join(dirname, filename), TechTreeContentHandler())

	# collect xml files
	os.path.walk(directory, processDir, None)

	# clean up 'type' in lists
	for key in attrs.keys():
		if type(attrs[key]) == types.ListType and len(attrs[key]) == 1:
			log.debug("Cleaning up", key)
			attrs[key] = []

	# link tech tree using researchRequires fields
	# construct researchEnables fields
	log.message('Converting symbolic fields...')
	for techID in techs.keys():
		tech = techs[techID]
		# convert symbolic names to numbers
		techIDs = []
		for techSymName in tech.researchRequires:
			#@log.debug('Converting REQ', techSymName)
			symName, improvement = techSymName.split('-')
			techIDs.append((getattr(Tech, symName), int(improvement)))
		tech.researchRequires = techIDs
		techIDs = {1: [], 2:[], 3:[], 4:[], 5:[], 6:[]}
		for techSymName in tech.researchEnables:
			#@log.debug('Converting EN', techSymName)
			improvement, symName = techSymName.split('-')
			techIDs[int(improvement)].append(getattr(Tech, symName))
		tech.researchEnables = techIDs
		techIDs = []
		for techSymName in tech.researchDisables:
			techIDs.append(getattr(Tech, techSymName))
		tech.researchDisables = techIDs
		techIDs = []
		if tech.unpackStruct:
			tech.unpackStruct = getattr(Tech, tech.unpackStruct)
		else:
			tech.unpackStruct = 0
		# strat. resources
		stratRes = []
		for sr in tech.researchReqSRes:
			stratRes.append(getattr(Const, sr))
		tech.researchReqSRes = stratRes
		stratRes = []
		for sr in tech.buildSRes:
			stratRes.append(getattr(Const, sr))
		tech.buildSRes = stratRes
		# evaluate researchMod
		if tech.researchMod == "expr":
			tech.researchMod = 1.0
		else:
			tech.researchMod = eval(tech.researchMod)
		#~ # convert weapons
		#~ techIDs = []
		#~ for weaponName in tech.weapons:
			#~ techIDs.append(getattr(Tech, weaponName))
		#~ tech.weapons = techIDs

	# link
	log.message('Linking tech tree...')
	for techID in techs.keys():
		tech = techs[techID]
		#@log.debug(techID, 'Req', tech.researchRequires)
		#@log.debug(techID, 'En', tech.researchEnables)
		for tmpTechID, improvement in tech.researchRequires:
			if techID not in techs[tmpTechID].researchEnables[improvement]:
				#@log.debug('Adding', tmpTechID, improvement, 'ENABLES', techID)
				techs[tmpTechID].researchEnables[improvement].append(techID)
		for improvement in tech.researchEnables.keys():
			for tmpTechID in tech.researchEnables[improvement]:
				if (techID, improvement) not in techs[tmpTechID].researchRequires:
					#@log.debug('Adding', tmpTechID, 'REQUIRES', techID, improvement)
					techs[tmpTechID].researchRequires.append((techID, improvement))

	changed = 1
	while changed:
		changed = 0
		log.debug("Tech disable iteration")
		for techID in techs:
			tech = techs[techID]
			for tech2ID in tech.researchDisables:
				tech2 = techs[tech2ID]
				if techID not in tech2.researchDisables and techID != tech2ID:
					tech2.researchDisables.append(techID)
					changed = 1
					log.debug("Adding", tech2ID, "DISABLES", techID, ", NOW", tech2.researchDisables)
				for tech3ID in tech2.researchDisables:
					tech3 = techs[tech3ID]
					if tech3ID not in tech.researchDisables and tech3ID != techID:
						tech.researchDisables.append(tech3ID)
						changed = 1
						log.debug("Adding", techID, "DISABLES", tech3ID, "NOW", tech.researchDisables)
	# just for debug
	#for techID in techs.keys():
	#	tech = techs[techID]
	#	log.debug('Link:', techID, tech.isStarting, tech.researchRequires, tech.researchEnables)

	# save new specification
	log.message('Saving specification...')
	pickle.dump(techs, open(os.path.join(directory, 'techs.spf'), 'wb'), 1)
	pickle.dump(Tech, open(os.path.join(directory, 'Tech.spf'), 'wb'), 1)
	fh = open(os.path.join(directory, 'checksum'), 'wb')
	fh.write(chsum.hexdigest())
	fh.close()

	log.message("There is %d technologies" % len(techs))

#~ # save DOT file
#~ dotName = os.path.join(os.path.dirname(__file__), "techtree.dot")
#~ fh = open(dotName, "w+")
#~ print >> fh, """
#~ digraph {
	#~ rankdir=LR;
	#~ ranksep=0.25;
	#~ nodesep=0.25;
	#~ overlap=scale;
	#~ spline=false;
	#~ node[shape=record,fontsize=10,height=0.25,fontname=Tahoma];
	#~ edge[fontsize=8,fontname=Tahoma]
	#~ {
		#~ TL1 -> TL2 -> TL3 -> TL4 -> TL5;
	#~ }
#~ """
#~ # process nodes
#~ for level in range(1,6):
	#~ print >>fh, "\tsubgraph xcluster_%d {" % level
	#~ print >>fh, "\t\tcolor = black;"
	#~ print >>fh, "\t\tTL%d;" % level,
	#~ for techID in techs:
		#~ tech = techs[techID]
		#~ if tech.level != level:
			#~ continue
		#~ print >>fh, '"{%s|%d}";' % (tech.name, tech.level),
	#~ print >>fh
	#~ print >>fh, "\t}"
	#~ for techID in techs:
		#~ tech = techs[techID]
		#~ if tech.level != level:
			#~ continue
		#~ for tech2ID, impr in tech.researchRequires:
			#~ tech2 = techs[tech2ID]
			#~ print >> fh, '\t"{%s|%d}" -> "{%s|%d}" [label = "%d"];' % (
				#~ tech2.name,
				#~ tech2.level,
				#~ tech.name,
				#~ tech.level,
				#~ impr,
			#~ )
#~ print >> fh, """
#~ }
#~ """
#~ fh.close()

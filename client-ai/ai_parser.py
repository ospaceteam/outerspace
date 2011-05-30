#
#  Copyright 2001 - 2011 Ludek Smid [http://www.ospace.net/]
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
import os
import shutil
import tarfile

from ige import log

class AIList:
	""" Class used to parse and work with list of ai players [which is then
	used by run_ai.py].

	It creates file in config directory, named ais_list where each line is
	one player, and the format is
	
	login password used_ai_script galaxy_name

	Data dumps used by ai clients are recommended to save to the directory
	configDir/ai_data/galaxy_name/
	to be processed correctly.

	"""
	
	def __init__(self, configDir):
		self.configDir = configDir
		self.lines = {}
		# parsing the file
		try:
			listfile = open(os.path.join(self.configDir, "ais_list"), "r")
			for row in listfile:
				line = row.strip().split(" ")
				if len(line) == 3:
					self.lines.update({line[0]:tuple([line[1], line[2]])})
				elif len(line) == 4:
					self.lines.update({line[0]:tuple([line[1], line[2], line[3]])})
				else:
					continue
			listfile.close()
		except Exception, e:
			listfile = open(os.path.join(self.configDir, "ais_list"), "a")
			listfile.close()
	
	def add(self, login, password, aiType):
		""" It adds new line to the ais_list. Now without galaxy_name,
		because game doesn't know yet, to which galaxy will the player go.

		"""
		self.lines.update({login:(password, aiType, None)})
		listfile = open(os.path.join(self.configDir, "ais_list"), "w")
		for item in self.lines:
			listfile.write(item + ' ' + reduce(lambda x,y: str(x) + ' ' + str(y), self.lines[item]) + '\n')
		return
	
	def remove(self, login):
		""" Removes the line associated with login.

		"""
		try:
			del self.lines[login]
		except KeyError, e:
			pass
		listfile = open(os.path.join(self.configDir, "ais_list"), "w")
		for item in self.lines:
			listfile.write(item + ' ' + reduce(lambda x,y: str(x) + ' ' + str(y), self.lines[item]) + '\n')
		listfile.close()
		return
	
	def getAll(self):
		return self.lines.items()
	
	def getLogins(self):
		return self.lines.keys()
		
	def removeAll(self):
		self.lines = {}
		listfile = open(os.path.join(self.configDir, "ais_list"), "w")
		listfile.close()

	def setGalaxy(self, login, galaxyName):
		""" Add [or change] the galaxy information to the line associated
		with login.

		"""
		password, aiType, galaxy = self.lines[login]
		self.lines.update({login:(password, aiType, galaxyName)})
		try:
			os.mkdir(os.path.join(self.configDir, "ai_data", galaxyName))
		except OSError:
			pass
		listfile = open(os.path.join(self.configDir, "ais_list"), "w")
		for item in self.lines:
			listfile.write(item + ' ' + reduce(lambda x,y: str(x) + ' ' + str(y), self.lines[item]) + '\n')
		listfile.close()
		return

	def finishGalaxy(self, galaxyName):
		""" Removes galaxy directory, and all player data contained within.

		"""
		for item in os.listdir(os.path.join(self.configDir, 'ai_data', galaxyName)):
			os.remove(os.path.join(self.configDir, 'ai_data', galaxyName, item))
		os.rmdir(os.path.join(self.configDir, 'ai_data', galaxyName))
		return

	def backup(self, backupPath):
		""" Creates bzip2 archive of ais_list file and ai_data directory

		"""
		log.debug('Creating backup %s-ais.osbackup' % backupPath)
		tar = tarfile.open('%s-ais.osbackup' % backupPath, 'w:bz2')
		tar.add(os.path.join(self.configDir, 'ais_list'))
		tar.add(os.path.join(self.configDir, 'ai_data'))
		tar.close()

	def restore(self, backupPath):
		""" Extracts data of the ai players, as well as the ais_list file.

		"""
		os.remove(os.path.join(self.configDir, 'ais_list'))
		shutil.rmtree(os.path.join(self.configDir, 'ai_data'))
		log.message('Restoring AI backup %s' % backupPath)
		tar = tarfile.open(backupPath, 'r:bz2')
		tar.extractall()
		tar.close()
		self.lines = {}
		# parsing the file
		try:
			listfile = open(os.path.join(self.configDir, "ais_list"), "r")
			for row in listfile:
				line = row.strip().split(" ")
				if len(line) == 3:
					self.lines.update({line[0]:tuple([line[1], line[2]])})
				elif len(line) == 4:
					self.lines.update({line[0]:tuple([line[1], line[2], line[3]])})
				else:
					continue
			listfile.close()
		except Exception, e:
			listfile = open(os.path.join(self.configDir, "ais_list"), "a")
			listfile.close()
		log.message('AI backup restored')
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

import copy
import sys
import os
import optparse
import shlex
import subprocess
import time
import tempfile

class ProcQueue():
	""" Process dispatcher. It is basically pool of subprocesses. Its size
	is defined by init parameter numberOfProcs.

	"""
	def __init__(self, numberOfProcs):
		self.maxNumberOfProcs = numberOfProcs
		self.procs = []
		self.outputs = []
		self.errors = []
    
	def addProc(self, args):
		""" Try to add another process to the pool.

		args - same args that will go to subprocess.Popen as a first parameter

		"""
		# First processes fill the pool
		if len(self.procs) < self.maxNumberOfProcs:
			self.outputs.append(tempfile.SpooledTemporaryFile())
			self.errors.append(tempfile.SpooledTemporaryFile())
			self.procs.append(subprocess.Popen(args, stdout=self.outputs[len(self.procs)], stderr=self.errors[len(self.procs)]))
			return
		else:
			# Other processes have to wait until one of already running ones
			# finish. Try each subprocess, and if there is not None, it means
			# the subprocess ended already. Fetch the spooled outputs, and
			# place there the waiting process.
			wait = True
			while wait:
				i = 0
				for proc in copy.copy(self.procs):
					if not proc.poll() == None:
						self.procs.remove(proc)
						self.outputs[i].seek(0)
						self.errors[i].seek(0)
						stdout = self.outputs[i].read()
						stderr = self.errors[i].read()
						self.errors[i].close()
						self.outputs[i].close()
						if len(stdout):
							print >> sys.stdout, stdout
						if len(stderr):
							print >> sys.stderr, stderr
						del self.errors[i]
						del self.outputs[i]
						self.errors.append(tempfile.SpooledTemporaryFile())
						self.outputs.append(tempfile.SpooledTemporaryFile())
						self.procs.append(subprocess.Popen(args, stdout=self.outputs[self.maxNumberOfProcs-1], stderr=self.errors[self.maxNumberOfProcs-1]))
						wait = False
						break
					i += 1
				time.sleep(0.05)
			return
    
	def waitForEnd(self):
		""" Wait until all subprocesses finish their jobs.

		"""
		i = 0
		for proc in self.procs:
			proc.wait()
			try:
				self.outputs[i].seek(0)
				self.errors[i].seek(0)
				stdout = self.outputs[i].read()
				stderr = self.errors[i].read()
				self.errors[i].close()
				self.outputs[i].close()
				if len(stdout):
					print >> sys.stdout, stdout
				if len(stderr):
					print >> sys.stderr, stderr
			except ValueError:
				continue
			finally:
				i += 1
		return


basepath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, os.path.join(basepath, "client-ai"))

for item in ("libsrvr", "server/lib"):
    path = os.path.join(basepath, item)
    if os.path.exists(path):
        sys.path.insert(0, path)
        break

from ai_parser import AIList


parser = optparse.OptionParser()
parser.add_option("",  "--configdir", dest = "configDir", 
	metavar = "DIRECTORY", 
	default = "var", 
	help = "Override default configuration directory", 
)
parser.add_option("",  "--server", dest = "server", 
	metavar = "HOSTNAME:PORT", 
	default = "localhost:9080",
	help = "Outer Space server location"
)
parser.add_option("",  "--procs", dest = "procs", 
	metavar = "PROCS", 
	default = "1",
	help = "Maximum number of concurrent processes"
)
parser.add_option("",  "--galaxy", dest = "galaxies", 
	metavar = "NAME", 
	action = "append",
	default = [],
	help = "Name of galaxy to enable AI for"
)

options, args = parser.parse_args()

if args:
	parser.error("No additional arguments are supported")

aiList = AIList(options.configDir)
procs = []
procQueue = ProcQueue(int(options.procs))
for login, (password, ais, galaxy) in aiList.getAll():
	if options.galaxies and galaxy not in options.galaxies:
		continue
	args = shlex.split('python %s/client-ai/ai_osc.py --configdir=%s --server=%s --login=%s --password=%s --ai=%s' %\
		(basepath, os.path.join(options.configDir, 'ai_data', galaxy), options.server, login, password, ais))
	procQueue.addProc(args)
#	os.system('python ../client-ai/ai_osc.py --configdir=%s --server=%s --login=%s --password=%s --ai=%s' %\
#		 (options.configDir, options.server, login, password, ais))
procQueue.waitForEnd()
sys.exit()

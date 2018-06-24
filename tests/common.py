#!/usr/bin/env python2

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

import atexit
import logging as log
import os
import shutil
import signal
import subprocess
import tempfile
import time

log.basicConfig(level=log.INFO, format='%(levelname)-7s: %(message)s')

TEMP_DIR = None
SERVER_OUT = None
UTILS_OUT = None
AI_OUT = None
BUP_OUT = None
CODE_ROOT=os.path.realpath(os.path.join(
          os.path.dirname(os.path.realpath(__file__)),
          '..'))

def killServer():
    try:
        with open(os.path.join(TEMP_DIR, 'server.pid'), 'r') as pid_file:
            pid=int(pid_file.read())
            log.warning('Cleaning up server process {0}'.format(pid))
            os.kill(pid, signal.SIGKILL)
    except:
        pass

def startServer(upgrade=False):
    args=[os.path.join(CODE_ROOT, 'outerspace.py'),
          'server',
          '--configdir=' + TEMP_DIR,
          '--mode=0']
    if upgrade:
        log.info('Starting server with upgrade')
        args.append('--upgrade')
    else:
        log.info('Starting server')
    subprocess.Popen(args, stdout=SERVER_OUT, stderr=subprocess.STDOUT)

    time.sleep(1) # give server process enough time to initialize
    start_time=time.time()
    while True:
        args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
              '--ping',
              '--configdir=' + TEMP_DIR]
        if subprocess.call(args, stdout=BUP_OUT,
                                 stderr=subprocess.STDOUT) == 0:
            break
        try:
            with open(os.path.join(TEMP_DIR, 'server.pid'), 'r') as pid_file:
                pid=int(pid_file.read())
                os.kill(pid, 0)
                if time.time() - start_time > 60:
                    log.error('Server takes too long to initialize')
                    killServer()
                    return False
                log.debug('Waiting for server to initialize')
                time.sleep(5)
        except (OSError, IOError):
            log.error('Server failed to initialize')
            return False
    log.info('Server has been initialized')
    return True

def stopServer():
    log.info('Stopping server')
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--shutdown',
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Server failed to stop')
        return False

    start_time=time.time()
    while os.path.isfile(os.path.join(TEMP_DIR, 'server.pid')):
        if time.time() - start_time > 60:
            log.error('Server takes too long to stop')
            return False
        log.debug('Waiting for server to stop')
        time.sleep(5)
    log.info('Server has been stopped')
    return True

def startServerTime():
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--starttime',
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Time failed to start')
        return False
    log.info('Time has been started')
    return True

def doTurns(amount, skip, slow=False, verbose=True):
    args_osclient=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--turns={0}'.format(skip),
          '--configdir=' + TEMP_DIR]
    args_ai=[os.path.join(CODE_ROOT, 'outerspace.py'),
          'ai-pool',
          '--configdir=' + TEMP_DIR,
          '--local']
    if slow:
        args_ai.append('--procs=1')
    for turn in range(0, amount, skip):
        subprocess.call(args_ai, stdout=AI_OUT,
                                 stderr=subprocess.STDOUT)
        subprocess.call(args_osclient, stdout=UTILS_OUT,
                                       stderr=subprocess.STDOUT)
        if verbose:
            log.info('Turn {0}'.format(turn + skip))

def createGalaxy(galaxy_type, galaxy_name = None):
    start_time = time.time()
    if galaxy_name is None:
        galaxy_name = galaxy_type
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--newgalaxy={0}'.format(galaxy_name),'{0}'.format(galaxy_type),
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Galaxy {0} has not been created'.format(galaxy_type))
    else:
        name_string = ''
        if galaxy_name:
            name_string = "named {0}".format(galaxy_name)
        log.info('Galaxy {0} {1} created ({2:.2g}s)'.format(galaxy_type, name_string, time.time() - start_time))

def deleteGalaxy(galaxy_id):
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--deletegalaxy={0}'.format(galaxy_id),
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Galaxy {0} has not been deleted'.format(galaxy_id))
    else:
        log.info('Galaxy {0} deleted'.format(galaxy_id))

def makeScreenshots(history_dir):
    try:
        os.makedirs(history_dir)
    except os.error:
        pass
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--chronicler',
          '--chronicler_dir=' + history_dir,
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Failed to make a screenshot.')

def closeLogs():
    SERVER_OUT.close()
    UTILS_OUT.close()
    AI_OUT.close()
    BUP_OUT.close()

def initPaths(configDir = None):
    global TEMP_DIR, SERVER_OUT, UTILS_OUT, AI_OUT, BUP_OUT
    TEMP_DIR=tempfile.mkdtemp()
    if configDir is not None:
        os.rmdir(TEMP_DIR)
        shutil.copytree(configDir, TEMP_DIR)
    SERVER_OUT=open(os.path.join(TEMP_DIR, 'server.out'), 'a')
    UTILS_OUT=open(os.path.join(TEMP_DIR, 'utils.out'), 'a')
    AI_OUT=open(os.path.join(TEMP_DIR, 'ai.out'), 'a')
    BUP_OUT=open(os.path.join(TEMP_DIR, 'bup.out'), 'a')
    log.info('Location of logs: ' + str(TEMP_DIR))
    atexit.register(closeLogs)

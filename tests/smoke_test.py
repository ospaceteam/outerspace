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

import argparse
import atexit
import httplib
import json
import logging as log
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

log.basicConfig(level=log.INFO, format='%(levelname)-7s: %(message)s')

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

def startServer():
    log.info('Starting server')
    args=[os.path.join(CODE_ROOT, 'outerspace.py'),
          'server',
          '--configdir=' + TEMP_DIR,
          '--mode=0']
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
                    sys.exit(1)
                log.debug('Waiting for server to initialize')
                time.sleep(5)
        except (OSError, IOError):
            log.error('Server failed to initialize')
            sys.exit(1)
    log.info('Server has been initialized')

def stopServer():
    log.info('Stopping server')
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--shutdown',
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Server failed to stop')
        sys.exit(1)

    start_time=time.time()
    while os.path.isfile(os.path.join(TEMP_DIR, 'server.pid')):
        if time.time() - start_time > 60:
            log.error('Server takes too long to stop')
            sys.exit(1)
        log.debug('Waiting for server to stop')
        time.sleep(5)
    log.info('Server has been stopped')

def startServerTime():
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--starttime',
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Time failed to start')
        sys.exit(1)
    log.info('Time has been started')

def doTurns(amount, skip, slow=False):
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
        log.info('Turn {0}'.format(turn + skip))

def createGalaxy(galaxy_type, galaxy_name = None):
    if galaxy_name is None:
        galaxy_name = galaxy_type
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--newgalaxy={0}'.format(galaxy_name),'{0}'.format(galaxy_type),
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Galaxy {0} has not been created'.format(galaxy_type))
    else:
        log.info('Galaxy {0} created'.format(galaxy_type))

def deleteGalaxy(galaxy_id):
    args=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--deletegalaxy={0}'.format(galaxy_id),
          '--configdir=' + TEMP_DIR]
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Galaxy {0} has not been deleted'.format(galaxy_id))
    else:
        log.info('Galaxy {0} deleted'.format(galaxy_id))

def assertGrep(pattern, text, flags=0):
    if re.search(pattern, text, flags|re.MULTILINE):
        return True
    return False

def checkServerStatus():
    conn = httplib.HTTPConnection('localhost', '9080', timeout = 10)
    conn.request('GET', '/status')
    response = conn.getresponse()
    content = response.read()
    if response.status != 200:
        log.error("Server status not available")
        return False
    if not assertGrep('Outer Space Status Reports', content):
        log.error("Server status is malformed")
        log.debug(content)
        return False
    log.info('Server status is present.')
    return True

def checkLogs():
    everything_ok = True
    for logfile in [SERVER_OUT, AI_OUT, UTILS_OUT]:
        with open(logfile.name) as readable_logfile:
            if assertGrep('error|traceback',
                          readable_logfile.read(),
                          re.IGNORECASE):
                log.error('Errors present in {0}'.format(logfile.name))
                everything_ok = False
    if everything_ok:
        log.info('No error messages found in log files')

def checkPlayerProgress():
    problem = False
    with open(os.path.join(TEMP_DIR, 'website',
                           'Alpha', 'json.txt'), 'r') as stats_file:
        stats = json.loads(stats_file.read())
        buildings_counts = []
        for galaxy in stats:
            if galaxy == 'turn':
                continue
            for player in stats[galaxy]['players']:
                player_stats = stats[galaxy]['players'][player]
                player_name = player_stats[0]
                if 'E.D.E.N.' in player_name or 'order' == player: continue
                buildings = int(player_stats[3])
                buildings_counts += [buildings]
                if buildings < 10:
                    log.error(player_stats)
                    problem = True
    if problem:
        log.error('There is an issue with player progress')
        log.debug('Building counts: {0}'.format(buildings_counts))
    else:
        log.info('Player progress ok')

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--slow", dest = "slow", default = False,
    action = "store_true", help = "Switches off multiprocessing of AI")
parser.add_argument("--turns", dest = "turns", default = 40,
    type = int, metavar = "N", help = "Process N turns on server")
parser.add_argument("--turn-skip", dest = "turnSkip", default = 5,
    type = int, metavar = "N", help = "Process N turns on server")
args = parser.parse_args()



# prepare logging
TEMP_DIR=tempfile.mkdtemp()
SERVER_OUT=open(os.path.join(TEMP_DIR, 'server.out'), 'w')
UTILS_OUT=open(os.path.join(TEMP_DIR, 'utils.out'), 'w')
AI_OUT=open(os.path.join(TEMP_DIR, 'ai.out'), 'w')
BUP_OUT=open(os.path.join(TEMP_DIR, 'bup.out'), 'w')
log.info('Location of logs: ' + str(TEMP_DIR))


# test itself
startServer()
atexit.register(killServer)
createGalaxy("Circle1SP")
createGalaxy("Circle3SP")
createGalaxy("Circle9P")
startServerTime()
deleteGalaxy(10000) # legacy
createGalaxy("Circle42P")
startServerTime()
doTurns(args.turns, args.turnSkip, slow=args.slow)
checkServerStatus()
stopServer()
checkPlayerProgress()

startServer()
doTurns(2*args.turnSkip, args.turnSkip, slow=args.slow)
checkServerStatus()
stopServer()
checkPlayerProgress()
checkLogs()


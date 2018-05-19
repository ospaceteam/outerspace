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
TEMP_DIR=tempfile.mkdtemp()
SERVER_OUT=open(os.path.join(TEMP_DIR, 'server.out'), 'w')
UTILS_OUT=open(os.path.join(TEMP_DIR, 'utils.out'), 'w')
AI_OUT=open(os.path.join(TEMP_DIR, 'ai.out'), 'w')
BUP_OUT=open(os.path.join(TEMP_DIR, 'bup.out'), 'w')

TURN_SKIP=5
TURN_AMOUNT=25
try:
    if sys.argv[1] == 'long':
        TURN_AMOUNT=300
        log.info('Starting a long running variant')
except IndexError:
    pass

log.info('Location of logs: ' + str(TEMP_DIR))

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
              '--configdir=' + TEMP_DIR,
              'admin']
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
          '--configdir=' + TEMP_DIR,
          'admin']
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
          '--configdir=' + TEMP_DIR,
          'admin']
    if subprocess.call(args, stdout=UTILS_OUT, stderr=subprocess.STDOUT) != 0:
        log.error('Time failed to start')
        sys.exit(1)
    log.info('Time has been started')

def doTurns(amount=TURN_AMOUNT, skip=TURN_SKIP):
    args_osclient=[os.path.join(CODE_ROOT, 'tools', 'osclient_cli.py'),
          '--turns={0}'.format(skip),
          '--configdir=' + TEMP_DIR,
          'admin']
    args_ai=[os.path.join(CODE_ROOT, 'outerspace.py'),
          'ai-pool',
          '--configdir=' + TEMP_DIR,
          '--procs=1',
          '--local']
    for turn in range(0, amount, skip):
        subprocess.call(args_ai, stdout=AI_OUT,
                                 stderr=subprocess.STDOUT)
        subprocess.call(args_osclient, stdout=UTILS_OUT,
                                       stderr=subprocess.STDOUT)
        log.info('Turn {0}'.format(turn + skip))

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
        for player in stats['10000']['players']:
            player_stats = stats['10000']['players'][player]
            player_name = player_stats[0]
            if 'E.D.E.N.' in player_name or 'order' == player: continue
            buildings = int(player_stats[3])
            buildings_counts += [buildings]
            if buildings < 10:
                problem = True
    if problem:
        log.error('There is an issue with player progress')
        log.debug('Building counts: {0}'.format(buildings_counts))
    else:
        log.info('Player progress ok')


startServer()
atexit.register(killServer)
startServerTime()
doTurns()
checkServerStatus()
stopServer()
checkPlayerProgress()

startServer()
doTurns(15)
checkServerStatus()
stopServer()
checkPlayerProgress()
checkLogs()


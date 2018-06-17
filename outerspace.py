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
import multiprocessing
import os, os.path
import sys
import time

relative_path = os.path.dirname(os.path.realpath(__file__))
# tweak PYTHONPATH
sys.path.insert(0, os.path.join(relative_path, "client"))
sys.path.insert(0, os.path.join(relative_path, "server"))
sys.path.insert(0, os.path.join(relative_path, "server", "data"))
sys.path.insert(0, os.path.join(relative_path, "client-ai"))
sys.path.insert(0, os.path.join(relative_path, "server","lib"))


parser = argparse.ArgumentParser()

common_parser = argparse.ArgumentParser(add_help=False)
common_parser.add_argument("--configdir", dest = "configDir",
    metavar = "DIRECTORY",
    default = os.path.join(os.path.expanduser("~"), ".outerspace"),
    help = "Override default configuration directory",
)
common_parser.add_argument("--server", dest = "server",
    metavar = "HOSTNAME:PORT",
    default = "pichu.dahaic.net:9080",
    help = "Outer Space server location"
)
common_parser.add_argument("--local", dest = "local",
    action = "store_true",
    default = False,
    help = "Setting on local mode (connections are made to localhost)"
)
common_parser.add_argument("--profile", dest = "profile",
    default=False,
    help = "Run with profiling enabled"
)
subparsers = parser.add_subparsers(help='Subcommands: client (default), server, ai, ai-pool')

parser_client = subparsers.add_parser('client', help='Game client of Outer Space', parents=[common_parser])
parser_server = subparsers.add_parser('server', help='Dedicated server', parents=[common_parser])
parser_ai = subparsers.add_parser('ai', help='Run one AI worker', parents=[common_parser])
parser_ai_pool = subparsers.add_parser('ai-pool', help='Batch run of AI players defined in configuration', parents=[common_parser])

# unfortunately, argparser does not support default subcommand (maybe it is
# messy approach? :( ) so we push 'client' when default should apply
if len(sys.argv) == 1 or sys.argv[1] not in ['client', 'server', 'ai', 'ai-pool', '--help', '-h']:
    sys.argv = [sys.argv[0]] + ['client'] + sys.argv[1:]

subcommand = sys.argv[1]

# common stuff

# client
parser_client.add_argument("--configfilename", dest = "configFilename",
    metavar = "FILENAME",
    default = "osci.ini",
    help = "Override default configuration file name",
)
parser_client.add_argument("--login", dest = "login",
    metavar = "HOSTNAME:PORT",
    default = None,
    help = "Account login"
)
parser_client.add_argument("--password", dest = "password",
    metavar = "HOSTNAME:PORT",
    default = None,
    help = "Account password"
)
parser_client.add_argument("--heartbeat", dest = "heartbeat",
    type = int,
    metavar = "SECONDS",
    default = 60,
    help = "Heartbeat for server connection"
)

# server
parser_server.add_argument("--configfilename", dest = "configFilename",
    metavar = "FILENAME",
    default = "osci.ini",
    help = "Override default configuration file name",
)
parser_server.add_argument("--restore", dest = "restore",
    metavar = "STRING",
    default = None,
    help = "Restore from backup files beginning with STRING",
)
parser_server.add_argument("--reset", dest = "reset",
    action = "store_true", default=False,
    help = "Server resets itself before starting up"
)
parser_server.add_argument("--upgrade", dest = "upgrade",
    action = "store_true", default=False,
    help = "Server will undergo upgrade routine"
)
parser_server.add_argument("--mode", dest = "mode",
    type=int,
    metavar = "MODE",
    default=1,
    help = "Server mode: 0 - debug, 1 - normal",
)

# ai
parser_ai.add_argument("--login", dest = "login",
    metavar = "LOGIN",
    default = None,
    help = "Login name of the AI player.",
)
parser_ai.add_argument("--password", dest = "password",
    metavar = "PASSWORD",
    default = None,
    help = "Corresponding password of the AI player.",
)
parser_ai.add_argument("--ai", dest = "ai",
    metavar = "AI",
    default = None,
    help = "Type of the AI applied."
)
parser_ai.add_argument("--game", dest = "game",
    metavar = "NAME",
    default = 'Alpha',
    help = "Name of game to which the AI belongs",
)
parser_ai.add_argument("--test-connection", dest = "test",
    action = "store_true", default=False,
    help = argparse.SUPPRESS
)
parser_ai.add_argument("--galaxy", dest = "galaxies",
    metavar = "NAME",
    action = "append",
    default = [],
    help = "Name of galaxy to enable AI for, no argument means all galaxies"
)


# ai-pool
parser_ai_pool.add_argument("--procs", dest = "procs",
    metavar = "PROCS",
    default = multiprocessing.cpu_count() * 4,
    type=int,
    help = "Maximum number of concurrent processes, default is 4 times cpu count."
)
parser_ai_pool.add_argument("--galaxy", dest = "galaxies",
    metavar = "NAME",
    action = "append",
    default = [],
    help = "Name of galaxy to enable AI for, no argument means all galaxies"
)
parser_ai_pool.add_argument("--game", dest = "game",
    metavar = "NAME",
    default = "Alpha",
    help = "Name of the game for which the AIs should be run.",
)

options = parser.parse_args()
options.configDir = os.path.expanduser(options.configDir)
if options.local:
    # we will set localhost as a connections
    options.server = 'localhost:9080'

if subcommand == 'server':
    from main_server import runServer
    task = runServer

elif subcommand == 'ai':
    from main_ai import runAIClient
    task = runAIClient

elif subcommand == 'ai-pool':
    from main_ai_pool import runAIPool
    task = runAIPool

# basically default (as we force it in case of nonexistent subcommand
elif subcommand == 'client':
    from main_client import runClient
    task = runClient

if __name__ == '__main__':
    if not os.path.exists(options.configDir):
        os.makedirs(options.configDir)
    # first, we have to initialize Rules (to provide it with configDir)
    import ige.ospace.Rules as Rules
    Rules.init(options.configDir)
    if options.profile:
        import cProfile
        profiling_output = '{0}.raw'.format(options.profile)
        cProfile.run('task(options)', profiling_output )
        import pstats
        with open(options.profile, 'w') as pro_file:
            stats = pstats.Stats(profiling_output, stream=pro_file)
            stats.strip_dirs()
            stats.sort_stats('time')
            stats.print_stats()
    else:
        task(options)

exit()


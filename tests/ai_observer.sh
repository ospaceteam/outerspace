#!/bin/bash
#
#  Copyright 2001 - 2017 Ludek Smid [http://www.ospace.net/]
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

HISTORY_DIR="./history"
mkdir -p ${HISTORY_DIR}

# if config dir provided, we won't setup, but continue instead
if [[ ! -z ${1// } ]]; then
    CONFIG_DIR=$1
    # start server
    ../outerspace.py server --configdir "$CONFIG_DIR" --local &> /dev/null &
    sleep 5
else
    # we have to create galaxies
    CONFIG_DIR=$(mktemp -d)
    echo ConfigDir: ${CONFIG_DIR}

    # start server
    ../outerspace.py server --configdir "$CONFIG_DIR" --local &> /dev/null &
    sleep 30 # just to be sure
    # now we delete Legacy galaxy - it's too big for common scenario
    ../tools/osclient_cli.py --deletegalaxy 10000 --configdir "$CONFIG_DIR" admin

    # create 1P galaxy
    ../tools/osclient_cli.py --newgalaxy Circle1P Circle1P --configdir "$CONFIG_DIR" admin

    # create 9P galaxy
    ../tools/osclient_cli.py --newgalaxy Circle9P Circle9P --configdir "$CONFIG_DIR" admin

    # create 42P galaxy (you can just comment removal above, legacy is 42P ^^ :) )
    #../tools/osclient_cli.py --newgalaxy Circle42P Circle42P --configdir "$CONFIG_DIR" admin

    # create 65P galaxy (probably never to be played - way too big)
    #../tools/osclient_cli.py --newgalaxy Circle65P Circle65P --configdir "$CONFIG_DIR" admin

    # start time
    ../tools/osclient_cli.py --starttime --configdir "$CONFIG_DIR" admin
fi

# by default, we are skipping quite a lot, and doing a week in one batch
# to prepare for smooth video, adjust accordingly
TURN_SKIP=6
DAYS=6
for i in `seq 0 ${TURN_SKIP} $((($DAYS * 24)))`;do
    # turn
    ../tools/osclient_cli.py --configdir "$CONFIG_DIR" --turns ${TURN_SKIP} admin

    # run AI
    ../outerspace.py ai-pool --configdir "$CONFIG_DIR" --local

    # make screenshots
    ../tools/osclient_cli.py --configdir "$CONFIG_DIR" --chronicler --chronicler_dir ${HISTORY_DIR} admin

done

# stop server
../tools/osclient_cli.py --configdir "$CONFIG_DIR" --shutdown admin
echo ConfigDir: ${CONFIG_DIR}

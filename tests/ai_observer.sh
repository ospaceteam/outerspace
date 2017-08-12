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

CONFIG_DIR=$(mktemp -d)
echo ConfigDir: ${CONFIG_DIR}
HISTORY_DIR="./history"
mkdir -p ${HISTORY_DIR}

# start server
../outerspace.py server --configdir "$CONFIG_DIR" --local &> /dev/null &
sleep 30 # just to be sure

# start time
../tools/osclient_cli.py --starttime --configdir "$CONFIG_DIR" admin

for i in `seq 1 24`;do
    # turn
    ../tools/osclient_cli.py --configdir "$CONFIG_DIR" --turn admin

    # run AI
    ../outerspace.py ai-pool --configdir "$CONFIG_DIR" --local

    # make screenshots
    ../tools/osclient_cli.py --configdir "$CONFIG_DIR" --chronicler --chronicler_dir ${HISTORY_DIR} admin

done

# stop server
../tools/osclient_cli.py --configdir "$CONFIG_DIR" --shutdown admin

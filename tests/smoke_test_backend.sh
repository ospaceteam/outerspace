#!/bin/bash

#
#  Copyright 2001 - 2016 Ludek Smid [http://www.ospace.net/]
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



# creates new server
# starts time in autocreated legacy galaxy
# runs for more than two weeks worth of turns (300)
# checks no exceptions are reported, and all players have evolved somehow

TEST_DIR=$(mktemp -d)

function cleanup() {
    popd > /dev/null
    [ -f $TEST_DIR/server.pid ] && kill $(cat $TEST_DIR/server.pid)
}

if [ ${1:-"quick"} == "long" ]; then
    echo "Running long test"
    DURATION=300
    SKIP=5
else
    echo "Running quick test"
    DURATION=25
    SKIP=5
fi

echo "Starting server"
echo "Location of logs: $TEST_DIR"
pushd ../ > /dev/null
./outerspace.py server --configdir=$TEST_DIR &> $TEST_DIR/server.out &
server_pid=$!
trap cleanup EXIT

while true; do
    # waiting for server initialization, turns0 is just dummy command

    ./server/osclient --ping --configdir=$TEST_DIR admin &> /dev/null
    [ $? == 0 ] && break
    if ! `ps -p $server_pid > /dev/null`; then
        echo "Server failed to start"
        exit 1
    fi
    echo "Waiting for server initialization"
    sleep 5
done

echo "Starting time"
./server/osclient --starttime --configdir=$TEST_DIR admin &>> $TEST_DIR/utils.out
for turn in `seq 0 $SKIP $DURATION`; do
    echo "Turn $turn"
    ./outerspace.py ai-pool --configdir=$TEST_DIR &> $TEST_DIR/ai.out
    ./server/osclient --turns=$SKIP --configdir=$TEST_DIR admin &>> $TEST_DIR/utils.out
done

sleep 5 &
sleep_pid=$!
echo "Fetching server status"
wget -O $TEST_DIR/status.out localhost:9080/status &> /dev/null
wait $sleep_pid

echo "Stopping server"
./server/osclient --shutdown --configdir=$TEST_DIR admin &>> $TEST_DIR/utils.out

# start of checks
failure=false
# checks that server produces status page
if ! `grep -q 'Outer Space Status Reports' $TEST_DIR/status.out`; then
    echo "Status page not valid"
    failure=true
fi

# checks that players had some progress at all
for buildings in `grep ... $TEST_DIR/website/Alpha/json.txt | egrep -v 'galaxyname|E.D.E.N.' | cut -d'"' -f10`;do
    printf '%f' $buildings &> /dev/null || continue # not a number
    if [[ "$buildings" < "10" ]]; then
        echo "WARNING: Some player has low building count ($buildings)"
    else
        positive_outcome=true
    fi
done
if ! $positive_outcome; then
    echo "Error in website data generation"
    failure=true
fi

if `egrep -iq 'error|traceback' $TEST_DIR/*.out`; then
    for log in $TEST_DIR/*.out; do
        if `egrep -iq 'error|traceback' $log`; then
            echo "Errors present in $log"
        fi
    done
    failure=true
fi

echo -e "\n---"
if $failure; then
    echo "Test failed"
    exit 1
else
    echo "Test passed"
    exit 0
fi

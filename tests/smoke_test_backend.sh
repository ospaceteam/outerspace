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

function cleanup() {
    popd > /dev/null
    [ -f $TEST_DIR/server.pid ] && kill $(cat $TEST_DIR/server.pid)
}

function startServer() {
    echo "Starting server"
    ./outerspace.py server --configdir=$TEST_DIR &>> $TEST_DIR/server.out &
    trap cleanup EXIT

    while true; do
        ./server/osclient --ping --configdir=$TEST_DIR admin &> /dev/null
        [ $? == 0 ] && break
        if [[ ! -f $TEST_DIR/server.pid ]] || [[ ! `ps -p $(cat $TEST_DIR/server.pid)` ]] ; then
            echo "Server failed to start"
            exit 1
        fi
        echo "Waiting for server initialization"
        sleep 5
    done
}

function stopServer() {
    echo "Stopping server"
    ./server/osclient --shutdown --configdir=$TEST_DIR admin &>> $TEST_DIR/utils.out
    while true; do
        [[ ! -f $TEST_DIR/server.pid ]] && break
        sleep 1
        echo "Waiting for server to stop"
    done
}

function startTime() {
    echo "Starting time"
    ./server/osclient --starttime --configdir=$TEST_DIR admin &>> $TEST_DIR/utils.out
}

function doTurns() {
    local turn
    for turn in `seq 0 ${2:-$SKIP} ${1:-$DURATION}`; do
        echo "Turn $turn"
        ./outerspace.py ai-pool --configdir=$TEST_DIR &> $TEST_DIR/ai.out
        ./server/osclient --turns=$SKIP --configdir=$TEST_DIR admin &>> $TEST_DIR/utils.out
    done
}

function fetchServerStatus() {
    sleep 5 &
    local sleep_pid=$!
    echo "Fetching server status"
    wget -O $TEST_DIR/status.out localhost:9080/status &> /dev/null
    wait $sleep_pid
}

function checkServerStatus() {
    if ! `grep -q 'Outer Space Status Reports' $TEST_DIR/status.out`; then
        echo "Status page not valid"
        FAILURE=true
    fi
}

function checkPlayerProgress() {
    local buildings
    local positive_outcome

    for buildings in `grep ... $TEST_DIR/website/Alpha/json.txt | egrep -v 'galaxyname|E.D.E.N.' | cut -d'"' -f10`;do
        printf '%f' $buildings &> /dev/null || continue # not a number
        if [[ "$buildings" < "10" ]]; then
            # it is warning only, because this player may be
            # active, but in process of being conquered
            echo "WARNING: Some player has low building count ($buildings)"
        else
            positive_outcome=true
        fi
    done
    if ! $positive_outcome; then
        echo "Error in website data generation"
        FAILURE=true
    fi
}

function checkLogs() {
    local log

    if `egrep -iq 'error|traceback' $TEST_DIR/*.out`; then
        for log in $TEST_DIR/*.out; do
            if `egrep -iq 'error|traceback' $log`; then
                echo "Errors present in $log"
            fi
        done
        FAILURE=true
    fi
}

######### GLOBAL VARIABLE DEFINITIONS #############

if [ ${1:-"quick"} == "long" ]; then
    echo "Running long test"
    DURATION=300
    SKIP=5
else
    echo "Running quick test"
    DURATION=25
    SKIP=5
fi
FAILURE=false
TEST_DIR=$(mktemp -d)


######## START #########

echo "Location of logs: $TEST_DIR"
pushd ../ > /dev/null

startServer
startTime
doTurns
fetchServerStatus
checkServerStatus
stopServer
checkPlayerProgress
### now check restart

startServer
doTurns 15
fetchServerStatus
checkServerStatus
stopServer
checkPlayerProgress

checkLogs


echo -e "\n---"
if $FAILURE; then
    echo "Test failed"
    exit 1
else
    echo "Test passed"
    exit 0
fi

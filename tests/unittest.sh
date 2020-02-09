#!/bin/bash
set -e
cd "${BASH_SOURCE%/*}/.." || exit


PYTHONPATH=client/pygameui python2 -m unittest Text

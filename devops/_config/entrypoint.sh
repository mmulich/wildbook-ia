#!/bin/bash

set -ex

setup

# XXX ...
pip install hupper watchdog
export HUPPER_DEFAULT_MONITOR=hupper.watchdog.WatchdogFileMonitor

exec gosu ${HOST_USER}:${HOST_USER} $@

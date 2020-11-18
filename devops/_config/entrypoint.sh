#!/bin/bash

set -ex

setup

# XXX ...
/virtualenv/env3/bin/pip install hupper watchdog
# export HUPPER_DEFAULT_MONITOR=hupper.watchdog.WatchdogFileMonitor
export HUPPER_DEFAULT_MONITOR=hupper.polling.PollingFileMonitor

exec gosu ${HOST_USER}:${HOST_USER} $@

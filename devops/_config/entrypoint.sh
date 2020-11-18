#!/bin/bash

set -ex

setup

# XXX ...
/virtualenv/env3/bin/pip install hupper watchdog
# export HUPPER_DEFAULT_MONITOR=hupper.watchdog.WatchdogFileMonitor
export HUPPER_DEFAULT_MONITOR=hupper.polling.PollingFileMonitor

# XXX Enable Sentry
/virtualenv/env3/bin/pip install "sentry-sdk[flask]>=0.10.2"

exec gosu ${HOST_USER}:${HOST_USER} $@

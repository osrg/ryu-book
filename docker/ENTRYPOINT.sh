#!/usr/bin/env bash

set -e -x

service openvswitch-switch start

bash

service openvswitch-switch stop

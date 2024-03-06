#!/bin/sh

interface=$1
airodump() {
    airodump-ng "$interface" -w temp_output --output-format csv &
    AIRDUMP_PID=$!
    sleep 10
    awk -F, '/^[[:space:]]*([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}/{print $1 "," $14}' temp_output-01.csv | sort -t, -k1,1 > sorted_ssids.csv
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
        print "  - {" $2 " } (" $1 ")";
    }' sorted_ssids.csv
}

airodump
get_Data
rm -f temp_output-*.csv sorted_ssids.csv

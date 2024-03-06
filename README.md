# Jukebox

An aircrack-ng utility

## [Installation / Usage](https://github.com/emreutkan/jukebox/wiki/Installation---Usage)

## Features
- Interface selection, mode changer (monitor, managed) `(iwconfig + ifconfig)`
- Interface mac spoof `(ip link)`
- Network Scan and target selection `(aireplay-ng)`
- Device Scan (on selected Network) and target selection  `(aireplay-ng)`
- Network Scan by OUI (Organizational Unique Identifier) `shell w/ aireplay-ng`


- Dos attack on target Network `(aireplay-ng)`
- Dos attack on target device `(aireplay-ng)`
- Dos attack on all devices on target Network `(aireplay-ng)`
- Dos attack on OUI (interval/indefinite) `(aireplay-ng)`


- Packet Capture `(airodump-ng)`
- Handshake Capture (WPA2/PSK) `(aireplay-ng + airodump-ng)`
- Brute Force attack on capture file (WPA2/PSK) `(aircrack-ng)`
- Decrypt Capture Packet of Target AP (WPA/WPA2) `(airdecap-ng)`


- handshake Capture on all Networks (`besside-ng`) 
- handshake Capture on target Network (`besside-ng`) 

- Network graph `(airgraph-ng)`


### requirements

- [aircrack-ng](https://www.aircrack-ng.org)
- [airgraph-ng](https://www.aircrack-ng.org/doku.php?id=airgraph-ng)

## Future plans
- Dos attack on all Networks (interval/indefinite) 
- `(airventriloquist-ng)`, `(wesside-ng)`,`wpaclean`, `airolib-ng`, `airdeclock-ng`





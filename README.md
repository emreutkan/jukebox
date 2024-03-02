# Jukebox

An aircrack-ng utility

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
- Brute Force attack on capture file (WPA2/PSK) `(aircrack-ng`
- Network graph `(airgraph-ng)`


- Dos + handshake Capture on all Networks (`besside-ng`) 

### requirements

- aircrack-ng
- airgraph-ng (optional)

## Future plans
- Dos attack on all Networks (interval/indefinite) 
- MITM attacks
- Rogue Network
- Port scan

## not planned

- Anything on WPA/WEP `(airdecap-ng / besside-ng)`
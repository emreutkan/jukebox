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
- Brute Force attack on capture file (WPA2/PSK) `(aircrack-ng)`
- Decrypt Capture Packet of Target AP (WPA/WPA2) `(airdecap-ng)`


- handshake Capture on all Networks (`besside-ng`) 
- handshake Capture on target Network (`besside-ng`) 

- Network graph `(airgraph-ng)`

- Rogue Network [hostapd](https://wiki.gentoo.org/wiki/Hostapd) ,[bridge-utils](https://archlinux.org/packages/extra/x86_64/bridge-utils/)


### requirements

- [aircrack-ng](https://www.aircrack-ng.org)
- [airgraph-ng](https://www.aircrack-ng.org/doku.php?id=airgraph-ng)
- [hostapd](https://wiki.gentoo.org/wiki/Hostapd)
- [bridge-utils](https://archlinux.org/packages/extra/x86_64/bridge-utils/)
- [dnsmasq](https://wiki.gentoo.org/wiki/Dnsmasq)

### helpful documentation

- [Network bridge management](https://wiki.archlinux.org/title/network_bridge)

## Working on 
- MITM
- Rogue ap with wpa, (not related to mitm)

## Future plans
- Dos attack on all Networks (interval/indefinite) 
- Encrypted Wi-Fi packet injection `(airventriloquist-ng)`
- Crack Wep key of an open network `(wesside-ng)`
- wpaclean, airolib-ng, airdeclock-ng
- airbase-ng
- Port scan






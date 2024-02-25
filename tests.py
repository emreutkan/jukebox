import time

from Network import scan_for_networks, scan_for_networks_by_OUI, process_ssids, Deauth, Deauth_By_OUI

def test1():
    ap = scan_for_networks('wlan0')
    print(ap)

def test2():
    scan_for_networks_by_OUI('wlan0')

def test3():
    process_ssids()

def test4():
    Deauth('wlan0','SUPERONLINE')

def test5():
    Deauth_By_OUI('wlan0','6A:6A:4D')
test5()
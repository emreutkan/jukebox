from Network import scan_for_networks, scan_for_networks_by_OUI, process_ssids

def test1():
    ap = scan_for_networks('wlan0')
    print(ap)

def test2():
    scan_for_networks_by_OUI('wlan0')

def test3():
    process_ssids()
test2()
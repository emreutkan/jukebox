import time
from main import spoof_MAC_of_Interface_with_random_byte
from Network import scan_for_networks, scan_for_networks_by_OUI, process_ssids, Deauth, Deauth_By_OUI,scan_devices_in_AP,scan_devices_in_AP_Select_Device,deauth_selected_device,get_BSSID_and_Station_from_AP

if __name__ == "__main__":
    while 1:
        input('jukebox > ')
        scan_for_networks('wlan0')

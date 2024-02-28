
import Network
import main

if __name__ == "__main__":
    # Network.deauth_devices_in_targetAP_with_interval('wlan0','SUPERONLINE')
    Network.scan_for_networks_by_OUI_Select_Router('wlan0')
    # Network.get_airodump_output('wlan0')
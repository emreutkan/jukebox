
import Network
import main

if __name__ == "__main__":
    # Network.deauth_devices_in_targetAP_with_interval('wlan0','SUPERONLINE')
    Network.Deauth_By_OUI('wlan0','SS:SS:SS')
    # Network.get_airodump_output('wlan0')
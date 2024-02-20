import glob
import subprocess
import time

def scan_for_networks(interface):
    airodump =  subprocess.Popen('airodump-ng {} -w /tmp/networks --output-format csv '.format(interface), shell=True)
    time.sleep(10)
    subprocess.run(["kill",str(airodump.pid)])
    subprocess.run('clear')
    files = sorted(glob.glob('/tmp/networks-*.csv'))
    subprocess.run('clear')
    time.sleep(10)
    latest_file = files[-1] if files else None
    if latest_file:
        with open(latest_file,'r') as file:
            print(file.read())
            target_AP = input('Write the Network name of the target AP')
            return target_AP
    else:
        print('no networks found')
        return ""


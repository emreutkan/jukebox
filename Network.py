import glob
import os
import random
import signal
import string
import subprocess
import time
import csv
import pandas as pd




def clear():
    subprocess.run('clear')


def scan_for_networks(interface):
    # airodump =  subprocess.Popen('airodump-ng {} -w /tmp/networks --output-format csv '.format(interface), shell=True)
    airodump = subprocess.Popen('airodump-ng {} -w /tmp/networks --output-format csv &'.format(interface), shell=True, preexec_fn=os.setsid)
    time.sleep(10)
    clear()
    # subprocess.run(["killall", "airodump-ng"])
    # airodump.terminate() this does not work because we are running it with shell=True which creates 2 processes. to kill a process run on shell=True
    # we need to execute this
    os.killpg(airodump.pid,signal.SIGTERM) # but in order for this to work we also have to add preexec_fn=os.setsid to the airodump argument
    time.sleep(0.5)
    files = sorted(glob.glob('/tmp/networks-*.csv'))
    latest_file = files[-1] if files else None
    if latest_file:
        with open(latest_file, 'r') as file:
            print(file.read())
            target_AP = input('Write the Network name of the target AP')
            return target_AP
    else:
        print('no networks found')
        return ""


def process_ssids(file_name):
    df = pd.read_csv(file_name, header=None)
    df.columns = ['bssid', 'ESSID']
    current_oui = None
    for index, row in df.iterrows():
        oui = row['bssid'][:8]
        if oui != current_oui:
            if current_oui:
                print()
            current_oui = oui
            print(f'OUI: {oui}')
        print(f'  - {row["ssid"]} ({row["bssid"]})')

#TODO
def scan_for_networks_by_OUI(interface):
    random_output_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    random_filtered_output_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    print('{}.csv'.format(random_filtered_output_file_name))

    # subprocess.run('airodump-ng {} -w /tmp/{}  --output-format csv &'.format(interface, random_output_file_name),shell=True)
    airodump = subprocess.Popen('airodump-ng {} -w /tmp/{}  --output-format csv &'.format(interface, random_output_file_name),shell=True,preexec_fn=os.setsid)

    time.sleep(1)

    csv_output_location = '/tmp/' + random_output_file_name+'-01.csv'
    csv_output = pd.read_csv(csv_output_location)
    csv_outputa = csv_output['BSSID'] + ',' + csv_output[' ESSID']
    csv_formatted_location = f"/tmp/{random_filtered_output_file_name}.csv"
    os.mknod(csv_formatted_location)
    csv_outputa.to_csv(csv_formatted_location, index=False)


    os.killpg(airodump.pid,signal.SIGTERM) # but in order for this to work we also have to add preexec_fn=os.setsid to the airodump argument
    time.sleep(0.5)
    process_ssids(csv_formatted_location)
    os.remove(f'/tmp/{random_output_file_name}-01.csv')  # '-01' becuase airodump adds a postfix to the csv
    os.remove(csv_formatted_location)

# so i couldnt figure out a way to work with my old shell script. instead of using a python method im calling
# a file from ShellScripts and im sending variables from python to shell then im starting script that relies on those variables

def scan_for_networks_by_OUI(interface):
    subprocess.run(['./ShellScripts/OUIFormatter.sh' + ' ' + f'{interface}'],shell=True)
    return input('Write the Network name of the target AP')

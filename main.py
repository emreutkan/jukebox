import subprocess
import random
import time

from Network import scan_for_networks,scan_for_networks_by_OUI_Select_Router,Deauth,Deauth_By_OUI
selected_interface = ""
TargetAP = ""
TargetDevice = ""
TargetRouterOUI = ""

def clear():
    subprocess.run('clear')

def change_interface():
    global selected_interface
    print("Avaliable Networks Interfaces: ")
    subprocess.run("ip link show | grep -oP '(?<=: )\w+(?=:)'", shell=True, executable="/bin/bash")
    selected_interface = input("Enter the name of the interface ")
    clear()
    subprocess.run('echo "{} is selected " '.format(selected_interface), shell=True)
    print()

def check_if_selected_interface_in_monitor_mode(interface):
    get_current_MAC_command = [f'iwconfig {interface}']
    process = subprocess.Popen(get_current_MAC_command, shell=True,stdout=subprocess.PIPE)
    output = process.stdout.read()
    output = output.decode(encoding='utf-8')
    current_mode = ""

    for i in range(-1, -len(output) - 1, -1):
        if (output[i] == 'M' or output[i] == 'm') and output[i+1] == 'o' and output[i+2] == 'd' and output[i+3] == 'e':
            # we are working with this output

            # wlan0     IEEE 802.11  Mode:Monitor  Frequency:2.412 GHz  Tx-Power=20 dBm
            #           Retry short limit:7   RTS thr:off   Fragment thr:off
            #           Power Management:on

            # so i+4 is : right after Mode
            i=i+5
            for j in range (0,7):
                current_mode=current_mode+(output[i+j])
    if current_mode.strip() == 'Monitor' or current_mode.strip() == 'monitor':
        return True
    else:
        return False


def switch_selected_interface_to_monitor_mode():
    global selected_interface
    clear()
    print('Setting ' + selected_interface + ' to monitor mode ')
    subprocess.run('ifconfig {} down '.format(selected_interface), shell=True)
    subprocess.run('iwconfig {} mode monitor '.format(selected_interface), shell=True)
    subprocess.run('ifconfig {} up '.format(selected_interface), shell=True)
    clear()

def selected_interface_managed_mode():
    global selected_interface
    clear()
    print('Setting ' + selected_interface + ' to managed mode ')
    subprocess.run('ifconfig {} down '.format(selected_interface), shell=True)
    subprocess.run('iwconfig {} mode managed '.format(selected_interface), shell=True)
    subprocess.run('ifconfig {} up '.format(selected_interface), shell=True)
    clear()

def get_MAC_of_interface(interface):
    interface_mac_address = ""
    get_current_MAC_command = [f'ip link show {interface}']
    process = subprocess.Popen(get_current_MAC_command,shell=True,stdout=subprocess.PIPE) # use of stdout=subprocess.PIPE allow the output of the subprocess to be stored in the variable
    output = process.stdout.read() # we store the output but its in byte data not string
    output = output.decode(encoding='utf-8') # now we switch it to string
    for i in range(-1, -len(output) - 1, -1): # in this loop im looking for a string match where if we see 'link/ether' we know that after that we have a space and the next 1 char is empty space and after that next 17 chars are the whole mac address according to theformat of 'ip link show interface'
        if output[i] == 'l' and output[i+1] == 'i' and output[i+4] == '/':
            # if all the cases are a match then we are at the level of i = l where i is the l in start of link/ether
            # so if we add 9 to i we set the i to the position of next empty char after the 'link/ether'
            # and if we add 1 more, it will start from the mac address since there is a space between
            i=i+10
            for j in range (1,18):
                interface_mac_address=interface_mac_address+(output[i+j])
            return interface_mac_address
    # up until this point it's all about getting the MAC ADDRESS

def spoof_MAC_of_Interface_with_random_byte(interface):
    interface_mac_address = get_MAC_of_interface(interface)
    if interface_mac_address == "":
        print(
            f"selected interface is not active right now or there is something wrong with the output of f'ip link show {interface}' if thats the case then let me know")
    else:
        print(f'current interface is {interface} and current MAC address is {interface_mac_address}')
        subprocess.Popen(f'ip link set dev {interface} down',shell=True)
        # random_mac = ':'.join(f"{random.randint(0x00, 0xFF):02X}" for _ in range(6)) ## i had a error here
        # and I solved it thanks to https://superuser.com/questions/725467/set-mac-address-fails-rtnetlink-answers-cannot-assign-requested-address
        # basically
        #    Bit 0 is the "multicast" bit, noting that the address is a multicast or broadcast address
        #    Bit 1 is the "local" bit, indicating that the MAC address was not assigned by the vendor and might not be entirely unique.

        # that means we need to modify the first octet

        # first bit of first octet cant start with 0 (cant be 0x)
        # Last bit of first octet cant end with 1 (cant be 1x)
        # also in my case it cant start with prime number
            # it cant end with 1
            # it cant end with 3
            # it cant end with 5
            # it cant end with 7
            # it cant end with 9
            # it cant end with a
            # it cant end with b
            # it cant end with d
            # it cant end with f

        # can end with 2 4 5 6 8 c e
        # can start with 2 3 4 5 6 8 9 a b c d e f

        first_bit = ['2','3','4','5','6','7','8','a','b','c','d','e','f']
        second_bit = ['2','4','6','8','c','e']
        first_octet = random.choice(first_bit)+random.choice(second_bit)
        random_mac = f'{first_octet}:' + ':'.join(f"{random.randint(0x00, 0xFF):02X}" for _ in range(5))

        print(f'randomly selected mac for {interface} is {random_mac}')
        subprocess.Popen(f'ip link set dev {interface} address {random_mac}', shell=True)
        time.sleep(0.5)
        subprocess.Popen(f'ip link set dev {interface} up',shell=True)


def spoof_MAC_of_Interface_with_known_OUI(interface):
    print()

art = [
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
    "",
    "",
    "",
]

def Interface_Section():
    for i in Interface_Options:
        print(i)


def Wireless_Section():
    for i in Wireless_Options_No_Target:
        print(i)

Interface = ["Interface", Interface_Section]
Wireless = ["Wireless", Wireless_Section]

Section = Interface
Previous_Section = Interface

if __name__ == "__main__":
    while (exit != "exit"):
        for i in art:
            print(i)
        Interface_Options = [
            "======Interface Options======",
            "1) Select interface",
            "2) Put interface in to monitor mode",
            "3) Put interface in to managed mode",
            "4) Spoof MAC Address"
            '',
            "N) Network Attacks",
            "P) Post Connection Attacks",
            '',
            f"Current Interface     :   {selected_interface}",
            "======Interface Options======",
            '',

        ]

        Wireless_Options_No_Target = [
            "======Wireless-Attacks======",
            "1) scan APs and Select a target AP",
            "2) scan and Group APs by OUI and Select a target OUI (Group by Router)",
            '',
            "D1) Deauth Target AP",
            "D2) Deauth all Devices in Selected OUI (Deauth all APs in same router with interval) ",
            "D3) Deauth a Specific Device in Target AP",
            "O1) Deauth all",
            '',

            f"Current Interface     :   {selected_interface}",
            f"Current Target AP     :   {TargetAP}",
            f"Current Target OUI    :   {TargetRouterOUI}",
            f"Current Target Device  :   {TargetDevice}",
            '',
            "Reset) Reset all Targets",
            "999) return",
            "======Wireless-Attacks======",
            '',

        ]

        Section[1]()
        print("type exit to close the program")
        print("type 999 to return to previous section")

        match input("jukebox > "):

            case 'print':
                print(selected_interface)
                time.sleep(30)
            case "999":
                Section = Previous_Section
            case "exit":
                exit = "exit"
                break
            case "reset":
                if (Section[0] == "Wireless"):
                    TargetAP = ""
                    TargetRouterOUI = ""
                    TargetDevice = ""
                    print("Target AP and Target Device has ben reset")
                    clear()
            case '1':
                if (Section[0] == "Interface"):
                    change_interface()
                elif (Section[0] == "Wireless"):
                    TargetAP = scan_for_networks(selected_interface)
            case '2':
                if (Section[0] == "Interface" and selected_interface == ""):
                    print("Cannot continue without selecting a interface")
                    print(selected_interface)
                elif (Section[0] == "Interface"):
                    switch_selected_interface_to_monitor_mode()
                elif (Section[0] == "Wireless"):
                     TargetRouterOUI = scan_for_networks_by_OUI_Select_Router(selected_interface)
            case '3':
                if (Section[0] == "Interface" and selected_interface == ""):
                    print("Cannot continue without selecting a interface")
                    print(selected_interface)
                elif (Section[0] == "Interface"):
                    selected_interface_managed_mode()

            case '4':
                if(selected_interface == ""):
                    print("Select an interface first")
                if(Section[0]=="Interface"):
                    spoof_MAC_of_Interface_with_random_byte(selected_interface)

            case 'D1':
                if (Section[0] == "Wireless"):
                    Deauth(selected_interface,TargetAP)
            case 'D2':
                if (Section[0] == "Wireless" and TargetRouterOUI == ""):
                    print("!NO PREDEFINED OUI DETECTED... Select option 2 and select a target OUI")
                elif (Section[0] == "Wireless"):
                    Deauth_By_OUI(selected_interface, TargetRouterOUI)
            case 'N' | 'n':
                if selected_interface == "":
                    clear()
                    print("Cannot continue with wireless attacks without selecting a interface")
                    input('Press enter to continue')
                elif not check_if_selected_interface_in_monitor_mode(selected_interface):
                    clear()
                    print(f"Cannot continue with wireless attacks without switching interface: {selected_interface} to -> monitor mode")
                    selection = input('Switch to monitor mode Y/N')
                    if selection == 'y' or selection =='Y':
                        switch_selected_interface_to_monitor_mode()
                elif (Section[0] == "Interface"):
                    Previous_Section = Section
                    Section = Wireless
        clear()

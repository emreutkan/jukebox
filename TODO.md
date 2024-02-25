in network attacks 

- some functions depend on other non-relevant functions to run in order for them to work  like deauth by oui depends on scan networks to create the networks.csv in /tmp/ because the deauth function depends on that networks.csv file and deauth by oui depends on deauth function
  - (SOLVED) ok so for the networks.csv file issue above i just added a fucntion to create that exact same folder to the shell script the Deauth_by_oui uses 'OUIFormatterKEEPFILE.sh' the general target selection OUIFormatter.sh still does not create the networks.cvs
  - then i added     
    - files = sorted(glob.glob('/tmp/networks-*.csv'))
    -   latest_file = files[-1] if files else '/tmp/networks-01.csv'
  - these to the method of Deauth_by_OUI and sent the latest file as a parameter to be used in 'awk' call of shell script 
  - also i added 'else '/tmp/networks-01.csv'' because if the file did not exist at first it will exist once we run the script anyway and this will be the first file 
- and some files are saved in /tmp/ while others are saved in the project folder


- some files are persistent while others get deleted after use


- no idea why clear() works sometimes but not always
---

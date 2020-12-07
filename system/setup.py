#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import sys, os, hashlib
from getpass import getpass
import classes.Colors as C


LOC = "/jarvisd"
APP_LOC = f"{LOC}/apps"
USR = os.getlogin()

def install():
	global LOC,APP_LOC,USR

	# check if sudo
	if not is_root():
		print("Must be root to install")
		exit(1)
	

	# get install location
	if input(f"Jarvis is going to be installed at {C.GREEN}{LOC}{C.END} . Is this okay? [y] ") not in ["y", "Y", "z", "Z", "", "\n"]:
		LOC = input("Enter a new installation location (absolute path): ")
		APP_LOC = f'{LOC}/apps'


	# check original user
	if input(f"Is your login user {C.GREEN}{USR}{C.END}? [y] ") not in ["y", "Y", "z", "Z", "", "\n"]:
		USR = input("Enter your login user: ")

	
	# check if service file exists
	if not os.path.isfile(os.path.abspath(os.path.dirname(sys.argv[0])) + "/system/jarvisd.service"):
		print("Service file not found")
		exit(1)

	# ask for keys and store them securely
	psk = getpass(" Pre-shared key : ")
	tk =  getpass("      Token key : ")
	print("I can also set a static IP. If you don't want to set a static IP, just keep the fields blank!")
	ip   =  input("      Static IP : ")
	mask, gate, dns = ["", "", ""]
	if ip != "":
		mask =  input(" CIDR Mask [24] : ")
		gate =  input("     Gateway IP : ")
		dns  =  input("         DNS IP : ")

		if mask == "":
			mask = "24"
		
		if not change_static_ip("wlan0", ip, gate, dns, mask):
			print("Failed to change static IP, not critical")


	hashed_psk = hashlib.sha256(psk.encode('utf-8')).hexdigest()
	f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/pre-shared.key", "w")
	f.write(hashed_psk)
	f.close()

	hashed_token_key = hashlib.sha256(tk.encode('utf-8')).hexdigest()
	f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/token.key", "w")
	f.write(hashed_token_key)
	f.close()


	if not os.path.exists(LOC):
		os.mkdir(LOC)
	if not os.path.exists(APP_LOC):
		os.mkdir(APP_LOC)
		do_action("apply permissions", f"sudo chmod 755 {APP_LOC}")

	do_action(f"move jarvisd to new location ({LOC})", 		f"sudo mv -v * {LOC}")
	do_action("install service file", 						f"sudo cp -v {LOC}/system/jarvisd.service /etc/systemd/system/jarvisd.service")
	do_action("install jarvisd executable", 				f"sudo cp -v {LOC}/system/jarvisd /usr/bin/jarvisd")
	do_action("change jarvisd executable permissions", 		"sudo chmod 777 /usr/bin/jarvisd")
	do_action("reload systemd daemon", 						"sudo systemctl daemon-reload")
	do_action("start jarvisd service", 						"sudo systemctl start jarvisd.service")
	do_action("enable jarvisd service", 					"sudo systemctl enable jarvisd.service")
	do_action(f"change ownership of directory (to {USR})",	f"sudo chown -R {USR}: {LOC}")


	print(f"Successfully set up Jarvisd in {LOC} and registered service")
	print("")
	print("Please reboot!")
	exit(0)


def is_root():
	return os.geteuid() == 0

def do_action(print_str, shell_command, show_output=True, on_fail="failed!", on_success="done!", exit_on_fail=True):
	print(print_str + "... ", end="")

	if not show_output:
		shell_command += " &> /dev/null"

	if not os.system(shell_command) == 0:
		print(on_fail)
		if exit_on_fail:
			exit(1)
	else:
		print(on_success)


def change_static_ip(interface, ip_address, routers, dns, cidr_mask):
	conf_file = '/etc/dhcpcd.conf'
	try:
		# Sanitize/validate params above
		with open(conf_file, 'r') as file:
			data = file.readlines()

		# Find if config exists
		ethFound = next((x for x in data if 'interface ' + interface in x), None)
		ethIndex = None

		if ethFound:
			ethIndex = data.index(ethFound)
			if data[ethIndex].startswith('#'):
				data[ethIndex] = data[ethIndex].replace('#', '') # commented out by default, make active

		# If config is found, use index to edit the lines you need ( the next 3)
		if ethIndex:
			data[ethIndex+1] = f'static ip_address={ip_address}/{cidr_mask}\n'
			data[ethIndex+2] = f'static routers={routers}\n'
			data[ethIndex+3] = f'static domain_name_servers={dns}\n'

			with open(conf_file, 'w') as file:
				file.writelines( data )
		else:
			with open(conf_file, 'a') as file:
				file.write("\ninterface {}\nstatic ip_address={}/{}\nstatic routers={}\nstatic domain_name_servers={}\n".format(interface, ip_address, cidr_mask, routers, dns))

		return True
	except Exception as ex:
		print("Static IP Error: {}".format(ex))
		raise ex
		return False
	finally:
		pass
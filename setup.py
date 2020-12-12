#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import sys, os, hashlib
from getpass import getpass
import classes.Colors as Colors
from classes.JSONConfig import JSONConfig

ROOT_DIR = "/jarvis"
LOC = f"{ROOT_DIR}/server"
APP_LOC = f"{ROOT_DIR}/apps"
USR = os.getlogin()
DIR = os.path.dirname(os.path.abspath(__file__))


def install():
	global ROOT_DIR,LOC,APP_LOC,USR,DIR

	# see if root
	if not is_root():
		print("You need to be root!")
		exit(1)


	# check for installation directory
	if input(f"The default Jarvis installation directory is {Colors.BLUE}{ROOT_DIR}{Colors.END}. Is this okay? [y] ") not in ["y", "Y", "z", "Z", "", "\n"]:
		ROOT_DIR = input("Enter a new installation directory (absolute path): ")
		LOC = f"{ROOT_DIR}/server"
		APP_LOC = f"{ROOT_DIR}/apps"


	# check for user
	if input(f"Your linux username is {Colors.BLUE}{USR}{Colors.END}. Is this correct? [y] ") not in ["y", "Y", "z", "Z", "", "\n"]:
		USR = input("Enter your linux username: ")


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



	# create/write config file
	config_file = f"/home/{USR}/.config/jarvis/main.conf"
	cnf = JSONConfig(config_file)
	if not cnf.exists():
		cnf.create()
		print(f"created config at {config_file}")
		do_action("changing config directory permissions", f"sudo chown -R {USR}: /home/{USR}/.config")
	else:
		print(f"using config at {config_file}")


	# set config parameters
	cnf.set_key("root_dir", ROOT_DIR)
	cnf.set_key("server_dir", LOC)
	cnf.set_key("app_dir", APP_LOC)
	cnf.set_key("user", USR)


	# create directories
	if not os.path.isdir(LOC):
		os.makedirs(LOC)
	if not os.path.isdir(APP_LOC):
		os.makedirs(APP_LOC)


	# check if service file exists
	if not os.path.isfile(os.path.abspath(os.path.dirname(sys.argv[0])) + "/system/jarvisd.service"):
		print("Service file not found")
		exit(1)


	# store hashed keys
	with open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/pre-shared.key", "w") as f:
		f.write(hashlib.sha256(psk.encode('utf-8')).hexdigest())
	with open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/token.key", "w") as f:
		f.write(hashlib.sha256(tk.encode('utf-8')).hexdigest())


	# modify service file
	replace_in_file(f"{DIR}/system/jarvis", "{{DIR}}", DIR)
	replace_in_file(f"{DIR}/system/jarvisd.service", "{{SRV_DIR}}", LOC)


	# execute shell commands
	do_action( "upgrade system",							 "sudo apt update ; sudo apt upgrade -y", exit_on_fail=False)
	do_action( "install packages", 							 "sudo apt install -y git python3-pip mosquitto")
	do_action( "install pip jarvis",						 "sudo pip3 install --upgrade filelock open-jarvis")
	do_action( "change application folder permissions",		f"sudo chmod 755 {APP_LOC}")
	do_action(f"move jarvisd to new location ({LOC})", 		f"sudo mv -v {DIR}/* {LOC}")
	do_action( "install service file", 						f"sudo cp -v {LOC}/system/jarvisd.service /etc/systemd/system/jarvisd.service")
	do_action( "install jarvisd executable", 				f"sudo cp -v {LOC}/system/jarvis /usr/bin/jarvis")
	do_action( "change jarvisd executable permissions", 	 "sudo chmod 777 /usr/bin/jarvis")
	do_action( "reload systemd daemon", 					 "sudo systemctl daemon-reload")
	do_action( "start jarvisd service", 					 "sudo systemctl start jarvisd.service")
	do_action( "enable jarvisd service", 					 "sudo systemctl enable jarvisd.service")
	do_action(f"change ownership of directory (to {USR})",	f"sudo chown -R {USR}: {LOC}")
	do_action(f"copy api documentation to {LOC}/apidoc",	f"git clone https://github.com/open-jarvis/open-jarvis.github.io {LOC}/apidoc")
	do_action( "clean up directory",						f"sudo rm -rf {DIR}")

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
def replace_in_file(path, search, replacement):
	contents = None
	with open(path, "r") as f:
		contents = f.read()

	if contents is None:
		do_action(f"reading file {path}", "false")
	
	contents = contents.replace(search, replacement)
	with open(path, "w") as f:
		f.write(contents)



install()
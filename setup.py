#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import sys, os, hashlib
from getpass import getpass


def install():
	# check if sudo
	if not is_root():
		print("Must be root to install")
		exit(1)
	
	# check if service file exists
	if not os.path.isfile(os.path.abspath(os.path.dirname(sys.argv[0])) + "/jarvisd.service"):
		print("Service file not found")
		exit(1)

	# ask for keys and store them securely
	psk = getpass(" Pre-shared key : ")
	tk =  getpass("      Token key : ")
	print("I can also set a static IP. If you don't want to set a static IP, just keep the fields blank!")
	ip   =  input("      Static IP : ")
	mask, gate, dns = ["", "", ""]
	if ip != "":
		mask =  input("CIDR Mask [/24] : ")
		gate =  input("     Gateway IP : ")
		dns  =  input("         DNS IP : ")


	hashed_psk = hashlib.sha256(psk.encode('utf-8')).hexdigest()
	f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/pre-shared.key", "w")
	f.write(hashed_psk)
	f.close()

	hashed_token_key = hashlib.sha256(tk.encode('utf-8')).hexdigest()
	f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/token.key", "w")
	f.write(hashed_token_key)
	f.close()

	# move all files
	if not os.path.exists("/jarvisd"):
   		os.mkdir("/jarvisd")
	
	if not os.system("sudo mv -v * /jarvisd") == 0:
		print("Failed to move folder..")
		exit(1)


	# move service file
	if not os.system("sudo cp -v /jarvisd/jarvisd.service /etc/systemd/system/jarvisd.service") == 0:
		print("Failed to move service file")
		exit(1)


	# reload daemon to get file
	if not os.system("sudo systemctl daemon-reload") == 0:
		print("Failed to reload systemd daemon")
		exit(1)

	
	# enable and start service
	if not os.system("sudo systemctl start jarvisd.service") == 0:
		print("Failed to start jarvisd")
		exit(1)

	if not os.system("sudo systemctl enable jarvisd.service") == 0:
		print("Failed to enable jarvisd")
		exit(1)


	# set static ip
	if ip != "":
		if not change_static_ip("wlan0", ip, gate, dns, mask):
			print("Failed to change static IP, not critical")

	print("Successfully set up Jarvisd in /jarvisd and registered service")
	exit(0)


def is_root():
	return os.geteuid() == 0

def change_static_ip(interface, ip_address, routers, dns, mask):
	conf_file = '/etc/dhcpcd.conf'
	try:
		# Sanitize/validate params above
		with open(conf_file, 'r') as file:
			data = file.readlines()

		# Find if config exists
		ethFound = next((x for x in data if 'interface ' + interface in x), None)

		if ethFound:
			ethIndex = data.index(ethFound)
			if data[ethIndex].startswith('#'):
				data[ethIndex] = data[ethIndex].replace('#', '') # commented out by default, make active

		# If config is found, use index to edit the lines you need ( the next 3)
		if ethIndex:
			data[ethIndex+1] = f'static ip_address={ip_address}/{mask}\n'
			data[ethIndex+2] = f'static routers={routers}\n'
			data[ethIndex+3] = f'static domain_name_servers={dns}\n'

		with open(conf_file, 'w') as file:
			file.writelines( data )
		
		return True
	except Exception as ex:
		return False
	finally:
		pass
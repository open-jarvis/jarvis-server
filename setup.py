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



	print("Successfully set up Jarvisd in /jarvisd and registered service")
	exit(0)


def is_root():
	return os.geteuid() == 0

#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import time, traceback
import classes.Storage as Storage
from jarvis import Exiter

running = True

# inactivity scan
def inactivity_scan(root_dir):
	while Exiter.running:
		try:
			devices = Storage.get_devices()
			for token, device in devices.items():
				if device["last-active"] + 20 < time.time():	# inactive
					device["status"] = "red"
				else:
					device["status"] = "green"
				devices[token] = device
			Storage.write_devices(devices)
		except Exception as e:
			print(traceback.format_exc())
		finally:
			time.sleep(2)

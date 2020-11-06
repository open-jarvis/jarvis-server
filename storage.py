#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import random, json, time, os, sys


EXPIRES_IN = 120	# seconds
DIRECTORY = os.path.abspath(os.path.dirname(sys.argv[0])) + "/storage"
TOKEN_FILE = DIRECTORY + "/tokens.json"
DEVICE_FILE = DIRECTORY + "/devices.json"
NOTIFICATION_FILE = DIRECTORY + "/notifications.json"


def get_tokens():
	f = open(TOKEN_FILE, "r")
	tokens = json.loads(f.read())
	f.close()
	return tokens

def write_tokens(tokens):
	f = open(TOKEN_FILE, "w")
	f.write(json.dumps(tokens))
	f.close()

def get_devices():
	f = open(DEVICE_FILE, "r")
	devs = json.loads(f.read())
	f.close()
	return devs

def write_devices(devices):
	f = open(DEVICE_FILE, "w")
	f.write(json.dumps(devices))
	f.close()

def get_notifications():
	f = open(NOTIFICATION_FILE, "r")
	tokens = json.loads(f.read())
	f.close()
	return tokens

def write_notifications(devices):
	f = open(NOTIFICATION_FILE, "w")
	f.write(json.dumps(devices))
	f.close()



def add_token(tk):
	try:
		tokens = get_tokens()

		invalid_tokens = []

		for token in tokens:
			if tokens[token] < time.time():
				invalid_tokens.append(token)
		
		for t in invalid_tokens:
			del tokens[t]

		tokens[tk] = time.time() + EXPIRES_IN
		write_tokens(tokens)
		return True
	except Exception as e:
		return False

def is_valid(tk):
	tokens = get_tokens()
	try:
		if tokens[tk] < time.time():
			del tokens[tk]
			write_tokens(tokens)
			return False
		else:
			return True
	except Exception as e:
		return False



def add_device(ip, name, token, app_or_web, connection):
	try:
		devices = get_devices()
		devices[token] = { "ip":ip, "name":name, "type": app_or_web, "connection":connection, "status":"green", "last-active": time.time() }
		write_devices(devices)

		tokens = get_tokens()
		del tokens[token]
		write_tokens(tokens)
		return True
	except Exception as e:
		return False

def remove_device(token):
	try:
		devices = get_devices()
		del devices[token]
		write_devices(devices)

		nots = get_notifications()
		del nots[token]
		write_notifications(nots)
		return True
	except Exception as e:
		return False

def set_notifications(device_token, updated_notifications):
	try:
		notifications = get_notifications()
		notifications[device_token] = {"last_update": time.time(), "notifications": updated_notifications}
		write_notifications(notifications)
		return True
	except Exception as e:
		raise e
		return False

def get_all_notifications():
	try:
		return get_notifications()
	except Exception as e:
		return {}

def get_notifications_for_device(device_token):
	try:
		return get_notifications()[device_token]
	except Exception as e:
		return False

def update_device_status(token, made_hello):
	if made_hello:
		try:
			dev = get_devices()
			dev[token]["last-active"] = time.time()
			dev[token]["status"] = "green"
			write_devices(dev)
			return True
		except Exception as e:
			return False
	else:
		try:
			dev = get_devices()
			if dev[token]["last-active"] + 20 < time.time():
				dev[token]["status"] = "red"
				write_devices(dev)
				return True
			else:
				return True
		except Exception as e:
			return False

#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import random, json, time, os, sys
import storage as Storage


def generate_token(ip, attrs, post_body):
	new_token = ''.join(random.choice("abcdef0123456789") for _ in range(8))
	b = Storage.add_token(new_token)
	if b:
		return {"success":b, "token": new_token}
	else:
		return {"success":b}

def register_device(ip, attrs, post_body):
	name = attrs["name"]
	passed_token = attrs["token"]
	dev_type = attrs["type"]
	con_type = "app" if (attrs["native"] == "true") else "web"

	if Storage.is_valid(passed_token):
		return {"success": Storage.add_device(ip, name, passed_token, dev_type, con_type) }
	else:
		return {"success": False, "error": "token is not valid!"}

def unregister_device(ip, attrs, post_body):
	if "token" in attrs:
		token = attrs["token"]
		return {"success": Storage.remove_device(token) }
	else:
		return {"success": False, "error": "no token provided!" }


def set_notifications(ip, attrs, post_body):
	token = attrs["token"]
	notifications = post_body["notifications"]

	return {"success": Storage.set_notifications(token, notifications) }

def get_notifications(ip, attrs, post_body):
	if "token" in attrs:
		res = Storage.get_notifications_for_device(attrs["token"])
		if res == False:
			return {"success": False, "error": "device not found!" }
		return {"success": True, "notifications": res}
	else:
		return {"success": True, "notifications": Storage.get_all_notifications() }


def set_location(ip, attrs, post_body):
	if "token" not in attrs:
		return {"success": False, "error": "no token provided!"}

	token = attrs["token"]
	loc = post_body["location"]

	return {"success": Storage.set_location(token, loc) }

def get_location(ip, attrs, post_body):
	locs = Storage.get_locations()
	
	if "token" in attrs:
		if attrs["token"] in locs:
			return {"success": True, "location": locs[attrs["token"]]}
		else:
			return {"success": False, "error": "device not found!"}
	else:
		return {"success": True, "locations": locs}
	

def get_devices(ip, attrs, post_body):
	if "token" in attrs:
		res = Storage.get_devices()
		if attrs["token"] in res:
			return {"success":True, "device": res[attrs["token"]]}
		else:
			return {"success":False, "error": "device not found"}
	else:
		return {"success": True, "devices": Storage.get_devices()}

def hello(ip, attrs, post_body):
	if "token" in attrs:
		res = Storage.update_device_status(attrs["token"], True)
		if res:
			return {"success": True}
		else:
			return {"success": False, "error": "couldn't find device"}
	else:
		return {"success":False, "error":"no token provided"}

def am_i_registered(ip, attrs, post_body):
	b = Storage.get_devices()
	if "token" in attrs:
		if attrs["token"] in b:
			return {"success": True}
		else:
			return {"success": False, "error": "device not found"}
	else:
		return {"success": False, "error": "no token provided!"}
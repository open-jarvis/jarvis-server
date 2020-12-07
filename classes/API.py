#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import random, json, time, os, sys
import classes.Storage as Storage


## HTTP API
def generate_token(ip, attrs, post_body, logger):
	if not "permission-level" in post_body or int(post_body["permission-level"]) > 4 or int(post_body["permission-level"]) < 1:
		return {"success":False, "error":"POST permission level either not set or invalid (range 1-4)"}
	new_token = ''.join(random.choice("abcdef0123456789") for _ in range(8))
	b = Storage.add_token(new_token, int(post_body["permission-level"]))
	if b:
		return {"success":b, "token": new_token}
	else:
		return {"success":b}
def get_devices(ip, attrs, post_body, logger):
	if "target_token" in post_body:
		res = Storage.get_devices()
		if post_body["token"] in res:
			return {"success":True, "device": res[post_body["target_token"]]}
		else:
			return {"success":False, "error": "device not found"}
	else:
		return {"success": True, "devices": Storage.get_devices()}


def register_device(ip, attrs, post_body, logger):
	name = attrs["name"]
	passed_token = attrs["token"]
	dev_type = attrs["type"]
	con_type = "app" if (attrs["native"] == "true") else "web"

	if Storage.is_valid(passed_token):
		return {"success": Storage.add_device(ip, name, passed_token, dev_type, con_type, Storage.get_permission_level_for_token(passed_token)) }
	else:
		return {"success": False, "error": "token is not valid!"}
def unregister_device(ip, attrs, post_body, logger):
	if "token" in attrs:
		token = attrs["token"]
		return {"success": Storage.remove_device(token) }
	else:
		return {"success": False, "error": "no token provided!" }


def set_property(ip, attrs, post_body, logger):
	if ("token" in attrs) and ("property" in post_body) and ("value" in post_body):
		return {"success":Storage.set_property(attrs["token"], post_body["property"], post_body["value"])}
	else:
		return {"success":False, "error":"make sure GET token and POST property,value are set"}
def get_property(ip, attrs, post_body, logger):
	if ("property" in post_body):
		if "token" in attrs:
			return {"success":True, "result":Storage.get_property(attrs["token"], post_body["property"])}
		else:
			return {"success":True, "result":Storage.get_all_properties(post_body["property"])}
	else:
		return {"success":False, "error":"make sure POST property is set"}


def hello(ip, attrs, post_body, logger):
	if "token" in attrs:
		res = Storage.update_device_status(attrs["token"], True)
		if res:
			return {"success": True}
		else:
			return {"success": False, "error": "couldn't find device"}
	else:
		return {"success":False, "error":"no token provided"}
def am_i_registered(ip, attrs, post_body, logger):
	b = Storage.get_devices()
	if "token" in attrs:
		if attrs["token"] in b:
			return {"success": True}
		else:
			return {"success": False, "error": "device not found"}
	else:
		return {"success": False, "error": "no token provided!"}


debug_session_started_by = ""
def start_debug(ip, attrs, post_body, logger):
	global debug_session_started_by, debug_running, debug_data
	if "token" in attrs:
		debug_session_started_by = attrs["token"]
		logger.enable_fast()
		logger.new_group({"timestamp":time.time(), "ip":ip})
		return {"success":True}
	else:
		return {"success":False,"error":"no token provided"}
def scan_debug(ip, attrs, post_body, logger):
	global debug_session_started_by, debug_running, debug_data
	if "token" in attrs:
		if debug_session_started_by == attrs["token"]:
			d = logger.get_fast()
			logger.clear_fast()
			logger.new_group({"timestamp":time.time(), "ip":ip, "token":attrs["token"]})
			return {"success":True, "data": d}
		else:
			return {"success":False, "error":"you didn't start the debug session"}
	else:
		return {"success":False, "error":"no token provided"}
def stop_debug(ip, attrs, post_body, logger):
	global debug_session_started_by, debug_running, debug_data
	if "token" in attrs:
		if debug_session_started_by == attrs["token"]:
			debug_session_started_by = ""
			logger.disable_fast()
			return {"success":True}
		else:
			return {"success":False, "error":"you didn't start the debug session"}
	else:
		return {"success":False, "error":"no token provided"}



## ID API
def id__ask(ip, attrs, post_body, logger):
	if ("token" in attrs) and ("type" in post_body) and ("name" in post_body) and ("infos" in post_body) and ("options" in post_body):
		tk = attrs["token"]
		tp = post_body["type"]
		nm = post_body["name"]
		nf = post_body["infos"]
		op = post_body["options"]


		if (len(op) == 0):
			return {"success": False, "error": "POST options has to contain at least 1 option"}
		
		Storage.instant_ask(tk,tp,nm,nf,op)

		return {"success":True}
	else:
		return {"success":False, "error": "GET token, POST type, name, infos and options have to be set"}
def id__answer(ip, attrs, post_body, logger):
	if ("token" in attrs) and ("target_token" in post_body) and ("type" in post_body) and ("option" in post_body):
		desc = ""
		if "description" in post_body:
			desc = post_body["description"]
		tk = attrs["token"]
		tt = post_body["target_token"]
		ty = post_body["type"]
		op = post_body["option"]

		Storage.instant_answer(tt,tk,ty,op,desc)

		return {"success":True}
	else:
		return {"success":False, "error":"GET token, POST target_token, type, options, (description) have to be set"}
def id__scan(ip, attrs, post_body, logger):
	if not "token" in attrs:
		return {"success":False, "error":"no token provided"}

	tk = False
	ty = False
	if ("target_token" in post_body):
		tk = post_body["target_token"]
	if ("type" in post_body):
		ty = post_body["type"]
	return {"success":True, "scan": Storage.instant_scan(tk,ty)}
def id__delete(ip, attrs, post_body, logger):
	if ("token" in attrs) and ("target_token" in post_body) and ("type" in post_body):
		Storage.instant_delete(post_body["target_token"], post_body["type"])
		return {"success":True}
	else:
		return {"success":False, "error":"GET token, POST target_token, type have to be set"}



## UNREACHABLE API
def get_permission_level(tk):
	return Storage.get_permission_level_for_token(tk)

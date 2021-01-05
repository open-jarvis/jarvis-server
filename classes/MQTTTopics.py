#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import classes.Storage as Storage


# data["token"] EXISTS!

def register(data):
	if "name" in data:
		Storage.add_token(data["token"], 5) # permission 5 because this file limits ability
		s = Storage.add_device("127.0.0.1", data["name"], data["token"], "application", "on-device", 5)
		return {"success":s}
	else:
		return {"success": False, "result": "name parameter missing"}

def get_devices(data):
	return {"success": True, "result": Storage.get_devices()}

def get_property(data):
	if "key" in data:
		return {"success": True, "result": Storage.get_property(data["target-token"], data["key"]) if "target-token" in data else Storage.get_all_properties(data["key"]) }
	else:
		return {"success": False, "error": "key parameter missing"}

def set_property(data):
	if "target-token" in data and "key" in data and "value" in data:
		return {"success": Storage.set_property(data["target-token"], data["key"], data["value"])}
	else:
		return {"success": False, "error": "target-token, key or value parameter missing"}

def id__ask(data):
	if "type" in data and "name" in data and "infos" in data and "options" in data:
		Storage.instant_ask(data["token"], data["type"], data["name"], data["infos"], data["options"])
		return {"success": True}
	else: 
		return {"success": False, "error": "type, name, infos or options parameter missing"}

def id__answer(data):
	if "target-token" in data and "type" in data and "option-index" in data and "description" in data:
		Storage.instant_answer(data["target-token"], data["token"], data["type"], data["option-index"], data["description"])
		return {"success": True}
	else:
		return {"success": False, "error": "target-token, type, option-index or description parameter missing"}

def id__scan(data):
	return {"success": True, "result": Storage.instant_scan(data["target-token"] if "target-token" in data else False, data["type"] if "type" in data else False)}

def id__delete(data):
	if "target-token" in data and "type" in data:
		Storage.instant_delete(data["target-token"], data["type"])
		return {"success": True}
	else:
		return {"success": False, "error": "target-token or type parameter missing"}


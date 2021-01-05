#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import random, json, time, os, sys
import classes.Permissions as Permissions
from filelock import FileLock
from jarvis import Logger


EXPIRES_IN = 120	# seconds
ROOT_DIRECTORY = os.path.abspath(os.path.dirname(sys.argv[0]))
DIRECTORY = ROOT_DIRECTORY + "/storage"
TOKEN_FILE = DIRECTORY + "/tokens.json"
DEVICE_FILE = DIRECTORY + "/devices.json"
STORAGE_FILE = DIRECTORY + "/brain.json"
INSTANT_FILE = DIRECTORY + "/instants.json"

MASTER_TOKEN = Permissions.get_mastertoken()

READS = {
	TOKEN_FILE:0,
	DEVICE_FILE:0,
	STORAGE_FILE:0,
	INSTANT_FILE:0
}

last_instant_read = 0
last_instant_contents = ""

LOGGER = Logger(f"{ROOT_DIRECTORY}/logs/file_operations.log", f"{ROOT_DIRECTORY}/logs")

def readf(f):
	global READS, LOGGER
	LOGGER.i("read", f)
	res = {}
	with open(f, "r") as fl:
		if f in READS:
			READS[f] += 1
		res = fl.read()
	return json.loads(res)
def writef(f,c):
	LOGGER.i("write", f"{f} -> {c}")
	lock = FileLock(f"{f}.lock")
	with lock:
		open(f, "w").write(c)

def get_tokens():
	return readf(TOKEN_FILE)
def get_devices():
	return readf(DEVICE_FILE)
def get_properties():
	return readf(STORAGE_FILE)
def get_instants():
	global last_instant_read, last_instant_contents
	lmod = os.stat(INSTANT_FILE).st_mtime
	if lmod > last_instant_read:
		last_instant_read = lmod
		last_instant_contents = readf(INSTANT_FILE)
		del lmod
	return last_instant_contents

def write_tokens(tokens):
	writef(TOKEN_FILE, json.dumps(tokens))
def write_devices(devices):
	writef(DEVICE_FILE, json.dumps(devices))
def write_properties(props):
	writef(STORAGE_FILE, json.dumps(props))
def write_instants(instants):
	writef(INSTANT_FILE, json.dumps(instants))




def add_token(tk, permission_level):
	tokens = get_tokens()
	invalid_tokens = []

	for token in tokens:
		if tokens[token]["valid_until"] < time.time():
			invalid_tokens.append(token)
	
	for t in invalid_tokens:
		del tokens[t]

	valid_until = time.time() + EXPIRES_IN
	tokens[tk] = {"valid_until": valid_until, "permission-level":permission_level}
	write_tokens(tokens)
	return True

def is_valid(tk):
	tokens = get_tokens()
	invalid_tokens = []
	valid = True
	made_changes = False

	for token in tokens:
		if tokens[token]["valid_until"] < time.time():
			if token == tk:
				valid = False
			invalid_tokens.append(token)
	
	for t in invalid_tokens:
		del tokens[t]
		made_changes = True

	if made_changes:
		write_tokens(tokens)

	return valid



def get_permission_level_for_token(tk):
	if tk == MASTER_TOKEN:
		return 5
	# check if not registered yet
	_get_tokens = get_tokens()
	if tk in _get_tokens:
		return _get_tokens[tk]["permission-level"]
	
	# check if already registered
	_get_devices = get_devices()
	if tk in _get_devices:
			return _get_devices[tk]["permission-level"]
	return 0

def add_device(ip, name, token, app_or_web, connection, permission_level):
	devices = get_devices()
	devices[token] = { "ip":ip, "name":name, "type": app_or_web, "connection":connection, "status":"green", "last-active": time.time(), "permission-level": permission_level }
	write_devices(devices)

	tokens = get_tokens()
	del tokens[token]
	write_tokens(tokens)
	return True

def remove_device(token):
	devices = get_devices()
	if token in devices:
		del devices[token]
	write_devices(devices)

	props = get_properties()
	if token in props:
		del props[token]
	write_properties(props)

	instants = get_instants()
	if token in instants:
		del instants[token]
	write_instants(instants)
	return True

def update_device_status(token, made_hello):
	if made_hello:
		dev = get_devices()
		dev[token]["last-active"] = time.time()
		dev[token]["status"] = "green"
		write_devices(dev)
		return True
	else:
		dev = get_devices()
		if dev[token]["last-active"] + 20 < time.time():
			dev[token]["status"] = "red"
			write_devices(dev)
			return True
		else:
				return True


def set_property(token, key, value):
	brain = get_properties()
	if token not in brain:
		brain[token] = {}
	brain[token][key] = value
	write_properties(brain)
	return True
def get_property(token, key):
	return get_properties()[token][key]
def get_all_properties(key):
	res = {}
	for tk in get_devices().keys():
		res[tk] = get_property(tk, key)
	return res


def instant_ask(token, typ, name, infos, options):
	instants = get_instants()
	if token not in instants:
		instants[token] = []
	
	instants[token].append({"answered":False, "answer": { "token": "", "description": "", "option": {} }, "timestamp":int(time.time()), "type": typ, "name":name, "infos":infos, "options":options})

	write_instants(instants)
def instant_scan(token=False, tpe=False):
	instants = get_instants()

	if token is not False:
		to_del = []
		for tk in instants:
			if tk != token:
				to_del.append(tk)
		for tk in to_del:
			del instants[tk]
	if tpe is not False:
			for tk in instants:
				to_del = []
				for i in range(len(instants[tk])):
					if instants[tk][i]["type"] != tpe:
						to_del.append(i)
				for index in to_del:
					del instants[tk][index]

	return instants
def instant_answer(token, sourcetoken, typ, option_index, description):
	instants = get_instants()

	if token not in instants:
		instants[token] = []

	write = False

	for i in range(len(instants[token])):
		if instants[token][i]["type"] == typ:
			instants[token][i]["answered"] = True
			instants[token][i]["answer"]["token"] = sourcetoken
			instants[token][i]["answer"]["description"] = description
			instants[token][i]["answer"]["option"] = instants[token][i]["options"][option_index]
			write = True
	
	if write:
		write_instants(instants)
def instant_delete(token, typ):
	instants = get_instants()
	to_del = -1

	if token not in instants:
		instants[token] = []

	for i in range(len(instants[token])):
		if instants[token][i]["type"] == typ:
			to_del = i
	if to_del is not -1:
		del instants[token][to_del]
		write_instants(instants)

		

	
	
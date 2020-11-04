#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import random, json, time, os, sys


EXPIRES_IN = 120	# seconds
TOKEN_FILE = os.path.abspath(os.path.dirname(sys.argv[0])) + "/tokens.json"
DEVICE_FILE = os.path.abspath(os.path.dirname(sys.argv[0])) + "/devices.json"

if not os.path.isfile(TOKEN_FILE):
	f = open(TOKEN_FILE, "w")
	f.write("{}")
	f.close()
if not os.path.isfile(DEVICE_FILE):
	f = open(DEVICE_FILE, "w")
	f.write("{}")
	f.close()


class Storage:
	@staticmethod
	def get_tokens():
		f = open(TOKEN_FILE, "r")
		tokens = json.loads(f.read())
		f.close()
		return tokens

	@staticmethod
	def write_tokens(tokens):
		f = open(TOKEN_FILE, "w")
		f.write(json.dumps(tokens))
		f.close()

	@staticmethod
	def get_devices():
		f = open(DEVICE_FILE, "r")
		tokens = json.loads(f.read())
		f.close()
		return tokens

	@staticmethod
	def write_devices(devices):
		f = open(DEVICE_FILE, "w")
		f.write(json.dumps(devices))
		f.close()



	@staticmethod
	def add_token(tk):
		try:
			tokens = Storage.get_tokens()

			invalid_tokens = []

			for token in tokens:
				if tokens[token] < time.time():
					invalid_tokens.append(token)
			
			for t in invalid_tokens:
				del tokens[t]

			tokens[tk] = time.time() + EXPIRES_IN
			Storage.write_tokens(tokens)
			return True
		except expression as identifier:
			return False

	@staticmethod
	def is_valid(tk):
		tokens = Storage.get_tokens()
		try:
			if tokens[tk] < time.time():
				del tokens[tk]
				Storage.write_tokens(tokens)
				return False
			else:
				return True
		except Exception as e:
			return False
	
	@staticmethod
	def add_device(ip, name, token, type, connection):
		try:
			devices = Storage.get_devices()
			devices[token] = { "ip":ip, "name":name, "type":type, "connection":connection }
			Storage.write_devices(devices)

			tokens = Storage.get_tokens()
			del tokens[token]
			Storage.write_tokens(tokens)
			return True
		except expression as identifier:
			return False

	@staticmethod
	def remove_device(token):
		try:
			devices = Storage.get_devices()
			del devices[token]
			Storage.write_devices(devices)
			return False
		except expression as identifier:
			return False





def ping(ip, attrs):
	return {"success":True,"message":"pong"}

def generate_token(ip, attrs):
	new_token = ''.join(random.choice("abcdef0123456789") for _ in range(8))
	b = Storage.add_token(new_token)
	if b:
		return {"success":b, "token": new_token}
	else:
		return {"success":b}


def register_device(ip, attrs):
	name = attrs["name"]
	passed_token = attrs["token"]
	dev_type = attrs["type"]
	con_type = "app" if (attrs["native"][0] == "true") else "web"

	b = Storage.add_device(ip, name, passed_token, dev_type, con_type)

	return {"success":b}

def unregister_device(ip, attrs):
	token = attrs["token"]
	b = Storage.remove_device(token)

	return {"success":b}



"""
	if Storage.is_valid():
			try:
				expdate = -1

				i = 0
				token_index = -1
				for token, extime in tokens:
					if token == passed_token:
						expdate = extime
						token_index = i
					i += 1
				
				if (expdate < time.time()):
					if token_index == -1:
						helper.log("jarvis", "token {} not found {} (user tried to auth)".format(passed_token, expdate))
						self.wfile.write(json.dumps({"success":False, "message":"Token invalid!"}).encode())
					else:
						tokens.pop(token_index)
						helper.log("jarvis", "token {} expired {} (user tried to auth)".format(passed_token, expdate))
						self.wfile.write(json.dumps({"success":False, "message":"Token expired!"}).encode())
				else:
					tokens.pop(token_index)
					registered_devices.append({
						"name": name,
						"ip": ip, 
						"type": dev_type, 
						"status": "green", 
						"connection": con_type,
						"id": token
					})
					helper.log("jarvis", "registered new device {} with token {}".format(ip, token))
					self.wfile.write(json.dumps({"success":True, "message": "Congrats! You're registered"}).encode())
			except Exception as e:
				helper.log("http", "error: /register-device - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
		if path == "/unregister-device":
			token = arguments["token"][0]
			
			try:
				i = 0
				popped = False
				for dev in registered_devices:
					if dev["id"] == token:
						registered_devices.pop(i)
						popped = True
					i += 1

				if popped:
					helper.log("jarvis", "unregistered device with token {}".format(token))
					self.wfile.write(json.dumps({"success":True, "message": "Unregistered!"}).encode())
				else:
					helper.log("jarvis", "couldn't unregister device with token {}: not found".format(token))
					self.wfile.write(json.dumps({"success":False, "message": "Couldn't find device with token {}".format(token)}).encode())
			except Exception as e:
				helper.log("http", "error: /unregister-device - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())
		if path == "/list-devices":
			try:
				self.wfile.write(json.dumps({"success":True, "devices":list(registered_devices)}).encode())
			except Exception as e:
				helper.log("http", "error: /list-devices - {}".format(traceback.format_exc().replace("\n", "<br>")))
				self.wfile.write(json.dumps({"success":False, "message": "an unknown error occured - {}".format(str(e))}).encode())

"""
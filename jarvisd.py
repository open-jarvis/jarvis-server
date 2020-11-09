#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: jarvisd.py
# 
# Manages data from smart devices
# 
# arguments:
#	--pre-shared-key <pre-shared-key>  Sets a pre-shared key for future requests
#	--pre-shared-key <pre-shared-key>  Sets a pre-shared key for future requests


import multiprocessing, time, sys, os, hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

# import custom http server to handle incoming web requests
from http_server import JarvisWebServer
import device_service
import setup

if "--install" in sys.argv:
	setup.install()


USAGE = "\nUsage: python3 jarvisd.py --pre-shared-key <psk> --token-key <tokenkey>"


if not "--use-stored" in sys.argv:
	psk = None
	token_key = None
	if "--pre-shared-key" in sys.argv:
		try:
			psk = sys.argv[sys.argv.index("--pre-shared-key") + 1]
		except Exception as e:
			print("pre-shared-key not set!" + USAGE)
			exit(1)
	else:
		print("pre-shared-key not set!" + USAGE)
		exit(1)

	if "--token-key" in sys.argv:
		try:
			token_key = sys.argv[sys.argv.index("--token-key") + 1]
		except Exception as e:
			print("token-key not set!" + USAGE)
			exit(1)
	else:
		print("token-key not set!" + USAGE)
		exit(1)


	hashed_psk = hashlib.sha256(psk.encode('utf-8')).hexdigest()
	f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/pre-shared.key", "w")
	f.write(hashed_psk)
	f.close()

	hashed_token_key = hashlib.sha256(token_key.encode('utf-8')).hexdigest()
	f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/token.key", "w")
	f.write(hashed_token_key)
	f.close()


# runs server
def startServer():
	server = HTTPServer(('', 2021), JarvisWebServer)
	server.serve_forever()


# starts the http server
server_process = multiprocessing.Process(target=startServer)
server_process.start()

# starts the device inactivity check
device_inactivity_scan = multiprocessing.Process(target=device_service.inactivity_scan)
device_inactivity_scan.start()


while True:
	time.sleep(1)

#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# usage: jarvisd.py
# 
# Manages data from smart devices
# 
# arguments:
#	--pre-shared-key <pre-shared-key>  Sets a pre-shared key for future requests


import multiprocessing, time, sys, os, hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

# import custom http server to handle incoming web requests
from http_server import JarvisWebServer


psk = None
if "--pre-shared-key" in sys.argv:
	try:
		psk = sys.argv[sys.argv.index("--pre-shared-key") + 1]
	except Exception as e:
		print("pre-shared-key not set!\nUsage: python3 jarvisd.py --pre-shared-key <psk>")
		exit(1)
else:
	print("pre-shared-key not set!\nUsage: python3 jarvisd.py --pre-shared-key <psk>")
	exit(1)


hashed_psk = hashlib.sha256(psk.encode('utf-8')).hexdigest()
f = open(os.path.abspath(os.path.dirname(sys.argv[0])) + "/pre-shared.key", "w")
f.write(hashed_psk)
f.close()


# runs server
def startServer():
	server = HTTPServer(('', 2021), JarvisWebServer)
	server.serve_forever()


# starts the http server
server_process = multiprocessing.Process(target=startServer)
server_process.start()


while True:
	time.sleep(1)

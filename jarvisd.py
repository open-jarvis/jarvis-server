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


import sys, os

if "--install" in sys.argv:
	import system.setup
	system.setup.install()
	exit(0)


# import custom http server to handle incoming web requests
import multiprocessing, time, os, hashlib, traceback, signal
from http.server import BaseHTTPRequestHandler, HTTPServer
import classes.BackendServer as BackendServer
import classes.DeviceService as DeviceService
import classes.AppLoader as AppLoader
from classes.Logger import Logger


DIR = os.path.dirname(os.path.realpath(__file__))
USAGE = "\nUsage: python3 jarvisd.py --pre-shared-key <psk> --token-key <tokenkey>"
PROCESSES = []


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
def start_server(root_dir):
	try:
		server = HTTPServer(('', 2021), BackendServer.JarvisWebServer)
		server.serve_forever()
	except Exception as e:
		raise e
def terminate_process(p, name, max_tries=3, time_between_tries=5, logging_instance=None):
	p.terminate()
	i = 0
	while p.is_alive():
		i += 1
		if i > max_tries:
			if logging_instance is not None:
				logging_instance.i("Process", f"killing process '{name}', didn't react to terminate signals")
			p.kill()
			return
		else:
			if logging_instance is not None:
				logging_instance.i("Process", f"waiting for the '{name}' process to terminate (try {i})")
			time.sleep(time_between_tries)
def register_process(target_function, process_name):
	global PROCESSES, DIR
	p = multiprocessing.Process(target=target_function, name=process_name, args=[DIR])
	p.start()
	PROCESSES.append(p)
def stop_all_processes(loggr):
	global PROCESSES, logger
	for p in PROCESSES:
		terminate_process(p, p.name, logging_instance=logger)
def on_SIGTERM():
	logger.e("Signal", "caught SIGTERM, stopping all subprocesses")
	stop_all_processes()
	exit(0)


# initiate logger
logger = Logger(DIR + "/logs/jarvisd.log", DIR + "/logs")
logger.console_on()


# start services
register_process(start_server, "server")							# launch http server and api
register_process(AppLoader.load_apps, "app loader")					# launch app loader service
register_process(DeviceService.inactivity_scan, "inactivity scan")	# launch inactivity scan


# handle system signals
signal.signal(signal.SIGINT, on_SIGTERM)


try:
	while True:
		time.sleep(1)
except Exception as e:
	logger.e("Stopping", f"caught exception in infinite loop, stopping all subprocesses: {traceback.format_exc()}")
	stop_all_processes()
	exit(0)
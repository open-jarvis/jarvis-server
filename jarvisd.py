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


from jarvis import Logger, Exiter, Config
import classes.MQTTServer as MQTTServer
import classes.MQTTLogger as MQTTLogger
import classes.AppLoader as AppLoader
import classes.DeviceService as DeviceService
import classes.BackendServer as BackendServer
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import os
import multiprocessing
import time
import os
import hashlib
import traceback

# define initial variables
DIR = os.path.dirname(os.path.realpath(__file__))
USAGE = "\nUsage: python3 jarvisd.py --pre-shared-key <psk> --token-key <tokenkey>"
PROCESSES = []

# perform some checks
if not "--use-stored" in sys.argv:
    psk = None
    token_key = None
    cnf = Config()
    if "--pre-shared-key" in sys.argv:
        try:
            psk = sys.argv[sys.argv.index("--pre-shared-key") + 1]
            cnf.set("pre-shared-key", hashlib.sha256(psk.encode('utf-8')).hexdigest())
        except Exception as e:
            print("pre-shared-key not set!" + USAGE)
            exit(1)
    else:
        print("pre-shared-key not set!" + USAGE)
        exit(1)

    if "--token-key" in sys.argv:
        try:
            token_key = sys.argv[sys.argv.index("--token-key") + 1]
            cnf.set("token-key", hashlib.sha256(token_key.encode('utf-8')).hexdigest())
        except Exception as e:
            print("token-key not set!" + USAGE)
            exit(1)
    else:
        print("token-key not set!" + USAGE)
        exit(1)


# import custom http server to handle incoming web requests


# runs server
def start_server(root_dir):
    try:
        server = HTTPServer(('', 2021), BackendServer.JarvisWebServer)
        server.serve_forever()
    except OSError as ose:
        print(ose)
        print("Maybe another Jarvis instance is already running?")
        exit(1)
    except Exception as e:
        raise e


def terminate_process(p, name, max_tries=3, time_between_tries=5, logging_instance=None):
    p.terminate()
    i = 0
    while p.is_alive():
        i += 1
        if i > max_tries:
            if logging_instance is not None:
                logging_instance.i(
                    "process", f"killing process '{name}', didn't react to terminate signals")
            p.kill()
            return
        else:
            if logging_instance is not None:
                logging_instance.i(
                    "process", f"waiting for the '{name}' process to terminate (try {i})")
            time.sleep(time_between_tries)


def register_process(target_function, process_name):
    global PROCESSES, DIR
    p = multiprocessing.Process(
        target=target_function, name=process_name, args=[DIR])
    p.start()
    PROCESSES.append(p)


def stop_all_processes():
    global PROCESSES, logger
    for p in PROCESSES:
        terminate_process(p, p.name, logging_instance=logger)


# initiate logger
logger = Logger("jarvisd")
logger.console_on()


# start services
# launch http server and api
register_process(start_server, "http api server")
# launch mqtt api server
register_process(MQTTServer.start_server, "mqtt api server")
# launch app loader service
register_process(AppLoader.load_apps, "app loader")
register_process(DeviceService.inactivity_scan,
                 "inactivity scan")  # launch inactivity scan
# launch mqtt sniffer and logger
register_process(MQTTLogger.start_logging, "mqtt sniffer")


try:
    while Exiter.running:
        time.sleep(1)
    logger.i("exiting", f"caught exit signal, exiting")
except Exception as e:
    logger.e(
        "stopping", f"caught exception in infinite loop, stopping all subprocesses: {traceback.format_exc()}")

stop_all_processes()
exit(0)

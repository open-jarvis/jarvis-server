#!/usr/bin/python3

#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import sys
import threading
import core.Trace as Trace


# set tracer
sys.settrace(Trace.tracer)
threading.settrace(Trace.tracer)


import os
import time
import json
import traceback
from jarvis import Logger, Exiter, ThreadPool, MQTT
import core.MQTTServer as MQTTServer
import satellite.DatabaseAnalytics as DatabaseAnalytics
import satellite.NLU as NLU
import satellite.AutoUpdate as AutoUpdate


# initiate logger
logger = Logger("jarvisd")
logger.console_on()


# save current file for updates
CURRENT_FILE = os.path.abspath(sys.argv[0])
VERSION_FILE = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/version"


# launch api servers
tpool = ThreadPool(logger)
tpool.register(MQTTServer.start_server, "mqtt api server")
tpool.register(DatabaseAnalytics.start_analysis, "database analytics")
tpool.register(AutoUpdate.update_checker, "autoupdate")
tpool.register(NLU.start_server, "nlu server")


# restart listener
mqtt = MQTT(client_id="jarvis")
"""
Listens to: jarvis/backend/restart|status
"""
def _on_MSG(a, b, msg):
    global CURRENT_FILE
    global logger, tpool, mqtt
    try:
        if msg.topic == "jarvis/backend/restart":
            logger.i("restart", "caught mqtt restart signal, restarting")
            try:
                os.execv(sys.executable, ["python3", CURRENT_FILE, "--upgraded"])
            except Exception:
                logger.e("failed-restart", "failed to restart script, see traceback", traceback.format_exc())
        if msg.topic == "jarvis/backend/status":
            data = json.loads(msg.payload.decode())
            if "reply-to" in data:
                result = {}
                for t in tpool.threads:
                    result[t.name] = t.is_alive()
                mqtt.publish(data["reply-to"], json.dumps({"status": "up", "threads": result}))
    except Exception:
        logger.e("jarvis-mqtt", "error in main mqtt endpoint, see traceback", traceback.format_exc())
mqtt.on_message(_on_MSG)
mqtt.subscribe("jarvis/backend/#")



def main():
    global logger
    logger.i("File", f"Running jarvis file {CURRENT_FILE}")
    try:
        with open(VERSION_FILE, "r") as f:
            logger.i("Version", f"Running version v{f.read().strip()}")
    except Exception:
        logger.w("Version", "Couldn't read version file")
    while Exiter.running:
        time.sleep(1)
    logger.i("Stop", f"Caught exit signal, exiting")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.e("Stop", f"Caught exception in main loop, stopping all threads", traceback.format_exc())
    exit(0)

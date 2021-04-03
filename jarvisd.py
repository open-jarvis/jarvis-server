#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import os
import sys
import time
import traceback
from jarvis import Logger, Exiter, ProcessPool, MQTT
from jarvis import update as jarvis_update
import core.MQTTServer as MQTTServer
import core.HTTPServer as HTTPServer
import satellite.DatabaseAnalytics as DatabaseAnalytics
import satellite.NLU as NLU

# initiate logger
logger = Logger("jarvisd")
logger.console_on()


# launch api servers
ppool = ProcessPool(logger)
ppool.register(HTTPServer.start_server, "http api server")
ppool.register(MQTTServer.start_server, "mqtt api server")
ppool.register(DatabaseAnalytics.start_analysis, "database analytics")
ppool.register(NLU.start_server, "nlu server")


# restart listener
mqtt = MQTT(client_id="jarvis")
"""
Listens to: jarvis/backend/restart
"""
def do_restart(a, b, c):
    logger.i("pip", "checking for new python package and installing if present")
    jarvis_update()
    logger.i("restart", "caught mqtt restart signal, stopping processes before restart")
    ppool.stop_all()
    logger.i("restart", "all processes are stopped, restart is being performed")
    os.execv(sys.executable, ['python3'] + [sys.argv[0]])
mqtt.on_message(do_restart)
mqtt.subscribe("jarvis/backend/restart")


try:
    while Exiter.running:
        time.sleep(1)
    logger.i("exiting", f"caught exit signal, exiting")
except Exception as e:
    logger.e(
        "stopping", f"caught exception in infinite loop, stopping all subprocesses", traceback.format_exc())

ppool.stop_all()
exit(0)

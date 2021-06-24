#!/usr/bin/python3

#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import sys
import threading
import core.Trace as Trace
import core.Checks as Checks


sys.settrace(Trace.tracer)
threading.settrace(Trace.tracer)

Checks.check_system()


import os
import traceback
from jarvis import Logger, Exiter, ThreadPool, API
import core.MQTTServer as MQTTServer
import satellite.NLU as NLU
import satellite.AutoUpdate as AutoUpdate
import satellite.DatabaseAnalytics as DatabaseAnalytics


CURRENT_FILE = os.path.abspath(sys.argv[0])


logger = Logger("Daemon")
logger.console_on()


tpool = ThreadPool(logger)
tpool.register(MQTTServer.start_server, "mqtt")
tpool.register(DatabaseAnalytics.start_analysis, "analytics")
tpool.register(AutoUpdate.update_checker, "update")
tpool.register(NLU.start_server, "nlu")


@API.route("jarvis/status")
def jarvis_status(args, client, data):
    global tpool
    result = {}
    for t in tpool.threads:
        result[t.name] = t.is_alive()
    return result

@API.route("jarvis/restart")
def jarvis_restart(args, client, data):
    global logger, CURRENT_FILE
    if client.id != "server":
        return False
    logger.i("Restart", "Restarting due to MQTT restart signal")
    try: 
        os.execv(sys.executable, ["python3", CURRENT_FILE, "--upgraded"])
    except Exception:
        logger.e("Restart", "Failed to restart Jarvis, see traceback", traceback.format_exc())


import core.Routing # import additional routes


def main():
    global logger
    logger.i("File", f"Running jarvis file {CURRENT_FILE}")
    Exiter.mainloop()
    logger.i("Stop", f"Caught exit signal, exiting")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.e("Stop", f"Caught exception in main loop, stopping all threads", traceback.format_exc())
    exit(0)

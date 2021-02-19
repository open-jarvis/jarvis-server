#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


from jarvis import Logger, Exiter, Config, ProcessPool
import classes.MQTTServer as MQTTServer
import classes.HTTPServer as HTTPServer
import sys
import os
import multiprocessing
from multiprocessing import Pool
import time
import os
import hashlib
import traceback


# initiate logger
logger = Logger("jarvisd")
logger.console_on()


# launch api servers
ppool = ProcessPool(logger)
ppool.register(HTTPServer.start_server, "http api server")
ppool.register(MQTTServer.start_server, "mqtt api server")


try:
    while Exiter.running:
        time.sleep(1)
    logger.i("exiting", f"caught exit signal, exiting")
except Exception as e:
    logger.e(
        "stopping", f"caught exception in infinite loop, stopping all subprocesses: {traceback.format_exc()}")

ppool.stop_all()
exit(0)

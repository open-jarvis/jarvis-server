#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import time
import traceback
from jarvis import Logger, Exiter, ProcessPool
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


try:
    while Exiter.running:
        time.sleep(1)
    logger.i("exiting", f"caught exit signal, exiting")
except Exception as e:
    logger.e(
        "stopping", f"caught exception in infinite loop, stopping all subprocesses", traceback.format_exc())

ppool.stop_all()
exit(0)

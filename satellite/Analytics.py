"""
Copyright (c) 2021 Philipp Scheer
"""


import time
import psutil
import traceback
from jarvis import Database, Exiter, Logger, ThreadPool
# from jarvis.Logger import Logger


POLL_INTERVAL = 60 * 5     # poll every 5 minutes
logger = Logger("Analytics")
tp = ThreadPool()


def start():
    """Start all analytics processes"""
    tp.register(analytics_loop, "Database Analytics", [db_analytics])
    tp.register(analytics_loop, "System Analytics", [sys_analytics])


def analytics_loop(fn):
    """Runs a function in a loop and restarts it every time an exception occurs"""
    global logger
    try:
        while Exiter.running:
            fn()
            for i in range(POLL_INTERVAL * 2):
                if Exiter.running:
                    time.sleep(0.49)
    except Exception:
        logger.e("Error", "Error occured while getting analytics", traceback.format_exc())
        time.sleep(5)
        analytics_loop(fn)


def sys_analytics():
    """Collects system data (CPU, RAM usage, etc...) and saves this data to database"""
    global POLL_INTERVAL
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(psutil.disk_partitions()[0].mountpoint)
    cpu_usage = psutil.cpu_percent(interval=1) / 100
    ram_used = ram.used
    ram_total = ram.total
    ram_usage = ram.percent / 100
    storage_used = disk.used
    storage_total = disk.total
    storage_usage = disk.percent / 100
    network = {
            "bytes": {
                "sent": psutil.net_io_counters().bytes_sent,
                "received": psutil.net_io_counters().bytes_recv
            },
            "packets": {
                "sent": psutil.net_io_counters().packets_sent,
                "received": psutil.net_io_counters().packets_recv
            }}
    Database().table("analytics").insert({
        "type": "system",
        "timestamp": int(time.time()),
        "stats": {
            "cpu": cpu_usage,
            "ram": { "used": ram_used, "total": ram_total, "usage": ram_usage },
            "storage": { "used": storage_used, "total": storage_total, "usage": storage_usage },
            "network": network
        }
    })


def db_analytics():
    """The actual DB analytics loop which runs in a given interval and collects data and saves to DB"""
    global POLL_INTERVAL
    stats = Database().stats
    formatted_stats = {}
    formatted_stats["reads"] = stats["couchdb"]["database_reads"]["value"]
    formatted_stats["purges"] = stats["couchdb"]["document_purges"]["total"]["value"]
    formatted_stats["writes"] = stats["couchdb"]["document_writes"]["value"]
    formatted_stats["inserts"] = stats["couchdb"]["document_inserts"]["value"]
    formatted_stats["codes"] = {}
    for code in [200, 201, 202, 204, 206, 301, 302, 304, 400, 401, 403, 404, 405, 406, 409, 412, 413, 414, 415, 416, 417, 500, 501, 503]:
        formatted_stats["codes"][code] = stats["couchdb"]["httpd_status_codes"][str(code)]["value"]

    Database().table("analytics").insert({
        "type": "db",
        "timestamp": int(time.time()),
        "stats": formatted_stats
    })


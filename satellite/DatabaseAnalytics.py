#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

from jarvis import Database, Exiter
import time


def start_analysis():
    while Exiter.running:
        stats = Database().stats
        formatted_stats = {}
        formatted_stats["reads"] = stats["couchdb"]["database_reads"]["value"]
        formatted_stats["purges"] = stats["couchdb"]["document_purges"]["total"]["value"]
        formatted_stats["writes"] = stats["couchdb"]["document_writes"]["value"]
        formatted_stats["inserts"] = stats["couchdb"]["document_inserts"]["value"]
        formatted_stats["codes"] = {}
        for code in [200, 201, 202, 204, 206, 301, 302, 304, 400, 401, 403, 404, 405, 406, 409, 412, 413, 414, 415, 416, 417, 500, 501, 503]:
            formatted_stats["codes"][code] = stats["couchdb"]["httpd_status_codes"][str(
                code)]["value"]

        Database().table("analytics").insert({
            "timestamp": int(time.time()),
            "stats": formatted_stats
        })

        time.sleep(60 * 15)

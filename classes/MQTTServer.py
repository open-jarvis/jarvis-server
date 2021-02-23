#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import time
import json
import traceback
from jarvis import MQTT, Exiter, Logger
import classes.API as API

ms = None
logger = None


class MQTTServer:
    def __init__(self):
        self.mqtt = MQTT(client_id="jarvis:MQTTServer")
        self.mqtt.on_message(on_message)
        self.mqtt.subscribe("jarvis/api/#")

    def start_mainloop(self):
        while Exiter.running:
            time.sleep(1)


def on_message(c, ud, msg):
    global ms, logger

    try:
        topic = msg.topic.replace(
            "jarvis/api/", "").replace("/", "__").replace("-", "_")
        data = json.loads(msg.payload.decode())

        res = json.dumps(getattr(API, topic)(data)) if "token" in data else json.dumps(
            {"success": False, "error": "token parameter missing"})

        if "reply-to" in data:
            logger.s(
                "on_msg", f"successfully ran endpoint '{topic}' and got response '{res}'")
            ms.mqtt.publish(data["reply-to"], res)
        else:
            logger.w("on_msg", "no 'reply-to' channel")
    except Exception as e:
        logger.e(
            "on_msg", f"unknown exception occured: {str(e)}", traceback.format_exc())


def start_server():
    global ms, logger
    logger = Logger("mqtt-api")
    logger.console_on()
    logger.i("start", "starting mqtt api server")
    ms = MQTTServer()
    ms.start_mainloop()

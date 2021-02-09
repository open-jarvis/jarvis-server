#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import sys
import time
import json
from jarvis import MQTT, Exiter, Logger
import classes.API as API
import classes.MQTTTopics as Topics

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

        res = json.dumps(getattr(Topics, topic)(data)) if "token" in data else json.dumps(
            {"success": False, "error": "token parameter missing"})

        if "reply-to" in data:
            logger.s(
                "on_msg", f"successfully ran endpoint '{topic}' and got response '{res}'")
            ms.mqtt.publish(data["reply-to"], res)
        else:
            logger.w("on_msg", "no 'reply-to' channel")
    except Exception as e:
        logger.e("on_msg", str(e))


def start_server(DIR):
    global ms, logger
    logger = Logger("mqttserver")
    logger.console_on()
    logger.i("mqtt_server", "starting server")
    ms = MQTTServer()
    ms.start_mainloop()

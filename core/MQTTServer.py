#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import time
import json
import traceback
from jarvis import MQTT, Exiter, Logger
from core.API import API


ms = None
logger = None


class MQTTServer:
    """
    MQTT helper class that provides a main loop
    """
    def __init__(self):
        """
        Initialize the server.  
        It automatically connects to the MQTT broker and subscribes to the `jarvis/api/#` topic
        """
        self.mqtt = MQTT(client_id="jarvis:MQTTServer")
        self.mqtt.on_message(on_message)
        self.mqtt.subscribe("jarvis/api/#")

    def start_mainloop(self):
        """
        Start the main loop.  
        While the parent process is running, do not exit
        """
        global logger
        while Exiter.running:
            time.sleep(1)
        logger.i("Exit", "Shutting down the MQTT server")
        


def on_message(c, ud, msg):
    """
    This function gets called whenever the MQTT server receives a message  
    It only listens to the `jarvis/api/#` topic and tries to find an appropriate endpoint in the API class
    """
    global ms, logger

    try:
        topic = msg.topic
        data = json.loads(msg.payload.decode())

        res = json.dumps(API.execute(topic))
        logger.s("MQTT API", f"Successfully ran endpoint '{topic}' and got response '{res}'")

        if "reply-to" in data:
            ms.mqtt.publish(data["reply-to"], res)
        else:
            logger.w("MQTT API", f"No 'reply-to' channel specified for topic '{topic}'")
    except Exception as e:
        logger.e("MQTT API", f"Unknown exception occured: {str(e)}", traceback.format_exc())


def start_server():
    """
    Start the MQTT API server.  
    Create a logging instance and an MQTT server, where we start the main loop
    """
    global ms, logger
    logger = Logger("mqtt-api")
    logger.console_on()
    logger.i("start", "starting mqtt api server")
    ms = MQTTServer()
    ms.start_mainloop()

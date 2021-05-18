#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import time
import json
import traceback
from jarvis import MQTT, Exiter, Logger
from classes.API import API


logger = Logger("MQTT API")
mqtt = MQTT(client_id="MQTT Server")


def on_message(c, ud, msg):
    """
    This function gets called whenever the MQTT server receives a message  
    It only listens to the `jarvis/#` topic and tries to find an appropriate endpoint in the API class
    """
    global logger, mqtt

    try:
        data = json.loads(msg.payload.decode())
        res = json.dumps(API.execute(msg.topic))
        logger.s("MQTT", f"Successfully ran endpoint '{msg.topic}' and got response '{res}'")

        if "reply-to" in data:
            mqtt.publish(data["reply-to"], res)
        else:
            logger.w("MQTT", f"No 'reply-to' channel specified for topic '{msg.topic}'")
    except Exception as e:
        logger.e("MQTT", f"Unknown exception occured: {str(e)}", traceback.format_exc())


def start_server():
    """
    Start the MQTT API server.  
    Create a logging instance and an MQTT server, where we start the main loop
    """
    global logger, mqtt
    logger.i("Start", "Starting MQTT API server")
    mqtt.on_message(on_message)
    mqtt.subscribe("jarvis/api/#")
    Exiter.mainloop()
    logger.i("Exit", "Shutting down MQTT API server")

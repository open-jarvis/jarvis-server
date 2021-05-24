"""
Copyright (c) 2021 Philipp Scheer
"""


import json
import traceback
from jarvis import MQTT, Exiter, Logger, Protocol, API
from core.Permissions import PUBLIC_KEY, PRIVATE_KEY, CLIENT_KEYS


logger = Logger("API")
mqtt = MQTT(userdata="server")


def on_message(c, ud, msg):
    """This function gets called whenever the MQTT server receives a message  
    It only listens to the `jarvis/#` topic and tries to find an appropriate endpoint in the API class.  
    The client has to provide its ID via the userdata parameter. Requests without userdata parameter are discarded"""
    global logger, mqtt

    print(c)
    print(ud)

    try:
        proto = Protocol(PRIVATE_KEY, PUBLIC_KEY, CLIENT_KEYS.get(ud, None), auto_rotate=True)
        data  = proto.decrypt( msg.payload.decode(), return_raw = True )
        res   = API.execute(msg.topic, data["data"])
        logger.s("Server", f"Successfully ran endpoint '{msg.topic}' and got response '{res}'")

        res = {
            "success": res[0],
            "response": res[1]
        }

        if "reply-to" in data:
            mqtt.publish(data["reply-to"], proto.encrypt(res, is_json=True))
        else:
            logger.w("Server", f"No 'reply-to' channel specified for topic '{msg.topic}'")
    except Exception as e:
        logger.e("Server", f"Unknown exception occured: {str(e)}", traceback.format_exc())


def start_server():
    """Start the MQTT API server.  
    Create a logging instance and an MQTT server, where we start the main loop"""
    global logger, mqtt
    logger.i("Start", "Starting MQTT API server")
    mqtt.on_message(on_message)
    mqtt.subscribe("jarvis/#")
    Exiter.mainloop()
    logger.i("Exit", "Shutting down MQTT API server")

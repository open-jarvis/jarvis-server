"""
Copyright (c) 2021 Philipp Scheer
"""


import json
import traceback
from jarvis import MQTT, Exiter, Logger, API
from core.Permissions import PRIVATE_KEY, PUBLIC_KEY
from classes.Client import Client


logger = Logger("API")
mqtt   = MQTT("server", PRIVATE_KEY, PUBLIC_KEY, None)


def on_message(topic: str, data: any, client_id: str):
    """This function gets called whenever the MQTT server receives a message  
    It only listens to the `jarvis/#` topic and tries to find an appropriate endpoint in the API class"""
    global logger, mqtt

    client = None
    try:
        client = Client.load(client_id)
    except Exception:
        res = json.dumps({ "success": False })
        mqtt.update_public_key(None)
        mqtt.publish(data["reply-to"], res)
        return

    data = json.loads(data)

    try:
        res = API.execute(topic, client, data)
        logger.s("Server", f"Successfully ran endpoint '{topic}' and got response '{res}'")
        res = { "success": res[0], "result": res[1] }
    except Exception as e:
        logger.e("Server", f"Unknown exception occured in endpoint '{topic}'", traceback.format_exc())

    client.reload()
    rpub = client.get("public-key", None)
    mqtt.update_public_key(rpub)
    mqtt.publish(data["reply-to"], res) \
        if "reply-to" in data else \
            logger.w("Server", f"No 'reply-to' channel specified for topic '{topic}'")


def start_server():
    """Start the MQTT API server.  
    Create a logging instance and an MQTT server, where we start the main loop"""
    global logger, mqtt
    logger.i("Start", "Starting MQTT API server")
    mqtt.on_message(on_message)
    mqtt.subscribe("jarvis/#")
    Exiter.mainloop()
    logger.i("Exit", "Shutting down MQTT API server")


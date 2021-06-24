"""
Copyright (c) 2021 Philipp Scheer
"""


import time
import json
import traceback
from jarvis import MQTT, Exiter, Logger, API
from core.Permissions import PRIVATE_KEY, PUBLIC_KEY, MQTT_SERVER, UNVERIFIED_ENDPOINTS
from classes.Client import Client


logger = Logger("MQTT-API")
mqtt   = MQTT_SERVER


def on_message(topic: str, data: any, client_id: str):
    """This function gets called whenever the MQTT server receives a message  
    It only listens to the `jarvis/#` topic and tries to find an appropriate endpoint in the API class"""
    global logger, mqtt

    start = time.time()
    client = None

    logger.d("Message", f"{topic} -> {data} : {client_id}")

    if topic not in UNVERIFIED_ENDPOINTS:
        try:
            client = Client.load(client_id)
            client.set("modified-at", int(time.time()))
        except Exception:
            logger.e("Client", f"Failed to get client '{client_id}'", traceback.format_exc())
            res = { "success": False }
            mqtt.update_public_key(None)
            mqtt.publish(data["reply-to"], res)
            logger.d("Timing", f"Executing MQTT endpoint '{topic}' took {time.time()-start :.2f}s")
            return

    try:
        res = API.execute(topic, client, data)
        res = { "success": res[0], "result": res[1] }
    except Exception as e:
        logger.e("Server", f"Unknown exception occured in endpoint '{topic}'", traceback.format_exc())

    if client:
        client.reload()
        rpub = client.get("public-key", None)
        mqtt.update_public_key(rpub)
    else:
        mqtt.update_public_key(None)

    mqtt.publish(data["reply-to"], res) \
        if "reply-to" in data else \
            logger.w("Server", f"No 'reply-to' channel specified for topic '{topic}'")

    logger.d("Timing", f"Executing MQTT endpoint '{topic}' took {time.time()-start :.2f}s")

    # mqtt.publish takes ~4s, encryption?


def start_server():
    """Start the MQTT API server.  
    Create a logging instance and an MQTT server, where we start the main loop"""
    global logger, mqtt
    logger.i("Start", "Starting MQTT API server")
    mqtt.on_message(on_message)
    mqtt.subscribe("jarvis/#")
    Exiter.mainloop()
    logger.i("Exit", "Shutting down MQTT API server")


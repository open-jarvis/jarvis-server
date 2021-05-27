"""
Copyright (c) 2021 Philipp Scheer
"""


import json
import traceback
from jarvis import MQTT, Exiter, Logger, Protocol, API
from core.Permissions import PRIVATE_KEY, PUBLIC_KEY, CLIENT_KEYS
from classes.Client import Client


logger = Logger("API")
server_mqtt = MQTT(userdata="server")
key_mqtt = MQTT(userdata="keyserver")


def on_message(c, client_id, msg):
    """This function gets called whenever the MQTT server receives a message  
    It only listens to the `jarvis/#` topic and tries to find an appropriate endpoint in the API class.  
    The client has to provide its ID via the userdata parameter. Requests without userdata parameter are discarded"""
    global logger, server_mqtt

    res = json.dumps({ "success": False })
    client_pub_key = CLIENT_KEYS.get(client_id, None)
    if client_pub_key is None:
        pass

    client = Client.load(client_id)
    # TODO: handle Client not found exception
    # TODO: no response is a good response too..

    try:
        proto = Protocol(PRIVATE_KEY, PUBLIC_KEY, client_pub_key, auto_rotate=True)
        data  = proto.decrypt(msg.payload.decode(), ignore_invalid_signature=False, return_raw=True)
        """If this step succeeds, this means that if the public key of the client matches the `client_id` and `client is not None`, 
        we can safely assume that the message really originated from the `client_id`"""
        res = API.execute(msg.topic, client, data["data"])
        logger.s("Server", f"Successfully ran endpoint '{msg.topic}' and got response '{res}'")
        res = { "success": res[0], "response": res[1] }
        res = proto.encrypt(res, is_json=True)
    except Exception as e:
        logger.e("Server", f"Unknown exception occured in endpoint '{msg.topic}'", traceback.format_exc())

    server_mqtt.publish(data["reply-to"], res) if "reply-to" in data else \
    logger.w("Server", f"No 'reply-to' channel specified for topic '{msg.topic}'")


def on_keyserver(c, client_id, msg):
    """This function gets called whenever the MQTT receives a keyserver request  
    Traffic to these endpoints is unencrypted as it only includes getting and setting public keys  
    It only listens to the `keyserver/#` topic and tries to find an appropriate endpoint in the API class  
    The client has to provide its ID via the userdata parameter. Requests without the userdata parameter are discarded"""
    global logger, key_mqtt

    if client_id.strip() == "":
        return

    client = Client.load(client_id)

    try:
        data = json.loads(msg.payload.decode())
        res  = API.execute(msg.topic, client, data)
        res  = { "success": res[0], "response": res[1] }
        res  = json.dumps(res)
    except Exception as e:
        logger.e("Server", f"Unknown exception occured in keyserver endpoint '{msg.topic}'", traceback.format_exc())

    key_mqtt.publish(data["reply-to"], res) if "reply-to" in data else \
    logger.w("Server", f"No 'reply-to' channel specified for topic '{msg.topic}'")


def start_server():
    """Start the MQTT API server.  
    Create a logging instance and an MQTT server, where we start the main loop"""
    global logger, mqtt
    logger.i("Start", "Starting MQTT API server")
    server_mqtt.on_message(on_message)
    server_mqtt.subscribe("jarvis/#")
    key_mqtt.on_message(on_keyserver)
    key_mqtt.subscribe("keyserver/#")
    Exiter.mainloop()
    logger.i("Exit", "Shutting down MQTT API server")


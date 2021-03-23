#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import time
import json
import traceback
import tempfile
from jarvis import Database, MQTT, Logger
import snips_nlu


QUERY_TIME = 10

logger = Logger("nlu")
nlu_engine = snips_nlu.SnipsNLUEngine()
currently_training = False

def start_server():
    """
    Starts the NLU server.
    This function also starts the training server which waits for new data to train the model
    The server first tries to fetch existing assistant data, if no data is stored in the database, 
        the script will wait for trained data to be written into the database and it'll fetch from there
    """
    start_training_server()

    assistant_data = get_assistant_data()
    while not assistant_data:
        time.sleep(QUERY_TIME)
        assistant_data = get_assistant_data()


def start_training_server():
    """
    Starts a training server
    Listens to jarvis/satellite/nlu { train: { ... data ... } }
    If it receives a valid message, train the NLU engine and save both the trained model and training data into the database
    """
    mqtt_training_server = MQTT(client_id="nlu-training-server")
    mqtt_training_server.subscribe("jarvis/satellite/nlu")

    def _training_server_on_msg(c, ud, msg):
        global logger
        try:
            data = json.loads(msg.payload.decode())

            if "train" in data:
                nlu_data = data["train"]
                # train the nlu instance
                nlu_engine.fit(dataset=nlu_data, force_retrain=True)
                engine_path = tempfile.TemporaryDirectory().name
                nlu_engine.persist(engine_path)
                logger.i("train", f"persisted trained engine at '{engine_path}'")

                # insert the data into the database
                db_object = {
                    "modified-at": int(time.time()),
                    "nlu-data": nlu_data 
                }
                assistant_table = Database().table("assistant")
                res = assistant_table.filter(lambda x: "nlu-data" in x)
                """
                `nlu-data` format:
                {
                    "created-at": "<unix timestamp>",
                    "modified-at": "<unix timestamp>",
                    "nlu-data": ... up to 256Mb data size (MQTT spec) ...
                }
                """
                if res.found:
                    res.update(db_object)
                else:
                    db_object["created-at"] = int(time.time())
                    assistant_table.insert(db_object)
                if "reply-to" in data:
                    mqtt_training_server.publish(data["reply-to"], json.dumps({"success": True}))
        except Exception:
            logger.e("train", "failed to parse data and insert into database", traceback.format_exc())
            if "reply-to" in data:
                mqtt_training_server.publish(data["reply-to"], json.dumps({"success": False}))
    mqtt_training_server.on_message(_training_server_on_msg)


def get_assistant_data():
    """
    Try to retrieve the already fitted NLU data
    If fitted data could be found, return it, else None
    """
    res = Database().table("assistant").filter({"type": "nlu-data"})
    if res.found:
        return res[0]
    else:
        return None

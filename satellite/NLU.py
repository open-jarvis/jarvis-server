#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import time
import json
import traceback
from jarvis import Database, MQTT, Logger
from jarvis.Exiter import Exiter
import snips_nlu


mqtt_training_server = MQTT(client_id="nlu-training-server")
mqtt_nlu_server = MQTT(client_id="nlu-server")
mqtt_status_server = MQTT(client_id="nlu-status-server")
logger = Logger("nlu")
nlu_engine = snips_nlu.SnipsNLUEngine()


QUERY_TIME = 10
STATISTICS = {
    "trained": False,
    "training": False,
    "avg-time": {
        "training": 0,
        "parsing": 0
    },
    "total-time": {
        "training": 0,
        "parsing": 0
    },
    "count": {
        "training": 0,
        "parsing": 0
    }
}


def start_server():
    """
    Starts the NLU server.
    This function also starts the training server which waits for new data to train the model
    The server first tries to fetch existing assistant data, if no data is stored in the database, 
        the script will wait for trained data to be written into the database and it'll fetch from there
    """
    global logger
    start_training_server()
    start_status_server()
    # try to get data from database
    assistant_data = get_assistant_data()
    # train nlu model
    logger.i("data", "successfully loaded data from database")
    train_nlu_model(assistant_data)
    # how to handle nlu utterance requests
    start_parsing_server()
    # start mainloop
    while Exiter.running:
        time.sleep(1)
    logger.i("shutdown", "shutting down nlu servers")
    return


def start_training_server():
    """
    Starts a training server
    Listens to jarvis/satellite/nlu/train { "data": ... data ..., 
                                            "reply-to": ... temporary mqtt reply to channel ... }
    If it receives a valid message, train the NLU engine and save both the trained model and training data into the database
    """
    global mqtt_training_server
    def _on_NLU_TRAINING(c, ud, msg):
        global logger
        try:
            # train the nlu instance
            data = json.loads(msg.payload.decode())
            nlu_data = data["data"]
            train_nlu_model(nlu_data)
            # save nlu data
            save_assistant_data({
                "modified-at": int(time.time()),
                "nlu-data": nlu_data
            })
            if "reply-to" in data:
                mqtt_training_server.publish(data["reply-to"], json.dumps({"success": True}))
        except Exception:
            if "reply-to" in data:
                mqtt_training_server.publish(data["reply-to"], json.dumps({"success": False}))
            logger.e("train", f"failed to train data '{json.dumps(nlu_data)}'", traceback.format_exc())
    mqtt_training_server.subscribe("jarvis/satellite/nlu/train")
    mqtt_training_server.on_message(_on_NLU_TRAINING)


def start_parsing_server():
    """
    Parsing server
    Listens to jarvis/satellite/nlu/parse { utterance: "... sentence ...", 
                                            reply-to: "... temporary mqtt reply channel ..." }
    Returns the parsing result
    """
    global mqtt_nlu_server
    def _on_NLU_UTTERANCE(c, ud, msg):
        global logger
        try:
            data = json.loads(msg.payload.decode())
            if "utterance" in data:
                utterance = data["utterance"]
                result = parse_nlu_model(utterance)
                if "reply-to" in data:
                    mqtt_nlu_server.publish(data["reply-to"], json.dumps({"success": True, "result": result}))
        except Exception:
            logger.e("parse", "failed to parse data, maybe model is not trained yet...")
            if "reply-to" in data:
                mqtt_nlu_server.publish(data["reply-to"], json.dumps({"success": False}))
    mqtt_nlu_server.on_message(_on_NLU_UTTERANCE)
    mqtt_nlu_server.subscribe("jarvis/satellite/nlu/parse")


def start_status_server():
    """
    Starts a status server
    Listens to jarvis/satellite/nlu/status
    Returns an object: {    trained: True|False, 
                            training: True|False,
                            avg-time: { 
                                training: int, 
                                parsing: int 
                            }, 
                            total-time: { 
                                training: int, 
                                parsing: int 
                            }, 
                            count: { 
                                training: int, 
                                parsing: int 
                            } 
                        }
    """
    global mqtt_status_server
    def _on_NLU_STATUS(c, ud, msg):
        global logger, STATISTICS
        try:
            data = json.loads(msg.payload.decode())
            if "reply-to" in data:
                mqtt_status_server.publish(data["reply-to"], json.dumps(STATISTICS))
        except Exception:
            logger.e("training", "failed to insert data into database", traceback.format_exc())
            if "reply-to" in data:
                mqtt_status_server.publish("jarvis/errors", json.dumps({"endpoint": "jarvis/satellite/nlu/status"}))
    mqtt_status_server.on_message(_on_NLU_STATUS)
    mqtt_status_server.subscribe("jarvis/satellite/nlu/status")



def get_assistant_data():
    """
    Try to retrieve the already fitted NLU data
    If fitted data could be found, return it, else None
    """
    def _get_assistant_data():
        res = Database().table("assistant").filter(lambda x: "nlu-data" in x)
        if res.found:
            return res[0]["nlu-data"]
        else:
            return None
    assistant_data = None
    while not assistant_data:
        time.sleep(QUERY_TIME)
        assistant_data = _get_assistant_data()
    return assistant_data


def save_assistant_data(data):
    assistant_table = Database().table("assistant")
    res = assistant_table.filter(lambda x: "nlu-data" in x)
    """
    `nlu-data` format:
    {
        "created-at": "<unix timestamp>",
        "modified-at": "<unix timestamp>",
        "nlu-data": ... up to 256Mb data size (MQTT spec limits) ...
    }
    """
    if res.found:
        res.update(data)
    else:
        data["created-at"] = int(time.time())
        assistant_table.insert(data)



def parse_nlu_model(utterance):
    global nlu_engine, logger, STATISTICS
    try:
        if not STATISTICS["trained"]:
            raise Exception("NLU Engine not fitted!")
        if STATISTICS["training"]:
            raise Exception("NLU Engine currently training...")
        logger.i("parsing", f"parsing '{utterance}'")
        start = time.time()
        result = nlu_engine.parse(text=utterance)
        took = time.time() - start
        logger.i("parse", f"parsed '{utterance}', result: '{json.dumps(result)}'")
        STATISTICS["total-time"]["parsing"] += took
        STATISTICS["count"]["parsing"] += 1
        STATISTICS["avg-time"]["parsing"] = STATISTICS["total-time"]["parsing"] / STATISTICS["count"]["parsing"]
        return result
    except Exception:
        logger.e("parse", "failed to parse utterance on nlu model", traceback.format_exc())
        return {"nlu": False}


def train_nlu_model(data):
    global nlu_engine, logger, STATISTICS
    STATISTICS["training"] = True
    logger.i("training", f"starting nlu model training")
    start = time.time()
    nlu_engine.fit(dataset=data, force_retrain=True)
    took = time.time() - start
    logger.i("training", f"took {took:.1f}s to train nlu model")
    STATISTICS["trained"] = nlu_engine.fitted
    STATISTICS["training"] = False
    STATISTICS["total-time"]["training"] += took
    STATISTICS["count"]["training"] += 1
    STATISTICS["avg-time"]["training"] = STATISTICS["total-time"]["training"] / STATISTICS["count"]["training"]

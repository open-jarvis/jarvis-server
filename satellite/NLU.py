#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


import time
import json
import traceback
from jarvis import Exiter, Database, Logger, API
import snips_nlu


logger = Logger("NLU")
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
    # try to get data from database
    assistant_data = get_assistant_data()
    # train nlu model
    logger.i("Data", "Successfully loaded data from database")
    train_nlu_model(assistant_data)
    # start mainloop
    Exiter.mainloop()
    logger.i("Shutdown", "Shutting down NLU Servers")
    return


def get_assistant_data():
    """
    Try to retrieve the already fitted NLU data
    If fitted data could be found, return it, else None  
    This starts an infinite loop which retries to get the data until it has been found or Jarvis stops
    """
    def _get_assistant_data():
        res = Database().table("assistant").filter(lambda x: "nlu-data" in x)
        if res.found:
            return res[0]["nlu-data"]
        return None
    assistant_data = None
    while not assistant_data and Exiter.running:
        time.sleep(QUERY_TIME)
        assistant_data = _get_assistant_data()
    return assistant_data


def save_assistant_data(data):
    """
    Save NLU data to the database  
    Use [get_assistant_data](#get_assistant_data) to retrieve the stored data  
    `nlu-data` format:
    ```python
    {
        "created-at": "<unix timestamp>",
        "modified-at": "<unix timestamp>",
        "nlu-data": ... up to 256Mb data size (MQTT spec limits) ...
    }
    ```
    """
    assistant_table = Database().table("assistant")
    res = assistant_table.filter(lambda x: "nlu-data" in x)
    if res.found:
        res.update(data)
    else:
        data["created-at"] = int(time.time())
        assistant_table.insert(data)


def parse_nlu_model(utterance):
    """
    Let the NLU engine parse the given string utterance (should be a sentence)  
    Throws an exception if the model is not fitted, currently training or another unknown error occurs.  
    Otherwise, returns the result
    """
    global nlu_engine, logger, STATISTICS
    try:
        if not STATISTICS["trained"]:
            raise Exception("NLU Engine not fitted!")
        if STATISTICS["training"]:
            raise Exception("NLU Engine currently training")
        logger.i("Parse", f"Parsing '{utterance}'")
        start = time.time()
        result = nlu_engine.parse(text=utterance)
        took = time.time() - start
        logger.i("Parse", f"Parsed '{utterance}', result: '{json.dumps(result)}'")
        STATISTICS["total-time"]["parsing"] += took
        STATISTICS["count"]["parsing"] += 1
        STATISTICS["avg-time"]["parsing"] = STATISTICS["total-time"]["parsing"] / STATISTICS["count"]["parsing"]
        return result
    except Exception as e:
        logger.e("Parse", "Failed to parse utterance on NLU model", traceback.format_exc())
        raise e


def train_nlu_model(data):
    """
    Train the NLU model with given `data`
    """
    global nlu_engine, logger, STATISTICS
    STATISTICS["training"] = True
    logger.i("Training", f"Starting NLU model training")
    try:
        start = time.time()
        nlu_engine.fit(dataset=data, force_retrain=True)
        took = time.time() - start
        logger.i("Training", f"Took {took:.1f}s to train NLU model")
        STATISTICS["total-time"]["training"] += took
        STATISTICS["count"]["training"] += 1
    except Exception:
        logger.e("Training", "Failed to train NLU engine", traceback.format_exc())
    STATISTICS["trained"] = nlu_engine.fitted
    STATISTICS["training"] = False
    STATISTICS["avg-time"]["training"] = STATISTICS["total-time"]["training"] / STATISTICS["count"]["training"]



@API.route("jarvis/nlu/train")
def train_nlu(data=None):
    """
    Train NLU  
    If it receives a valid message, train the NLU engine and save both the trained model and training data into the database
    """
    global logger
    try:
        # train the nlu instance
        nlu_data = data["data"]
        train_nlu_model(nlu_data)
        # save nlu data
        save_assistant_data({
            "modified-at": int(time.time()),
            "nlu-data": nlu_data
        })
        if "reply-to" in data:
            return True
    except Exception:
        logger.e("train", f"failed to train data '{json.dumps(nlu_data)}'", traceback.format_exc())
        return False


@API.route("jarvis/nlu/parse")
def parse_nlu(data=None):
    """
    Parse a sentence  
    The sentence will be parsed by the trained NLU.  
    If the NLU is not trained yet, throw an exception
    """
    global logger
    if "utterance" not in data:
        return {"success": False, "error": "No utterance provided!"}
    return parse_nlu_model(data["utterance"])


@API.route("jarvis/nlu/status")
def nlu_status():
    """
    Starts a status server
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
    return STATISTICS


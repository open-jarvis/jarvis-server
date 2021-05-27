"""
Copyright (c) 2021 Philipp Scheer
"""


import time
from jarvis import Database


class Client():
    """
    Client representing outside world devices and internal applications that connect through the MQTT API
    """

    REQUIREMENTS = {
        "ip": str,
        "data": dict,
        "secure": bool,
        "last-seen": int,
        "modified-at": int,
        "created-at": int
    }
    """Required fields that have to be in a client object"""

    DEFAULTS = {
        "ip": "127.0.0.1",
        "token": None,
        "data": {},
        "secure": False,
        "last-seen": None,
        "modified-at": None,
        "created-at": None
    }
    """Default values when creating a new client"""

    def __init__(self, client_object = {}) -> None:
        """Initialize a new client with an object from the database"""
        self.data = client_object
        if "created-at" not in self.data:
            self.data["created-at"] = int(time.time())
        self.check()


    def save(self):
        """Save the current client object into the database"""
        self.data["modified-at"] = int(time.time())
        self.check()
        if "id" in self.data:
            self.data["_id"] = self.data["id"]
            del self.data["id"]
        return Database().table("clients").insert(self.data)


    def check(self):
        """Check if all data entries match the client requirements specified by [Client.REQUIREMENTS](Client#REQUIREMENTS), if not throw an Exception"""
        assert all([k in self.data and isinstance(self.data[k],v) for k,v in Client.REQUIREMENTS.items()]), "Make sure all the required fields are present (and have the right data type): " + ", ".join(Device.REQUIREMENTS.keys())


    @staticmethod
    def load(id):
        """Load a client from the database given its id"""
        res = Database().table("clients").find({ "_id": { "$eq": id } })
        if res.found:
            res[0]["id"] = res[0]["_id"]
            del res[0]["_id"]
            del res[0]["_rev"]
            return Client(res[0])
        else:
            raise Exception(f"No client found with id '{id}'")

    @staticmethod
    def new(data):
        """Generate a new device with given data"""
        return Client({**Client.DEFAULTS, **data})

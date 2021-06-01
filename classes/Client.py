"""
Copyright (c) 2021 Philipp Scheer
"""


import time
from jarvis import Database


class Client():
    """
    Client representing outside world devices and internal applications that connect through the MQTT API
    """

    DEFAULTS = {
        "ip": "127.0.0.1",
        "data": {},
        "secure": True,
        "public-key": None,
        "last-seen": None,
        "created-at": None,
        "modified-at": None
    }
    """Default values when creating a new client"""

    def __init__(self, client_object = {}) -> None:
        """Initialize a new client with an object from the database"""
        self.data = client_object
        if "created-at" not in self.data or self.data["created-at"] is None:
            self.data["created-at"] = int(time.time())
            self.data["modified-at"] = int(time.time())
            self.data["last-seen"] = -1

    def save(self):
        """Save the current client object into the database"""
        self.data["modified-at"] = int(time.time())
        if "id" in self.data:
            self.data["_id"] = self._id
            self.data["_rev"] = self._rev
            del self.data["id"]
        return Database().table("clients").insert(self.data)

    def get(self, key: str, or_else: any = None):
        """Get an element from the class data object"""
        if key == "id":
            key = "_id"
        return self.data.get(key, or_else)

    def set(self, key: str, value: any):
        """Set a specific key of the class data object"""
        self.data[key] = value

    def get_data(self, key: str, or_else: any = None):
        """Get an element from the client data object"""
        if key == "id":
            key = "_id"
        return self.data["data"].get(key, or_else)

    def set_data(self, key: str, value: any):
        """Set a specific key of the client data object"""
        self.data["data"][key] = value


    @property
    def id(self):
        return self.get("_id")

    @staticmethod
    def load(id):
        """Load a client from the database given its id"""
        res = Database().table("clients").find({ "_id": { "$eq": id } })
        if res.found:
            res[0]["id"] = res[0]["_id"]
            _id = res[0]["_id"]
            _rev = res[0]["_rev"]
            del res[0]["_id"]
            del res[0]["_rev"]
            c = Client(res[0])
            c._id = _id
            c._rev = _rev
            return c
        else:
            raise Exception(f"No client found with id '{id}'")

    @staticmethod
    def new(data):
        """Generate a new device with given data"""
        assert "id" not in data and "_id" not in data, "If you generate a new device, you cannot specify an id"
        return Client({**Client.DEFAULTS, **data})

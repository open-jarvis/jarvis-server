"""
Copyright (c) 2021 Philipp Scheer
"""


from os import stat
import time
from jarvis import Database


class Device():
    """
    Device representing outside world devices that connect through the MQTT API
    """

    REQUIREMENTS = {
        "ip": str,
        "token": str, 
        "data": list,
        "last-seen": int,
        "modified-at": int,
        "created-at": int
    }
    """
    Required fields that have to be in a device object
    """

    def __init__(self, device_object = {}) -> None:
        """
        Initialize a new device with an object from the database
        """
        self.data = device_object
        if "created-at" not in self.data:
            self.data["created-at"] = int(time.time())
        self.check()


    def save(self):
        """
        Save the current device object into the database
        """
        self.data["modified-at"] = int(time.time())
        self.check()
        if "id" in self.data:
            self.data["_id"] = self.data["id"]
            del self.data["id"]
        return Database().table("devices").insert(self.data)


    def check(self):
        """
        Check if all data entries match the device requirements specified by [Device.REQUIREMENTS](Device#REQUIREMENTS), if not throw an Exception
        """
        assert all([k in self.data and isinstance(self.data[k],v) for k,v in Device.REQUIREMENTS.items()]), "Make sure all the required fields are present (and have the right data type): " + ", ".join(Device.REQUIREMENTS.keys())


    @staticmethod
    def load(id):
        """
        Load a device from the database given its id
        """
        res = Database().table("devices").find({ "_id": { "$eq": id } })
        if res.found:
            res[0]["id"] = res[0]["_id"]
            del res[0]["_id"]
            del res[0]["_rev"]
            return Device(res[0])
        else:
            raise Exception(f"No device found with id {id}")

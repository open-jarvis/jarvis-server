#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

"""
Function names follow this scheme:

```
/id/ask -> id__ask
/jarvis/api/id/answer -> id__answer
```

Rules:
```
- becomes _
/ becomes __
```

The HTTP and MQTT backend strip off the leading `/` or `/jarvis/api/`  
Functions get a data object and return a tuple
consisting of `(success: bool, data_or_err: str)`
"""

import time
import random
from jarvis import Database


TOKEN_LENGTH = 8
"""
Length of a token  
Tokens are used to identify a client when he wants to register
"""

TOKEN_EXPIRATION_SECONDS = 120
"""
Amount of seconds until an issued token expires. Currently 2min  
Tokens are being issued by generate_token and consumed by register_device
"""


def generate_token(data: dict, token: str = None) -> tuple:
    """
    Generate a token  
    Required fields:
    * `permission-level` - An integer from [Permissions.PERMISSIONS](Permissions#PERMISSIONS)
    """
    require(data, ["permission-level"])

    if token is None:
        token = ''.join(random.choice("abcdef0123456789")
                        for _ in range(TOKEN_LENGTH))

    Database().table("tokens").insert({
        "token": token,
        "permission-level": data["permission-level"],
        "requested-at": int(time.time()),
        "expires-at": int(time.time() + TOKEN_EXPIRATION_SECONDS)
    })
    return (True, token)


def register_device(data: dict) -> tuple:
    """
    Register a device  
    Required fields:  
    * `name` - Name of the device
    * `token` - Token issued by [generate_token](#generate_token)
    * `type` - Connection type, can be whatever you want but `app`, `web`, `device`, etc... are good types
    """
    require(data, ["name", "token", "type"])

    if data["token"].startswith("app:"):
        generate_token({"permission-level": 4}, data["token"])

    token = Database().table("tokens").filter(
        {"token": data["token"]})[0]

    Database().table("tokens").filter({"token": data["token"]}).delete()
    if token["expires-at"] < time.time():
        return (False, "token didn't exist or expired")

    device_object = {
        "token": data["token"],
        "requested-at": token["requested-at"],
        "registered-at": int(time.time()),
        "last-seen": int(time.time()),
        "name": data["name"],
        "permission-level": token["permission-level"],
        "connection-type": data["type"],
        "ip": data["ip"] if "ip" in data else "127.0.0.1",
        "data": {}
    }

    return (True, Database().table("devices").insert(device_object))


def unregister_device(data: dict) -> tuple:
    """
    Remove a registered device  
    Required fields:
    * `target-token` - Token of the app/device you want to remove
    """
    require(data, ["target-token"])

    Database().table("instants").filter(
        {"asked-by": data["target-token"]}).delete()
    return (True, Database().table("devices").filter({"token": data["target-token"]}).delete())


def get_devices(data: dict) -> tuple:
    """
    Get a list of devices
    """
    require(data, ["token"])

    filter = {}
    if "target-token" in data:
        filter["token"] = data["target-token"]

    return (True, list(Database().table("devices").filter(filter)))


def set_property(data: dict) -> tuple:
    """
    Set a device property
    Required fields:
    * `token` - The app/device token you want to set a property on
    * `property` - Property to set
    * `value` - Value to set  
    This function sets a key:value entry on the given app/device and saves it back to the database
    """
    require(data, ["token", "property", "value"])

    updated_object = Database().table(
        "devices").filter({"token": data["token"]})[0]
    updated_object["data"][data["property"]] = data["value"]

    return (True, Database().table("devices").filter({"token": data["token"]}).update(updated_object))


def get_property(data: dict) -> tuple:
    """
    Get a device property (must be set by [set_property](#set_property))
    Required fields:
    * `token` - Token of app/device you want to get a property of
    * `property` - Property you want to get  
    If no property is set on the given token, `None` is returned instead
    """
    require(data, ["token", "property"])

    if "target-token" in data:
        try:
            return (True, list(Database().table("devices").filter({"token": data["target-token"]})[0]["data"][data["property"]]))
        except KeyError as e:
            return (True, None)
    return (True, list(Database().table("devices").filter(lambda y: data["property"] in y["data"])))


def hello(data: dict) -> tuple:
    require(data, ["token"])

    return (True, Database().table("devices").filter({"token": data["token"]}).update({
        "last-seen": int(time.time())
    }))


def am_i_registered(data: dict) -> tuple:
    require(data, ["token"])

    return (Database().table("devices").filter({"token": data["token"]}).found, None)


def decision__ask(data: dict) -> tuple:
    require(data, ["token", "type", "title", "infos", "options"])

    id = "".join(random.choice("abcdef0123456") for _ in range(32))
    Database().table("instants").insert({
        "id": id,
        "asked-by": data["token"],
        "asked-at": int(time.time()),
        "type": data["type"],
        "title": data["title"],
        "infos": data["infos"],
        "options": data["options"],
        "answered": False,
        "answer": {}
    })
    return (True, id)


def decision__answer(data: dict) -> tuple:
    require(data, ["token", "id", "option"])

    result = Database().table("instants").filter({"id": data["id"]})[0]
    if result["answered"]:
        return (False, "instant decision already got an answer")

    answer_object = result["options"][int(data["option"])]
    if "description" in data:
        answer_object["description"] = data["description"]
    Database().table("instants").filter(
        {"id": data["id"]}).update({"answer": answer_object})

    return (True, Database().table("instants").filter({"id": data["id"]}).update({"answered": True}))


def decision__scan(data: dict) -> tuple:
    require(data, ["token"])

    filter_object = {}
    if "target-token" in data:
        filter_object["token"] = data["target-token"]
    if "type" in data:
        filter_object["type"] = data["type"]

    return (True, list(Database().table("instants").filter(filter_object)))


def decision__delete(data: dict) -> tuple:
    require(data, ["token", "id"])

    return (True, Database().table("instants").filter({"id": data["id"]}).delete())


def get_permission_level(data: dict) -> tuple:
    require(data, ["token"])

    return (True, Database().table("devices").filter({"token": data["token"]})[0]["permission-level"])


# helper functions
def require(existing: dict, required: list) -> None:
    assert all(x in existing for x in required)

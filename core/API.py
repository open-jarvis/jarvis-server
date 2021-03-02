#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

# Functions follow this scheme:
#
# /id/ask
# |--> id__ask
#
# /jarvis/api/id/answer
# |--> id__answer
#
# So, - will become _  and
#     / will become __
#
# The backend will already strip off the leading / and
# on mqtt the leading /jarvis/api/
#
# Functions get a data object and return a tuple
# consisting of (success: bool, data_or_err: str)

from jarvis import Database
import time
import random

TOKEN_EXPIRATION_SECONDS = 120
TOKEN_LENGTH = 8


def generate_token(data: dict, token: str = None) -> tuple:
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
    require(data, ["target-token"])

    Database().table("instants").filter(
        {"asked-by": data["target-token"]}).delete()
    return (True, Database().table("devices").filter({"token": data["target-token"]}).delete())


def get_devices(data: dict) -> tuple:
    require(data, ["token"])

    filter = {}
    if "target-token" in data:
        filter["token"] = data["target-token"]

    return (True, list(Database().table("devices").filter(filter)))


def set_property(data: dict) -> tuple:
    require(data, ["token", "property", "value"])

    updated_object = Database().table(
        "devices").filter({"token": data["token"]})[0]
    updated_object["data"][data["property"]] = data["value"]

    return (True, Database().table("devices").filter({"token": data["token"]}).update(updated_object))


def get_property(data: dict) -> tuple:
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

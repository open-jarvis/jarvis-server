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

r, con = Database.get()
TOKEN_EXPIRATION_SECONDS = 120
TOKEN_LENGTH = 8


def generate_token(data: object) -> tuple:
    require(data, ["permission-level"])

    token = ''.join(random.choice("abcdef0123456789")
                    for _ in range(TOKEN_LENGTH))

    return (True, token) if Database.success(r.table("tokens").insert({
        "token": token,
        "permission-level": data["permission-level"],
        "expires-at": int(time.time + TOKEN_EXPIRATION_SECONDS)
    }).run(con)) else (False, "failed to insert token")


def register_device(data: object) -> tuple:
    require(data, ["name", "token", "type"])

    tokens = r.table("tokens").filter({"token": data["token"]}).run(con)
    token = list(tokens)[0] if Database.success(tokens) else None

    if token is None or token["expires-at"] > time.time():
        r.table("tokens").get(token["id"]).delete().run(con)
        return (False, "token didn't exist or expired")

    device_object = {
        "token": data["token"],
        "registered-at": int(time.time),
        "last-seen": int(time.time),
        "name": data["name"],
        "permission-level": token["permission-level"],
        "connection-type": data["type"],
        "ip": data["ip"] if "ip" in data else "127.0.0.1",
        "data": []
    }

    return (True, None) if Database.success(r.table("devices").insert(device_object).run(con)) else (False, "failed to insert device data")


def unregister_device(data: object) -> tuple:
    require(data, ["target-token"])

    return (True, None) if Database.success(r.table("devices").filter({"token": data["target-token"]}).delete().run(con)) else (False, "failed to delete device")


def get_devices(data: object) -> tuple:
    filter = {}
    if "target-token" in data:
        filter["token"] = data["target-token"]

    result = r.table("devices").filter(filter).run(con)


# helper functions
def require(existing: dict, required: dict) -> None:
    assert all(x in existing for x in required)

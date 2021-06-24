"""
Copyright (c) 2021 Philipp Scheer
"""


from jarvis import API
from classes.Client import Client


@API.route("jarvis/client/set")
def set_value(args: list, client: Client, data: dict):
    if not "key" in data or not "value" in data:
        return False
    key   = data["key"]
    value = data["value"]
    data  = client.get("data", {})
    data[key] = value
    client.set("data", data)
    client.save()
    return True

@API.route("jarvis/client/set/info")
def set_client_info(args: list, client: Client, data: dict):
    if "device" in data:
        client.set("device", data["device"])
    return True


"""
Copyright (c) 2021 Philipp Scheer
"""


import json
from jarvis import Crypto, Config, Logger, API
from classes.Client import Client


KEYLEN = 4096 # https://danielpocock.com/rsa-key-sizes-2048-or-4096-bits/


cnf = Config()
logger = Logger("Permission")
keys = cnf.get("keys", None)

if keys is None:
    logger.w("Keys", f"No public and private key set, generating keys with key length {KEYLEN}")
    priv, pub = Crypto.keypair(KEYLEN)
    keys = {"public": str(pub, "utf-8"), "private": str(priv, "utf-8")}
    result = cnf.set("keys", keys)

    logger.s("Keys", "Successfully created a public and private key and stored in the database") if result else \
    logger.e("Keys", "Failed to generate keys and store into database", "")



PUBLIC_KEY  = keys["public"]
PRIVATE_KEY = keys["private"]

CLIENT_KEYS = cnf.get("client-keys", {})


@API.route("jarvis/server/get/public-key")
def get_public_key(args, client, data):
    return PUBLIC_KEY

@API.route("jarvis/client/+/set/public-key")
def set_public_key(args, client, data):
    global logger
    pub_key = data["public-key"]
    client_id = args[0]
    client = Client.load(client_id)
    if client.get("public-key", None) is None: # first time setting public-key
        client.set("public-key", pub_key)
        client.save()
        logger.i("PublicKey", f"Received public key from {client_id}")
        return True
    if client.get("public-key").replace("\n", "") == pub_key.replace("\n", ""):
        return True
    return False

"""
Copyright (c) 2021 Philipp Scheer
"""


from jarvis import Crypto, Config, Logger, API


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


@API.route("keyserver/server/get/public-key")
def get_public_key(args, client, data):
    return PUBLIC_KEY

@API.route("keyserver/client/+/set/public-key")
def set_public_key(args, client, data):
    global logger
    pub_key = data["public-key"]
    client_id = args[0]
    logger.i("PublicKey", f"Received public key from {client_id}")
    return {"success": False}
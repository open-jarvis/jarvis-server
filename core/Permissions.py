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
    if result:
        logger.s("Keys", "Successfully created a public and private key and stored in the database")
    else:
        logger.e("Keys", "Failed to generate keys and store into database", "")


PUBLIC_KEY = keys["public"]
PRIVATE_KEY = keys["private"]

CLIENT_KEYS = cnf.get("client-keys", {})


@API.route("jarvis/server/get/public-key")
def get_public_key(args, d):
    return PUBLIC_KEY

@API.route("jarvis/client/+/set/public-key")
def set_public_key(args, d):
    pub_key = d["public-key"]
    client_id = args[0]
    print(f"setting public key of {client_id} to {pub_key}")
    return {"success": False}
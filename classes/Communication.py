"""
Copyright (c) 2021 Philipp Scheer
"""


import json
import traceback
from jarvis import MQTT, Logger
from jarvis.Config import Config
from .Device import Device
from .Crypto import Crypto
from .MessageProtocol import MessageProtocol
from .API import API

logger = Logger("Communication")
cnf = Config()


keys = cnf.get("keys", None)

if keys is None:
    logger.w("Keys", "Private and Public RSA keys not set, generating keys")
    keys = {}
    keys["private"], keys["public"] = Crypto.keypair(2048)
    cnf.set("keys", keys)
    pass


PRIVATE_KEY = keys["private"]
PUBLIC_KEY = keys["public"]


class Communication:
    """A client-server communication wrapper.  
    There are two communication (MQTT) channels:  
    - `jarvis/client/<id>/#` handles key and information exchange  
        The client device must listen to this channel and eg. provide it's public key on request  
        Possible messages:
        - GET
            - public-key
                * The server sends `jarvis/client/<id>/get/public-key` -> `{"format": "PEM", "reply-to": ... one time channel ... }`  
                * The client should respond: `<one time channel>` -> `{"public-key": false|"... PEM representation of RSA public key ..."}`  
                If the `public-key` is `false`, the client device will be marked as `insecure` and traffic will be unencrypted.  
                The server might ask the client for a public key periodically. As long as the client does not send a valid `public-key` it will stay `insecure` 
                TODO: add client implementation
    - `jarvis/#` handles any other traffic (eg. getting NLU results, etc...)
    """

    KEY_START_SEQ = "-----BEGIN RSA PUBLIC KEY-----"
    """The starting sequence for client public keys"""

    def __init__(self, id) -> None:
        """Create a new Communication session between the Jarvis server and client device"""
        self.id = id
        self.device = Device.load(id) # throws an exception if no device is found for this id
        self.secure = self.device["secure"]
        self.rpub = None
        self.refresh_aes()
        self.proto = MessageProtocol(PRIVATE_KEY, PUBLIC_KEY, self.rpub, self.key, self.iv) # TODO handle self.rpub = None!

    def refresh_aes(self):
        """Get a new AES key and initialization vector.  
        Timing for generating keys and initialization vectors:  
        ```
        | Amount of key - iv pairs  | Took time         |
        |---------------------------|-------------------|
        |                     1,000 | 0.0117s - 0.0123s |
        |                    10,000 | 0.1173s - 0.1247s |
        |                   100,000 | 1.1763s - 1.1811s |
        ```
        You can see a linear relationship between the number of keys generated and the time required
        """
        self.key, self.iv = Crypto.symmetric()

    def get_public_key(self):
        """Try to retrieve the client public key"""
        try:
            result = json.loads(MQTT.onetime(f"jarvis/client/{self.id}/get/public-key", {"format": "PEM"}, timeout=15))
            self.device["secure"] = False
            assert "public-key" in result, "Public key not in result"
            assert result["public-key"].startswith(Communication.KEY_START_SEQ), f"Public key does not start with sequence '{Communication.KEY_START_SEQ}', check format (DER vs. PEM)"
            self.device["data"]["public-key"] = result["public-key"]
            self.device["secure"] = True
            logger.s("PublicKey", f"Received public-key from {self.id}")
        except Exception:
            logger.e("PublicKey", f"Couldn't retrieve public key of client {self.id}", traceback.format_exc)
            # we do not set secure to false, because the client might be offline and can get back online in a few seconds

    def send(self, topic: str, message: object, await_reponse=True):
        """Send a message to the client  
        If `await` is `True`, create a one-time channel and wait for a reply, otherwise send out the message and don't wait for a response"""
        # TODO: do encryption
        MessageProtocol
        return MQTT.onetime(topic, message, 15 if await_reponse else 0, True)



@API.route("jarvis/server/get/public-key")
def provide_public_key():
    global PUBLIC_KEY
    if PUBLIC_KEY.startswith(Communication.KEY_START_SEQ):
        return {"success": True, "secure": True, "public-key": PUBLIC_KEY}
    return {"success": False, "secure": False}

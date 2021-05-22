"""
Copyright (c) 2021 Philipp Scheer
"""


import sys
import json
import base64
from Crypto import Crypto


class Communication:
    def __init__(self, local_private_key: str, local_public_key: str, remote_public_key: str, aes_key: bytes, aes_iv: bytes) -> None:
        """Wrapper class for secure communication"""
        self.priv = local_private_key
        self.pub = local_public_key
        self.rpub = remote_public_key
        self.key = aes_key
        self.iv = aes_iv
    
    def encrypt(self, message: object, is_json: bool = True) -> dict:
        """Encrypt a message using a symmetric key, sign the message and encrypt the symmetric key using RSA
        Returns:
        ```python
        >>> encrypt('{"this": "is", "a": "test"}', is_json=True)
        {
            "m": ... encrypted message ...,
            "s": ... message signature ...,
            "k": ... encrypted symmetric key ...
        }
        ```"""
        if is_json:
            message = json.dumps(message)
        message = _str_to_bytes(message)
        message_signature = Crypto.sign(message, self.priv)
        encrypted_message = Crypto.aes_encrypt(message, self.key, self.iv)
        symkey = json.dumps({ "key": b64e(self.key), "iv": b64e(self.iv) })
        encrypted_symmetric_key = Crypto.encrypt(_str_to_bytes(symkey), self.pub)
        return json.dumps({
            "m": b64e(encrypted_message),
            "s": b64e(message_signature),
            "k": b64e(encrypted_symmetric_key)
        })
    
    def decrypt(self, data: str, ignore_invalid_signature: bool = False) -> object:
        """Takes an encrypted message (must be encrypted by an official Jarvis `Communication.encrypt()` message)
        """
        data = json.loads(data)
        m = b64d(data["m"])
        s = b64d(data["s"])
        k = b64d(data["k"])
        symkey = json.loads(_bytes_to_str(Crypto.decrypt(k, _bytes_to_str(self.priv))))
        key = b64d(symkey["key"])
        iv = b64d(symkey["iv"])
        decrypted_message = Crypto.aes_decrypt(m, key, iv)
        sign_match = Crypto.verify(decrypted_message, s, self.rpub)
        if not sign_match:
            if not ignore_invalid_signature:
                raise Exception("Invalid Signature")
        return _bytes_to_str(decrypted_message)


def b64e(bytes):
    return _bytes_to_str(base64.b64encode(bytes))

def b64d(bytes):
    return base64.b64decode(bytes)

def _bytes_to_str(byte_like_obj: bytes):
    return byte_like_obj.decode("utf-8")


def _str_to_bytes(string: str):
    return str.encode(string, "utf-8")


if "--test" in sys.argv:
    lpriv, lpub = Crypto.keypair(1024)
    rpriv, rpub = Crypto.keypair(1024)
    lkey, liv = Crypto.symmetric()
    rkey, riv = Crypto.symmetric()
    lcom = Communication(lpriv, lpub, rpub, lkey, liv)
    rcom = Communication(rpriv, rpub, lpub, rkey, riv)
    enc = lcom.encrypt("jeremiasz ist dumm", is_json=False)
    print(enc)
    dec = rcom.decrypt(enc, ignore_invalid_signature=False)
    print(dec)

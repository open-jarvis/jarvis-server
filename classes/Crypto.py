"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import sys
import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Crypto:
    """An RSA helper class to secure the connection between MQTT clients"""
    
    @staticmethod
    def keypair(keylen: int = 4096) -> tuple:
        """Generate a private and public key  
        Returns a tuple:
        ```python
        private_key, public_key = Crypto.keypair(8192)
        ```
        This method uses the `cryptography` library to generate large keys faster (2s vs. 9s of the `rsa` package)"""
        key = crypto_rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=keylen
        )
        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.TraditionalOpenSSL,
            crypto_serialization.NoEncryption())
        public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PublicFormat.PKCS1
        )
        return ( private_key, public_key) 
    
    @staticmethod
    def sign(message: bytes, private_key: str) -> bytes:
        """Take a string `message` and a PEM `private_key` and return the signed message."""
        priv = rsa.PrivateKey.load_pkcs1(private_key, format="PEM")
        return rsa.sign(message, priv, hash_method="SHA-512") # 'MD5’, 'SHA-1’, 'SHA-224’, SHA-256’, 'SHA-384’ or 'SHA-512'

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: str):
        """Take the public key and see if it matches the signature"""
        pub = rsa.PublicKey.load_pkcs1(public_key, format="PEM")
        return True if rsa.verify(message, signature, pub) else False

    @staticmethod
    def encrypt(message: bytes, public_key: str):
        """Take a string `message` and a PEM `public_key` and return an encrypted message"""
        pub = rsa.PublicKey.load_pkcs1(public_key, format="PEM")
        return rsa.encrypt(message, pub)
    
    @staticmethod
    def decrypt(encrypted: bytes, private_key: str):
        """Decrypt an encrypted message using the private key"""
        priv = rsa.PrivateKey.load_pkcs1(private_key, format="PEM")
        return rsa.decrypt(encrypted, priv)

    @staticmethod
    def symmetric(key_size: int = 256, initialization_vector_size: int = 128):
        """Generate a random key and initialization vector for symmetric encryption  
        `key_size` has to be `128`, `192` or `256`  
        `initializaion_vector_size` has to be `128`  
        Usage:
        ```python3
        key, iv = Crypto.symmetric(256)
        ```"""
        key_size //= 8
        initialization_vector_size //= 8
        return (os.urandom(key_size), os.urandom(initialization_vector_size))

    @staticmethod
    def aes_encrypt(message: bytes, key: bytes, iv: bytes):
        """Encrypt a `message` with AES using a given `key` and initialization vector `iv`"""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        while not len(message) % len(key) == 0:
            message += b'\x00'
        encryptor = cipher.encryptor()
        return encryptor.update(message) + encryptor.finalize()
    
    @staticmethod
    def aes_decrypt(encrypted: bytes, key: bytes, iv: bytes) -> bytes:
        """Decrypt an `encrypted` message with AES using a given `key` and initialization vector `iv`"""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        return (decryptor.update(encrypted) + decryptor.finalize()).rstrip(b'\x00')


# if "--test" in sys.argv:
#     key, iv = Crypto.symmetric(256)
#     msg = b",!" * 15
#     enc = Crypto.aes_encrypt(msg, key, iv)
#     dec = Crypto.aes_decrypt(enc, key, iv)
#     print(f"Encrypt message '{msg}' (len {len(msg)}) using AES: ", enc)
#     print(f"Decrypt message '{enc}' using AES: ", dec)
#     print()
#     priv, pub = Crypto.keypair()
#     print("Private Key: ", priv)
#     print("Public Key: ", pub)

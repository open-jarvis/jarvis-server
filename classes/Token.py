"""
Copyright (c) 2021 Philipp Scheer
"""


import time
import random
from jarvis.Database import Database


TOKEN_LENGTH = 8
"""
Length of a token  
Tokens are used to identify a client when he wants to register
"""

TOKEN_EXPIRATION_SECONDS = 120
"""
Amount of seconds until an issued token expires. Currently 2min
"""


class Token():
    """
    A helper class to issue tokens to registering devices
    """

    REQUIREMENTS = {
        "token": str,
        "permission": int, 
        "requested-at": list,
        "expires-at": int,
        "redeemed": bool
    }
    """
    Required fields that have to be in a token object
    """

    def __init__(self, token, permission) -> None:
        """
        Initialize a token with no rights
        """
        self.data = {
            "token": token,
            "permission": permission,
            "requested-at": int(time.time()),
            "expires-at": int(time.time() + TOKEN_EXPIRATION_SECONDS),
            "redeemed": False
        }
        self.check()

    def save(self):
        """
        Save the current token to the database
        """
        self.check()
        Database().table("tokens").insert(self.data)
        return self

    def update(self):
        """
        Load the most recent token information into this class
        """
        info = Database().table("tokens").find({ "token": { "$eq": self.token } })
        if info.found:
            info = info[0]
            self.data = info
            self.check()
        else:
            raise Exception("token could not be found")
        return self

    def is_expired(self):
        """
        Check if the token expired
        """
        self.update()
        return self.data["expires"] < time.time()
            
    def is_redeemed(self):
        """
        Check if the token already got redeemed
        """
        self.update()
        return self.data["redeemed"]

    def is_app(self):
        """
        Check if the registered token belongs to an app
        """
        self.update()
        return self.data["token"].startswith("app:")
    
    def check(self):
        """
        Check if all data entries match the token requirements specified by [Token.REQUIREMENTS](Token#REQUIREMENTS), if not throw an Exception
        """
        assert all([k in self.data and isinstance(self.data[k],v) for k,v in Token.REQUIREMENTS.items()]), \
                "Make sure all the required fields are present (and have the right data type): " + ", ".join(Token.REQUIREMENTS.keys())

    def __getattr__(self, attr):
        """
        Get an attribute from the data dict
        """
        return self.data[attr]

    @staticmethod
    def load(token):
        """
        Load a token from the database
        """
        token = Token(token, 0)
        token.update()
        return token

    @staticmethod
    def new(permission):
        """
        Create a new random token with given permissions
        """
        token = ''.join(random.choice("abcdef0123456789") for _ in range(TOKEN_LENGTH))
        token = Token(token, permission)
        return token

    @staticmethod
    def static(token, permission):
        """
        Create a new token with a given key and given permissions
        """
        token = Token(token, permission)
        return token
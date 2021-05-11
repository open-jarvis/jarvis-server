#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

"""
Function names follow this scheme:

```
/id/ask -> id__ask
/jarvis/api/id/answer -> id__answer
```

Rules:
```
- becomes _
/ becomes __
```

The HTTP and MQTT backend strip off the leading `/` or `/jarvis/api/`  
Functions get a data object and return a tuple
consisting of `(success: bool, data_or_err: str)`
"""


from classes.Token import Token
import time
import random
from jarvis import Database
from classes import Device


class API():
    """
    API helper class to register MQTT routes
    """

    routes = {}
    """
    A dictionary containing all registered routes
    """

    @staticmethod
    def _get(route):
        """
        Get a route from array, else return the default route
        """
        if route in API.routes:
            return API.routes[route]
        return API.default_route
    
    @staticmethod
    def execute(route, *args, **kwargs):
        """
        Execute a route with given arguments
        """
        try:
            return (True, API._get(route, *args, **kwargs)())
        except Exception as e:
            return (False, str(e))

    @staticmethod
    def default_route():
        """
        This is the default route and gets handled if no route was registered when trying to execute it
        """
        raise Exception("endpoint not found")
    
    @staticmethod
    def route(path):
        """
        Decorator to register a route
        """
        def decor(func):
            def wrap(*args, **kwargs):
                res = func(*args, **kwargs)
                return res
            API.routes[path] = wrap
            return wrap
        return decor



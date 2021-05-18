"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import sys
import json
import traceback
from collections import OrderedDict


class API():
    """
    API helper class to register MQTT routes

    Example usage:  
    ```python
    @API.route("jarvis/ping")
    def serve_ping(*args, **kwargs):
        return "pong"
    
    @API.route("jarvis/status")
    def serve_status(use_json=True):
        return { "status": True } if use_json else True
    
    @API.route("jarvis/exception")
    def serve_test_exception():
        raise Exception("This is a test") # will get caught by API and converted to 'This is a test'
    ```

    If you want to execute an API endpoint, use:
    ```python
    result = API.execute("jarvis/status", use_json=True)
    # { "status": True }
    ```
    """

    DOCUMENTATION = {}
    """
    A dictionary containing all the function documentations  
    Format: { <endpoint>: <documentation> }
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
        Returns a tuple with `(True|False, string result)`  
        If the function does not return a string, it will be converted to a string using `json.dumps()`
        """
        try:
            res = API._get(route, *args, **kwargs)()
            if isinstance(res, bool):
                res = { "success": res }
            if not isinstance(res, str):
                res = json.dumps(res)
            return (True, res)
        except Exception as e:
            return (False, str(e))

    @staticmethod
    def default_route():
        """
        This is the default route and gets handled if no function was found for route
        """
        raise Exception("endpoint not found")

    @staticmethod
    def route(path):
        """
        Decorator to register a route  
        [See usage](#API)
        """
        def decor(func):
            API.DOCUMENTATION[path] = func.__doc__
            API._save_docs(f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/APIDOC.md")
            def wrap(*args, **kwargs):
                res = func(*args, **kwargs)
                return res
            API.routes[path] = wrap
            return wrap
        return decor

    @staticmethod
    def _save_docs(to_file):
        try:
            with open(to_file, "w") as f:
                f.write("# API Documentation\n\n")
                doc = OrderedDict(sorted(API.DOCUMENTATION.items()))
                for e, d in doc.items():
                    f.write(f"## {e}  \n\n{d}\n\n")
        except Exception:
            print(traceback.format_exc())

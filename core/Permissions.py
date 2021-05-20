"""
Copyright (c) 2021 Philipp Scheer
"""


import os
from jarvis import Config, Logger


PERMISSIONS = {
    "device": "jarvis/device/get/#"
}


cnf = Config()
logger = Logger("Permission")
keys = cnf.get("keys", None)

if keys is None:
    

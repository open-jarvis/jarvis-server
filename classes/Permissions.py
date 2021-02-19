#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import os
from jarvis import Config

PERMISSIONS = {
    "TOKEN_MASTER": ["generate_token", "unregister_device", "get_devices"],
    5: ["register_device", "am_i_registered", "hello", "id__scan", "id__answer", "get_devices", "get_property", "id__ask", "id__delete", "set_property", "generate_token", "unregister_device"	],
    4: ["register_device", "am_i_registered", "hello", "id__scan", "id__answer", "get_devices", "get_property", "id__ask", "id__delete", "set_property"											],
    3: ["register_device", "am_i_registered", "hello", "id__scan", 												"id__ask", "id__delete", "set_property"											],
    2: ["register_device", "am_i_registered", "hello", "id__scan", "id__answer", "get_devices", "get_property"																					],
    1: ["register_device", "am_i_registered", "hello"																																			],
    0: []
}
MASTER_TOKEN = "MASTER"


cnf = Config()
PRE_SHARED_KEY = cnf.get("pre-shared-key", None)
TOKEN_KEY = cnf.get("token-key", None)
if PRE_SHARED_KEY is None or TOKEN_KEY is None:
    raise Exception("jarvis api keys not configured")


DIRECTORY = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/..")

SECURITY_VIOLATION = {"success": False, "error": "permission denied"}
FAILED_MESSAGE = {"success": False, "error": "unknown error, check logs"}

def get_allowed_functions(permission_level: int = 0):
    """
    Return a list of allowed functions for a given permission level
    """
    if permission_level in PERMISSIONS:
        return PERMISSIONS[permission_level]
    else:
        return []

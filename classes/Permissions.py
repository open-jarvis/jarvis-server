#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import os

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


DIRECTORY = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/..")

SECURITY_VIOLATION = {"success": False, "error": "permission denied"}


def get_allowed_functions(permission_level):
    if permission_level in PERMISSIONS:
        return PERMISSIONS[permission_level]
    else:
        return []


def get_mastertoken():
    return MASTER_TOKEN

#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import json
import time
from jarvis import Logger, Exiter
from classes.App import App

APPS = []
LOGGER = None


def load_apps(root_dir: str) -> None:
    global APPS, LOGGER
    LOGGER = Logger("apploader")
    LOGGER.console_on()

    LOGGER.i("apps", f"reading config file at {root_dir}/storage/jarvis.conf")
    Exiter(on_exit, [LOGGER])

    with open(f"{root_dir}/storage/jarvis.conf", "r") as f:
        jarvis_conf = json.loads(f.read())
        loaded_apps = jarvis_conf["loaded_apps"]

    for app in loaded_apps:
        app_name = app["name"]
        app_dir = f"{jarvis_conf['app_dir']}/{app_name}"
        app = App(app_dir, LOGGER)
        app_ok = app.is_ok()

        LOGGER.i(f"app:{app_name}", f"ok: {str(app_ok)}")

        if app_ok[0]:
            app.start()
            APPS.append(app)
        else:
            LOGGER.e(f"app:{app_name}", f"error during start: {app_ok[1]}")


def on_exit(lgr: Logger) -> None:
    lgr.i("shutdown", "stopping all apps")
    for app in APPS:
        i = 0
        while app.is_running():
            if i >= 3:
                lgr.i(
                    "shutdown", f"killed {app} because it didn't respond to SIGTERM signal")
                app.kill()
                break
            app.stop()
            i += 1
            time.sleep(2)

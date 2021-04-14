"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import json
import time
import shutil
import requests
import traceback
from packaging import version
from jarvis import Logger, Config, MQTT, Exiter
from jarvis import update as jarvis_update


# initialize jarvis classes
logger = Logger("updater")
cnf = Config()


# initially set data server
if cnf.get("update-server", None) is None:
    cnf.set("update-server", "jarvisdata.philippscheer.com")

# define constants
DATASERVER = cnf.get("update-server", "jarvisdata.philippscheer.com")
TO_CHECK = [
    # ACTION:       if below                        >   this                            ;  then download this                               ; and install here      ; automatically install?
    [  f"http://{DATASERVER}/web/version"           ,   "/jarvis/web/version"           ,  f"http://{DATASERVER}/web-latest.tar.gz"         , "/jarvis/web"         , False ],
    [  f"http://{DATASERVER}/server/version"        ,   "/jarvis/server/version"        ,  f"http://{DATASERVER}/server-latest.tar.gz"      , "/jarvis/server"      , False ],
]


DOWNLOADS_FOLDER = "/jarvis/downloads"
POLL_INTERVAL = 60 * 60 * 1 # CHECK EVERY HOUR FOR UPDATE
CURRENT_ACTION = "idle"


# helper functions
def install_downloaded_archive(downloaded_archive, local_installation_path):
    shutil.rmtree(local_installation_path, ignore_errors=True)
    shutil.unpack_archive(downloaded_archive, local_installation_path)
    os.unlink(downloaded_archive)


def store(url, path):
    r = requests.get(url)
    size = len(r.content)
    with open(path, "wb") as f:
        f.write(r.content)
    return size


def check_versions(version_url, version_local):
    remote_version = requests.get(version_url).text.strip()
    with open(version_local, "r") as f:
        local_version = f.read().strip()
    return (version.parse(remote_version), version.parse(local_version))


def download_pending():
    for el in TO_CHECK:
        remote, local = check_versions(el[0], el[1])
        if remote > local:
            return True
    return False


def installation_pending():
    for fname in os.listdir(DOWNLOADS_FOLDER):
        if fname.startswith("server-latest") or fname.startswith("web-latest"):
            return True
    return False



"""
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 
#@        MQTT SPECIFICATIONS        @
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Listening to MQTT messages:
jarvis/update/poll          !!! NEED REPLY TO  !!!
    -> { success: true|false  , ?error = "No internet connection! "}
jarvis/update/download      !!! NEED REPLY TO !!!
    -> { success : true|false , ?error = "No update available!" }
jarvis/update/install       !!! NEED REPLY TO !!!
    -> { success: true|false ,  ?error = "No update available!" }
jarvis/update/status        !!! NEED REPLY TO !!!
    -> { current-action : idle|downloading|installing, available: download|installation|null, version: { current: 0.0.1, remote: 0.0.2 } }
"""
def _on_REQUEST(client: object, userdata: object, message: object):
    try:
        global CURRENT_ACTION, TO_CHECK, logger, mqtt
        topic = message.topic
        data = json.loads(message.payload.decode())
        action = topic.split("/")[-1]

        result = { "success": True }

        if action == "poll":
            logger.i("poll", "received mqtt poll signal")
            poll()
        if action == "download":
            logger.i("download", "received mqtt download signal")
            if not download_pending():
                result["success"] = False
                result["error"] = "No update available!"
            else:
                poll(download=True)
        if action == "install":
            logger.i("install", "received mqtt install signal")
            if not installation_pending():
                result["success"] = False
                result["error"] = "No update available!"
            else:
                poll(install=True)
        if action == "status":
            logger.i("install", "received mqtt status signal")
            del result["success"]
            result["current-action"] = CURRENT_ACTION
            result["available"] = { "download": None, "install": None }
            remote, local = check_versions(TO_CHECK[0][0], TO_CHECK[0][1])
            if download_pending():
                result["available"]["download"] = { "remote": str(remote), "local": str(local) }
            if installation_pending():
                result["available"]["install"] = { "remote": str(remote), "local": str(local) }     # TODO: remote version always stays the same

        if "reply-to" in data:
            mqtt.publish(data["reply-to"], json.dumps(result))
    except Exception:
        logger.e("on-mqtt", "an error occured while handling an mqtt endpoint, see traceback", traceback.format_exc())


mqtt = MQTT(client_id="updater")
mqtt.on_message(_on_REQUEST)
mqtt.subscribe("jarvis/update/#")


def poll(download=False, install=False):
    global CURRENT_ACTION, DATASERVER, logger, mqtt
    logger.i("polling", f"polling for updates from server {DATASERVER}")
    at_least_one_update = False
    do_restart = False
    for el in TO_CHECK:
        if el[4]:
            download = True
            install = True
        latest_file_name = el[2].split("/")[-1]
        downloaded_file_path = DOWNLOADS_FOLDER + "/" + latest_file_name
        local_installation_path = el[3]

        remote, local = check_versions(el[0], el[1])
        if remote > local:
            at_least_one_update = True
            logger.i("available", f"update available from v{local} to v{remote}")

            if download or cnf.get("auto-download-updates", False):
                CURRENT_ACTION = "downloading"
                size = store(el[2], downloaded_file_path)
                logger.i("download", f"downloaded update {remote}, size: {size}")

            if install or cnf.get("auto-install-updates", False):
                do_restart = True
                CURRENT_ACTION = "installing"
                install_downloaded_archive(downloaded_file_path, local_installation_path)
                logger.i("install", f"installed update v{remote}")

            CURRENT_ACTION = "idle"
    if do_restart:
        mqtt.publish("jarvis/backend/restart", "{}")
    if not at_least_one_update:
        logger.i("polling", f"no update found on server {DATASERVER}")


def update_checker():
    global mqtt, logger, POLL_INTERVAL
    try:
        while Exiter.running:
            poll()
            for i in range(POLL_INTERVAL):
                if not Exiter.running:
                    break
                time.sleep(0.95)
        logger.i("shutdown", "shutting down autoupdate server")
    except Exception as e:
        logger.e("mainloop", f"an exception occured, next try in {POLL_INTERVAL // 1.5}s, see traceback", traceback.format_exc())
        for i in range(int((POLL_INTERVAL // 1.5) * 2)):
            if not Exiter.running:
                return
            time.sleep(0.49)
        update_checker()

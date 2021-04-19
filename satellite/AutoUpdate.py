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


# initialize jarvis classes
logger = Logger("updater")
cnf = Config()


# define constants
VERSION_NAMES = {
    "0.0.0": "Alpine Aplha",
    "0.0.1": "Alpine Beta",
    "0.0.2": "Alpine"
}
UPDATE_REPOS = [ "server", "web" ]
CURRENT_ACTION = "idle"
DOWNLOADS_FOLDER = "/jarvis/downloads"
POLL_INTERVAL = 60 * 60 * 1 # CHECK EVERY HOUR FOR UPDATE
SERVER = cnf.get("update-server", "jarvisdata.philippscheer.com")
ROOT_DIR = cnf.get("directories", {"root": "/jarvis"})["root"]


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


def update_size():
    global TO_CHECK
    total_size = 0
    for el in TO_CHECK:
        total_size += int(requests.head(el[2]).headers["content-length"])
    return total_size


def check_versions(version_url, version_local):
    remote_version = requests.get(version_url).text.strip()
    with open(version_local, "r") as f:
        local_version = f.read().strip()
    return (version.parse(remote_version), version.parse(local_version))


def get_update_notes(remote_url, local_url):
    rmt = requests.get(remote_url).text.strip()
    with open(local_url, "r") as f:
        lcl = f.read().strip()
    return (rmt, lcl)


def download_pending():
    global TO_CHECK
    for el in TO_CHECK:
        remote, local = check_versions(el[0], el[1])
        if remote > local:
            return True
    return False


def installation_pending():
    global DOWNLOADS_FOLDER
    for fname in os.listdir(DOWNLOADS_FOLDER):
        if fname.startswith("server-latest") or fname.startswith("web-latest"):
            return True
    return False


def _on_REQUEST(client: object, userdata: object, message: object):
    try:
        global CURRENT_ACTION, TO_CHECK, logger, mqtt
        topic = message.topic
        data = json.loads(message.payload.decode())
        action = topic.split("/")[-1]

        result = { "success": True }

        """jarvis/update/poll|download|install|status"""

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
            result["remote"] = str(remote)
            result["local"] = str(local)

        if "reply-to" in data:
            mqtt.publish(data["reply-to"], json.dumps(result))
    except Exception:
        logger.e("on-mqtt", "an error occured while handling an mqtt endpoint, see traceback", traceback.format_exc())


mqtt = MQTT(client_id="updater")
mqtt.on_message(_on_REQUEST)
mqtt.subscribe("jarvis/update/#")


def poll(download=False, install=False):
    global CURRENT_ACTION, UPDATE_REPOS, SERVER, VERSION_NAMES, logger, mqtt, cnf
    logger.i("polling", f"polling for updates from server {SERVER}")
    at_least_one_update = False
    do_restart = False
    for repo in UPDATE_REPOS:
        latest_file_path                = f"{repo}-latest.tar.gz"
        remote_server_latest_file_path  = f"https://{SERVER}/{latest_file_path}"
        
        remote_version_file             = f"https://{SERVER}/{repo}/version"
        local_version_file              = f"{ROOT_DIR}/{repo}/version"
        
        remote_update_notes             = f"https://{SERVER}/{repo}/UPDATE.md"
        local_update_notes              = f"{ROOT_DIR}/{repo}/UPDATE.md"
        
        download_file_path              = f"{DOWNLOADS_FOLDER}/{latest_file_path}"
        local_installation_path         = f"{ROOT_DIR}/{repo}"

        remote, local = check_versions(remote_version_file, local_version_file)

        if repo == "server":    # we use the server repo as reference
            update_remote, update_local = get_update_notes(remote_update_notes, local_update_notes)
            cnf.set("version", {
                "remote": str(remote),
                "local": str(local),
                "name": {
                    "remote": VERSION_NAMES[str(remote)],
                    "local": VERSION_NAMES[str(local)]
                },
                "update-size": update_size(),
                "server": SERVER,
                "timestamp": int(time.time()),
                "notes": {
                    "remote": update_remote,
                    "local": update_local
                }
            })

        if remote > local:
            at_least_one_update = True
            logger.i("available", f"update available from v{local} to v{remote}")

            if download or cnf.get("auto-download-updates", False):
                CURRENT_ACTION = "downloading"
                size = store(remote_server_latest_file_path, download_file_path)
                logger.i("download", f"downloaded update {remote}, size: {size}")

            if install or cnf.get("auto-install-updates", False):
                do_restart = True
                CURRENT_ACTION = "installing"
                install_downloaded_archive(download_file_path, local_installation_path)
                logger.i("install", f"installed update v{remote}")

            CURRENT_ACTION = "idle"
    if do_restart:
        mqtt.publish("jarvis/backend/restart", "{}")
    if not at_least_one_update:
        logger.i("polling", f"no update found on server {SERVER}")


def update_checker():
    global mqtt, logger, POLL_INTERVAL, DOWNLOADS_FOLDER

    try:
        if not os.path.isdir(DOWNLOADS_FOLDER):
            os.makedirs(DOWNLOADS_FOLDER)

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

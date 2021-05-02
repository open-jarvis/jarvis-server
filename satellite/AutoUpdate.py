"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import sys
import json
import time
import shutil
import requests
import traceback
from packaging import version
from jarvis import Logger, Config, MQTT, Exiter, ThreadPool


# initialize jarvis classes
logger = Logger("updater")
cnf = Config()


# define constants
VERSION_NAMES = {
    "0.0.0": "Alpine Alpha",
    "0.0.1": "Alpine Beta",
    "0.0.2": "Alpine"
}
UPDATE_REPOS     = [ "server", "web" ]
CURRENT_ACTION   = "idle"
DOWNLOADS_FOLDER = "/jarvis/downloads"
POLL_INTERVAL    = 60 * 60 * 1 # CHECK EVERY HOUR FOR UPDATE
SERVER           = cnf.get("update-server", "jarvisdata.philippscheer.com")
ROOT_DIR         = cnf.get("directories", {"root": "/jarvis"})["root"]
PROTOCOL         = "https"
SUFFIX           = "-latest.tar.gz"

download_pending = False
installation_pending = False
download_progress = 0
tpool = ThreadPool()

# helper functions
def install_downloaded_archive(downloaded_archive, local_installation_path):
    shutil.rmtree(local_installation_path, ignore_errors=True)
    shutil.unpack_archive(downloaded_archive, local_installation_path)
    os.unlink(downloaded_archive)


def store(url, path):
    # r = requests.get(url)
    # size = len(r.content)
    # with open(path, "wb") as f:
    #     f.write(r.content)
    # return size
    global download_progress
    download_progress = 0
    with open(path, "wb") as f:
        response = requests.get(url, stream=True)
        size = response.headers.get('content-length')

        if size is None:
            f.write(response.content)
            download_progress = 1
        else:
            dl = 0
            size = int(size)
            for data in response.iter_content(chunk_size=4096):
                # time.sleep(3)
                dl += len(data)
                download_progress = dl / size
                f.write(data)
    download_progress = 1
    return size


def update_size():
    global UPDATE_REPOS, PROTOCOL
    total_size = 0
    for repo in UPDATE_REPOS:
        total_size += int(requests.head(f"{PROTOCOL}://{SERVER}/{repo}{SUFFIX}").headers["content-length"])
    return total_size


def check_versions(version_url, version_local):
    remote_version = requests.get(version_url).text.strip()
    with open(version_local, "r") as f:
        local_version = f.read().strip()
    return (version.parse(remote_version), version.parse(local_version))


def get_update_notes(remote_url, local_url):
    rsp  = requests.get(remote_url)
    stmp = int(time.mktime(time.strptime(rsp.headers["last-modified"], "%a, %d %b %Y %I:%M:%S %Z")))
    rmt  = rsp.text.strip()
    with open(local_url, "r") as f:
        lcl = f.read().strip()
    return (rmt, lcl, stmp)


def _on_REQUEST(client: object, userdata: object, message: object):
    try:
        global CURRENT_ACTION, UPDATE_REPOS, logger, mqtt, download_pending, installation_pending, download_progress
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
            if not download_pending:
                result["success"] = False
                result["error"] = "No update available!"
            else:
                tpool.register(poll, f"install update {int(time.time())}", [True, False])
        if action == "install":
            logger.i("install", "received mqtt install signal")
            if not installation_pending:
                result["success"] = False
                result["error"] = "No update available!"
            else:
                tpool.register(poll, f"install update {int(time.time())}", [False, True])
        if action == "status":
            logger.i("install", "received mqtt status signal")
            result = cnf.get("version", {})
            result["success"] = True
            result["current-action"] = CURRENT_ACTION
            result["available"] =   {
                                        "download": download_pending, 
                                        "install": installation_pending 
                                    }
            if download_pending:
                download_progress = 0
            result["progress"] = download_progress
        if "reply-to" in data:
            mqtt.publish(data["reply-to"], json.dumps(result))
    except Exception:
        logger.e("on-mqtt", "an error occured while handling an mqtt endpoint, see traceback", traceback.format_exc())


mqtt = MQTT(client_id="updater")
mqtt.on_message(_on_REQUEST)
mqtt.subscribe("jarvis/update/#")


def poll(download=False, install=False):
    global CURRENT_ACTION, UPDATE_REPOS, SERVER, VERSION_NAMES, logger, mqtt, cnf, download_pending, installation_pending
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
            update_remote, update_local, remote_timestamp = get_update_notes(remote_update_notes, local_update_notes)
            cnf.set("version", {
                "remote": str(remote),
                "local": str(local),
                "name": {
                    "remote": VERSION_NAMES[str(remote)],
                    "local": VERSION_NAMES[str(local)]
                },
                "update-size": update_size(),
                "server": SERVER,
                "timestamp": {
                    "local": int(time.time()),
                    "remote": remote_timestamp
                },
                "notes": {
                    "remote": update_remote,
                    "local": update_local
                }
            })

        if remote > local:
            at_least_one_update = True
            logger.i("available", f"update available from v{local} to v{remote}")

            download_pending = True

            if download or cnf.get("auto-download-updates", False):
                CURRENT_ACTION = "downloading"
                download_pending = False
                size = store(remote_server_latest_file_path, download_file_path)
                logger.i("download", f"downloaded update {remote}, size: {size}")
                installation_pending = True

            if install or cnf.get("auto-install-updates", False):
                do_restart = True
                installation_pending = False
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
            for i in range(POLL_INTERVAL * 2):
                if not Exiter.running:
                    break
                time.sleep(0.49)
        logger.i("shutdown", "shutting down autoupdate server")
    except Exception as e:
        logger.e("mainloop", f"an exception occured, next try in {POLL_INTERVAL // 1.5}s, see traceback", traceback.format_exc())
        for i in range(int((POLL_INTERVAL // 1.5) * 2)):
            if not Exiter.running:
                return
            time.sleep(0.49)
        update_checker()

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
from dateutil.parser import parse as parsedate
from jarvis import Logger, Config, Exiter, ThreadPool, API


logger = Logger("Update")
cnf = Config()
tpool = ThreadPool()
download_pending = False
installation_pending = False
download_progress = 0


VERSION_NAMES = {
    "0.0.0": "Alpine Alpha",
    "0.0.1": "Alpine Beta",
    "0.0.2": "Alpine"
}
UPDATE_REPOS     = [ "server", "web" ]
CURRENT_ACTION   = "idle"
DOWNLOADS_FOLDER = "/jarvis/downloads"
POLL_INTERVAL    = 60 * 60 * 1 # CHECK EVERY HOUR FOR UPDATE
SERVER           = cnf.get("update-server", "jarvis.fipsi.at")
ROOT_DIR         = cnf.get("directories", {"root": "/jarvis"})["root"]
PROTOCOL         = "https"
SUFFIX           = "-latest.tar.gz"


def install_downloaded_archive(downloaded_archive, local_installation_path):
    """Unpack the downloaded archive from `downloaded_archive` path -> `local_installation_path`  
    Removes existing data in `downloaded_archive`"""
    shutil.rmtree(local_installation_path, ignore_errors=True)
    shutil.unpack_archive(downloaded_archive, local_installation_path)
    os.unlink(downloaded_archive)

def download(url, path):
    """Download `url` and store to `path`"""
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
                dl += len(data)
                download_progress = dl / size
                f.write(data)
    download_progress = 1
    return size

def calculate_update_size():
    """Calculate the total size of all repositories"""
    global UPDATE_REPOS, PROTOCOL
    total_size = 0
    for repo in UPDATE_REPOS:
        total_size += int(requests.head(f"{PROTOCOL}://{SERVER}/{repo}{SUFFIX}").headers["content-length"])
    return total_size

def fetch_versions(version_url, version_local):
    """Get local and remote versions  
    * `version_url` - The URL to a file containing a version string like `v0.0.1`, `v2.15.3`, etc.  
    * `version_local` - File path to a file containing a version string"""
    remote_version = requests.get(version_url).text.strip()
    with open(version_local, "r") as f:
        local_version = f.read().strip()
    return (version.parse(remote_version), version.parse(local_version))

def get_update_notes(remote_url, local_url):
    """Get the remote and local update notes  
    * `remote_url` - URL of a markdown file containing update notes  
    * `local_url` - File path of a markdown file containing the current update notes"""
    rsp  = requests.get(remote_url)
    stmp = int(time.mktime(parsedate(rsp.headers["last-modified"]).timetuple()))
    rmt  = rsp.text.strip()
    with open(local_url, "r") as f:
        lcl = f.read().strip()
    return (rmt, lcl, stmp)

def poll(download=False, install=False):
    """Poll for updates  
    * If [`download`]() is set, automatically download the file. Overrides the config setting  
    * If `install` is set, automatically install the update. Overrides the config setting"""
    global CURRENT_ACTION, UPDATE_REPOS, SERVER, VERSION_NAMES, logger, mqtt, cnf, download_progress, download_pending, installation_pending
    # TODO: install a jarvis repo on my server
    logger.d("Poll", "Skipping poll")
    return
    logger.i("Poll", f"Polling for updates from server {SERVER}")
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

        start = time.time()
        remote, local = fetch_versions(remote_version_file, local_version_file)

        if repo == "server":    # we use the server repo as reference
            start = time.time()
            update_remote, update_local, remote_timestamp = get_update_notes(remote_update_notes, local_update_notes)
            start = time.time()
            cnf.set("version", {
                "remote": str(remote),
                "local": str(local),
                "name": {
                    "remote": VERSION_NAMES[str(remote)],
                    "local": VERSION_NAMES[str(local)]
                },
                "update-size": calculate_update_size(),
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
            logger.i("Available", f"Update available from v{local} to v{remote}")

            # download is only pending, if remote file was not downloaded
            download_pending = not os.path.isfile(download_file_path)
            if not download_pending:
                download_progress = 1
                installation_pending = True

            if download or cnf.get("auto-download-updates", False):
                CURRENT_ACTION = "downloading"
                download_pending = False
                size = download(remote_server_latest_file_path, download_file_path)
                logger.i("Download", f"Downloaded update {remote}, size: {size}")
                installation_pending = True

            if install or cnf.get("auto-install-updates", False):
                do_restart = True
                installation_pending = False
                CURRENT_ACTION = "installing"
                install_downloaded_archive(download_file_path, local_installation_path)
                logger.i("Install", f"Installed update v{remote}")

            CURRENT_ACTION = "idle"
    if do_restart:
        # TODO: fix this variable
        mqtt.publish("jarvis/backend/restart", "{}")
    if not at_least_one_update:
        logger.i("Poll", f"No update found on server {SERVER}")

def schedule_loop():
    """In a loop, check if the scheduled install timestamp has passed and if so, install the update"""
    global logger
    while Exiter.running:
        schedule = cnf.get("schedule-install", False)
        if schedule:
            if schedule < time.time():
                logger.i("Schedule", "Running a scheduled installation")
                cnf.set("schedule-install", False)
                poll(False, True)
        time.sleep(1)

def update_checker():
    """Starts the mainloop (`schedule_loop` and poll loop)"""
    global mqtt, logger, tpool, POLL_INTERVAL, DOWNLOADS_FOLDER

    try:
        tpool.register(schedule_loop, "schedule install loop")
        if not os.path.isdir(DOWNLOADS_FOLDER):
            os.makedirs(DOWNLOADS_FOLDER)

        while Exiter.running:
            poll()
            for i in range(POLL_INTERVAL * 2):
                if not Exiter.running:
                    break
                time.sleep(0.49)
        logger.i("Shutdown", "Shutting down AutoUpdate server")
    except Exception as e:
        logger.e("Mainloop", f"An exception occured, next try in {POLL_INTERVAL // 1.5}s", traceback.format_exc())
        for i in range(int((POLL_INTERVAL // 1.5) * 2)):
            if not Exiter.running:
                return
            time.sleep(0.49)
        update_checker()


@API.route("jarvis/update/poll")
def poll_for_updates(args, client, data):
    """Manually poll for new updates  
    Checks the update server and compare the remote to the local version  
    If an update is available, retrieve the update notes  
    Returns update information:
    ```python
    {
        "success": true|false,
        "update": {
                "remote": str, # version string (eg. 1.2, 2.15.3)
                "local": str, # version string (eg. 1.2, 2.15.3)
                "name": {
                    "remote": str, # version name (eg. Beta)
                    "local": str # version name (eg. Aplha)
                },
                "update-size": int, # size of update in bytes
                "server": "jarvisdata.philippscheer.com",
                "timestamp": {
                    "local": int, # unix timestamp of last file change
                    "remote": int # unix timestamp of last file change
                },
                "notes": {
                    "remote": str, # markdown of remote update notes
                    "local": str # markdown of local update notes
                }
            }|{}
    }
    ```"""
    global logger
    logger.i("Poll", "Received MQTT poll signal")
    poll()
    return {"success": True, "update": cnf.get("version", {})}

@API.route("jarvis/update/download")
def download_update(args, client, data):
    """Download an update  
    Make sure to call `jarvis/update/poll` before downloading  
    Returns:
    ```python
    {
        "success": true|false,
        "error?": ...
    }
    ```"""
    global logger, download_pending
    logger.i("Download", "Received MQTT download signal")
    if not download_pending:
        return {"success": False, "error": "No update available!"}
    else:
        tpool.register(poll, f"download update {int(time.time())}", [True, False])
        return True

@API.route("jarvis/update/install")
def install_update(args, client, data):
    """Install an update  
    Make sure to call `jarvis/update/poll` and `jarvis/update/download` before installing  
    Returns:
    ```python
    {
        "success": true|false,
        "error?": ...
    }
    ```"""
    global logger, installation_pending
    logger.i("Install", "Received MQTT install signal")
    if not installation_pending:
        return {"success": False, "error": "No update available!"}
    else:
        tpool.register(poll, f"install update {int(time.time())}", [False, True])
        return True

@API.route("jarvis/update/status")
def update_status(args, client, data):
    """Gets the current update status
    Returns:
    ```python
    {
        "success": true|false,
        "current-action": "idle|downloading|installing",
        "available": {
            "download": true|false,
            "install": true|false
        },
        "schedule-install": int|false, # timestamp of scheduled install
        "progress": {
            "download": float # float percentage of progress 0-1
        }
    }
    ```"""
    global CURRENT_ACTION, download_pending, installation_pending, download_progress
    logger.i("Install", "Received MQTT status signal")
    result = cnf.get("version", {})  # benchmark: 0.17 - 0.2s
    result["success"] = True
    result["current-action"] = CURRENT_ACTION
    result["available"] =   {
                                "download": download_pending, 
                                "install":  False if download_pending else installation_pending
                                # if download == True, then you cannot directly install
                            }
    result["schedule-install"] = cnf.get("schedule-install", False)
    if download_pending:
        download_progress = 0
    result["progress"] = { "download": download_progress }
    # takes abt. 1.5s
    return result

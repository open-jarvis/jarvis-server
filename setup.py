#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

from jarvis import SetupTools, Config, Colors, Database
from getpass import getpass
import hashlib
import os
import sys


ROOT_DIR = "/jarvis"
LOC = f"{ROOT_DIR}/server"
APP_DIR = f"{ROOT_DIR}/apps"
WEB_DIR = f"{ROOT_DIR}/web"
USR = os.getlogin()
DIR = os.path.dirname(os.path.abspath(__file__))


[Database().table(x) for x in ["devices", "applications", "logs",
                               "instants", "tokens", "config", "brain"]]
cnf = Config()


def install():
    global cnf, ROOT_DIR, LOC, APP_DIR, WEB_DIR, USR, DIR

    SetupTools.check_python_version(3)
    SetupTools.check_root()
    if "--no-input" not in sys.argv:
        ROOT_DIR = SetupTools.get_default_installation_dir(ROOT_DIR)
        LOC = f"{ROOT_DIR}/server"
        APP_DIR = f"{ROOT_DIR}/apps"
        WEB_DIR = f"{ROOT_DIR}/web"
        USR = SetupTools.get_default_user(USR)

        if cnf.get("pre-shared-key", None) is None or cnf.get("token-key", None) is None:
            ask_and_store_credentials()

    if cnf.get("pre-shared-key", None) is None or cnf.get("token-key", None) is None:
        print(f"{Colors.RED}No Pre-Shared key or Token key stored yet{Colors.END}")
        exit(1)

    cnf.set("directories", {
        "root": ROOT_DIR,
        "server": LOC,
        "apps": APP_DIR,
        "web": WEB_DIR
    })
    cnf.set("install-user", USR)

    # create directories
    for d in [LOC, APP_DIR, WEB_DIR, f"{LOC}/logs"]:
        if not os.path.isdir(d):
            os.makedirs(d)

    # modify service file
    replace_in_file(f"{DIR}/system/jarvisd.service", "{{SRV_DIR}}", LOC)

    # install jarvis packages
    SetupTools.do_action(
        "updating package sources", "sudo apt update", exit_on_fail=False)
    SetupTools.do_action("installing packages",
                         "sudo apt install -y git python3-pip mosquitto")

    # installation of files
    SetupTools.do_action(
        "changing application folder permissions", f"sudo chmod 755 {APP_DIR}")
    SetupTools.do_action("installing service files",
                         f"sudo cp -v {DIR}/system/*.service /etc/systemd/system/")
    SetupTools.do_action("reloading systemd daemon",
                         "sudo systemctl daemon-reload")
    SetupTools.do_action("installing jarvisd executable",
                         f"sudo cp -v {DIR}/system/jarvis /usr/bin/jarvis")
    SetupTools.do_action(
        "changing jarvisd executable permissions", "sudo chmod 777 /usr/bin/jarvis")
    SetupTools.do_action(
        f"changing ownership of directory (to {USR})", f"sudo chown -R {USR}: {ROOT_DIR}")
    SetupTools.do_action(f"copying api documentation to {LOC}/apidoc",
                         f"git clone https://github.com/open-jarvis/open-jarvis.github.io {LOC}/apidoc")

    # start jarvis
    SetupTools.do_action("starting and enabling jarvisd service",
                         "sudo systemctl start jarvisd.service ; sudo systemctl enable jarvisd.service")

    # clean up
    SetupTools.do_action(
        f"moving jarvisd to new location ({LOC})", f"sudo mv -v {DIR}/* {LOC}")
    SetupTools.do_action("cleaning up directory", f"sudo rm -rf {DIR}")

    # exit snippet
    print(f"Successfully set up Jarvis in {LOC} and registered service")
    print("")
    print("Please reboot!")
    exit(0)


def replace_in_file(path, search, replacement):
    contents = None
    with open(path, "r") as f:
        contents = f.read()

    if contents is None:
        SetupTools.do_action(f"reading file {path}", "false")

    contents = contents.replace(search, replacement)
    with open(path, "w") as f:
        f.write(contents)


def ask_and_store_credentials():
    # ask for keys and store them securely
    psk = getpass("  Pre-shared key : ")
    tk = getpass("       Token key : ")

    # NOTE: maybe switch to sha512 -> slower but more secure
    cnf.set("pre-shared-key", hashlib.sha256(psk.encode('utf-8')).hexdigest())
    cnf.set("token-key", hashlib.sha256(tk.encode('utf-8')).hexdigest())


if "-c" in sys.argv or "--credentials" in sys.argv:
    ask_and_store_credentials()
    exit(0)
if "-h" in sys.argv or "--help" in sys.argv:
    print("Usage: python3 setup.py [-h | --help] [-c | --credentials]")
    exit(0)
else:
    install()

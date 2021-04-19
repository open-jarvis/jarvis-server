#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import os
import sys
import argparse
from jarvis import SetupTools, Config, Colors, Database, Security
from getpass import getpass


parser = argparse.ArgumentParser(description='Jarvis Setup Script')
parser.add_argument("-b", "--blind", default=False, action="store_true", help="Do not ask for installation directory, and use default values (best for non-user interactive scripts)")
parser.add_argument("-c", "--credentials", default=False, action="store_true", help="Only ask for pre-shared-key and token-key credentials, then exit")
args = parser.parse_args()


ROOT_DIR = "/jarvis"
try:
    USR = os.getlogin()
except Exception: # docker container
    USR = "root"
DIR = os.path.dirname(os.path.abspath(__file__))


[Database().table(x) for x in ["devices", "applications", "logs", "analytics", "users", "skills",
                               "instants", "tokens", "config", "brain"]]
Database().table("users").insert({"username": "jarvis", "password": Security.password_hash("jarvis")})
cnf = Config()


def install():
    global args, cnf, ROOT_DIR, USR

    SetupTools.check_python_version(3)
    SetupTools.check_root()
    if not args.blind:
        ROOT_DIR = SetupTools.get_default_installation_dir(ROOT_DIR)
        USR = SetupTools.get_default_user(USR)

        if cnf.get("pre-shared-key", None) is None or cnf.get("token-key", None) is None:
            ask_and_store_credentials()

        if args.credentials:
            exit(0)


    LOC = f"{ROOT_DIR}/server"
    APP_DIR = f"{ROOT_DIR}/apps"
    WEB_DIR = f"{ROOT_DIR}/web"
    DOWNLOADS_DIR = f"{ROOT_DIR}/downloads"
    LOGS_DIR = f"{ROOT_DIR}/logs"


    if cnf.get("pre-shared-key", None) is None or cnf.get("token-key", None) is None:
        print(f"{Colors.RED}No Pre-Shared key or Token key stored yet, setting default{Colors.END}")
        cnf.set("pre-shared-key", "jarvis")
        cnf.set("token-key", "jarvis")

    cnf.set("directories", {
        "root": ROOT_DIR,
        "server": LOC,
        "apps": APP_DIR,
        "web": WEB_DIR,
        "downloads": DOWNLOADS_DIR
    })
    cnf.set("install-user", USR)

    # create directories
    for d in [LOC, APP_DIR, WEB_DIR, f"{LOC}/logs", LOGS_DIR, DOWNLOADS_DIR]:
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
                         "sudo systemctl daemon-reload", exit_on_fail=False)

    SetupTools.do_action("installing service files",
                         f"sudo cp -v {DIR}/system/*.service /etc/init.d/", exit_on_fail=False)
    SetupTools.do_action("installing jarvisd executable",
                         f"sudo cp -v {DIR}/system/jarvis /usr/bin/jarvis", exit_on_fail=False)
    SetupTools.do_action(
        "changing jarvisd executable permissions", "sudo chmod 777 /usr/bin/jarvis", exit_on_fail=False)
    SetupTools.do_action(
        f"changing ownership of directory (to {USR})", f"sudo chown -R {USR}: {ROOT_DIR}")
    SetupTools.do_action(f"copying api documentation to {LOC}/apidoc",
                         f"git clone https://github.com/open-jarvis/open-jarvis.github.io {LOC}/apidoc", exit_on_fail=False)

    # start jarvis
    SetupTools.do_action("starting and enabling jarvisd service",
                         "sudo systemctl start jarvisd.service ; sudo systemctl enable jarvisd.service", exit_on_fail=False)

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
    cnf.set("pre-shared-key", Security.password_hash(psk))
    cnf.set("token-key", Security.password_hash(tk))


if args.credentials:
    ask_and_store_credentials()
    exit(0)
install()

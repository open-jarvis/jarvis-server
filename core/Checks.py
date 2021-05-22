"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import sys
from jarvis import Logger, Database


VERSION_FILE = f"{os.path.dirname(os.path.abspath(sys.argv[0]))}/version"


logger = Logger("Checks")
do_exit = False


def check_system(skip_checks: bool = False):
    """
    Check if the system can run Jarvis  
    If you want to skip checks, set the `skip_checks` variable to `True`, throws a warning message
    """
    global logger, do_exit, VERSION_FILE
    if skip_checks:
        logger.w("Skip", "Skipping checks is not recommended")
        return
    _check_database()
    if do_exit:
        _err("Requirements are not met. Jarvis cannot run")
        exit(1)
    else:
        logger.s("Passed", "All checks performed, Jarvis is able to run")
        try:
            logger.i("Version", f"Running version v{open(VERSION_FILE, 'r').read().strip()}")
        except Exception:
            logger.w("Version", "Couldn't read version file")


def _check_database():
    """
    Check if the database is up.  
    The connection is checked and also credentials
    """
    if not Database(exit_on_fail=False).up:
        _err("Database is not running")


def _err(msg):
    """
    Log an error and mark that Jarvis cannot run
    """
    global logger, do_exit
    logger.c("Error", msg)
    do_exit = True
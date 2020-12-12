#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import os, glob, json, signal, subprocess, shlex
from jarvis import Logger
from classes.App import App

APPS = []
LOGGER = None

def load_apps(root_dir):
	global APPS, LOGGER

	APPS_DIR = f"{root_dir}/apps"
	LOGGER = Logger(f"{root_dir}/logs/apps.log", f"{root_dir}/logs")

	for filename in glob.iglob(f"{APPS_DIR}/**", recursive=False):
		if os.path.isdir(filename):
			app = App(filename, LOGGER)
			app.start()
			APPS.append(app)


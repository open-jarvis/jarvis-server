#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import os, glob, json, signal, subprocess, shlex
from classes.Logger import Logger

APPS = []
LOGGER = None
REQUIRED_APP_FIELDS = [
	"script",
	"name"
]

def load_apps(root_dir):
	global APPS, LOGGER

	APPS_DIR = f"{root_dir}/apps"
	LOGGER = Logger(f"{root_dir}/logs/apps.log")

	for filename in glob.iglob(f"{APPS_DIR}/**", recursive=False):
		if os.path.isdir(filename):
			app = App(filename, LOGGER)
			app.start()
			APPS.append(app)


class App:
	def __init__(self, directory, logger):
		self.dir = directory
		self.config_file = f"{directory}/system/app.json"
		self.error = None
		self.logger = logger

		try:
			with open(self.config_file, "r") as f:
				self.config = json.loads(f.read())
		except Exception as e:
			self.is_startable = False
			self.error = f"{self.config_file} either not readable or contains invalid json"
			return
	
		for key in REQUIRED_APP_FIELDS:
			if key not in self.config:
				self.is_startable = False
				self.error = f"{self.config} json doesn't contain required key {key}"
				return
		
		self.is_startable = True
		
		self.running = False
		self.process = None
		
		self.name = self.config["name"]
		self.script = self.config["script"]


	def start(self):
		self.logger.i(f"{self.name}", f"starting app with startup script {self.script}")
		self.process = subprocess.Popen(shlex.split(self.script))

	def stop(self):
		self.logger(f"{self.name}", "stopping app")
		self.process.kill()
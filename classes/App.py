#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import json, subprocess, shlex

REQUIRED_APP_FIELDS = [
	"script",
	"name"
]

class App:
	def __init__(self, directory, logger):
		self.dir = directory
		self.config_file = f"{directory}/system/app.json"
		self.error = None
		self.logger = logger
		self.is_startable = True

		try:
			with open(self.config_file, "r") as f:
				self.config = json.loads(f.read())
			for key in REQUIRED_APP_FIELDS:
				if key not in self.config:
					self.is_startable = False
					self.error = f"{self.config} json doesn't contain required key {key}"
		except Exception as e:
			self.is_startable = False
			self.error = f"{self.config_file} either not readable or contains invalid json: {e}"

		if self.is_startable:
			self.name = self.config["name"].lower()
			self.script = self.config["script"]


	def start(self):
		self.logger.i(f"app:{self.name}", f"starting app with startup script '{self.script}'")
		self.process = subprocess.Popen(shlex.split(self.script), cwd=self.dir)

	def stop(self):
		self.logger.i(f"app:{self.name}", "stopping app")
		self.process.terminate()

	def kill(self):
		self.logger.i(f"app:{self.name}", "killing app")
		self.process.kill()

	def is_running(self):
		return self.process.returncode == None

	def is_ok(self):
		return (self.is_startable, self.error)
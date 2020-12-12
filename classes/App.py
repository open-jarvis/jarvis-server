#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

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
		self.setup_script = f"{directory}/system/setup.py"
		if not os.path.isfile(self.setup_script):
			self.is_startable = False
			self.error = f"setup file at {self.setup_script} doesn't exist"


	def start(self):
		self.logger.i(f"{self.name}", f"starting app with startup script {self.script}")
		self.process = subprocess.Popen(shlex.split(self.script))

	def stop(self):
		self.logger(f"{self.name}", "stopping app")
		self.process.kill()
	
	def run_setup(self):
		print(f"running setup: python3 {self.setup_script}. Press enter to continue ")
		input("")
		return_code = os.system(f"python3 {self.setup_script}")
		if return_code != 0:
			print(f"error: setup script exited with code {return_code}")
			return False
		else:
			print("successfully ran setup script")
			return True

	def is_ok(self):
		if self.error is not None:
			return (True, self.error)
		else:
			return (False, self.error)
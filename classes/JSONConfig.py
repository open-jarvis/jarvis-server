#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

"""
JSONConfig
	.exists()               -> boolean
	.create()               -> void
	.get()                  -> object
	.set_key(key, value)    -> void
	.get_key(key, or_else)  -> any
"""

import os, json

class JSONConfig:
	def __init__(self, config_file):
		self.file = config_file
		self.path = os.path.dirname(os.path.abspath(self.file))
	def exists(self):
		return os.path.exists(self.file)
	def create(self):
		if not os.path.exists(self.path):
			os.makedirs(self.path)
			with open(self.file, "w") as f:
				f.write(json.dumps({}))
	def get(self):
		cnf = {}
		try:
			if not self.exists():
				self.create()
			with open(self.file, "r") as f:
				cnf = json.loads(f.read())
		except Exception as e:
			pass
		return cnf
	def set_key(self, key, value):
		cnf = self.get()
		cnf[key] = value
		with open(self.file, "w") as f:
			f.write(json.dumps(cnf))
	def get_key(self, key, or_else):
		cnf = self.get()
		if key in cnf:
			return cnf[key]
		else:
			return or_else

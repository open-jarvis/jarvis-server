#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

from datetime import datetime
import os, zipfile, json

#MAX_LOGF_SIZE = 100 * 1024 * 1024		# 100MB
MAX_LOGF_SIZE = 20 * 1024 * 1024		# 20MB
MAX_FAST_LENGTH = 1000					# 1000 entries

class Logger:
	def __init__(self, logfile, compressed_folder):
		self.logfile = logfile
		self.compressed_folder = compressed_folder
		self.on = True
		self.fast = False
		self.grouping = False
		self.to_console = False
		self.fast_log_data = []

	def off(self):
		self.on = False
	def on(self):
		self.on = True

	def console_on(self):
		self.to_console = True
	def console_off(self):
		self.to_console = False

	def new_group(self, data):
		self.grouping = True
		self.fast_log_data.append({"meta":data, "data":[]})

	def i(self, tag, message):
		self.wr("I", tag, message)
	def e(self, tag, message):
		self.wr("E", tag, message)
	def w(self, tag, message):
		self.wr("W", tag, message)
	def s(self, tag, message):
		self.wr("S", tag, message)
	def c(self, tag, message):
		self.wr("C", tag, message)


	def enable_fast(self):
		self.fast = True
		self.clear_fast()
	def disable_fast(self):
		self.fast = False
		self.clear_fast()
	def clear_fast(self):
		del self.fast_log_data
		self.fast_log_data = []
	def get_fast(self):
		return self.fast_log_data

	def wr(self, pre, tag, message):
		if self.fast:
			if len(self.fast_log_data) > MAX_FAST_LENGTH:
				self.clear_fast()
			
			msg_to_store = message # should be an object
			if isinstance(message, str):
				try:
					msg_to_store = json.loads(message)
				except Exception as e:
					# print(e)
					pass

			if self.grouping:
				# print(len(self.fast_log_data))
				self.fast_log_data[-1]["data"].append({
					"severity": pre,
					"tag": tag,
					"message": msg_to_store
				})
			if not self.grouping:
				self.fast_log_data.append({
					"severity": pre,
					"tag": tag,
					"message": msg_to_store
				})

		if self.to_console:
			print(logstr)
		if not self.on:
			return
		
		logstr = "{} {}/{}{} {}".format(str(datetime.now()), pre, tag, " " * (10-len(tag)), message)

		with open(self.logfile, "a+") as f:
			f.write(logstr + "\n")
		self.check_file_size()
	
	def check_file_size(self):
		if os.path.getsize(self.logfile) > MAX_LOGF_SIZE:
			# TODO: replace logs/... with consistent path
			zipfile.ZipFile("{}/jarvis_http.log.{}.zip".format(self.compressed_folder, str(datetime.now()).replace(" ", "_").replace(":", "-")), 'w', zipfile.ZIP_DEFLATED).write(self.logfile)
			with open(self.logfile, "w") as f:
				f.write("")
		
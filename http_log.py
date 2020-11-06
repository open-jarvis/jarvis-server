from datetime import datetime

class Logger:
	def __init__(self, logfile="./logs/jarvis_http.log"):
		self.logfile = logfile
		self.on = True

	def off(self):
		self.on = False

	def on(self):
		self.on = True

	def i(self, tag, message):
		if not self.on:
			return
		with open(self.logfile, "a+") as f:
			f.write("{} I/{}{} {}\n".format(str(datetime.now()), tag, " " * (10-len(tag)), message))
	
	def e(self, tag, message):
		if not self.on:
			return
		with open(self.logfile, "a+") as f:
			f.write("{} E/{}{} {}\n".format(str(datetime.now()), tag, " " * (10-len(tag)), message))
	
	def w(self, tag, message):
		if not self.on:
			return
		with open(self.logfile, "a+") as f:
			f.write("{} W/{}{} {}\n".format(str(datetime.now()), tag, " " * (10-len(tag)), message))
	
	def s(self, tag, message):
		if not self.on:
			return
		with open(self.logfile, "a+") as f:
			f.write("{} S/{}{} {}\n".format(str(datetime.now()), tag, " " * (10-len(tag)), message))
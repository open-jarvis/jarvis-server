#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import sys
from jarvis import MQTT
import API as API

class MQTTServer:
	def __init__(self):
		self.mqtt = MQTT(client_id="jarvis:MQTTServer")
		self.mqtt.on_message(MQTTServer.on_message)
		self.mqtt.subscribe("#")

	@staticmethod
	def on_message(c,ud,msg):
		topic = msg.topic
		message = msg.payload.decode()

		if not topic.startswith("jarvis/api"):
			return

		api_call = topic.split("/api")[-1]
		api_function_name = api_call.replace("-", "_")
		api_function = getattr(API, api_function_name)

	@staticmethod
	def start_server():
		ms = MQTTServer()



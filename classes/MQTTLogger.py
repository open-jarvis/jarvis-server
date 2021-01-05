#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import time
from jarvis import MQTT, Logger, Exiter

mqtt = None
logger = None

def start_logging(root_dir):
	global logger
	logger = Logger(f"{root_dir}/logs/jarvis_mqtt.log", f"{root_dir}/logs")
	logger.console_on()

	mqtt = MQTT(client_id="sniffer")
	mqtt.on_message(log_mqtt)
	mqtt.subscribe("#")
	while Exiter.running:
		time.sleep(1)

def log_mqtt(client, userdata, message):
	global logger
	data = message.payload.decode()
	topic = message.topic
	logger.i("mqtt-sniff", f"{topic} -> {data}")


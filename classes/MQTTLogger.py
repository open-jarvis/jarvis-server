#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import time
from jarvis import MQTT, Logger

mqtt = None
logger = None

def start_logging(root_dir):
	logger = Logger(f"{root_dir}/logs/jarvis_mqtt.log", f"{root_dir}/logs")

	mqtt = MQTT(client_id="sniffer")
	mqtt.on_message(log_mqtt)
	mqtt.subscribe("#")
	while True:
		time.sleep(1)

def log_mqtt(client, userdata, message):
	data = message.payload.decode()
	topic = message.topic
	logger.i("mqttD", f"{topic} -> {data}")


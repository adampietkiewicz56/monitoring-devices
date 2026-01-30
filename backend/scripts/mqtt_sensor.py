import paho.mqtt.client as mqtt
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "monitoring/alerts"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("[SENSOR] Connected to MQTT broker")
    else:
        logger.error(f"[SENSOR] Connection failed: {rc}")

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_start()

try:
    counter = 0
    while True:
        counter += 1
        payload = {
            "host_id": 1,
            "status": "DOWN",
            "message": f"Sensor alert #{counter} - Host unreachable"
        }
        client.publish(MQTT_TOPIC, json.dumps(payload))
        logger.info(f"[SENSOR] Published: {payload}")
        time.sleep(5)
except KeyboardInterrupt:
    logger.info("[SENSOR] Stopping...")
finally:
    client.loop_stop()
    client.disconnect()

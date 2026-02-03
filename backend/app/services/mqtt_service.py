import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from sqlmodel import Session, select

from app.db.session import engine
from app.db.models import Alert, Host

logger = logging.getLogger(__name__)

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_SUB = "monitoring/alerts"
MQTT_TOPIC_PUB = "monitoring/alerts/published"


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT: Connected to broker")
            self.connected = True
            client.subscribe(MQTT_TOPIC_SUB)
            logger.info(f"MQTT: Subscribed to {MQTT_TOPIC_SUB}")
        else:
            logger.error(f"MQTT: Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"MQTT: Received: {payload}")
            
            host_id = payload.get("host_id")
            status = payload.get("status")
            message = payload.get("message", "")
            severity = "CRITICAL" if status == "DOWN" else "INFO"
            
            # Save alert to database
            with Session(engine) as session:
                # Check if host exists
                host = session.get(Host, host_id)
                if not host:
                    logger.warning(f"MQTT: Host {host_id} not found")
                    return
                
                # Create alert
                alert = Alert(
                    host_id=host_id,
                    message=f"[MQTT] {message}",
                    severity=severity
                )
                session.add(alert)
                session.commit()
                logger.info(f"MQTT: Alert saved for host {host_id}")
                
        except Exception as e:
            logger.error(f"MQTT: Error processing message: {e}")

    def publish_alert(self, host_id: int, host_name: str, severity: str, message: str):
        """Publish alert to MQTT topic - 0.75 pkt extension"""
        try:
            if not self.connected:
                logger.warning("MQTT: Not connected, cannot publish")
                return
            
            payload = {
                "host_id": host_id,
                "host_name": host_name,
                "severity": severity,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.client.publish(MQTT_TOPIC_PUB, json.dumps(payload), qos=1)
            logger.debug(f"MQTT: Published alert for host {host_name}: {message}")
        except Exception as e:
            logger.error(f"MQTT: Publish error: {e}")

    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"MQTT: Failed to connect: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


mqtt_client = MQTTClient()

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
MQTT_TOPIC = "monitoring/alerts"


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Connected to broker")
            self.connected = True
            client.subscribe(MQTT_TOPIC)
            print(f"[MQTT] Subscribed to {MQTT_TOPIC}")
        else:
            print(f"[MQTT] Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"[MQTT] Received: {payload}")
            
            host_id = payload.get("host_id")
            status = payload.get("status")
            message = payload.get("message", "")
            severity = "CRITICAL" if status == "DOWN" else "INFO"
            
            # Save alert to database
            with Session(engine) as session:
                # Check if host exists
                host = session.get(Host, host_id)
                if not host:
                    print(f"[MQTT] Host {host_id} not found")
                    return
                
                # Create alert
                alert = Alert(
                    host_id=host_id,
                    message=f"[MQTT] {message}",
                    severity=severity
                )
                session.add(alert)
                session.commit()
                print(f"[MQTT] Alert saved for host {host_id}")
                
        except Exception as e:
            print(f"[MQTT] Error processing message: {e}")

    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTT] Failed to connect: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


mqtt_client = MQTTClient()

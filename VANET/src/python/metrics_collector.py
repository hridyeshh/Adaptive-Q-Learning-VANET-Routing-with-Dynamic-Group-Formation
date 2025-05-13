import json
import logging
from typing import Callable, Dict, Optional
import paho.mqtt.client as mqtt

class MetricsCollector:
    def __init__(self, broker_address: str = "localhost", broker_port: int = 1883):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.callbacks = []
        self.logger = logging.getLogger(__name__)
        
        # Set up MQTT client callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.logger.info("Connected to MQTT broker")
            # Subscribe to RSU metrics topic
            client.subscribe("vanet/rsu/+/metrics")
        else:
            self.logger.error(f"Failed to connect to MQTT broker with code: {rc}")
            
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received."""
        try:
            # Parse metrics from message
            metrics = json.loads(msg.payload.decode())
            rsu_id = msg.topic.split('/')[2]  # Extract RSU ID from topic
            
            # Notify all registered callbacks
            for callback in self.callbacks:
                callback(rsu_id, metrics)
                
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse metrics message: {msg.payload}")
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker."""
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
            
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.broker_address, self.broker_port)
            self.client.loop_start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            return False
            
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        
    def register_callback(self, callback: Callable[[str, Dict], None]):
        """Register a callback function to be called when metrics are received."""
        self.callbacks.append(callback)
        
    def unregister_callback(self, callback: Callable[[str, Dict], None]):
        """Unregister a previously registered callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback) 
#!/usr/bin/env python3
"""
MQTT Test Tool for VANET Simulation
----------------------------------
This script tests MQTT connectivity and publishes test data
to help diagnose connection issues.
"""

import paho.mqtt.client as mqtt
import json
import time
import argparse
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mqtt_test")

def on_connect(client, userdata, flags, rc):
    """Callback for MQTT connection."""
    if rc == 0:
        logger.info("Connected to MQTT broker successfully!")
        client.connected = True
    else:
        error_messages = {
            1: "Connection refused: incorrect protocol version",
            2: "Connection refused: invalid client identifier",
            3: "Connection refused: server unavailable",
            4: "Connection refused: bad username or password",
            5: "Connection refused: not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error (code: {rc})")
        logger.error(f"Failed to connect to MQTT broker: {error_msg}")
        client.connected = False

def on_disconnect(client, userdata, rc):
    """Callback for MQTT disconnection."""
    if rc == 0:
        logger.info("Disconnected from MQTT broker cleanly")
    else:
        logger.warning(f"Unexpected disconnection from MQTT broker (code: {rc})")
    client.connected = False

def on_publish(client, userdata, mid):
    """Callback for MQTT message publishing."""
    logger.info(f"Message {mid} published successfully")

def test_mqtt_connection(broker, port, topic_prefix="rsu/metrics"):
    """Test MQTT connection and publish sample data."""
    logger.info(f"Testing connection to MQTT broker at {broker}:{port}")
    
    # Create MQTT client
    client = mqtt.Client("vanet_test_tool")
    client.connected = False
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    
    try:
        # Connect to broker
        logger.info(f"Attempting to connect to {broker}:{port}...")
        client.connect(broker, port, 60)
        client.loop_start()
        
        # Wait for connection to establish
        time.sleep(2)
        
        if not client.connected:
            logger.error("Failed to connect to MQTT broker")
            return False
        
        # Generate and publish test data
        for rsu_id in range(3):
            topic = f"{topic_prefix}/{rsu_id}"
            
            # Create test metrics
            metrics = {
                "vehicle_density": 10 + rsu_id * 5,
                "avg_link_loss": 0.1 + (rsu_id * 0.1),
                "degree_centrality": 0.8 - (rsu_id * 0.1),
                "position": {
                    "lat": 28.6139 + (rsu_id * 0.01),
                    "lng": 77.2090 + (rsu_id * 0.01)
                }
            }
            
            # Convert to JSON
            payload = json.dumps(metrics)
            
            # Publish message
            logger.info(f"Publishing test metrics to {topic}")
            result = client.publish(topic, payload)
            
            # Check publish result
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish message: {mqtt.error_string(result.rc)}")
            
            # Wait a bit between messages
            time.sleep(1)
        
        # Wait for last message to be published
        time.sleep(2)
        
        # Disconnect
        client.loop_stop()
        client.disconnect()
        
        logger.info("MQTT connection test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during MQTT test: {e}")
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
        return False

def run_continuous_test(broker, port, interval=5, duration=60):
    """Run a continuous test, publishing data at regular intervals."""
    logger.info(f"Starting continuous test for {duration} seconds (interval: {interval}s)")
    
    # Create MQTT client
    client = mqtt.Client("vanet_continuous_test")
    client.connected = False
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        client.connect(broker, port, 60)
        client.loop_start()
        
        # Wait for connection to establish
        time.sleep(2)
        
        if not client.connected:
            logger.error("Failed to connect to MQTT broker")
            return False
        
        # Calculate how many iterations we need
        iterations = duration // interval
        
        logger.info(f"Will publish data {iterations} times over {duration} seconds")
        
        # Run for the specified duration
        for i in range(iterations):
            if not client.connected:
                logger.error("Lost connection to MQTT broker")
                break
                
            # Generate and publish test data for 3 RSUs
            for rsu_id in range(3):
                topic = f"rsu/metrics/{rsu_id}"
                
                # Create test metrics with some variation
                metrics = {
                    "vehicle_density": 10 + rsu_id * 5 + (i % 5),
                    "avg_link_loss": 0.1 + (rsu_id * 0.1) + ((i % 10) * 0.01),
                    "degree_centrality": 0.8 - (rsu_id * 0.1) - ((i % 10) * 0.01),
                    "position": {
                        "lat": 28.6139 + (rsu_id * 0.01),
                        "lng": 77.2090 + (rsu_id * 0.01)
                    }
                }
                
                # Convert to JSON
                payload = json.dumps(metrics)
                
                # Publish message
                logger.info(f"[{i+1}/{iterations}] Publishing metrics to {topic}")
                result = client.publish(topic, payload)
                
                # Check publish result
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    logger.error(f"Failed to publish message: {mqtt.error_string(result.rc)}")
            
            # Wait for the next interval
            time.sleep(interval)
        
        # Disconnect
        client.loop_stop()
        client.disconnect()
        
        logger.info("Continuous test completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
        return True
        
    except Exception as e:
        logger.error(f"Error during continuous test: {e}")
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
        return False

def check_mqtt_broker(broker, port):
    """Check if MQTT broker is accessible without publishing."""
    logger.info(f"Checking if MQTT broker at {broker}:{port} is accessible...")
    
    client = mqtt.Client("vanet_check")
    client.connected = False
    client.on_connect = on_connect
    
    try:
        client.connect(broker, port, 5)
        client.loop_start()
        
        # Wait for connection to establish
        time.sleep(2)
        
        result = client.connected
        
        client.loop_stop()
        client.disconnect()
        
        if result:
            logger.info("✓ MQTT broker is accessible")
        else:
            logger.error("✗ MQTT broker is not accessible")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Error connecting to MQTT broker: {e}")
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
        return False

def main():
    """Main function to run the MQTT test tool."""
    parser = argparse.ArgumentParser(description="MQTT Test Tool for VANET Simulation")
    
    parser.add_argument("--broker", default="localhost", help="MQTT broker address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--mode", choices=["check", "test", "continuous"], default="check",
                      help="Test mode: check (just check connection), test (publish once), " +
                           "continuous (publish regularly)")
    parser.add_argument("--interval", type=int, default=5, 
                      help="Interval between messages in continuous mode (seconds)")
    parser.add_argument("--duration", type=int, default=60,
                      help="Duration for continuous test (seconds)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Run the selected test mode
    if args.mode == "check":
        success = check_mqtt_broker(args.broker, args.port)
    elif args.mode == "test":
        success = test_mqtt_connection(args.broker, args.port)
    elif args.mode == "continuous":
        success = run_continuous_test(args.broker, args.port, args.interval, args.duration)
    
    # Exit with appropriate status
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
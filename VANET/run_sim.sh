#!/bin/bash

# Check if Mosquitto is running
if ! brew services list | grep -q "mosquitto.*started"; then
    echo "Starting Mosquitto MQTT broker..."
    brew services start mosquitto
    sleep 2  # Wait for broker to start
fi

# Start the Flask application in the background
echo "Starting Flask application..."
python run.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Start the RSU simulator in the background
echo "Starting RSU simulator..."
python test_mqtt.py &
SIMULATOR_PID=$!

# Function to handle cleanup
cleanup() {
    echo "Stopping simulation..."
    kill $FLASK_PID
    kill $SIMULATOR_PID
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Keep script running
echo "Simulation is running. Press Ctrl+C to stop."
wait 
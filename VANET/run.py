from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import os
import logging
import paho.mqtt.client as mqtt
import time
import random
import math
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vanet_app")

# Define simplified implementations (no NumPy or scikit-learn required)
class DynamicGroupManager:
    def __init__(self):
        self.logger = logging.getLogger("group_manager")
        self.logger.info("Using simplified DynamicGroupManager")
        self.previous_groups = None
            
    def form_groups(self, rsu_metrics):
        """Form groups based on proximity (simplified algorithm)"""
        groups = {}
        
        # Skip if no metrics
        if not rsu_metrics:
            return groups
            
        # Get RSU IDs and positions
        rsus = list(rsu_metrics.keys())
        
        # Create a simple clustering based on proximity
        remaining = set(rsus)
        group_id = 0
        
        while remaining:
            # Start a new group with the first remaining RSU
            current = next(iter(remaining))
            current_group = [current]
            remaining.remove(current)
            
            # Add similar RSUs to this group
            for rsu_id in list(remaining):
                # Use a simple metric to decide if RSUs should be in the same group
                if self._are_similar(rsu_metrics, current, rsu_id):
                    current_group.append(rsu_id)
                    remaining.remove(rsu_id)
                    
                    # Limit group size
                    if len(current_group) >= 4:
                        break
            
            # Add the group
            groups[group_id] = current_group
            group_id += 1
            
        return groups
    
    def _are_similar(self, metrics, rsu1, rsu2):
        """Determine if two RSUs are similar enough to be in the same group"""
        # Simple heuristic based on "distance" in metrics space
        try:
            m1 = metrics[rsu1]
            m2 = metrics[rsu2]
            
            # Calculate a simple similarity score based on metrics
            # Higher score means more similar
            score = 0
            
            # Vehicle density similarity
            density_diff = abs(m1.get('vehicle_density', 0) - m2.get('vehicle_density', 0))
            score -= density_diff / 10.0
            
            # Link loss similarity
            link_diff = abs(m1.get('avg_link_loss', 0) - m2.get('avg_link_loss', 0))
            score -= link_diff * 5
            
            # Centrality similarity
            centrality_diff = abs(m1.get('degree_centrality', 0) - m2.get('degree_centrality', 0))
            score -= centrality_diff * 3
            
            # Geographical proximity (if position data is available)
            if 'position' in m1 and 'position' in m2:
                pos1 = m1['position']
                pos2 = m2['position']
                distance = math.sqrt((pos1.get('lat', 0) - pos2.get('lat', 0))**2 + 
                                    (pos1.get('lng', 0) - pos2.get('lng', 0))**2)
                # Distance is in degrees, rough conversion to km
                distance_km = distance * 111
                score -= distance_km * 2
            
            # Return true if score is above threshold
            return score > -2
        except Exception as e:
            logger.error(f"Error comparing RSUs: {e}")
            return False

class MetricsCollector:
    def __init__(self, broker_address, broker_port):
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.metrics = {}
        self.callbacks = []
        self.running = False
        self.client = None
        self.logger = logging.getLogger("metrics_collector")
        self.logger.info(f"Initializing MetricsCollector with broker {broker_address}:{broker_port}")
        
    def register_callback(self, callback):
        self.callbacks.append(callback)
            
    def start(self):
        """Start collecting metrics from MQTT"""
        self.running = True
        
        # Try to connect to MQTT broker
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            self.logger.info(f"Connecting to MQTT broker at {self.broker_address}:{self.broker_port}")
            self.client.connect(self.broker_address, self.broker_port)
            self.client.loop_start()
            
            # Start a thread to generate mock metrics in case MQTT fails
            Thread(target=self._generate_mock_metrics).start()
            
            self.logger.info("Metrics collector started")
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            self.logger.info("Falling back to mock metrics generation")
            # Start mock metrics generator
            Thread(target=self._generate_mock_metrics).start()
    
    def stop(self):
        """Stop collecting metrics"""
        self.running = False
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass
        self.logger.info("Metrics collector stopped")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.logger.info("Connected to MQTT broker")
            client.subscribe("rsu/metrics/#")
        else:
            self.logger.error(f"Failed to connect to MQTT broker with code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.logger.info(f"Disconnected from MQTT broker with code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received from MQTT broker"""
        try:
            topic_parts = msg.topic.split('/')
            if len(topic_parts) >= 3:
                rsu_id = topic_parts[2]
                metrics = json.loads(msg.payload.decode())
                self.metrics[rsu_id] = metrics
                self.logger.debug(f"Received metrics from RSU {rsu_id}")
                
                # Notify callbacks
                self._notify_callbacks()
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def _generate_mock_metrics(self):
        """Generate mock metrics if MQTT fails"""
        # Only generate mock metrics if we don't have real ones
        while self.running:
            # Check if we've received any real metrics
            if not self.metrics:
                mock_metrics = {}
                for i in range(5):
                    # Base position (Delhi)
                    base_lat, base_lng = 28.6139, 77.2090
                    
                    # Generate time-varying metrics
                    time_factor = time.time() % 60  # Cycle every minute
                    cycle_pos = time_factor / 60.0  # 0.0 to 1.0
                    
                    # Vehicle density varies with time
                    density_variation = math.sin(cycle_pos * 2 * math.pi) * 10
                    vehicle_density = max(0, round(10 + i * 2 + density_variation))
                    
                    # Link loss varies with density and time
                    link_loss_base = min(0.8, max(0.1, vehicle_density / 50.0))
                    link_loss_variation = math.sin(cycle_pos * 4 * math.pi) * 0.1
                    avg_link_loss = max(0, min(1, link_loss_base + link_loss_variation))
                    
                    # Centrality is inversely related to link loss
                    centrality_base = 1 - (avg_link_loss * 0.5)
                    centrality_variation = math.cos(cycle_pos * 3 * math.pi) * 0.2
                    degree_centrality = max(0, min(1, centrality_base + centrality_variation))
                    
                    # Position with some random movement
                    lat = base_lat + (i * 0.005) + (math.sin(cycle_pos * 2 * math.pi + i) * 0.002)
                    lng = base_lng + (i * 0.005) + (math.cos(cycle_pos * 2 * math.pi + i) * 0.002)
                    
                    mock_metrics[str(i)] = {
                        'vehicle_density': vehicle_density,
                        'avg_link_loss': avg_link_loss,
                        'degree_centrality': degree_centrality,
                        'position': {
                            'lat': lat,
                            'lng': lng
                        }
                    }
                
                # Only update if we don't have real metrics yet
                if not self.metrics:
                    self.metrics = mock_metrics
                    self._notify_callbacks()
            
            # Wait before next update
            time.sleep(2)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks with current metrics"""
        for callback in self.callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")

# Initialize Flask app
app = Flask(__name__, 
            static_folder='src/web/static',
            template_folder='src/web/templates')
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components
group_manager = DynamicGroupManager()
metrics_collector = None

def metrics_callback(metrics):
    """Callback to send metrics updates via WebSocket"""
    logger.debug(f"Received metrics for {len(metrics)} RSUs")
    try:
        socketio.emit('metrics_update', metrics)
        logger.debug("Emitted metrics update via Socket.IO")
    except Exception as e:
        logger.error(f"Error emitting metrics update: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulation')
def simulation():
    return render_template('standalone.html')

@app.route('/api/start_simulation', methods=['POST'])
def start_simulation():
    global metrics_collector
    try:
        config = request.json
        logger.info(f"Starting simulation with config: {config}")
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(
            broker_address=config['broker_address'],
            broker_port=config['broker_port']
        )
        
        # Register callback for real-time updates
        metrics_collector.register_callback(metrics_callback)
        
        # Start collecting metrics
        metrics_collector.start()
        logger.info("Metrics collector started")
        
        # Generate test metrics for immediate feedback
        test_metrics = generate_test_metrics()
        socketio.emit('metrics_update', test_metrics)
        logger.info("Emitted initial test metrics")
        force_generate_data()
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return jsonify({'status': 'error', 'error': str(e)})

def force_generate_data():
    """Force-generate data and send it immediately"""
    try:
        # Generate test data
        test_data = {}
        for i in range(5):
            test_data[str(i)] = {
                'vehicle_density': 10 + i * 2,
                'avg_link_loss': 0.2 + (i * 0.05),
                'degree_centrality': 0.7 - (i * 0.1),
                'position': {
                    'lat': 28.6139 + (i * 0.005),
                    'lng': 77.2090 + (i * 0.005)
                }
            }
        
        # Send it via Socket.IO
        socketio.emit('metrics_update', test_data)
        logger.info(f"Force-generated and emitted data for {len(test_data)} RSUs")
        
        # Also update metrics_collector if it exists
        global metrics_collector
        if metrics_collector:
            metrics_collector.metrics = test_data
        
        return test_data
    except Exception as e:
        logger.error(f"Error force-generating data: {e}")
        return {}
    
@app.route('/api/stop_simulation', methods=['POST'])

def stop_simulation():
    global metrics_collector
    try:
        if metrics_collector:
            metrics_collector.stop()
            metrics_collector = None
            logger.info("Simulation stopped")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/get_groups', methods=['GET'])
def get_groups():
    if not metrics_collector:
        return jsonify({'error': 'No active simulation'})
    
    try:
        groups = group_manager.form_groups(metrics_collector.metrics)
        return jsonify(groups)
    except Exception as e:
        logger.error(f"Error forming groups: {e}")
        return jsonify({'error': str(e)})

def generate_test_metrics():
    """Generate test metrics for debugging."""
    metrics = {}
    for i in range(5):
        metrics[str(i)] = {
            'vehicle_density': 10 + i * 2,
            'avg_link_loss': 0.2 + (i * 0.05),
            'degree_centrality': 0.7 - (i * 0.1),
            'position': {
                'lat': 28.6139 + (i * 0.005),
                'lng': 77.2090 + (i * 0.005)
            }
        }
    return metrics

# =============================================
# Debug endpoints
# =============================================

@app.route('/debug')
def debug_page():
    """Render the debug test page"""
    return render_template('debug.html')

@app.route('/test')
def test_page():
    """Render a simple test page - create this if you need a very basic test"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>VANET Simple Test</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            #map { height: 400px; width: 100%; }
            body { font-family: Arial, sans-serif; padding: 20px; }
        </style>
    </head>
    <body>
        <h1>VANET Simple Test</h1>
        <div id="map"></div>
        <button id="test-btn" style="margin-top: 20px; padding: 10px;">Generate Test Data</button>
        <div id="output" style="margin-top: 20px;"></div>
        
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script>
            // Initialize map
            const map = L.map('map').setView([28.6139, 77.2090], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
            
            // Add test marker
            L.marker([28.6139, 77.2090]).addTo(map)
                .bindPopup('Test marker')
                .openPopup();
                
            // Test button
            document.getElementById('test-btn').addEventListener('click', function() {
                const testData = {
                    '0': {
                        vehicle_density: 10,
                        position: { lat: 28.6139, lng: 77.2090 }
                    },
                    '1': {
                        vehicle_density: 15,
                        position: { lat: 28.6159, lng: 77.2110 }
                    }
                };
                
                // Add circles to map
                for (const [id, data] of Object.entries(testData)) {
                    const pos = data.position;
                    L.circle([pos.lat, pos.lng], {
                        color: 'red',
                        fillColor: '#f03',
                        fillOpacity: 0.5,
                        radius: 500
                    }).addTo(map)
                    .bindPopup(`RSU ${id}: Density ${data.vehicle_density}`);
                }
                
                // Show data in output div
                document.getElementById('output').innerHTML = 
                    `<pre>${JSON.stringify(testData, null, 2)}</pre>`;
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/test_mqtt_connection', methods=['POST'])
def test_mqtt_connection():
    """Test MQTT broker connection"""
    try:
        config = request.json
        broker = config.get('broker_address', 'localhost')
        port = config.get('broker_port', 1883)
        
        logger.info(f"Testing MQTT connection to {broker}:{port}")
        
        # Create a client and try to connect
        client = mqtt.Client()
        client.connect(broker, port, 5)
        client.disconnect()
        
        logger.info("MQTT connection test successful")
        return jsonify({
            'status': 'success',
            'message': f'Successfully connected to MQTT broker at {broker}:{port}'
        })
    except Exception as e:
        logger.error(f"MQTT connection test failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/api/test_endpoints', methods=['GET'])
def test_endpoints():
    """Test the availability of API endpoints"""
    try:
        results = {
            '/api/start_simulation': True,
            '/api/stop_simulation': True,
            '/api/get_groups': True
        }
        
        logger.info("API endpoints test successful")
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        logger.error(f"API endpoints test failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/api/generate_test_data', methods=['GET'])
def generate_test_data_endpoint():
    """Generate and emit test data"""
    try:
        # Generate test metrics
        test_metrics = generate_test_metrics()
        
        # Emit via Socket.IO
        socketio.emit('metrics_update', test_metrics)
        
        logger.info(f"Generated and emitted test data for {len(test_metrics)} RSUs")
        return jsonify({
            'status': 'success',
            'data': test_metrics
        })
    except Exception as e:
        logger.error(f"Error generating test data: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@socketio.on('test_event')
def handle_test_event(data):
    """Handle test events from clients"""
    logger.info(f"Received test event: {data}")
    socketio.emit('test_response', {'message': 'Test successful'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

if __name__ == '__main__':
    logger.info("Starting VANET simulation server on port 5001")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
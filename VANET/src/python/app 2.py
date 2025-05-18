from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from .metrics_collector import MetricsCollector
from .dynamic_group import DynamicGroupManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
    template_folder='../web/templates',
    static_folder='../web/static'
)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize components
metrics_collector = None
group_manager = DynamicGroupManager()

def metrics_callback(rsu_id: str, metrics: dict):
    """Callback for handling metrics updates."""
    try:
        # Process metrics and emit updates via WebSocket
        socketio.emit('metrics_update', {
            rsu_id: {
                'vehicle_density': metrics.get('vehicle_density', 0),
                'avg_link_loss': metrics.get('avg_link_loss', 0),
                'degree_centrality': metrics.get('degree_centrality', 0),
                'latitude': metrics.get('latitude', 0),
                'longitude': metrics.get('longitude', 0)
            }
        })
    except Exception as e:
        logger.error(f"Error in metrics callback: {str(e)}")

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/simulation')
def simulation():
    """Render the simulation page."""
    return render_template('simulation.html')

@app.route('/api/start_simulation', methods=['POST'])
def start_simulation():
    """Start the simulation with the given configuration."""
    try:
        config = request.json
        global metrics_collector
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(
            broker_address=config.get('broker_address', 'localhost'),
            broker_port=config.get('broker_port', 1883)
        )
        
        # Register callback and connect
        metrics_collector.register_callback(metrics_callback)
        if not metrics_collector.connect():
            return jsonify({'status': 'error', 'message': 'Failed to connect to MQTT broker'})
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stop_simulation', methods=['POST'])
def stop_simulation():
    """Stop the simulation."""
    try:
        global metrics_collector
        if metrics_collector:
            metrics_collector.disconnect()
            metrics_collector = None
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/get_groups', methods=['GET'])
def get_groups():
    if not metrics_collector:
        return jsonify({'error': 'No active simulation'})
    
    groups = group_manager.form_groups(metrics_collector.metrics)
    return jsonify(groups)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001) 
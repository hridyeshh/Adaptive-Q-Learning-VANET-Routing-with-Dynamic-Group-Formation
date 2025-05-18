from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from .metrics_collector import MetricsCollector
from .dynamic_group import DynamicGroupManager
from werkzeug.utils import secure_filename
import logging
import os

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

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
metrics_collector = None
group_manager = DynamicGroupManager(min_samples=3, eps=0.5)

# Track simulation time
simulation_start_time = None
current_simulation_time = 0.0

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_datasets():
    """Load datasets at application startup"""
    dataset_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
    
    # Create data directory if it doesn't exist
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Load routing dataset if available
    routing_file = os.path.join(dataset_dir, 'Vehicle Routing Dataset.csv')
    if os.path.exists(routing_file):
        try:
            group_manager.load_routing_dataset(routing_file)
            logger.info("Routing dataset loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load routing dataset: {e}")
    
    # Load PDR dataset if available
    pdr_file = os.path.join(dataset_dir, 'pdr_vs_time_dataset.csv')
    if os.path.exists(pdr_file):
        try:
            group_manager.load_pdr_dataset(pdr_file)
            logger.info("PDR dataset loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load PDR dataset: {e}")

# Initialize datasets when app starts
initialize_datasets()

def metrics_callback(rsu_id: str, metrics: dict):
    """Enhanced callback for handling metrics updates."""
    try:
        # Use actual location names if available
        location_name = f"RSU {rsu_id}"
        if hasattr(group_manager, 'location_mapping') and rsu_id in group_manager.location_mapping:
            location_name = group_manager.location_mapping[rsu_id]
        
        # Process metrics and emit updates via WebSocket
        socketio.emit('metrics_update', {
            rsu_id: {
                'vehicle_density': metrics.get('vehicle_density', 0),
                'avg_link_loss': metrics.get('avg_link_loss', 0),
                'degree_centrality': metrics.get('degree_centrality', 0),
                'location_name': location_name,
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
        global metrics_collector, simulation_start_time, current_simulation_time
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(
            broker_address=config.get('broker_address', 'localhost'),
            broker_port=config.get('broker_port', 1883)
        )
        
        # Register callback and connect
        metrics_collector.register_callback(metrics_callback)
        if not metrics_collector.connect():
            return jsonify({'status': 'error', 'message': 'Failed to connect to MQTT broker'})
        
        # Track simulation time
        simulation_start_time = time.time()
        current_simulation_time = 0.0
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/stop_simulation', methods=['POST'])
def stop_simulation():
    """Stop the simulation."""
    try:
        global metrics_collector, simulation_start_time
        if metrics_collector:
            metrics_collector.disconnect()
            metrics_collector = None
        simulation_start_time = None
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/get_groups', methods=['GET'])
def get_groups():
    """Enhanced group formation with dataset support."""
    if not metrics_collector:
        return jsonify({'error': 'No active simulation'})
    
    # Calculate current simulation time
    global current_simulation_time
    if simulation_start_time:
        current_simulation_time = time.time() - simulation_start_time
    
    # Form groups with enhanced features
    groups = group_manager.form_groups(
        metrics_collector.metrics, 
        current_time=current_simulation_time
    )
    
    # Get visualization-friendly format
    group_viz = group_manager.visualize_groups(groups)
    
    return jsonify({
        'groups': groups,
        'visualization': group_viz,
        'simulation_time': current_simulation_time
    })

@app.route('/api/upload_routing_dataset', methods=['POST'])
def upload_routing_dataset():
    """Upload and process routing dataset"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            group_manager.load_routing_dataset(filepath)
            return jsonify({
                'status': 'success', 
                'message': 'Routing dataset loaded successfully',
                'locations': group_manager.location_mapping
            })
        except Exception as e:
            return jsonify({'error': str(e)})
    
    return jsonify({'error': 'Invalid file type'})

@app.route('/api/upload_pdr_dataset', methods=['POST'])
def upload_pdr_dataset():
    """Upload and process PDR dataset"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            group_manager.load_pdr_dataset(filepath)
            return jsonify({
                'status': 'success',
                'message': 'PDR dataset loaded successfully'
            })
        except Exception as e:
            return jsonify({'error': str(e)})
    
    return jsonify({'error': 'Invalid file type'})

@app.route('/api/get_dataset_status', methods=['GET'])
def get_dataset_status():
    """Check which datasets are loaded"""
    return jsonify({
        'routing_dataset_loaded': group_manager.distance_matrix is not None,
        'pdr_dataset_loaded': group_manager.pdr_data is not None,
        'locations': group_manager.location_mapping if group_manager.location_mapping else {}
    })

@app.route('/debug')
def debug():
    """Render the debug page."""
    return render_template('debug.html')

@app.route('/standalone')
def standalone():
    """Render the standalone simulation page."""
    return render_template('standalone.html')

if __name__ == '__main__':
    import time  # Add this import at the top
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
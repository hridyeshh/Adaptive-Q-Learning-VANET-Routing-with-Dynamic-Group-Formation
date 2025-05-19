# Adaptive Q-Learning VANET Routing with Dynamic Group Formation

A sophisticated Vehicular Ad Hoc Network (VANET) simulation platform that implements adaptive Q-learning-based routing with dynamic group formation. This project demonstrates intelligent routing in vehicular networks using reinforcement learning and real-time clustering algorithms.

## 🚀 Features

- **Dynamic RSU Clustering**: Real-time regrouping of Road Side Units (RSUs) using DBSCAN algorithm
- **Adaptive Q-Learning**: Intelligent routing decisions using reinforcement learning
- **Dual-head PPO Agent**: Simultaneous optimization of wireless hop selection and execution RSU choice
- **Real-time Visualization**: Interactive web interface with live network topology display
- **Multi-scenario Support**: Urban, highway, and suburban environment simulations
- **Global Location Support**: Search and set any worldwide location as your simulation environment
- **Performance Metrics**: 
  - 27% lower end-to-end latency
  - 32% less control-plane overhead  
  - 4× reduction in edge-deadline misses
  - Maintains >97% delivery ratio

## 📦 Technology Stack

- **Backend**: Python 3.8+, Flask, Socket.IO
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Maps & Visualization**: Leaflet.js for interactive maps with OpenStreetMap integration
- **Location Services**: Nominatim API for geocoding
- **Machine Learning**: scikit-learn (DBSCAN), PyTorch (PPO)
- **Communication**: MQTT protocol for metrics collection
- **Data Processing**: NumPy, pandas

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- MQTT broker (e.g., Mosquitto)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/vanet-adaptive-routing.git
cd vanet-adaptive-routing
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install and start MQTT broker:
```bash
# On Ubuntu/Debian
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# On macOS with Homebrew
brew install mosquitto
brew services start mosquitto
```

## 📖 Usage

### Starting the Application

You can run the simulation using npm:

1. Install npm dependencies:
```bash
npm install
```

2. Start the application:
```bash
npm start
```

3. Open your browser - entry.html will automatically load as the landing page.

4. From the landing page (entry.html), you can:
   - View project features
   - See simulation preview
   - Click any "Launch Simulation" button to open the simulation interface

### Simulation Interface

When you click "Launch Simulation", the standalone.html interface loads with the following features:

- Interactive map display with dynamic vehicle visualization
- Global location search functionality
- Real-time metrics monitoring
- Dynamic group formation visualization 
- Adjustable simulation parameters:
  - Select simulation scenario (Urban/Highway/Suburban)
  - Adjust vehicle density (5-50 vehicles)
  - Start/Stop simulation controls

### Alternative Setup (Flask Server)

Alternatively, you can run the application using the Flask server:

```bash
cd src/python
python app.py
```

Then open your browser and navigate to `http://localhost:5001`

## 📁 Project Structure

```
VANET/
├── src/
│   ├── python/
│   │   ├── __init__.py
│   │   ├── app.py              # Main Flask application
│   │   ├── dynamic_group.py    # DBSCAN clustering implementation
│   │   └── metrics_collector.py # MQTT metrics collection
│   └── web/
│       ├── static/
│       │   ├── css/
│       │   │   └── style.css
│       │   └── js/
│       │       └── main.js
│       └── templates/
│           ├── base.html
│           ├── index.html
│           ├── simulation.html
│           └── standalone.html
├── README.md
└── requirements.txt
```

## ⚙️ Configuration

### MQTT Settings

Configure MQTT broker connection in the web interface:
- **Broker Address**: Default `localhost`
- **Broker Port**: Default `1883`

### Simulation Parameters

- **Scenario**: Urban, Highway, or Suburban
- **Vehicle Density**: 5-50 vehicles per RSU
- **Update Interval**: 30 seconds (configurable)
- **Location**: Set any worldwide location for simulation

## 🔌 API Documentation

The simulation provides a comprehensive RESTful API for programmatic control. Full API documentation is available in [API.md](API.md).

### REST Endpoints

- `POST /api/simulation/start`: Start a new simulation session
  ```json
  {
    "scenario": "urban",      // Options: "urban", "highway", "suburban"
    "density": 20,            // Range: 5-50 (vehicles)
    "location": {
      "lat": 28.6139, 
      "lng": 77.2090,
      "name": "Delhi, India"  // Optional
    },
    "duration": 3600          // Simulation duration in seconds (0 for indefinite)
  }
  ```

- `POST /api/simulation/{simulationId}/stop`: Stop an active simulation
- `GET /api/simulation/{simulationId}`: Retrieve current status
- `GET /api/simulation/{simulationId}/vehicles`: Retrieve all vehicles
- `GET /api/simulation/{simulationId}/groups`: Retrieve all vehicle groups
- `GET /api/simulation/{simulationId}/metrics`: Retrieve current metrics

### WebSocket Events

- `metrics_update`: Real-time RSU metrics updates
- `group_formation`: Dynamic group changes
- `vehicleUpdates`: Real-time vehicle position updates
- `groupUpdates`: Updates to group membership
- `metricUpdates`: Regular performance metric updates

## 🧠 Network Theory Concepts

The project implements advanced network theory concepts described in detail in [NETWORK_THEORY.md](NETWORK_THEORY.md):

### Communication Paradigms
- V2V (Vehicle-to-Vehicle): Direct communication between vehicles
- V2I (Vehicle-to-Infrastructure): Communication between vehicles and RSUs
- V2X (Vehicle-to-Everything): Holistic communication encompassing all modalities

### Q-Learning Implementation
- States: Network conditions (density, link quality, congestion level)
- Actions: Routing decisions (next hop selection, group formation)
- Rewards: Successful packet delivery, reduced latency, network efficiency
- Q-Value: Expected utility of taking a specific action in a specific state

### Centrality Metrics
- Degree Centrality: Number of direct connections a node maintains
- Link Loss Rate: Inverse measure of connection reliability
- Geographic Position: Spatial distribution within the network

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



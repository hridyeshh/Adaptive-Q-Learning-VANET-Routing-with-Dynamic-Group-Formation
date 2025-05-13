# Adaptive-Q-Learning-VANET-Routing-with-Dynamic-Group-Formation


A sophisticated Vehicular Ad Hoc Network (VANET) simulation platform that implements adaptive Q-learning-based routing with dynamic group formation. This project demonstrates intelligent routing in vehicular networks using reinforcement learning and real-time clustering algorithms.

## 🚀 Features

- **Dynamic RSU Clustering**: Real-time regrouping of Road Side Units (RSUs) using DBSCAN algorithm
- **Adaptive Q-Learning**: Intelligent routing decisions using reinforcement learning
- **Dual-head PPO Agent**: Simultaneous optimization of wireless hop selection and execution RSU choice
- **Real-time Visualization**: Interactive web interface with live network topology display
- **Multi-scenario Support**: Urban, highway, and suburban environment simulations
- **Performance Metrics**: 
  - 27% lower end-to-end latency
  - 32% less control-plane overhead  
  - 4× reduction in edge-deadline misses
  - Maintains >97% delivery ratio

## 📦 Technology Stack

- **Backend**: Python 3.8+, Flask, Socket.IO
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Visualization**: Leaflet.js for interactive maps
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

1. Start the Flask web server:
```bash
cd src/python
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5001
```

3. Configure simulation parameters:
   - Select simulation scenario (Urban/Highway/Suburban)
   - Set MQTT broker address and port
   - Adjust vehicle density
   - Click "Start Simulation"

### Standalone Mode

For testing without MQTT broker:
```
http://localhost:5001/standalone.html
```

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

## 🔌 API Documentation

### REST Endpoints

- `POST /api/start_simulation`: Start the simulation
  ```json
  {
    "broker_address": "localhost",
    "broker_port": 1883,
    "scenario": "urban"
  }
  ```

- `POST /api/stop_simulation`: Stop the simulation

- `GET /api/get_groups`: Retrieve current RSU groups

### WebSocket Events

- `metrics_update`: Real-time RSU metrics updates
- `group_formation`: Dynamic group changes

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📚 Based on

This work is based on the research paper:
> "Adaptive HQGR-Plus: A Hierarchical Reinforcement Learning Framework for Compute-Aware VANET Routing with Dynamic Group Formation"

## 🙏 Acknowledgments

- Dr. Poonam Rani (Supervisor)
- Ms. Monika Yadav (Co-supervisor)
- Department of Computer Science & Engineering, NSUT
- OpenStreetMap contributors for map data


## 👥 Authors

- **Hridyesh Kumar** - 2021UCM2346
- **Sumit Rawat** - 2021UCM2370  
- **Mridul Singla** - 2021UCM2830

Netaji Subhas University of Technology, Delhi

---

⭐ Star this repository if you find it helpful!

# Adaptive Q-Learning VANET Routing with Dynamic Group Formation

A comprehensive simulation platform for vehicular ad-hoc networks (VANETs) implementing adaptive Q-Learning routing algorithms with dynamic vehicle group formation capabilities.

![VANET Simulation](/api/placeholder/800/400)

## Features

- **Multiple Simulation Environments**: Urban, highway, and suburban scenarios with different traffic patterns
- **Dynamic Group Formation**: Autonomous formation of vehicle groups based on proximity and network conditions
- **Adaptive Q-Learning Algorithm**: Reinforcement learning approach that optimizes routing decisions in real-time
- **Interactive Visualization**: Real-time visualization of network topology and metrics
- **Customizable Parameters**: Adjust vehicle density, location, and Q-Learning parameters
- **Comprehensive API**: RESTful and WebSocket APIs for programmatic interaction
- **Standalone Mode**: Run simulations without external dependencies
- **Metrics Analysis**: Monitor link loss, centrality, and group stability in real-time

## Installation

### Prerequisites

- Python 3.8 or higher
- Flask and Flask-SocketIO
- MQTT broker (optional, for distributed mode)
- Modern web browser

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/hridyeshh/Adaptive-Q-Learning-VANET-Routing-with-Dynamic-Group-Formation.git
   cd Adaptive-Q-Learning-VANET-Routing-with-Dynamic-Group-Formation
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Set up MQTT broker:
   ```bash
   # Install Mosquitto MQTT broker
   # On Ubuntu/Debian:
   sudo apt-get install mosquitto
   # On macOS:
   brew install mosquitto
   # On Windows: Download from https://mosquitto.org/download/
   ```

## Usage

### Running the Simulation

1. Start the server:
   ```bash
   python run.py
   ```

2. Access the web interface:
   - Open your browser and navigate to `http://localhost:5001`
   - The main portal page will be displayed with options to launch different simulation modes

3. Launch the simulation:
   - Click on "Launch Simulation" from the portal
   - Configure simulation parameters:
     - Select scenario (urban, highway, suburban)
     - Adjust vehicle density
     - Set location (worldwide support)
   - Click "Start Simulation" to begin

### Simulation Modes

- **Full Mode**: Requires MQTT broker, provides distributed simulation capabilities
- **Standalone Mode**: Self-contained simulation that runs entirely in the browser

## Project Structure

```
.
├── API.md                 # API documentation
├── NETWORK_THEORY.md      # Theoretical background
├── app.py                 # Flask application entry point
├── run.py                 # Development server runner
├── src/
│   ├── simulation/        # Simulation core logic
│   │   ├── metrics_collector.py  # Collects network metrics
│   │   └── dynamic_group.py      # Group formation algorithms
│   └── web/               # Web interface
│       ├── static/        # CSS, JS, and static assets
│       └── templates/     # HTML templates
│           ├── entry.html       # Portal landing page
│           ├── simulation.html  # Main simulation interface
│           ├── standalone.html  # Standalone simulation
│           └── debug.html       # Debug interface
├── data/                  # Dataset files
└── uploads/               # User-uploaded files
```

## Technical Details

The simulation implements several key components:

1. **Q-Learning Algorithm**: Model-free reinforcement learning that adapts to changing network conditions
   ```
   Q(s,a) = Q(s,a) + α[R + γ·max Q(s',a') - Q(s,a)]
   ```
   Where:
   - α is the learning rate
   - γ is the discount factor
   - R is the reward
   - s and a are the current state and action
   - s' and a' are the next state and potential actions

2. **Dynamic Group Formation**: Uses distance-based clustering to form vehicle groups with:
   - Euclidean distance calculations
   - Adaptive proximity thresholds
   - Environment-specific parameters

3. **Network Metrics**: Tracks key performance indicators:
   - Vehicle Density: Number of vehicles per unit area
   - Link Loss Rate: Percentage of failed transmissions
   - Degree Centrality: Connection count per node
   - Group Stability: Duration of group configuration

## API Reference

The simulation provides a comprehensive RESTful API and WebSocket interface. For detailed documentation, see [API.md](API.md).

### Key Endpoints

```
POST /api/simulation/start     # Start a new simulation
POST /api/simulation/{id}/stop # Stop an active simulation
GET  /api/simulation/{id}      # Get simulation status
GET  /api/simulation/{id}/metrics # Get current metrics
```

### WebSocket Events

```
vehicleUpdates  # Real-time vehicle position updates
groupUpdates    # Group formation changes
metricUpdates   # Performance metrics updates
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Hridyesh - [hridyesh2309@gmail.com](mailto:hridyesh2309@gmail.com)

GitHub: [https://github.com/hridyeshh](https://github.com/hridyeshh)  
LinkedIn: [https://www.linkedin.com/in/hridyeshh/](https://www.linkedin.com/in/hridyeshh/)  
Twitter: [https://x.com/hridyeshhh](https://x.com/hridyeshhh)

Project Link: [https://github.com/hridyeshh/Adaptive-Q-Learning-VANET-Routing-with-Dynamic-Group-Formation](https://github.com/hridyeshh/Adaptive-Q-Learning-VANET-Routing-with-Dynamic-Group-Formation)

---

*Last updated: May 18, 2025*

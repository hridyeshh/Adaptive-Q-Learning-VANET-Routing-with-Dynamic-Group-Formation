const express = require('express');
const path = require('path');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');

// Simulation data store (would use a proper database in production)
const simulations = new Map();
const apiKeys = new Map([
  ['test_key_123', { type: 'standard', owner: 'test_user' }],
  ['premium_key_456', { type: 'premium', owner: 'premium_user' }]
]);

// Initialize Express app
const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Middleware
app.use(express.json());
app.use(cors());

// API versioning prefix
const API_VERSION = 'v1';
const API_BASE = `/api/${API_VERSION}`;

// Rate limiting middleware
const standardLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 60, // 60 requests per minute
  standardHeaders: true,
  keyGenerator: (req) => req.get('Authorization')?.split(' ')[1] || req.ip,
  handler: (req, res) => {
    res.status(429).json({
      error: {
        code: 'rate_limit_exceeded',
        message: 'API request rate limit exceeded',
        details: {
          limit: 60,
          reset: new Date(Date.now() + 60 * 1000)
        }
      }
    });
  }
});

const premiumLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 1000, // 1000 requests per minute
  standardHeaders: true,
  keyGenerator: (req) => req.get('Authorization')?.split(' ')[1] || req.ip
});

// Authentication middleware
const authenticateAPI = (req, res, next) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: {
        code: 'unauthorized',
        message: 'Authentication required. Please provide a valid API key.'
      }
    });
  }

  const apiKey = authHeader.split(' ')[1];
  const keyInfo = apiKeys.get(apiKey);

  if (!keyInfo) {
    return res.status(401).json({
      error: {
        code: 'unauthorized',
        message: 'Invalid API key.'
      }
    });
  }

  // Store key info for rate limiting decisions
  req.keyInfo = keyInfo;
  next();
};

// Apply appropriate rate limiter based on API key type
const applyRateLimit = (req, res, next) => {
  if (req.keyInfo && req.keyInfo.type === 'premium') {
    return premiumLimiter(req, res, next);
  }
  return standardLimiter(req, res, next);
};

// Simulation validation middleware
const validateSimulation = (req, res, next) => {
  const simulationId = req.params.simulationId;
  if (!simulationId || !simulations.has(simulationId)) {
    return res.status(404).json({
      error: {
        code: 'not_found',
        message: 'Simulation not found',
        details: { simulationId }
      }
    });
  }
  
  req.simulation = simulations.get(simulationId);
  next();
};

// Serve static files
app.use(express.static(path.join(__dirname, 'src/web/templates')));
app.use('/api/placeholder', express.static(path.join(__dirname, 'api/placeholder')));

// Web routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'src/web/templates/entry.html'));
});

app.get('/simulation', (req, res) => {
    res.sendFile(path.join(__dirname, 'src/web/templates/standalone.html'));
});

// API Routes
// Apply authentication to all API routes
app.use(API_BASE, authenticateAPI, applyRateLimit);

// Start Simulation
app.post(`${API_BASE}/simulation/start`, (req, res) => {
  try {
    const { scenario, density, location, duration } = req.body;
    
    // Validate parameters
    if (!scenario || !['urban', 'highway', 'suburban'].includes(scenario)) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid scenario. Must be one of: urban, highway, suburban.',
          details: { parameter: 'scenario', provided: scenario }
        }
      });
    }
    
    if (!density || density < 5 || density > 50) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid vehicle density. Value must be between 5 and 50.',
          details: { parameter: 'density', provided: density, allowedRange: [5, 50] }
        }
      });
    }
    
    if (!location || !location.lat || !location.lng) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid location. Must provide latitude and longitude.',
          details: { parameter: 'location' }
        }
      });
    }
    
    // Create new simulation
    const simulationId = `sim_${uuidv4().substring(0, 10)}`;
    const startTime = new Date().toISOString();
    
    const simulation = {
      simulationId,
      status: 'running',
      startTime,
      scenario,
      density,
      location,
      duration: duration || 0,
      vehicles: generateVehicles(density, location),
      groups: [],
      metrics: {
        vehicleDensity: { current: density, history: [] },
        linkLoss: { current: 0.15, history: [] },
        centrality: { current: 0.7, history: [] },
        groupCount: { current: 0, history: [] }
      },
      qLearning: {
        learningRate: 0.1,
        discountFactor: 0.9,
        explorationRate: 0.2,
        stateSpace: ["vehicleDensity", "linkLoss", "centrality"],
        actionSpace: ["joinGroup", "leaveGroup", "formGroup", "chooseNextHop"],
        rewardFunction: "combinedMetric",
        convergenceMetric: 0.85
      },
      connections: new Map(),
      owner: req.keyInfo.owner
    };
    
    simulations.set(simulationId, simulation);
    
    // Start simulation update interval
    startSimulationUpdates(simulationId);
    
    res.status(201).json({
      simulationId,
      status: 'running',
      startTime
    });
  } catch (error) {
    console.error('Error starting simulation:', error);
    res.status(500).json({
      error: {
        code: 'internal_error',
        message: 'An internal error occurred while starting the simulation.'
      }
    });
  }
});

// Get Simulation Status
app.get(`${API_BASE}/simulation/:simulationId`, validateSimulation, (req, res) => {
  const { simulation } = req;
  const elapsed = Math.floor((new Date() - new Date(simulation.startTime)) / 1000);
  
  res.json({
    simulationId: simulation.simulationId,
    status: simulation.status,
    scenario: simulation.scenario,
    elapsed,
    vehicleCount: simulation.vehicles.length,
    groupCount: simulation.groups.length
  });
});

// Stop Simulation
app.post(`${API_BASE}/simulation/:simulationId/stop`, validateSimulation, (req, res) => {
  const { simulation } = req;
  
  if (simulation.status !== 'running') {
    return res.status(400).json({
      error: {
        code: 'simulation_not_running',
        message: 'The simulation is not running and cannot be stopped.',
        details: { simulationId: simulation.simulationId, status: simulation.status }
      }
    });
  }
  
  simulation.status = 'stopped';
  simulation.endTime = new Date().toISOString();
  simulation.duration = Math.floor((new Date(simulation.endTime) - new Date(simulation.startTime)) / 1000);
  
  // Calculate final metrics
  const avgVehicleDensity = simulation.metrics.vehicleDensity.history.reduce((sum, val) => sum + val, 0) / 
                            (simulation.metrics.vehicleDensity.history.length || 1);
  
  const avgLinkLoss = simulation.metrics.linkLoss.history.reduce((sum, val) => sum + val, 0) / 
                      (simulation.metrics.linkLoss.history.length || 1);
  
  res.json({
    simulationId: simulation.simulationId,
    status: 'stopped',
    duration: simulation.duration,
    metrics: {
      avgVehicleDensity: parseFloat(avgVehicleDensity.toFixed(2)) || simulation.density,
      avgLinkLoss: parseFloat(avgLinkLoss.toFixed(2)) || 0.15,
      groupsFormed: simulation.groups.length
    }
  });
});

// Get Vehicles
app.get(`${API_BASE}/simulation/:simulationId/vehicles`, validateSimulation, (req, res) => {
  const { simulation } = req;
  const limit = parseInt(req.query.limit) || 100;
  const offset = parseInt(req.query.offset) || 0;
  
  const vehicles = simulation.vehicles.slice(offset, offset + limit).map(vehicle => ({
    id: vehicle.id,
    position: vehicle.position,
    speed: vehicle.speed,
    direction: vehicle.direction,
    groupId: vehicle.groupId,
    density: vehicle.density,
    linkLoss: vehicle.linkLoss,
    centrality: vehicle.centrality
  }));
  
  res.json({
    count: simulation.vehicles.length,
    vehicles
  });
});

// Get Vehicle Details
app.get(`${API_BASE}/simulation/:simulationId/vehicles/:vehicleId`, validateSimulation, (req, res) => {
  const { simulation } = req;
  const { vehicleId } = req.params;
  
  const vehicle = simulation.vehicles.find(v => v.id === vehicleId);
  if (!vehicle) {
    return res.status(404).json({
      error: {
        code: 'not_found',
        message: 'Vehicle not found',
        details: { vehicleId }
      }
    });
  }
  
  const connections = Array.from(simulation.connections.get(vehicleId) || []).map(connId => {
    const connectedVehicle = simulation.vehicles.find(v => v.id === connId);
    return {
      vehicleId: connId,
      linkQuality: calculateLinkQuality(vehicle, connectedVehicle),
      distance: calculateDistance(
        vehicle.position.lat,
        vehicle.position.lng,
        connectedVehicle.position.lat,
        connectedVehicle.position.lng
      )
    };
  });
  
  res.json({
    id: vehicle.id,
    position: vehicle.position,
    speed: vehicle.speed,
    direction: vehicle.direction,
    groupId: vehicle.groupId,
    connections,
    metrics: {
      linkLoss: vehicle.linkLoss,
      centrality: vehicle.centrality,
      qValue: vehicle.qValue || 0.72
    },
    history: {
      path: vehicle.path || []
    }
  });
});

// Get Groups
app.get(`${API_BASE}/simulation/:simulationId/groups`, validateSimulation, (req, res) => {
  const { simulation } = req;
  
  const groups = simulation.groups.map(group => ({
    id: group.id,
    size: group.members.length,
    centroid: group.centroid,
    leaderId: group.leaderId,
    members: group.members,
    formationTime: group.formationTime,
    stability: group.stability
  }));
  
  res.json({
    count: groups.length,
    groups
  });
});

// Get Metrics
app.get(`${API_BASE}/simulation/:simulationId/metrics`, validateSimulation, (req, res) => {
  const { simulation } = req;
  const timeframe = parseInt(req.query.timeframe) || 60;
  const interval = parseInt(req.query.interval) || 1;
  
  res.json({
    simulationId: simulation.simulationId,
    timestamp: new Date().toISOString(),
    timeframeSeconds: timeframe,
    intervalSeconds: interval,
    metrics: {
      vehicleDensity: {
        current: simulation.metrics.vehicleDensity.current,
        average: average(simulation.metrics.vehicleDensity.history),
        history: simulation.metrics.vehicleDensity.history.slice(-timeframe)
      },
      linkLoss: {
        current: simulation.metrics.linkLoss.current,
        average: average(simulation.metrics.linkLoss.history),
        history: simulation.metrics.linkLoss.history.slice(-timeframe)
      },
      centrality: {
        current: simulation.metrics.centrality.current,
        average: average(simulation.metrics.centrality.history),
        history: simulation.metrics.centrality.history.slice(-timeframe)
      },
      groupFormation: {
        current: simulation.metrics.groupCount.current,
        average: average(simulation.metrics.groupCount.history),
        history: simulation.metrics.groupCount.history.slice(-timeframe)
      }
    }
  });
});

// Update Simulation Parameters
app.patch(`${API_BASE}/simulation/:simulationId`, validateSimulation, (req, res) => {
  const { simulation } = req;
  const { density, scenario } = req.body;
  const updated = [];
  
  if (simulation.status !== 'running') {
    return res.status(400).json({
      error: {
        code: 'simulation_not_running',
        message: 'Cannot update parameters of a non-running simulation.'
      }
    });
  }
  
  if (density !== undefined) {
    if (density < 5 || density > 50) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid vehicle density. Value must be between 5 and 50.',
          details: { parameter: 'density', provided: density, allowedRange: [5, 50] }
        }
      });
    }
    simulation.density = density;
    updated.push('density');
  }
  
  if (scenario !== undefined) {
    if (!['urban', 'highway', 'suburban'].includes(scenario)) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid scenario. Must be one of: urban, highway, suburban.',
          details: { parameter: 'scenario', provided: scenario }
        }
      });
    }
    simulation.scenario = scenario;
    updated.push('scenario');
  }
  
  res.json({
    simulationId: simulation.simulationId,
    status: simulation.status,
    updated,
    currentSettings: {
      scenario: simulation.scenario,
      density: simulation.density,
      location: simulation.location
    }
  });
});

// Get Available Locations
app.get(`${API_BASE}/locations`, (req, res) => {
  res.json({
    locations: [
      {
        name: "Delhi, India",
        lat: 28.6139,
        lng: 77.2090,
        type: "urban"
      },
      {
        name: "Interstate 80, Nevada, USA",
        lat: 40.7128,
        lng: -119.0059,
        type: "highway"
      }
    ]
  });
});

// Get Q-Learning Configuration
app.get(`${API_BASE}/simulation/:simulationId/qlearning`, validateSimulation, (req, res) => {
  const { simulation } = req;
  res.json(simulation.qLearning);
});

// Update Q-Learning Parameters
app.patch(`${API_BASE}/simulation/:simulationId/qlearning`, validateSimulation, (req, res) => {
  const { simulation } = req;
  const { learningRate, explorationRate } = req.body;
  const updated = [];
  
  if (simulation.status !== 'running') {
    return res.status(400).json({
      error: {
        code: 'simulation_not_running',
        message: 'Cannot update parameters of a non-running simulation.'
      }
    });
  }
  
  if (learningRate !== undefined) {
    if (learningRate < 0 || learningRate > 1) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid learning rate. Value must be between 0 and 1.',
          details: { parameter: 'learningRate', provided: learningRate, allowedRange: [0, 1] }
        }
      });
    }
    simulation.qLearning.learningRate = learningRate;
    updated.push('learningRate');
  }
  
  if (explorationRate !== undefined) {
    if (explorationRate < 0 || explorationRate > 1) {
      return res.status(400).json({
        error: {
          code: 'invalid_parameter',
          message: 'Invalid exploration rate. Value must be between 0 and 1.',
          details: { parameter: 'explorationRate', provided: explorationRate, allowedRange: [0, 1] }
        }
      });
    }
    simulation.qLearning.explorationRate = explorationRate;
    updated.push('explorationRate');
  }
  
  res.json({
    updated,
    current: {
      learningRate: simulation.qLearning.learningRate,
      discountFactor: simulation.qLearning.discountFactor,
      explorationRate: simulation.qLearning.explorationRate,
      convergenceMetric: simulation.qLearning.convergenceMetric
    }
  });
});

// WebSocket connection handler
wss.on('connection', (ws, req) => {
  const simulationId = req.url.split('/').pop();
  const simulation = simulations.get(simulationId);
  
  if (!simulation) {
    ws.close(1008, 'Simulation not found');
    return;
  }
  
  // Add this connection to the simulation's connections
  if (!simulation.wsConnections) {
    simulation.wsConnections = new Set();
  }
  simulation.wsConnections.add(ws);
  
  ws.on('close', () => {
    simulation.wsConnections.delete(ws);
  });
});

// Helper functions
function generateVehicles(count, location) {
  const vehicles = [];
  for (let i = 0; i < count; i++) {
    vehicles.push({
      id: `v_${uuidv4().substring(0, 6)}`,
      position: {
        lat: location.lat + (Math.random() - 0.5) * 0.01,
        lng: location.lng + (Math.random() - 0.5) * 0.01
      },
      speed: Math.floor(Math.random() * 60) + 20, // 20-80 km/h
      direction: Math.floor(Math.random() * 360), // 0-359 degrees
      groupId: null,
      density: Math.random() * 0.5 + 0.5, // 0.5-1.0
      linkLoss: Math.random() * 0.2, // 0-0.2
      centrality: Math.random() * 0.5 + 0.5, // 0.5-1.0
      path: []
    });
  }
  return vehicles;
}

function generateDummyHistory(currentValue, count) {
  return Array(count).fill(0).map(() => currentValue + (Math.random() - 0.5) * 0.1);
}

function average(arr) {
  return arr.length ? arr.reduce((sum, val) => sum + val, 0) / arr.length : 0;
}

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371e3; // Earth's radius in meters
  const φ1 = lat1 * Math.PI/180;
  const φ2 = lat2 * Math.PI/180;
  const Δφ = (lat2-lat1) * Math.PI/180;
  const Δλ = (lon2-lon1) * Math.PI/180;

  const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
          Math.cos(φ1) * Math.cos(φ2) *
          Math.sin(Δλ/2) * Math.sin(Δλ/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

  return R * c; // Distance in meters
}

function calculateLinkQuality(vehicle1, vehicle2) {
  const distance = calculateDistance(
    vehicle1.position.lat,
    vehicle1.position.lng,
    vehicle2.position.lat,
    vehicle2.position.lng
  );
  // Simple model: quality decreases with distance
  return Math.max(0, 1 - (distance / 1000)); // 1km range
}

function startSimulationUpdates(simulationId) {
  const simulation = simulations.get(simulationId);
  if (!simulation) return;
  
  // Update simulation state every second
  simulation.updateInterval = setInterval(() => {
    if (simulation.status !== 'running') {
      clearInterval(simulation.updateInterval);
      return;
    }
    
    // Update vehicle positions and metrics
    simulation.vehicles.forEach(vehicle => {
      // Update position based on speed and direction
      const speedInDegrees = vehicle.speed / 111000; // Convert km/h to degrees per second
      vehicle.position.lat += speedInDegrees * Math.cos(vehicle.direction * Math.PI/180);
      vehicle.position.lng += speedInDegrees * Math.sin(vehicle.direction * Math.PI/180);
      
      // Add to path history
      vehicle.path.push({
        lat: vehicle.position.lat,
        lng: vehicle.position.lng,
        timestamp: new Date().toISOString()
      });
      
      // Keep only last 100 points
      if (vehicle.path.length > 100) {
        vehicle.path.shift();
      }
    });
    
    // Update metrics
    simulation.metrics.vehicleDensity.history.push(simulation.vehicles.length);
    simulation.metrics.linkLoss.history.push(average(simulation.vehicles.map(v => v.linkLoss)));
    simulation.metrics.centrality.history.push(average(simulation.vehicles.map(v => v.centrality)));
    simulation.metrics.groupCount.history.push(simulation.groups.length);
    
    // Keep only last 60 points
    ['vehicleDensity', 'linkLoss', 'centrality', 'groupCount'].forEach(metric => {
      if (simulation.metrics[metric].history.length > 60) {
        simulation.metrics[metric].history.shift();
      }
    });
    
    // Broadcast updates to WebSocket clients
    if (simulation.wsConnections) {
      const update = {
        type: 'metricUpdates',
        timestamp: new Date().toISOString(),
        metrics: {
          vehicleDensity: simulation.vehicles.length,
          linkLoss: average(simulation.vehicles.map(v => v.linkLoss)),
          centrality: average(simulation.vehicles.map(v => v.centrality)),
          groupCount: simulation.groups.length
        }
      };
      
      simulation.wsConnections.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify(update));
        }
      });
    }
  }, 1000);
}

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
}); 
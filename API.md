# VANET Simulation API Reference

## Overview

This document provides comprehensive details about the API endpoints available in the Adaptive Q-Learning VANET Routing Simulation. The API allows developers to programmatically interact with the simulation, retrieve data, and control simulation parameters.

## Base URL

For local development:
```
http://localhost:3000/api
```

## Authentication

API requests require authentication using API keys. Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

To obtain an API key, please contact the system administrator.

## Endpoints

### Simulation Control

#### Start Simulation

```
POST /api/simulation/start
```

Start a new simulation session.

**Request Body:**
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

**Response:**
```json
{
  "simulationId": "sim_12345abcde",
  "status": "running",
  "startTime": "2025-05-18T10:30:45Z"
}
```

#### Stop Simulation

```
POST /api/simulation/{simulationId}/stop
```

Stop an active simulation.

**Response:**
```json
{
  "simulationId": "sim_12345abcde",
  "status": "stopped",
  "duration": 1450,         // Actual duration in seconds
  "metrics": {
    "avgVehicleDensity": 22.5,
    "avgLinkLoss": 0.15,
    "groupsFormed": 8
  }
}
```

#### Get Simulation Status

```
GET /api/simulation/{simulationId}
```

Retrieve current status of a simulation.

**Response:**
```json
{
  "simulationId": "sim_12345abcde",
  "status": "running",
  "scenario": "urban",
  "elapsed": 1250,          // Seconds elapsed
  "vehicleCount": 23,
  "groupCount": 6
}
```

### Data Retrieval

#### Get Vehicles

```
GET /api/simulation/{simulationId}/vehicles
```

Retrieve all vehicles in the current simulation.

**Query Parameters:**
- `limit` (optional): Maximum number of vehicles to return (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "count": 23,
  "vehicles": [
    {
      "id": "v_123456",
      "position": {
        "lat": 28.6154,
        "lng": 77.2090
      },
      "speed": 45,           // km/h
      "direction": 270,      // degrees
      "groupId": "g_abc123", // null if not in a group
      "density": 15,
      "linkLoss": 0.12,
      "centrality": 0.85
    }
  ]
}
```

#### Get Vehicle Details

```
GET /api/simulation/{simulationId}/vehicles/{vehicleId}
```

Retrieve detailed information about a specific vehicle.

**Response:**
```json
{
  "id": "v_123456",
  "position": {
    "lat": 28.6154,
    "lng": 77.2090
  },
  "speed": 45,
  "direction": 270,
  "groupId": "g_abc123",
  "connections": [
    {
      "vehicleId": "v_234567",
      "linkQuality": 0.95,
      "distance": 120       // meters
    }
  ],
  "metrics": {
    "linkLoss": 0.12,
    "centrality": 0.85,
    "qValue": 0.72
  }
}
```

#### Get Groups

```
GET /api/simulation/{simulationId}/groups
```

Retrieve all vehicle groups in the current simulation.

**Response:**
```json
{
  "count": 6,
  "groups": [
    {
      "id": "g_abc123",
      "size": 4,
      "centroid": {
        "lat": 28.6155,
        "lng": 77.2095
      },
      "leaderId": "v_123456",
      "members": ["v_123456", "v_234567", "v_345678", "v_456789"],
      "formationTime": "2025-05-18T10:32:15Z",
      "stability": 0.85     // 0-1 scale
    }
  ]
}
```

#### Get Metrics

```
GET /api/simulation/{simulationId}/metrics
```

Retrieve current metrics for the simulation.

**Query Parameters:**
- `timeframe` (optional): Data points to return (default: 60)
- `interval` (optional): Interval between data points in seconds (default: 1)

**Response:**
```json
{
  "simulationId": "sim_12345abcde",
  "timestamp": "2025-05-18T10:35:45Z",
  "timeframeSeconds": 60,
  "intervalSeconds": 1,
  "metrics": {
    "vehicleDensity": {
      "current": 23,
      "average": 22.5,
      "history": [21, 21, 22, 22, 23, 23, 23]
    },
    "linkLoss": {
      "current": 0.15,
      "average": 0.16,
      "history": [0.17, 0.16, 0.16, 0.15, 0.15]
    },
    "centrality": {
      "current": 0.72,
      "average": 0.70,
      "history": [0.68, 0.69, 0.70, 0.71, 0.72]
    },
    "groupFormation": {
      "current": 6,
      "average": 5.8,
      "history": [5, 5, 6, 6, 6, 6]
    }
  }
}
```

### Configuration

#### Update Simulation Parameters

```
PATCH /api/simulation/{simulationId}
```

Update parameters of a running simulation.

**Request Body:**
```json
{
  "density": 30,            // New vehicle density
  "scenario": "highway"     // New scenario type
}
```

**Response:**
```json
{
  "simulationId": "sim_12345abcde",
  "status": "running",
  "updated": ["density", "scenario"],
  "currentSettings": {
    "scenario": "highway",
    "density": 30,
    "location": {
      "lat": 28.6139,
      "lng": 77.2090,
      "name": "Delhi, India"
    }
  }
}
```

#### Get Available Locations

```
GET /api/locations
```

Retrieve a list of predefined locations for simulations.

**Response:**
```json
{
  "locations": [
    {
      "name": "Delhi, India",
      "lat": 28.6139,
      "lng": 77.2090,
      "type": "urban"
    },
    {
      "name": "Interstate 80, Nevada, USA",
      "lat": 40.7128,
      "lng": -119.0059,
      "type": "highway"
    }
  ]
}
```

### Q-Learning Parameters

#### Get Q-Learning Configuration

```
GET /api/simulation/{simulationId}/qlearning
```

Retrieve current Q-Learning algorithm parameters.

**Response:**
```json
{
  "learningRate": 0.1,
  "discountFactor": 0.9,
  "explorationRate": 0.2,
  "stateSpace": ["vehicleDensity", "linkLoss", "centrality"],
  "actionSpace": ["joinGroup", "leaveGroup", "formGroup", "chooseNextHop"],
  "rewardFunction": "combinedMetric",
  "convergenceMetric": 0.85
}
```

#### Update Q-Learning Parameters

```
PATCH /api/simulation/{simulationId}/qlearning
```

Update Q-Learning algorithm parameters.

**Request Body:**
```json
{
  "learningRate": 0.15,
  "explorationRate": 0.1
}
```

**Response:**
```json
{
  "updated": ["learningRate", "explorationRate"],
  "current": {
    "learningRate": 0.15,
    "discountFactor": 0.9,
    "explorationRate": 0.1,
    "convergenceMetric": 0.85
  }
}
```

## WebSocket API

Real-time updates are available via WebSocket connection:

```
ws://localhost:3000/api/simulation/{simulationId}/live
```

### Message Types

#### Vehicle Updates

```json
{
  "type": "vehicleUpdates",
  "timestamp": "2025-05-18T10:36:45Z",
  "vehicles": [
    {
      "id": "v_123456",
      "position": {"lat": 28.6160, "lng": 77.2095},
      "speed": 47,
      "groupId": "g_abc123"
    }
  ]
}
```

#### Group Updates

```json
{
  "type": "groupUpdates",
  "timestamp": "2025-05-18T10:36:50Z",
  "groups": [
    {
      "id": "g_abc123",
      "size": 5,
      "members": ["v_123456", "v_234567", "v_345678", "v_456789", "v_567890"],
      "stability": 0.75
    }
  ]
}
```

#### Metric Updates

```json
{
  "type": "metricUpdates",
  "timestamp": "2025-05-18T10:36:55Z",
  "metrics": {
    "vehicleDensity": 24,
    "linkLoss": 0.14,
    "centrality": 0.73,
    "groupCount": 6
  }
}
```

## Error Handling

### Error Response Format

All API errors return a JSON response with the following structure:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "Invalid vehicle density. Value must be between 5 and 50.",
    "details": {
      "parameter": "density",
      "provided": 60,
      "allowedRange": [5, 50]
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_parameter` | 400 | A request parameter is invalid |
| `not_found` | 404 | The requested resource was not found |
| `simulation_not_running` | 400 | The requested simulation is not running |
| `unauthorized` | 401 | Authentication failed or insufficient permissions |
| `rate_limit_exceeded` | 429 | API request rate limit exceeded |
| `internal_error` | 500 | Internal server error |

## Rate Limits

API requests are subject to rate limiting:

- 60 requests per minute for standard API keys
- 1000 requests per minute for premium API keys

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1621345678
```

## Versioning

The API version is included in the base URL path (e.g., `/api/v1/`). When new incompatible changes are introduced, the version number will be incremented.

## Support

For API support and questions, please contact:
- Email: hridyesh2309@gmail.com
- GitHub Issues: [Create an issue](https://github.com/hridyeshh/Adaptive-Q-Learning-VANET-Routing-with-Dynamic-Group-Formation/issues)

---

*This documentation is subject to change as new features are added. Last updated: May 18, 2025* 
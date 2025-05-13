// Global variables for map markers and layers
let map = null;
let rsuMarkers = {};
let groupLayers = {};
let rsuCircles = {};
let isMapInitialized = false;

// Initialize functionality when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM Content Loaded");
    
    // Only attempt to initialize the map if we're on the simulation page
    const mapElement = document.getElementById('map');
    if (mapElement) {
        console.log("Map element found, initializing map");
        // We'll initialize the map in simulation.html
        // This is just a backup in case the inline script doesn't run
        if (!isMapInitialized) {
            initializeMap();
        }
    }
});

// Function to initialize the map (as a backup)
function initializeMap() {
    console.log("Initializing map from main.js");
    try {
        const mapElement = document.getElementById('map');
        if (!mapElement) {
            console.error("Map element not found");
            return;
        }
        
        // Ensure the map has proper dimensions
        mapElement.style.height = '600px';
        mapElement.style.width = '100%';
        
        // Create the map
        map = L.map('map').setView([28.6139, 77.2090], 13); // Delhi coordinates
        
        // Add the tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Add a test marker to ensure the map is working
        L.marker([28.6139, 77.2090])
            .addTo(map)
            .bindPopup('Map initialized successfully!')
            .openPopup();
            
        console.log("Map initialized successfully");
        isMapInitialized = true;
        
        // Force a resize after a delay to handle any rendering issues
        setTimeout(() => {
            if (map) {
                map.invalidateSize(true);
            }
        }, 500);
    } catch (error) {
        console.error("Error initializing map:", error);
    }
}

// Function to update the map with RSU data
function updateMap(metrics) {
    console.log("Updating map with metrics:", metrics);
    
    // Ensure the map exists
    if (!map || !isMapInitialized) {
        console.warn("Map not initialized yet, initializing now");
        initializeMap();
    }
    
    try {
        // Update RSU positions and metrics on the map
        for (const [rsu_id, data] of Object.entries(metrics)) {
            // Extract position data or use a default if not available
            const position = data.position || { 
                lat: 28.6139 + (Math.random() - 0.5) * 0.05, 
                lng: 77.2090 + (Math.random() - 0.5) * 0.05 
            };
            
            // Create a color based on vehicle density
            const density = data.vehicle_density || 0;
            let color = "#4C9AFF"; // Default blue
            if (density > 20) {
                color = "#FF5630"; // Red for high density
            } else if (density > 10) {
                color = "#FFAB00"; // Yellow for medium density
            } else {
                color = "#36B37E"; // Green for low density
            }
            
            // Create or update circle for RSU coverage
            if (rsuCircles[rsu_id]) {
                // Update existing circle
                rsuCircles[rsu_id].setLatLng([position.lat, position.lng]);
                rsuCircles[rsu_id].setStyle({
                    color: color,
                    fillColor: color
                });
                
                // Update popup content
                rsuCircles[rsu_id].setPopupContent(createPopupContent(rsu_id, data));
            } else {
                // Create new circle
                const circle = L.circle([position.lat, position.lng], {
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.3,
                    radius: 100 + (density * 10) // Size based on vehicle density
                }).addTo(map);
                
                circle.bindPopup(createPopupContent(rsu_id, data));
                rsuCircles[rsu_id] = circle;
            }
        }
        
        // Update map view to fit all RSUs if we have new data
        if (Object.keys(rsuCircles).length > 0) {
            const markers = Object.values(rsuCircles);
            const group = L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
        
    } catch (error) {
        console.error("Error updating map:", error);
    }
}

// Function to create popup content for RSU
function createPopupContent(rsu_id, data) {
    return `
        <div class="rsu-popup">
            <h6>RSU ${rsu_id}</h6>
            <table class="table table-sm">
                <tr>
                    <td>Vehicle Density:</td>
                    <td><strong>${data.vehicle_density || 'N/A'}</strong></td>
                </tr>
                <tr>
                    <td>Link Loss:</td>
                    <td>${data.avg_link_loss ? (data.avg_link_loss * 100).toFixed(1) + '%' : 'N/A'}</td>
                </tr>
                <tr>
                    <td>Centrality:</td>
                    <td>${data.degree_centrality ? data.degree_centrality.toFixed(2) : 'N/A'}</td>
                </tr>
            </table>
        </div>
    `;
}

// Function to update metrics display
function updateMetrics(metrics) {
    const container = document.getElementById('metrics-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (Object.keys(metrics).length === 0) {
        container.innerHTML = '<p class="text-muted">No metrics available yet.</p>';
        return;
    }
    
    for (const [rsu_id, data] of Object.entries(metrics)) {
        const metricDiv = document.createElement('div');
        metricDiv.className = 'metric-item';
        
        // Determine status class based on density
        let statusClass = 'bg-success';
        if (data.vehicle_density > 20) {
            statusClass = 'bg-danger';
        } else if (data.vehicle_density > 10) {
            statusClass = 'bg-warning';
        }
        
        metricDiv.innerHTML = `
            <h6 class="d-flex justify-content-between">
                RSU ${rsu_id}
                <span class="badge ${statusClass}">${data.vehicle_density}</span>
            </h6>
            <p>Link Loss: ${(data.avg_link_loss * 100).toFixed(1)}%</p>
            <p>Centrality: ${data.degree_centrality.toFixed(2)}</p>
        `;
        
        container.appendChild(metricDiv);
    }
}

// Function to show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(notification, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}
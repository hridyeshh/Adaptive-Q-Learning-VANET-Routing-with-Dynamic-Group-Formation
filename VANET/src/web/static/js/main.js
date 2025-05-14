// Global variables for map markers
let rsuMarkers = {};
let groupLayers = {};

// Initialize the map when the page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('map')) {
        initializeMap();
    }
});

function initializeMap() {
    // Map initialization is now in simulation.html
}

function updateMap(metrics) {
    if (!window.map) return;

    // Clear existing markers
    Object.values(rsuMarkers).forEach(marker => marker.remove());
    rsuMarkers = {};

    // Add new markers for each RSU
    for (const [rsu_id, data] of Object.entries(metrics)) {
        if (data.latitude && data.longitude) {
            const marker = L.marker([data.latitude, data.longitude])
                .bindPopup(`RSU ${rsu_id}<br>Density: ${data.vehicle_density}`);
            marker.addTo(map);
            rsuMarkers[rsu_id] = marker;
        }
    }
} 
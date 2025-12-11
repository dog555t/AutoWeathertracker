// In-Car AQI Monitor - JavaScript

// Configuration
const UPDATE_INTERVAL = 5000; // Update every 5 seconds
const CHART_MAX_POINTS = 60; // Show last 60 minutes

// Chart instance
let aqiChart = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('AQI Monitor initialized');
    
    // Initialize chart
    initChart();
    
    // Start updating data
    updateData();
    setInterval(updateData, UPDATE_INTERVAL);
    
    // Update history chart less frequently
    updateHistory();
    setInterval(updateHistory, 60000); // Every minute
});

// Fetch and update current AQI data
async function updateData() {
    try {
        const response = await fetch('/api/current');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update connection status
        updateConnectionStatus(true);
        
        // Update UI with new data
        updateAQIDisplay(data);
        updatePMValues(data);
        updateInfoSections(data);
        updateTimestamp(data.timestamp);
        
    } catch (error) {
        console.error('Error fetching data:', error);
        updateConnectionStatus(false);
    }
}

// Update the main AQI display
function updateAQIDisplay(data) {
    const aqiValue = document.getElementById('aqi-value');
    const aqiCategory = document.getElementById('aqi-category');
    const aqiDisplay = document.getElementById('aqi-display');
    
    // Update values
    aqiValue.textContent = data.aqi || '--';
    aqiCategory.textContent = data.category || 'Unknown';
    
    // Update background color based on AQI
    aqiDisplay.className = 'aqi-display ' + getAQIClass(data.aqi);
}

// Update PM values
function updatePMValues(data) {
    const pm25Value = document.getElementById('pm25-value');
    const pm10Value = document.getElementById('pm10-value');
    
    pm25Value.textContent = data.pm25 !== undefined ? `${data.pm25} µg/m³` : '-- µg/m³';
    // Note: API returns 'pm100' which represents PM10 particles (10µm diameter)
    pm10Value.textContent = data.pm100 !== undefined ? `${data.pm100} µg/m³` : '-- µg/m³';
}

// Update description and recommendation
function updateInfoSections(data) {
    const description = document.getElementById('description');
    const recommendation = document.getElementById('recommendation');
    
    description.textContent = data.description || 'No data available';
    recommendation.textContent = data.recommendation || 'No data available';
}

// Update timestamp
function updateTimestamp(timestamp) {
    const lastUpdate = document.getElementById('last-update');
    
    if (timestamp) {
        const date = new Date(timestamp);
        lastUpdate.textContent = `Last updated: ${date.toLocaleTimeString()}`;
    } else {
        lastUpdate.textContent = 'Waiting for data...';
    }
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusIndicator = document.getElementById('connection-status');
    const sensorStatus = document.getElementById('sensor-status');
    
    if (connected) {
        statusIndicator.classList.remove('disconnected');
        sensorStatus.textContent = 'Sensor: Active';
    } else {
        statusIndicator.classList.add('disconnected');
        sensorStatus.textContent = 'Sensor: Disconnected';
    }
}

// Get CSS class for AQI value
function getAQIClass(aqi) {
    if (aqi <= 50) return 'aqi-good';
    if (aqi <= 100) return 'aqi-moderate';
    if (aqi <= 150) return 'aqi-usg';
    if (aqi <= 200) return 'aqi-unhealthy';
    if (aqi <= 300) return 'aqi-very-unhealthy';
    return 'aqi-hazardous';
}

// Get color for AQI value
function getAQIColor(aqi) {
    if (aqi <= 50) return '#00E400';
    if (aqi <= 100) return '#FFFF00';
    if (aqi <= 150) return '#FF7E00';
    if (aqi <= 200) return '#FF0000';
    if (aqi <= 300) return '#8F3F97';
    return '#7E0023';
}

// Initialize Chart.js chart
function initChart() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not available, skipping chart initialization');
        return;
    }
    
    const ctx = document.getElementById('aqi-chart').getContext('2d');
    
    aqiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'AQI',
                data: [],
                borderColor: '#00E400',
                backgroundColor: 'rgba(0, 228, 0, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#ffffff',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            return `AQI: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#aaaaaa',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 300,
                    ticks: {
                        color: '#aaaaaa',
                        stepSize: 50
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

// Fetch and update history chart
async function updateHistory() {
    // Skip if Chart.js is not available
    if (!aqiChart) {
        console.warn('Chart not initialized, skipping history update');
        return;
    }
    
    try {
        const response = await fetch('/api/history?minutes=60');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        const data = result.data || [];
        
        // Prepare chart data
        const labels = [];
        const values = [];
        const colors = [];
        
        data.forEach(item => {
            const date = new Date(item.timestamp);
            labels.push(date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            values.push(item.aqi);
            colors.push(getAQIColor(item.aqi));
        });
        
        // Update chart
        if (aqiChart) {
            aqiChart.data.labels = labels;
            aqiChart.data.datasets[0].data = values;
            
            // Use the latest color for the line
            if (colors.length > 0) {
                aqiChart.data.datasets[0].borderColor = colors[colors.length - 1];
                aqiChart.data.datasets[0].backgroundColor = colors[colors.length - 1] + '20';
            }
            
            aqiChart.update();
        }
        
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

// Log any errors
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

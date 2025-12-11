#!/usr/bin/env python3
"""
Flask Web Application for AQI Dashboard

Provides a web interface to display real-time air quality data.
Runs on http://192.168.4.1:5000 when configured as WiFi access point.
"""

import os
import logging
from flask import Flask, render_template, jsonify
from sensor_reader import PMS5003Reader, SimulatedSensor
from aqi_calculator import AQICalculator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global sensor reader instance
sensor_reader = None


def init_sensor():
    """Initialize the sensor reader"""
    global sensor_reader
    
    if sensor_reader is None:
        try:
            # Try to use real PMS5003 sensor
            sensor_reader = PMS5003Reader(history_size=120)
            logger.info("Initialized PMS5003 sensor reader")
        except Exception as e:
            logger.warning(f"Could not initialize PMS5003 sensor: {e}")
            logger.info("Falling back to simulated sensor")
            sensor_reader = SimulatedSensor(history_size=120)
        
        # Start reading in background
        sensor_reader.start()
        logger.info("Sensor reader started")


@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')


@app.route('/api/current')
def get_current():
    """
    API endpoint to get current AQI reading
    
    Returns:
        JSON with current AQI, PM values, category, color, etc.
    """
    if sensor_reader is None:
        return jsonify({
            'error': 'Sensor not initialized'
        }), 500
    
    reading = sensor_reader.get_current_reading()
    
    if reading is None:
        return jsonify({
            'error': 'No sensor data available yet',
            'message': 'Please wait for first reading...'
        }), 503
    
    # Calculate AQI
    pm25 = reading.get('pm25', 0)
    pm100 = reading.get('pm100', 0)
    aqi_result = AQICalculator.calculate_aqi(pm25=pm25, pm10=pm100)
    
    # Build response
    response = {
        'timestamp': reading.get('timestamp'),
        'aqi': aqi_result['aqi'],
        'category': aqi_result['category'],
        'color': aqi_result['color'],
        'description': aqi_result['description'],
        'recommendation': AQICalculator.get_recommendation(aqi_result['aqi']),
        'pm25': pm25,
        'pm10': reading.get('pm10', 0),
        'pm100': pm100
    }
    
    return jsonify(response)


@app.route('/api/history')
def get_history():
    """
    API endpoint to get historical AQI data
    
    Query parameters:
        minutes: Number of minutes of history (default 60)
    
    Returns:
        JSON array of historical readings with AQI calculated
    """
    from flask import request
    
    if sensor_reader is None:
        return jsonify({
            'error': 'Sensor not initialized'
        }), 500
    
    minutes = request.args.get('minutes', default=60, type=int)
    history = sensor_reader.get_history(minutes=minutes)
    
    # Convert history to AQI values
    history_with_aqi = []
    for reading in history:
        pm25 = reading.get('pm25', 0)
        pm100 = reading.get('pm100', 0)
        aqi_result = AQICalculator.calculate_aqi(pm25=pm25, pm10=pm100)
        
        history_with_aqi.append({
            'timestamp': reading.get('timestamp'),
            'aqi': aqi_result['aqi'],
            'category': aqi_result['category'],
            'color': aqi_result['color'],
            'pm25': pm25,
            'pm100': pm100
        })
    
    return jsonify({
        'count': len(history_with_aqi),
        'data': history_with_aqi
    })


@app.route('/api/status')
def get_status():
    """
    API endpoint to get system status
    
    Returns:
        JSON with system information
    """
    import platform
    
    status = {
        'system': platform.system(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'sensor_active': sensor_reader is not None and sensor_reader.is_running,
        'sensor_type': sensor_reader.__class__.__name__ if sensor_reader else None
    }
    
    return jsonify(status)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


def main():
    """Run the Flask application"""
    # Initialize sensor
    init_sensor()
    
    # Get configuration from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask web server on {host}:{port}")
    logger.info(f"Dashboard will be available at http://{host}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if sensor_reader:
            sensor_reader.stop()
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")
        if sensor_reader:
            sensor_reader.stop()
        raise


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Sensor Reader Module for Air Quality Monitoring

This module handles reading data from particulate matter sensors.
Currently implements support for PMS5003/PMS7003 sensors over UART.
Can be extended to support other sensors (SDS011, I2C sensors, etc.)

Wiring for PMS5003/PMS7003 (UART):
- VCC -> 5V (Pin 2 or 4)
- GND -> GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
- TXD -> RXD (GPIO 15, Pin 10)
- RXD -> TXD (GPIO 14, Pin 8)

For I2C sensors, wire:
- VCC -> 3.3V or 5V (depending on sensor)
- GND -> GND
- SDA -> GPIO 2 (Pin 3)
- SCL -> GPIO 3 (Pin 5)

Note: Enable UART/I2C in raspi-config before use:
    sudo raspi-config
    -> Interface Options -> Serial Port (No to login shell, Yes to serial hardware)
    -> Interface Options -> I2C (Enable)
"""

import time
import json
import threading
from datetime import datetime
from collections import deque
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SensorReader:
    """Base class for air quality sensor readers"""
    
    def __init__(self, history_size=120):
        """
        Initialize the sensor reader
        
        Args:
            history_size: Number of readings to keep in history (default 120 = 2 hours at 1min intervals)
        """
        self.history = deque(maxlen=history_size)
        self.current_reading = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def read_sensor(self):
        """Override this method to read from specific sensor"""
        raise NotImplementedError("Subclasses must implement read_sensor()")
    
    def start(self):
        """Start continuous reading in background thread"""
        if self.is_running:
            logger.warning("Sensor reader already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()
        logger.info("Sensor reader started")
    
    def stop(self):
        """Stop the background reading thread"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Sensor reader stopped")
    
    def _read_loop(self):
        """Background loop for continuous sensor reading"""
        while self.is_running:
            try:
                reading = self.read_sensor()
                if reading:
                    with self.lock:
                        self.current_reading = reading
                        self.history.append(reading)
                    logger.debug(f"New reading: PM2.5={reading.get('pm25')}, PM10={reading.get('pm10')}")
            except Exception as e:
                logger.error(f"Error reading sensor: {e}")
            
            # Read every 60 seconds
            time.sleep(60)
    
    def get_current_reading(self):
        """Get the most recent sensor reading"""
        with self.lock:
            return self.current_reading.copy() if self.current_reading else None
    
    def get_history(self, minutes=60):
        """
        Get historical readings
        
        Args:
            minutes: Number of minutes of history to return
            
        Returns:
            List of readings
        """
        with self.lock:
            history_list = list(self.history)
        
        if minutes and len(history_list) > minutes:
            return history_list[-minutes:]
        return history_list


class PMS5003Reader(SensorReader):
    """Reader for PMS5003/PMS7003 particulate matter sensors over UART"""
    
    def __init__(self, port='/dev/serial0', baudrate=9600, history_size=120):
        """
        Initialize PMS5003 reader
        
        Args:
            port: Serial port (default /dev/serial0 for Raspberry Pi)
            baudrate: Baud rate (default 9600)
            history_size: Number of readings to keep in history
        """
        super().__init__(history_size)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self._initialize_serial()
    
    def _initialize_serial(self):
        """Initialize serial connection"""
        try:
            import serial
            self.serial = serial.Serial(self.port, self.baudrate, timeout=2)
            logger.info(f"Serial port {self.port} opened successfully")
        except ImportError:
            logger.error("pyserial not installed. Install with: pip3 install pyserial")
            self.serial = None
        except Exception as e:
            logger.error(f"Failed to open serial port {self.port}: {e}")
            self.serial = None
    
    def read_sensor(self):
        """
        Read data from PMS5003 sensor
        
        Returns:
            Dictionary with PM1.0, PM2.5, PM10 values in µg/m³
        """
        if not self.serial:
            # Simulate data for testing without actual hardware
            return self._simulate_reading()
        
        try:
            # Read until we find the start bytes (0x42, 0x4d)
            while True:
                byte1 = self.serial.read(1)
                if byte1 == b'\x42':
                    byte2 = self.serial.read(1)
                    if byte2 == b'\x4d':
                        break
            
            # Read the rest of the frame (30 bytes)
            data = self.serial.read(30)
            
            if len(data) < 30:
                logger.warning("Incomplete data frame")
                return None
            
            # Parse the data (use atmospheric environment values)
            pm10_std = (data[2] << 8) | data[3]
            pm25_std = (data[4] << 8) | data[5]
            pm100_std = (data[6] << 8) | data[7]
            
            pm10_env = (data[8] << 8) | data[9]
            pm25_env = (data[10] << 8) | data[11]
            pm100_env = (data[12] << 8) | data[13]
            
            return {
                'timestamp': datetime.now().isoformat(),
                'pm10': pm10_env,
                'pm25': pm25_env,
                'pm100': pm100_env,
                'pm10_std': pm10_std,
                'pm25_std': pm25_std,
                'pm100_std': pm100_std
            }
            
        except Exception as e:
            logger.error(f"Error reading PMS5003: {e}")
            return None
    
    def _simulate_reading(self):
        """Simulate sensor reading for testing without hardware"""
        import random
        
        # Simulate realistic PM values that vary over time
        base_pm25 = 25 + random.gauss(0, 10)
        base_pm10 = base_pm25 * 1.5 + random.gauss(0, 5)
        base_pm100 = base_pm10 * 1.2 + random.gauss(0, 8)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'pm10': max(0, int(base_pm10 * 0.3)),
            'pm25': max(0, int(base_pm25)),
            'pm100': max(0, int(base_pm100)),
            'pm10_std': max(0, int(base_pm10 * 0.3)),
            'pm25_std': max(0, int(base_pm25)),
            'pm100_std': max(0, int(base_pm100))
        }
    
    def close(self):
        """Close the serial connection"""
        if self.serial:
            self.serial.close()
            logger.info("Serial port closed")


class SimulatedSensor(SensorReader):
    """Simulated sensor for testing without hardware"""
    
    def read_sensor(self):
        """Generate simulated sensor readings"""
        import random
        
        # Simulate realistic varying PM values
        base_pm25 = 25 + random.gauss(0, 15)
        base_pm10 = base_pm25 * 1.5 + random.gauss(0, 8)
        base_pm100 = base_pm10 * 1.3 + random.gauss(0, 10)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'pm10': max(0, int(base_pm10 * 0.3)),
            'pm25': max(0, int(base_pm25)),
            'pm100': max(0, int(base_pm100))
        }


def main():
    """Test the sensor reader"""
    import sys
    
    # Try to use real sensor, fall back to simulated
    try:
        sensor = PMS5003Reader()
        logger.info("Using PMS5003 sensor reader")
    except:
        sensor = SimulatedSensor()
        logger.info("Using simulated sensor reader")
    
    sensor.start()
    
    try:
        while True:
            time.sleep(10)
            reading = sensor.get_current_reading()
            if reading:
                print(f"\nCurrent reading:")
                print(f"  PM2.5: {reading.get('pm25', 'N/A')} µg/m³")
                print(f"  PM10:  {reading.get('pm100', 'N/A')} µg/m³")
                print(f"  Time:  {reading.get('timestamp', 'N/A')}")
    except KeyboardInterrupt:
        print("\nStopping...")
        sensor.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()

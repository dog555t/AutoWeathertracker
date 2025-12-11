#!/bin/bash
# Installation script for In-Car AQI Monitor
# This script sets up all dependencies and services

set -e

echo "=========================================="
echo "In-Car AQI Monitor Installation"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Installation directory: $SCRIPT_DIR"
echo ""

# Check if running as root for some operations
if [ "$EUID" -eq 0 ]; then
    echo "Warning: Running as root. It's better to run as regular user and use sudo when needed."
    echo ""
fi

# Update system packages
echo "Step 1: Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
echo ""
echo "Step 2: Installing system dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv git

# Enable I2C and UART interfaces
echo ""
echo "Step 3: Enabling I2C and UART interfaces..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 1  # Disable serial console
sudo raspi-config nonint do_serial_hw 0  # Enable serial hardware

# Create Python virtual environment
echo ""
echo "Step 4: Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install Python packages
echo ""
echo "Step 5: Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install systemd service
echo ""
echo "Step 6: Installing systemd service..."
sudo cp services/aqi-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aqi-monitor.service
echo "Service installed and enabled"

# Setup WiFi Access Point (optional)
echo ""
echo "=========================================="
read -p "Do you want to set up WiFi Access Point? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    read -p "Enter WiFi SSID [CarAQI]: " AP_SSID
    AP_SSID=${AP_SSID:-CarAQI}
    
    read -p "Enter WiFi Password [caraqimonitor]: " AP_PASSWORD
    AP_PASSWORD=${AP_PASSWORD:-caraqimonitor}
    
    export AP_SSID
    export AP_PASSWORD
    
    sudo bash services/setup-wifi-ap.sh
    WIFI_SETUP=true
else
    echo "Skipping WiFi Access Point setup"
    echo "You can run it later with: sudo bash services/setup-wifi-ap.sh"
    WIFI_SETUP=false
fi

# Print completion message
echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "The AQI monitor service has been installed and will start automatically on boot."
echo ""
echo "To start the service now:"
echo "  sudo systemctl start aqi-monitor.service"
echo ""
echo "To view service status:"
echo "  sudo systemctl status aqi-monitor.service"
echo ""
echo "To view service logs:"
echo "  sudo journalctl -u aqi-monitor.service -f"
echo ""

if [ "$WIFI_SETUP" = true ]; then
    echo "WiFi Access Point has been configured."
    echo "After rebooting, you can connect to:"
    echo "  SSID: ${AP_SSID}"
    echo "  Password: ${AP_PASSWORD}"
    echo "  Dashboard: http://192.168.4.1:5000"
    echo ""
    echo "REBOOT REQUIRED: sudo reboot"
else
    echo "To access the dashboard:"
    echo "  Find your Pi's IP address with: hostname -I"
    echo "  Open browser to: http://[PI_IP]:5000"
    echo ""
    echo "REBOOT RECOMMENDED: sudo reboot"
fi

echo ""
echo "=========================================="

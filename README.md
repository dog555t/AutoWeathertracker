# 🚗 In-Car Air Quality (AQI) Monitor

An automatic air quality monitoring system for your car using a Raspberry Pi. This system continuously measures particulate matter (PM2.5/PM10) levels, calculates the Air Quality Index (AQI), and displays the data on a car-friendly web dashboard that works offline.

## 🌟 Features

- **Real-time Air Quality Monitoring**: Continuously reads PM2.5 and PM10 values from an air quality sensor
- **AQI Calculation**: Converts raw sensor data to standard US EPA Air Quality Index with color-coded levels
- **Car-Friendly Dashboard**: Large, easy-to-read display with color-coded status indicators
- **Historical Data**: View AQI trends over the last hour with an interactive chart
- **Auto-Refresh**: Dashboard updates automatically every 5 seconds without page reload
- **Offline Operation**: Runs entirely on local network with no internet required
- **WiFi Hotspot**: Pi creates its own WiFi access point for easy connection from phones/tablets
- **Auto-Start**: Everything starts automatically when the Pi boots up

## 📋 Requirements

### Hardware

1. **Raspberry Pi** (Model 3B+ or newer recommended)
   - Raspberry Pi 4 Model B (2GB+ RAM) ideal for best performance
   - Raspberry Pi 3B+ also works well
   - Raspberry Pi Zero 2 W can work but may be slower

2. **Air Quality Sensor** (Choose one):
   - **PMS5003** or **PMS7003** (Recommended, UART interface)
   - **SDS011** (Alternative, UART interface)
   - Any I2C particulate matter sensor (requires code adaptation)

3. **Power Supply**:
   - Official Raspberry Pi power supply (5V 3A for Pi 4, 5V 2.5A for Pi 3)
   - USB car charger with sufficient amperage
   - Alternative: 12V to 5V DC-DC converter wired to car power

4. **MicroSD Card**: 16GB or larger, Class 10 or better

5. **Optional**:
   - Case for Raspberry Pi
   - Mounting hardware for car installation

### Software

- Raspberry Pi OS (formerly Raspbian) - Lite or Desktop version
- Python 3.7 or newer (included in Raspberry Pi OS)

## 🔌 Sensor Wiring

### PMS5003 / PMS7003 (UART Connection)

The PMS5003/PMS7003 sensors use a UART serial connection. These sensors have 8 pins, but we only need 4:

```
PMS5003/7003    Raspberry Pi
Pin 1 (VCC)  →  Pin 2 or 4 (5V)
Pin 2 (GND)  →  Pin 6 (GND)
Pin 4 (RXD)  →  Pin 8 (GPIO 14, TXD)
Pin 5 (TXD)  →  Pin 10 (GPIO 15, RXD)
```

**Visual Reference**:
```
Raspberry Pi GPIO Header:
    3.3V  [1] [2]  5V    ← Connect VCC here
    GPIO2 [3] [4]  5V
    GPIO3 [5] [6]  GND   ← Connect GND here
    GPIO4 [7] [8]  GPIO14 (TXD) ← Connect sensor RXD here
    GND   [9] [10] GPIO15 (RXD) ← Connect sensor TXD here
    ...
```

**Important Notes**:
- Sensor VCC connects to Pi 5V power
- Sensor GND connects to Pi GND
- **Sensor RX connects to Pi TX** (GPIO 14, Pin 8)
- **Sensor TX connects to Pi RX** (GPIO 15, Pin 10)
- The sensor requires 5V power but uses 3.3V logic levels (safe for Pi)

### Alternative: I2C Sensor

If using an I2C-based air quality sensor:

```
Sensor      Raspberry Pi
VCC      →  Pin 1 (3.3V) or Pin 2 (5V)
GND      →  Pin 6 (GND)
SDA      →  Pin 3 (GPIO 2, SDA)
SCL      →  Pin 5 (GPIO 3, SCL)
```

You'll need to modify `sensor_reader.py` to read from I2C instead of UART.

## 🚀 Installation

### Quick Install (Recommended)

1. **Clone the repository**:
   ```bash
   cd ~
   git clone https://github.com/dog555t/AutoWeathertracker.git
   cd AutoWeathertracker
   ```

2. **Run the installation script**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

   The script will:
   - Update system packages
   - Install required dependencies
   - Enable I2C and UART interfaces
   - Create Python virtual environment
   - Install Python packages
   - Set up systemd service for auto-start
   - Optionally configure WiFi access point

3. **Reboot**:
   ```bash
   sudo reboot
   ```

### Manual Installation

If you prefer to install manually or need to customize:

1. **Update system and install dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   sudo apt-get install -y python3 python3-pip python3-venv git
   ```

2. **Enable UART interface**:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → Serial Port
   # "Would you like a login shell accessible over serial?" → No
   # "Would you like the serial port hardware to be enabled?" → Yes
   ```

3. **Enable I2C interface** (if using I2C sensor):
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → I2C → Enable
   ```

4. **Clone repository**:
   ```bash
   cd ~
   git clone https://github.com/dog555t/AutoWeathertracker.git
   cd AutoWeathertracker
   ```

5. **Set up Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Install systemd service**:
   ```bash
   sudo cp services/aqi-monitor.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable aqi-monitor.service
   sudo systemctl start aqi-monitor.service
   ```

7. **Set up WiFi Access Point** (optional):
   ```bash
   sudo bash services/setup-wifi-ap.sh
   ```

8. **Reboot**:
   ```bash
   sudo reboot
   ```

## 📱 WiFi Access Point Setup

To use the system in your car without existing WiFi:

1. **During installation**, choose to set up WiFi access point when prompted, or:

2. **Run the setup script manually**:
   ```bash
   sudo bash services/setup-wifi-ap.sh
   ```

3. **Default credentials**:
   - SSID: `CarAQI`
   - Password: `caraqimonitor`
   - IP Address: `192.168.4.1`

4. **Custom credentials** (optional):
   ```bash
   export AP_SSID="MyCarAQI"
   export AP_PASSWORD="mypassword123"
   sudo bash services/setup-wifi-ap.sh
   ```

5. **After reboot**:
   - Connect your phone/tablet to the `CarAQI` WiFi network
   - Open browser to: `http://192.168.4.1:5000`
   - Bookmark this page for easy access

## 🎯 Usage

### Accessing the Dashboard

**With WiFi Access Point**:
1. Connect to the Pi's WiFi network (default SSID: `CarAQI`)
2. Open browser to: `http://192.168.4.1:5000`

**Without WiFi Access Point** (using existing network):
1. Find Pi's IP address: `hostname -I`
2. Open browser to: `http://[PI_IP]:5000`

### Dashboard Features

The dashboard displays:
- **Large AQI Number**: Color-coded (green to red) for quick assessment
- **AQI Category**: Good, Moderate, Unhealthy, etc.
- **PM Values**: Real-time PM2.5 and PM10 measurements
- **Health Description**: What the current AQI level means
- **Recommendations**: Activity recommendations based on air quality
- **Historical Chart**: AQI trends over the last hour
- **Status Indicators**: Connection and sensor status

### Service Management

**Check service status**:
```bash
sudo systemctl status aqi-monitor.service
```

**View live logs**:
```bash
sudo journalctl -u aqi-monitor.service -f
```

**Restart service**:
```bash
sudo systemctl restart aqi-monitor.service
```

**Stop service**:
```bash
sudo systemctl stop aqi-monitor.service
```

**Disable auto-start**:
```bash
sudo systemctl disable aqi-monitor.service
```

## 🏗️ Project Structure

```
AutoWeathertracker/
├── sensor_reader.py          # Sensor reading and data collection
├── aqi_calculator.py          # AQI calculation logic
├── web_app.py                 # Flask web application
├── requirements.txt           # Python dependencies
├── install.sh                 # Installation script
├── README.md                  # This file
├── services/
│   ├── aqi-monitor.service    # Systemd service file
│   └── setup-wifi-ap.sh       # WiFi access point setup
├── templates/
│   └── index.html             # Web dashboard HTML
└── static/
    ├── style.css              # Dashboard styles
    └── app.js                 # Dashboard JavaScript
```

## 🔧 Customization

### Adjust Update Frequency

Edit `web_app.py` and modify the sensor reading interval:

```python
# Change from 60 seconds to desired interval
time.sleep(60)  # Sensor reading interval
```

Edit `static/app.js` to change dashboard update rate:

```javascript
const UPDATE_INTERVAL = 5000; // Milliseconds (5 seconds)
```

### Change WiFi Settings

Edit `services/setup-wifi-ap.sh` or set environment variables:

```bash
export AP_SSID="MyCustomSSID"
export AP_PASSWORD="MyCustomPassword"
sudo bash services/setup-wifi-ap.sh
```

### Change Web Server Port

Edit `services/aqi-monitor.service`:

```ini
Environment="FLASK_PORT=8080"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart aqi-monitor.service
```

## 🐛 Troubleshooting

### Sensor Not Reading

1. **Check wiring**: Ensure all connections are secure
2. **Check UART**: Run `ls -l /dev/serial0` - should exist
3. **Check permissions**: Run `sudo usermod -a -G dialout pi`
4. **Test sensor directly**:
   ```bash
   cd ~/AutoWeathertracker
   source venv/bin/activate
   python3 sensor_reader.py
   ```

### Dashboard Not Loading

1. **Check service status**:
   ```bash
   sudo systemctl status aqi-monitor.service
   ```

2. **Check logs for errors**:
   ```bash
   sudo journalctl -u aqi-monitor.service -n 50
   ```

3. **Verify Flask is running**:
   ```bash
   sudo netstat -tulpn | grep :5000
   ```

4. **Check firewall** (if enabled):
   ```bash
   sudo ufw allow 5000/tcp
   ```

### WiFi Access Point Not Working

1. **Check hostapd status**:
   ```bash
   sudo systemctl status hostapd
   ```

2. **Check dnsmasq status**:
   ```bash
   sudo systemctl status dnsmasq
   ```

3. **Verify wlan0 configuration**:
   ```bash
   ip addr show wlan0
   ```

4. **Check hostapd logs**:
   ```bash
   sudo journalctl -u hostapd -n 50
   ```

### No Data / Loading Forever

- **Wait 1-2 minutes** after service start for first reading
- Sensor readings are taken every 60 seconds by default
- Check sensor power and connections
- View logs for sensor errors

## 🔒 Security Notes

- The WiFi access point uses WPA2 encryption
- Change default password before deployment
- The web interface has no authentication (suitable for car use)
- No data is transmitted to external servers
- All data stays on the Pi

## 📊 Understanding AQI

| AQI Range | Category | Color | Health Impact |
|-----------|----------|-------|---------------|
| 0-50 | Good | Green | Air quality is satisfactory |
| 51-100 | Moderate | Yellow | Acceptable, some risk for sensitive people |
| 101-150 | Unhealthy for Sensitive Groups | Orange | Sensitive groups may experience effects |
| 151-200 | Unhealthy | Red | Everyone may experience health effects |
| 201-300 | Very Unhealthy | Purple | Health alert for everyone |
| 301-500 | Hazardous | Maroon | Emergency conditions |

## 🙏 Credits

- AQI calculation based on US EPA standards
- Dashboard uses Chart.js for data visualization
- Flask framework for web application

## 📝 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## ⚠️ Disclaimer

This device is for informational purposes only. For critical air quality decisions, use professionally calibrated equipment. Sensor accuracy may vary with environmental conditions and sensor age.
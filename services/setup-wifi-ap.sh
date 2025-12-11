#!/bin/bash
# Setup Raspberry Pi as WiFi Access Point
# This script configures the Pi to create a WiFi hotspot for in-car use

set -e

echo "=========================================="
echo "WiFi Access Point Setup Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Configuration variables
AP_SSID="${AP_SSID:-CarAQI}"
AP_PASSWORD="${AP_PASSWORD:-caraqimonitor}"
AP_IP="192.168.4.1"
DHCP_RANGE_START="192.168.4.2"
DHCP_RANGE_END="192.168.4.20"

echo "Installing required packages..."
apt-get update
apt-get install -y hostapd dnsmasq iptables

# Stop services while configuring
echo "Stopping services..."
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# Configure static IP for wlan0
echo "Configuring static IP for wlan0..."
cat > /etc/dhcpcd.conf.d/wlan0-ap.conf << EOF
interface wlan0
    static ip_address=${AP_IP}/24
    nohook wpa_supplicant
EOF

# Configure dnsmasq (DHCP and DNS server)
echo "Configuring dnsmasq..."
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
cat > /etc/dnsmasq.conf << EOF
interface=wlan0
dhcp-range=${DHCP_RANGE_START},${DHCP_RANGE_END},255.255.255.0,24h
domain=local
address=/aqi.local/${AP_IP}
EOF

# Configure hostapd (WiFi access point)
echo "Configuring hostapd..."
cat > /etc/hostapd/hostapd.conf << EOF
interface=wlan0
driver=nl80211
ssid=${AP_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${AP_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Point hostapd to our configuration
echo "Setting hostapd configuration path..."
if ! grep -q "DAEMON_CONF=" /etc/default/hostapd; then
    echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' >> /etc/default/hostapd
else
    sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
    sed -i 's|^DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
fi

# Unmask and enable services
echo "Enabling services..."
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

# Reboot required for changes to take effect
echo ""
echo "=========================================="
echo "WiFi Access Point Setup Complete!"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  SSID: ${AP_SSID}"
echo "  Password: ${AP_PASSWORD}"
echo "  IP Address: ${AP_IP}"
echo "  Dashboard URL: http://${AP_IP}:5000"
echo "  Also accessible at: http://aqi.local:5000"
echo ""
echo "IMPORTANT: Reboot required for changes to take effect"
echo "Run: sudo reboot"
echo ""

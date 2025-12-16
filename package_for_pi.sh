#!/bin/bash
# Pi2Printer Deployment Packaging Script
# Creates a clean deployment package for Raspberry Pi

set -e

PROJECT_NAME="pi2printer"
VERSION="1.0.0"
PACKAGE_NAME="${PROJECT_NAME}-${VERSION}"
DEPLOY_DIR="./deploy"
PACKAGE_DIR="${DEPLOY_DIR}/${PACKAGE_NAME}"

echo "🚀 Packaging Pi2Printer for Raspberry Pi Deployment"
echo "======================================================"

# Create deployment directory
echo "📁 Creating deployment package..."
rm -rf "${DEPLOY_DIR}"
mkdir -p "${PACKAGE_DIR}"

# Copy essential files
echo "📋 Copying core files..."
cp email_monitor.py "${PACKAGE_DIR}/"
cp pi2printer_cli.py "${PACKAGE_DIR}/"
cp printer_service.py "${PACKAGE_DIR}/"
cp database.py "${PACKAGE_DIR}/"
cp utils.py "${PACKAGE_DIR}/"
cp pi_config.py "${PACKAGE_DIR}/"
cp requirements.txt "${PACKAGE_DIR}/"
cp start_monitoring.sh "${PACKAGE_DIR}/"
cp test_bluetooth_printer.py "${PACKAGE_DIR}/"
cp DEPLOY_TO_PI.md "${PACKAGE_DIR}/"
cp README.md "${PACKAGE_DIR}/"

# Create .env template
echo "⚙️  Creating configuration templates..."
cat > "${PACKAGE_DIR}/.env.example" << EOF
# Pi2Printer Configuration
# Copy this to .env and fill in your values

# Gemini AI API Key (Required)
# Get from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Printer Configuration
# Uncomment and set if using specific printer connection

# For Bluetooth printer
# PRINTER_BLUETOOTH_ADDR=XX:XX:XX:XX:XX:XX

# For Serial printer  
# PRINTER_SERIAL_PORT=/dev/ttyUSB0

# For Network printer
# PRINTER_NETWORK_HOST=192.168.1.100
EOF

# Create Pi-specific startup script
echo "🔧 Creating Pi startup script..."
cat > "${PACKAGE_DIR}/setup_pi.sh" << 'EOF'
#!/bin/bash
# Pi2Printer Raspberry Pi Setup Script

set -e

echo "🥧 Setting up Pi2Printer on Raspberry Pi"
echo "========================================"

# Check if running on Pi
if ! grep -q "Raspberry Pi\|BCM" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3-pip git libcups2-dev libusb-1.0-0-dev

# Install Python packages
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Setup printer permissions
echo "🖨️  Setting up printer permissions..."
sudo usermod -a -G lp,dialout $USER

# Create udev rules for thermal printers
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", MODE="0666"' | sudo tee /etc/udev/rules.d/99-thermal-printer.rules > /dev/null
sudo udevadm control --reload-rules

# Setup environment
if [ ! -f .env ]; then
    echo "⚙️  Setting up environment file..."
    cp .env.example .env
    echo "❗ Please edit .env file and add your GEMINI_API_KEY"
fi

# Test configuration
echo "🧪 Testing configuration..."
python3 pi_config.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "2. Run: python3 -c \"from utils import setup_gmail_auth; setup_gmail_auth()\""
echo "3. Test with: python3 email_monitor.py --check-once"
echo "4. Start monitoring: ./start_monitoring.sh"
echo ""
echo "For auto-start setup, see DEPLOY_TO_PI.md"
EOF

chmod +x "${PACKAGE_DIR}/setup_pi.sh"

# Create systemd service template
echo "🖥️  Creating systemd service template..."
cat > "${PACKAGE_DIR}/pi2printer.service.template" << EOF
[Unit]
Description=Pi2Printer Email Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/pi2printer
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 email_monitor.py --interval 10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create deployment README
echo "📖 Creating deployment README..."
cat > "${PACKAGE_DIR}/QUICK_START.md" << 'EOF'
# Pi2Printer Quick Start Guide

## 🚀 **Rapid Deployment**

### **1. Setup (5 minutes)**
```bash
./setup_pi.sh
```

### **2. Configure APIs**
```bash
# Add your Gemini API key to .env
nano .env

# Setup Gmail authentication  
python3 -c "from utils import setup_gmail_auth; setup_gmail_auth()"
```

### **3. Test & Start**
```bash
# Test everything works
python3 email_monitor.py --check-once

# Start monitoring
./start_monitoring.sh
```

### **4. Auto-Start (Optional)**
```bash
# Copy service file
sudo cp pi2printer.service.template /etc/systemd/system/pi2printer.service

# Enable auto-start
sudo systemctl daemon-reload
sudo systemctl enable pi2printer.service
sudo systemctl start pi2printer.service
```

## 🎯 **That's it!** 
Your Mission Impossible email printer is ready! 🕵️‍♂️
EOF

# Create package archive
echo "📦 Creating deployment archive..."
cd "${DEPLOY_DIR}"
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}/"

# Create checksums
echo "🔐 Creating checksums..."
sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.sha256"

echo ""
echo "✅ Package created successfully!"
echo "📁 Location: ${DEPLOY_DIR}/${PACKAGE_NAME}.tar.gz"
echo "📊 Size: $(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "🚀 To deploy to Raspberry Pi:"
echo "1. Copy ${PACKAGE_NAME}.tar.gz to your Pi"
echo "2. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. Run: cd ${PACKAGE_NAME} && ./setup_pi.sh"
echo ""
echo "🎯 Happy Mission Impossible printing! 🕵️‍♂️"
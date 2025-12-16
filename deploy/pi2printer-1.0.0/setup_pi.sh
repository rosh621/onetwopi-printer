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

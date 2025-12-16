# Pi2Printer Raspberry Pi Deployment Guide

## 📋 **Prerequisites**

### **Hardware:**
- Raspberry Pi Zero 2W (or Pi 3/4)
- 58mm USB thermal printer (ESC/POS compatible)
- OR Bluetooth thermal printer
- MicroSD card (16GB+)
- Reliable power supply

### **Software Setup:**

#### **1. Raspberry Pi OS Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip git -y

# Install printer libraries
sudo apt install libcups2-dev libusb-1.0-0-dev -y
```

#### **2. Clone Pi2Printer**
```bash
cd ~
git clone <your-repo> pi2printer
cd pi2printer
```

#### **3. Install Python Dependencies**
```bash
# Install requirements
pip3 install -r requirements.txt

# Additional Pi-specific packages
pip3 install RPi.GPIO gpiozero  # For hardware integration (optional)
```

#### **4. Setup Printer Permissions**
```bash
# Add user to printer groups
sudo usermod -a -G lp,dialout $USER

# Create udev rules for thermal printer (if USB)
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", MODE="0666"' | sudo tee /etc/udev/rules.d/99-thermal-printer.rules
sudo udevadm control --reload-rules
```

#### **5. Configure APIs**
```bash
# Setup environment file
cp .env.example .env
nano .env
# Add your GEMINI_API_KEY

# Setup Gmail credentials
python3 -c "from utils import setup_gmail_auth; setup_gmail_auth()"
```

#### **6. Test System**
```bash
# Test APIs
python3 utils.py

# Test printer
python3 -c "from printer_service import PrinterService; PrinterService().get_printer_info()"

# Run single check
python3 email_monitor.py --check-once
```

## 🖨️ **Printer Configuration**

### **USB Thermal Printer:**
- Connect via USB
- Auto-detected by printer service
- No additional setup needed

### **Bluetooth Thermal Printer:**
```bash
# Pair Bluetooth printer
sudo bluetoothctl
> scan on
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX

# Update printer_service.py with Bluetooth MAC address
```

### **Test Printing:**
```bash
# List available missions
python3 pi2printer_cli.py list

# Print a mission
python3 pi2printer_cli.py print MI-XXXXXXXX
```

## 🚀 **Auto-Start Setup**

### **1. Create Systemd Service**
```bash
sudo nano /etc/systemd/system/pi2printer.service
```

### **2. Service Configuration:**
```ini
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
ExecStart=/usr/bin/python3 email_monitor.py --interval 5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **3. Enable Auto-Start**
```bash
sudo systemctl daemon-reload
sudo systemctl enable pi2printer.service
sudo systemctl start pi2printer.service

# Check status
sudo systemctl status pi2printer.service
```

## 🔧 **Pi-Specific Optimizations**

### **1. Reduce Resource Usage**
```bash
# In email_monitor.py, consider:
# - Longer intervals for battery saving (15-30 minutes)
# - Lower logging levels
# - Smaller email batch sizes
```

### **2. Handle Pi Restarts**
```bash
# Cron job for health checks
crontab -e

# Add line:
*/10 * * * * /usr/bin/systemctl is-active --quiet pi2printer.service || /usr/bin/systemctl restart pi2printer.service
```

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Printer Not Detected:**
```bash
# Check USB devices
lsusb

# Check printer permissions
ls -la /dev/usb/

# Test manual printer connection
python3 -c "
from escpos.printer import Usb
try:
    printer = Usb(0x04b8, 0x0202)  # Epson example
    printer.text('Test print\n')
    printer.cut()
    print('Printer works!')
except Exception as e:
    print(f'Printer error: {e}')
"
```

#### **Gmail API Issues:**
```bash
# Check network connectivity
ping -c 4 gmail.googleapis.com

# Re-authenticate
rm token.json
python3 -c "from utils import setup_gmail_auth; setup_gmail_auth()"
```

#### **Service Not Starting:**
```bash
# Check service logs
sudo journalctl -u pi2printer.service -f

# Check Python path
which python3
```

## 📊 **Monitoring**

### **Check System Status:**
```bash
# Service status
sudo systemctl status pi2printer.service

# View logs
sudo journalctl -u pi2printer.service --since "1 hour ago"

# Check recent missions
python3 pi2printer_cli.py status
```

### **Performance Monitoring:**
```bash
# CPU/Memory usage
top
htop

# Disk space
df -h

# Network usage
iftop
```

## 🔋 **Battery Optimization (Pi Zero)**

### **Power Saving Tips:**
1. **Reduce check frequency** to 15-30 minutes
2. **Disable unnecessary services** (Bluetooth if using USB)
3. **Use lightweight OS** (Pi OS Lite)
4. **Optimize GPU memory split** (minimum for headless)

```bash
# GPU memory split
sudo raspi-config
# Advanced Options > Memory Split > 16
```

## 🌐 **Remote Management**

### **SSH Access:**
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### **Remote Commands:**
```bash
# From your laptop, manage Pi remotely:
ssh pi@<pi-ip-address>

# Check missions remotely
ssh pi@<pi-ip-address> "cd pi2printer && python3 pi2printer_cli.py list"
```

---

## 🎯 **Final Checklist**

- [ ] Hardware connected and powered
- [ ] Python dependencies installed
- [ ] APIs configured (Gmail + Gemini)
- [ ] Printer detected and tested
- [ ] Service running and auto-starting
- [ ] Remote access configured
- [ ] First mission printed successfully

**Your Mission Impossible printer is ready for deployment! 🕵️‍♂️📧🖨️**
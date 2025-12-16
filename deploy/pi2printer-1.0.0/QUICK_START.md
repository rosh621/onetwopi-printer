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

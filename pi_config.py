#!/usr/bin/env python3
"""
Pi2Printer Raspberry Pi Configuration
Hardware-specific settings and printer configurations
"""

import os

# Raspberry Pi Detection
def is_raspberry_pi():
    """Detect if running on Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
    except FileNotFoundError:
        return False

# Hardware Configuration
PI_MODEL = os.environ.get('PI_MODEL', 'auto')  # 'zero', 'pi3', 'pi4', 'auto'
IS_PI = is_raspberry_pi()

# Printer Configuration for Pi
PRINTER_CONFIG = {
    # USB Printer (Primary)
    'usb': {
        'enabled': False,
        'vendor_id': None,  # Auto-detect
        'product_id': None,  # Auto-detect
    },
    
    # Bluetooth Printer
    'bluetooth': {
        'enabled': True,
        'address': '60:6E:41:15:4A:EE',  # Your printer's MAC address
        'port': '/dev/rfcomm0',  # Bluetooth serial port (fallback)
        'baudrate': 9600,
        'direct_socket': True,  # Use direct socket instead of serial
    },
    
    # Serial Printer (GPIO or USB-Serial)
    'serial': {
        'enabled': True,
        'port': '/dev/ttyUSB0',  # Or /dev/ttyAMA0, /dev/serial0
        'baudrate': 9600,
        'timeout': 1,
    },
    
    # Network Printer (WiFi thermal printers)
    'network': {
        'enabled': False,
        'host': None,  # IP address of network printer
        'port': 9100,  # Standard ESC/POS port
    }
}

# Performance Settings
PERFORMANCE_CONFIG = {
    'check_interval_minutes': 5 if not IS_PI else 10,  # Longer interval on Pi
    'max_emails_per_check': 20 if not IS_PI else 10,   # Fewer emails on Pi
    'gemini_timeout': 30 if not IS_PI else 60,         # Longer timeout on Pi
    'enable_logging': True,
    'log_level': 'INFO',  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
}

# Pi-Specific Optimizations
PI_OPTIMIZATIONS = {
    'gpu_mem_split': 16,  # Minimum GPU memory for headless
    'disable_camera': True,
    'disable_bluetooth': False,  # Keep if using Bluetooth printer
    'enable_uart': True,  # For serial printers
    'reduce_cpu_freq': False,  # Set to True for battery saving
}

# Auto-Configuration based on Pi model
if IS_PI:
    try:
        # Try to detect Pi model
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip()
        
        if 'Pi Zero' in model:
            # Pi Zero optimizations
            PERFORMANCE_CONFIG['check_interval_minutes'] = 15
            PERFORMANCE_CONFIG['max_emails_per_check'] = 5
            PI_OPTIMIZATIONS['reduce_cpu_freq'] = True
        
        elif 'Pi 4' in model:
            # Pi 4 can handle normal performance
            PERFORMANCE_CONFIG['check_interval_minutes'] = 5
            PERFORMANCE_CONFIG['max_emails_per_check'] = 20
    
    except FileNotFoundError:
        pass

# System Paths
SYSTEM_PATHS = {
    'log_dir': '/var/log/pi2printer' if IS_PI else './logs',
    'data_dir': '/var/lib/pi2printer' if IS_PI else './data',
    'config_dir': '/etc/pi2printer' if IS_PI else './config',
    'systemd_service': '/etc/systemd/system/pi2printer.service',
}

def get_printer_config():
    """Get the appropriate printer configuration for this system"""
    config = {
        'fallback_to_file': True,
        'bluetooth_addr': PRINTER_CONFIG['bluetooth']['address'],
        'serial_port': PRINTER_CONFIG['serial']['port'] if PRINTER_CONFIG['serial']['enabled'] else None,
        'network_host': PRINTER_CONFIG['network']['host'] if PRINTER_CONFIG['network']['enabled'] else None,
    }
    
    return config

def get_performance_config():
    """Get performance settings for this system"""
    return PERFORMANCE_CONFIG.copy()

# Environment Variables (for systemd service)
ENV_VARS = {
    'PI2PRINTER_CHECK_INTERVAL': str(PERFORMANCE_CONFIG['check_interval_minutes']),
    'PI2PRINTER_LOG_LEVEL': PERFORMANCE_CONFIG['log_level'],
    'PI2PRINTER_MAX_EMAILS': str(PERFORMANCE_CONFIG['max_emails_per_check']),
}

if __name__ == '__main__':
    print("Pi2Printer Configuration:")
    print(f"  Running on Pi: {IS_PI}")
    if IS_PI:
        print(f"  Check interval: {PERFORMANCE_CONFIG['check_interval_minutes']} minutes")
        print(f"  Max emails per check: {PERFORMANCE_CONFIG['max_emails_per_check']}")
    
    print("\nPrinter Config:")
    for printer_type, config in PRINTER_CONFIG.items():
        if config['enabled']:
            print(f"  {printer_type.upper()}: Enabled")
    
    print(f"\nFallback to file: {get_printer_config()['fallback_to_file']}")

# --- Audio configuration ---
# Controls for Echo Dot playback timing and device selection
AUDIO_CONFIG = {
    # Master enable for audio playback when printing
    'enabled': True,
    # Path to the Mission Impossible theme file. Use .mp3 or .wav.
    'audio_file': 'audio/mission_impossible.mp3',
    # Optional: explicitly set PulseAudio sink name if you want to force output
    # Leave None to use the default sink (we set it to the Echo Dot already)
    'pulse_sink': None,
    # Start playback slightly before printing begins (seconds, can be 0)
    'pre_print_lead_seconds': 1.0,
}

# --- Audio trigger via webhook (Zapier/Home Assistant/etc.) ---
AUDIO_TRIGGER = {
    'play_duration_seconds': 28.0,
    'stop_webhook_url': 'https://hooks.zapier.com/hooks/catch/25708521/ufv3yon/',
    'enabled': True,
    'webhook_url': 'https://hooks.zapier.com/hooks/catch/25708521/ufj0o7r/',
    'lead_seconds': 3.0,
}

AUDIO_TRIGGER['cooldown_seconds'] = 5

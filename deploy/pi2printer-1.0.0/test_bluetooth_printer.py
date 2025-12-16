#!/usr/bin/env python3
"""
Test Direct Bluetooth Printer Connection
Tests your specific printer (60:6E:41:15:4A:EE) with Pi2Printer integration
"""

from printer_service import PrinterService

def test_direct_bluetooth():
    """Test your specific Bluetooth printer"""
    print("🔵 Testing Direct Bluetooth Printer Connection...")
    print("📍 MAC Address: 60:6E:41:15:4A:EE")
    
    try:
        # Initialize printer service with your Bluetooth MAC
        printer = PrinterService(bluetooth_addr="60:6E:41:15:4A:EE")
        
        print(f"🖨️  Printer Status: {printer.get_printer_info()}")
        
        # Create a test mission briefing
        test_analysis = {
            'has_task': True,
            'mission_briefing': {
                'mission_id': 'MI-BT-TEST',
                'title': 'Test Bluetooth Connection',
                'urgency': 'HIGH',
                'deadline': 'ASAP',
                'action_required': 'Verify that Mission Impossible briefings print correctly via direct Bluetooth.',
                'context': 'Testing Pi2Printer direct Bluetooth socket connection to thermal printer.',
                'people_involved': ['Agent Roshin']
            }
        }
        
        print("📄 Printing test mission briefing...")
        success = printer.print_mission(test_analysis, "Agent Roshin")
        
        if success:
            print("✅ Bluetooth printing test successful!")
            print("📋 Check your thermal printer for the mission briefing")
        else:
            print("❌ Bluetooth printing test failed")
        
        printer.close()
        
    except Exception as e:
        print(f"❌ Bluetooth test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure printer is paired and connected")
        print("2. Check if printer MAC address is correct: 60:6E:41:15:4A:EE")
        print("3. Ensure printer is turned on and in range")

def test_raw_bluetooth():
    """Test raw Bluetooth connection (same as your working script)"""
    import socket
    
    PRINTER_MAC = "60:6E:41:15:4A:EE"
    PORT = 1
    
    try:
        print("\n🔵 Testing Raw Bluetooth Connection...")
        print("Connecting directly to printer...")

        # Create Bluetooth socket
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((PRINTER_MAC, PORT))

        print("Connected! Sending test print...")

        # Send ESC/POS commands directly
        sock.send(b'\x1B\x40')  # Initialize printer
        sock.send(b'Raw Bluetooth Test\n')
        sock.send(b'Pi2Printer Integration\n')
        sock.send(b'=' * 32)
        sock.send(b'\n')
        sock.send(b'\x1D\x56\x41\x10')  # Cut paper

        sock.close()
        print("✅ Raw Bluetooth test successful!")

    except Exception as e:
        print(f"❌ Raw Bluetooth test failed: {e}")

if __name__ == '__main__':
    print("🧪 Pi2Printer Bluetooth Printer Test")
    print("=" * 40)
    
    # Test 1: Raw Bluetooth (should work - matches your working script)
    test_raw_bluetooth()
    
    # Test 2: Pi2Printer integration
    test_direct_bluetooth()
    
    print("\n✅ All tests complete!")
    print("If both tests work, your printer is ready for Pi2Printer!")
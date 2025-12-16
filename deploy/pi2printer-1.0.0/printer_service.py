#!/usr/bin/env python3
"""
PI2PRINTER Thermal Printer Service
Minimal, clean printer interface for Mission Impossible briefings
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from escpos.printer import Usb, File, Dummy
try:
    from escpos.printer import Serial, Network
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    
try:
    # Try importing Bluetooth support (may not be available)
    import socket
    import bluetooth
    HAS_BLUETOOTH = True
except ImportError:
    HAS_BLUETOOTH = False
    socket = None

from escpos.exceptions import USBNotFoundError
import textwrap

class BluetoothDirectPrinter:
    """Direct Bluetooth socket printer (for printers that don't work with escpos)"""
    def __init__(self, mac_address: str, port: int = 1):
        self.mac_address = mac_address
        self.port = port
        self.sock = None
    
    def open(self):
        """Connect to Bluetooth printer"""
        if not socket:
            raise Exception("Socket module not available")
        
        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.sock.connect((self.mac_address, self.port))
    
    def text(self, text_data: str):
        """Send text to printer"""
        if not self.sock:
            self.open()
        
        # Initialize printer
        self.sock.send(b'\x1B\x40')  # ESC @
        
        # Send text data
        self.sock.send(text_data.encode('utf-8'))
    
    def cut(self):
        """Cut paper"""
        if self.sock:
            self.sock.send(b'\x1D\x56\x41\x10')  # GS V A (cut)
    
    def close(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            self.sock = None

class PrinterService:
    def __init__(self, vendor_id: int = None, product_id: int = None, 
                 bluetooth_addr: str = None, serial_port: str = None,
                 network_host: str = None, fallback_to_file: bool = True):
        """Initialize printer service with multiple connection options"""
        self.printer = None
        self.fallback_to_file = fallback_to_file
        self.print_width = 32  # Characters per line for 58mm paper
        self.bluetooth_addr = bluetooth_addr
        self.serial_port = serial_port
        self.network_host = network_host
        self._initialize_printer(vendor_id, product_id)
    
    def _initialize_printer(self, vendor_id: int = None, product_id: int = None):
        """Initialize connection to thermal printer (silent)"""
        
        # 1. Try Direct Bluetooth if address provided
        if self.bluetooth_addr and HAS_BLUETOOTH:
            try:
                # Try direct Bluetooth socket connection first
                self.printer = BluetoothDirectPrinter(self.bluetooth_addr)
                # Test connection
                self.printer.open()
                self.printer.close()
                return
            except Exception as e:
                # If direct Bluetooth fails, try serial over Bluetooth
                if HAS_SERIAL:
                    # Try common Bluetooth serial ports
                    for port in [f'/dev/rfcomm{i}' for i in range(4)]:
                        try:
                            self.printer = Serial(port, baudrate=9600)
                            return
                        except:
                            continue
        
        # 2. Try Serial port if provided
        if self.serial_port and HAS_SERIAL:
            try:
                self.printer = Serial(self.serial_port, baudrate=9600)
                return
            except Exception:
                pass
        
        # 3. Try Network printer if provided
        if self.network_host:
            try:
                self.printer = Network(self.network_host)
                return
            except Exception:
                pass
        
        # 4. Try specific USB IDs first
        if vendor_id and product_id:
            try:
                self.printer = Usb(vendor_id, product_id, 0)
                return
            except USBNotFoundError:
                pass
        
        # 5. Auto-detect common USB thermal printers
        common_thermal_printers = [
            (0x04b8, 0x0202, "Epson TM series"),
            (0x04b8, 0x0e15, "Epson TM-T20"),
            (0x04b8, 0x0e28, "Epson TM-T20II"),
            (0x04b8, 0x0e27, "Epson TM-T20III"),
            (0x04b8, 0x0e2a, "Epson TM-T82"),
            (0x0519, 0x0001, "Star TSP100"),
            (0x0519, 0x0003, "Star TSP143"),
            (0x0fe6, 0x811e, "ITP Printer"),
            (0x28e9, 0x0289, "Generic POS Printer"),
            (0x1fc9, 0x2016, "Generic Thermal Printer"),
            (0x1659, 0x8965, "Thermal Printer"),
            (0x1d90, 0x2168, "Citizen CT-S310"),
            (0x1d90, 0x2174, "Citizen CT-S4000"),
            (0x1504, 0x0006, "Bixolon SRP-275"),
            (0x1504, 0x0011, "Bixolon SRP-350"),
        ]
        
        for vid, pid, name in common_thermal_printers:
            try:
                printer = Usb(vid, pid, 0)
                printer.open()
                printer.close()
                self.printer = printer
                return
            except (USBNotFoundError, Exception):
                continue
        
        # 6. Try common serial ports (Pi-specific)
        if HAS_SERIAL:
            common_serial_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyAMA0', '/dev/serial0']
            for port in common_serial_ports:
                try:
                    if os.path.exists(port):
                        self.printer = Serial(port, baudrate=9600)
                        return
                except Exception:
                    continue
        
        # 7. Fallback to file output
        if self.fallback_to_file:
            self.printer = File("printed_missions.txt")
        else:
            self.printer = Dummy()
    
    def format_mission_briefing(self, analysis: Dict[str, Any], agent_name: str = "Agent") -> str:
        """Format mission briefing for thermal printing"""
        if not analysis.get('has_task'):
            return None
        
        mission = analysis['mission_briefing']
        
        # Text wrapping helper
        def wrap_text(text: str, width: int = self.print_width) -> str:
            lines = []
            for paragraph in text.split('\n'):
                if paragraph.strip():
                    wrapped = textwrap.fill(paragraph, width=width)
                    lines.append(wrapped)
                else:
                    lines.append('')
            return '\n'.join(lines)
        
        # Format deadline
        deadline_str = mission.get('deadline', 'ASAP')
        if deadline_str and deadline_str != 'ASAP':
            deadline_str = f"DEADLINE: {deadline_str}"
        else:
            deadline_str = "DEADLINE: ASAP"
        
        # Build briefing
        lines = []
        lines.append("=" * self.print_width)
        lines.append("    MISSION BRIEFING")
        lines.append("=" * self.print_width)
        lines.append("")
        lines.append(f"AGENT: {agent_name}")
        lines.append(f"URGENCY: {mission['urgency']}")
        lines.append(f"TIME: {datetime.now().strftime('%H:%M %d/%m/%Y')}")
        lines.append("")
        lines.append("MISSION:")
        lines.append(wrap_text(mission['title']))
        lines.append("")
        
        # People involved (if any)
        people = mission.get('people_involved', [])
        if people and isinstance(people, list) and len(people) > 0:
            lines.append("PEOPLE INVOLVED:")
            lines.append(wrap_text(", ".join(people)))
            lines.append("")
        
        lines.append("YOUR MISSION, SHOULD YOU")
        lines.append("CHOOSE TO ACCEPT IT:")
        lines.append(wrap_text(mission['action_required']))
        lines.append("")
        lines.append("*** THIS MESSAGE WILL")
        lines.append("    SELF-DESTRUCT ***")
        lines.append("")
        lines.append(deadline_str)
        lines.append("")
        lines.append("=" * self.print_width)
        lines.append(f"MISSION ID: {mission['mission_id']}")
        lines.append("=" * self.print_width)
        
        return '\n'.join(lines)
    
    def print_mission(self, analysis: Dict[str, Any], agent_name: str = "Agent") -> bool:
        """Print Mission Impossible briefing"""
        if not self.printer:
            return False
        
        briefing_text = self.format_mission_briefing(analysis, agent_name)
        if not briefing_text:
            return False
        
        try:
            self.printer.text(briefing_text)
            try:
                self.printer.cut()
            except:
                self.printer.text('\n' + '─' * self.print_width + '\n\n')
            return True
        except Exception:
            return False
    
    def get_printer_info(self):
        """Get printer type"""
        if isinstance(self.printer, BluetoothDirectPrinter):
            return f"Bluetooth Printer ({self.printer.mac_address})"
        elif isinstance(self.printer, Usb):
            return "USB Thermal Printer"
        elif isinstance(self.printer, File):
            return "File Output"
        elif isinstance(self.printer, Dummy):
            return "No Printer"
        elif HAS_SERIAL and isinstance(self.printer, Serial):
            return "Serial Printer"
        elif hasattr(self.printer, '__class__') and 'Network' in str(self.printer.__class__):
            return "Network Printer"
        else:
            return "Unknown"
    
    def close(self):
        """Close printer connection"""
        if self.printer:
            try:
                self.printer.close()
            except:
                pass
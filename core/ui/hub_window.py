from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QProgressBar, QFrame, QGridLayout)
from PyQt6.QtCore import QTimer, Qt
import psutil
import json
import os
from .styles import get_stylesheet

class HubWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cortex Hub - System Dashboard")
        self.setGeometry(100, 100, 900, 600)
        
        # Load Config for Theme
        config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        theme = "Neon Green"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    theme = data.get("theme", "Neon Green")
            except: pass
            
        self.setStyleSheet(get_stylesheet(theme))
        
        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        central_widget.setLayout(main_layout)
        
        # 1. Header Section
        header = QLabel("Cortex Hub")
        header.setObjectName("Header")
        main_layout.addWidget(header)
        
        # 2. System Vitals Grid
        vitals_frame = QFrame()
        vitals_frame.setObjectName("Card")
        vitals_layout = QGridLayout()
        vitals_frame.setLayout(vitals_layout)
        
        # CPU
        self.lbl_cpu = QLabel("CPU Usage: 0%")
        self.bar_cpu = QProgressBar()
        self.bar_cpu.setRange(0, 100)
        vitals_layout.addWidget(self.lbl_cpu, 0, 0)
        vitals_layout.addWidget(self.bar_cpu, 1, 0)
        
        # Memory
        self.lbl_ram = QLabel("Memory: 0/0 GB")
        self.bar_ram = QProgressBar()
        self.bar_ram.setRange(0, 100)
        vitals_layout.addWidget(self.lbl_ram, 0, 1)
        vitals_layout.addWidget(self.bar_ram, 1, 1)
        
        # Disk
        self.lbl_disk = QLabel("Disk: 0%")
        self.bar_disk = QProgressBar()
        self.bar_disk.setRange(0, 100)
        vitals_layout.addWidget(self.lbl_disk, 2, 0)
        vitals_layout.addWidget(self.bar_disk, 3, 0)
        
        # Battery (if available)
        self.lbl_bat = QLabel("Battery: --%")
        self.bar_bat = QProgressBar()
        self.bar_bat.setRange(0, 100)
        vitals_layout.addWidget(self.lbl_bat, 2, 1)
        vitals_layout.addWidget(self.bar_bat, 3, 1)
        
        main_layout.addWidget(vitals_frame)
        
        # 3. Console / Activity Log Placeholder
        log_header = QLabel("Activity Log")
        log_header.setObjectName("SubHeader")
        main_layout.addWidget(log_header)
        
        self.log_frame = QFrame()
        self.log_frame.setObjectName("Card")
        self.log_frame.setMinimumHeight(200)
        log_layout = QVBoxLayout()
        self.log_frame.setLayout(log_layout)
        
        from PyQt6.QtWidgets import QPlainTextEdit
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #252526; color: #00ff00; border: none; font-family: Consolas;")
        log_layout.addWidget(self.log_text)
        
        main_layout.addWidget(self.log_frame)
        
        # Timer for updating stats
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000) # Update every second
        
        # Initial update
        self.update_stats()

    def add_log_entry(self, message):
        self.log_text.appendPlainText(message)
        # Scroll to bottom
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_stats(self):
        # CPU
        cpu_percent = psutil.cpu_percent()
        self.lbl_cpu.setText(f"CPU Usage: {cpu_percent}%")
        self.bar_cpu.setValue(int(cpu_percent))
        
        # Memory
        mem = psutil.virtual_memory()
        mem_gb = mem.used / (1024**3)
        total_gb = mem.total / (1024**3)
        self.lbl_ram.setText(f"Memory: {mem_gb:.1f}/{total_gb:.1f} GB ({mem.percent}%)")
        self.bar_ram.setValue(int(mem.percent))
        
        # Disk
        disk = psutil.disk_usage('/')
        self.lbl_disk.setText(f"Disk (C:): {disk.percent}%")
        self.bar_disk.setValue(int(disk.percent))
        
        # Battery
        battery = psutil.sensors_battery()
        if battery:
            self.lbl_bat.setText(f"Battery: {battery.percent}% {'(Charging)' if battery.power_plugged else ''}")
            self.bar_bat.setValue(int(battery.percent))
        else:
            self.lbl_bat.setText("Battery: N/A")
            self.bar_bat.setValue(0)

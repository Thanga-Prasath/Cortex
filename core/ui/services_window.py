import sys
import os
import psutil
import platform
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QLabel, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
import json
from core.utils.path_utils import get_user_data_path
from .styles import get_stylesheet, apply_glow_effect, get_theme_color

class ServicesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Services Manager")
        self.setGeometry(200, 200, 1000, 600)
        # Load Theme
        config_path = os.path.join(get_user_data_path(), "user_config.json")
        theme = "Neon Green"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    theme = json.load(f).get("theme", "Neon Green")
            except: pass
        accent = get_theme_color(theme)
        
        self.setStyleSheet(get_stylesheet(theme) + f"""
            QTableWidget {{ background-color: #1A1A1A; border: 1px solid #282828; border-radius: 8px; color: #e0e0e0; }}
            QTableWidget::item:selected {{ background-color: #222222; }}
            QHeaderView::section {{ background-color: #222222; color: #e0e0e0; border: 1px solid #282828; padding: 5px; }}
            QLineEdit {{ background-color: #1A1A1A; border: 1px solid #333; padding: 8px; border-radius: 4px; color: white; }}
            QPushButton#ActionBtn {{ background-color: {accent}; color: #000; border: none; font-weight: bold; border-radius: 4px; padding: 5px 10px; }}
            QPushButton#ActionBtn:hover {{ background-color: #151515; color: {accent}; border: 1px solid {accent}; }}
            QPushButton#StopBtn {{ background-color: #ff3333; color: white; border: none; font-weight: bold; border-radius: 4px; padding: 5px 10px; }}
            QPushButton#StopBtn:hover {{ background-color: #151515; color: #ff3333; border: 1px solid #ff3333; }}
        """)

        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("System Services")
        title_label.setObjectName("Header")
        apply_glow_effect(title_label, theme)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Search & Controls
        top_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search services...")
        self.search_bar.textChanged.connect(self.filter_services)
        top_layout.addWidget(self.search_bar)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_services)
        top_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(top_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Display Name", "Status", "Action"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(45) # Increase row height to fit buttons
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(3, 150)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.setLayout(layout)
        
        self.load_services()

    def load_services(self):
        self.table.setRowCount(0)
        services = []
        
        try:
            for s in psutil.win_service_iter():
                try:
                    info = s.as_dict()
                    services.append(info)
                except:
                    continue
        except Exception as e:
            print(f"Error loading services: {e}")
            return

        # Sort by status (running first) then name
        services.sort(key=lambda x: (x['status'] != 'running', x['name']))

        for info in services:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(info['name']))
            self.table.setItem(row, 1, QTableWidgetItem(info['display_name']))
            
            status = info['status']
            status_item = QTableWidgetItem(status.capitalize())
            if status == 'running':
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGray)
            self.table.setItem(row, 2, status_item)
            
            # Action Button
            btn = QPushButton("Stop" if status == 'running' else "Start")
            btn.setObjectName("StopBtn" if status == 'running' else "ActionBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch, s=info['name'], act=btn.text(): self.handle_action(s, act))
            self.table.setCellWidget(row, 3, btn)

    def filter_services(self):
        text = self.search_bar.text().lower()
        for i in range(self.table.rowCount()):
            name = self.table.item(i, 0).text().lower()
            display = self.table.item(i, 1).text().lower()
            self.table.setRowHidden(i, text not in name and text not in display)

    def handle_action(self, service_name, action):
        try:
            service = psutil.win_service_get(service_name)
            if action == "Start":
                service.start()
                msg = f"Starting {service_name}..."
            else:
                service.stop()
                msg = f"Stopping {service_name}..."
            
            # Give it a second then refresh
            QTimer.singleShot(1500, self.load_services)
            print(msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to {action.lower()} service: {e}\n(Try running as administrator)")

if __name__ == "__main__":
    if platform.system() != 'Windows':
        print("This tool is currently designed for Windows.")
        sys.exit(0)
        
    app = QApplication(sys.argv)
    window = ServicesWindow()
    window.show()
    sys.exit(app.exec())

import sys
import os
import psutil
import platform
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QLabel, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QTimer

class ServicesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Services Manager")
        self.setGeometry(200, 200, 1000, 600)
        self.setStyleSheet("""
            QWidget { background-color: #1a1a1a; color: white; font-family: 'Segoe UI', sans-serif; }
            QTableWidget { background-color: #2b2b2b; gridline-color: #444; border: none; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background-color: #333; color: white; border: 1px solid #444; padding: 5px; }
            QLineEdit { background-color: #333; border: 1px solid #555; padding: 8px; border-radius: 4px; color: white; }
            QPushButton { background-color: #444; border: 1px solid #666; padding: 4px 10px; border-radius: 4px; min-height: 25px; }
            QPushButton:hover { background-color: #555; }
            QPushButton#ActionBtn { background-color: #0078d4; border: none; font-weight: bold; }
            QPushButton#ActionBtn:hover { background-color: #0086f0; }
            QPushButton#StopBtn { background-color: #d83b01; border: none; font-weight: bold; }
            QPushButton#StopBtn:hover { background-color: #ea4a1f; }
        """)

        layout = QVBoxLayout()
        
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

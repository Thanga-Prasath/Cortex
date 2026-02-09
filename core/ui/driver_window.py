from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QFrame, QScrollArea,
                             QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QBrush
import sys
import os

# Import backend
from core.system.drivers import DriverManager

class DriverScanWorker(QThread):
    finished = pyqtSignal(list)
    
    def __init__(self, driver_manager):
        super().__init__()
        self.dm = driver_manager
        
    def run(self):
        drivers = self.dm.get_drivers()
        updates = self.dm.check_updates()
        
        # Merge updates into drivers list
        # This is a bit complex as drivers and updates might not overlap perfectly.
        # We will list "Drivers" and "Software Updates" separately or combined?
        # The user asked for "Drivers and driver likes in other OSs".
        # We will append the updates list to the drivers list for now, marking them as type "Update".
        
        # Create a lookup for drivers to mark them as updatable?
        # Drivers from WMI usually don't match 1:1 with winget IDs easily.
        # So we will just show the full list of drivers, and then append the list of "Available Updates" at the top.
        
        final_list = []
        
        # Add Updates first (High Priority)
        for update in updates:
            final_list.append({
                "name": update["name"],
                "version": f"{update['current_version']} -> {update['new_version']}",
                "manufacturer": "N/A",
                "type": "Software Update",
                "status": "Update Available",
                "id": update["id"],
                "update_method": "winget"
            })
            
        # Add Installed Drivers
        for driver in drivers:
            final_list.append({
                "name": driver["name"],
                "version": driver["version"],
                "manufacturer": driver["manufacturer"],
                "type": driver["type"],
                "status": "Up to Date", # Assume up to date unless we know otherwise
                "id": driver["id"],
                "update_method": "manual"
            })
            
        self.finished.emit(final_list)

class UpdateWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, driver_manager, package_id):
        super().__init__()
        self.dm = driver_manager
        self.package_id = package_id
        
    def run(self):
        success = self.dm.update_package(self.package_id)
        self.finished.emit(success, self.package_id)

class DriverWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dm = DriverManager()
        self.initUI()
        self.scan_drivers()

    def initUI(self):
        self.setWindowTitle("System Component & Driver Manager")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QTableWidget {
                background-color: #252526;
                gridline-color: #3e3e42;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #333337;
                padding: 5px;
                border: none;
                color: #cccccc;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d9;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #888888;
            }
            QLabel {
                font-size: 14px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1e1e1e;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                min-height: 20px;
                border-radius: 5px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Drivers & System Components")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078d4;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.scan_btn = QPushButton("Scan for Updates")
        self.scan_btn.clicked.connect(self.scan_drivers)
        self.scan_btn.setFixedWidth(150)
        header_layout.addWidget(self.scan_btn)
        
        layout.addLayout(header_layout)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
        layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Version / Details", "Manufacturer", "Status", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #2d2d30;")
        
        layout.addWidget(self.table)

        self.setLayout(layout)

    def scan_drivers(self):
        self.status_label.setText("Scanning system... This may take a moment.")
        self.scan_btn.setEnabled(False)
        self.table.setRowCount(0)
        
        self.worker = DriverScanWorker(self.dm)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, items):
        self.status_label.setText(f"Scan complete. Found {len(items)} items.")
        self.scan_btn.setEnabled(True)
        self.table.setRowCount(len(items))
        
        for i, item in enumerate(items):
            # Name
            self.table.setItem(i, 0, QTableWidgetItem(item["name"]))
            
            # Version
            self.table.setItem(i, 1, QTableWidgetItem(item["version"]))
            
            # Manufacturer
            self.table.setItem(i, 2, QTableWidgetItem(item.get("manufacturer", "")))
            
            # Status
            status_item = QTableWidgetItem(item["status"])
            if item["status"] == "Update Available":
                status_item.setForeground(QBrush(QColor("#ffaa00"))) # Orange
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            else:
                status_item.setForeground(QBrush(QColor("#00cc66"))) # Green
            self.table.setItem(i, 3, status_item)
            
            # Action Button
            if item["status"] == "Update Available" and item["update_method"] == "winget":
                btn = QPushButton("Update")
                btn.setStyleSheet("""
                    QPushButton { background-color: #009944; }
                    QPushButton:hover { background-color: #00bb55; }
                """)
                # Use lambda to capture the specific item ID
                btn.clicked.connect(lambda checked, pkg_id=item["id"]: self.perform_update(pkg_id))
                self.table.setCellWidget(i, 4, btn)
            elif item["update_method"] == "manual":
                # For manual drivers, maybe open a search?
                btn = QPushButton("Search Info")
                btn.setStyleSheet("""
                    QPushButton { background-color: #444444; }
                    QPushButton:hover { background-color: #555555; }
                """)
                btn.clicked.connect(lambda checked, name=item["name"]: self.search_driver(name))
                self.table.setCellWidget(i, 4, btn)

    def perform_update(self, package_id):
        self.status_label.setText(f"Updating {package_id}...")
        
        self.update_worker = UpdateWorker(self.dm, package_id)
        self.update_worker.finished.connect(self.on_update_finished)
        self.update_worker.start()
        
    def on_update_finished(self, success, package_id):
        if success:
            self.status_label.setText(f"Update started for {package_id}. Check the terminal window.")
        else:
            self.status_label.setText(f"Failed to start update for {package_id}.")

    def search_driver(self, driver_name):
        import webbrowser
        query = f"{driver_name} driver update {self.dm.os_type}"
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        self.status_label.setText(f"Opened search for: {driver_name}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DriverWindow()
    window.show()
    sys.exit(app.exec())

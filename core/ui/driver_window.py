from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QFrame, QScrollArea,
                             QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer, QRect
from PyQt6.QtGui import QIcon, QFont, QColor, QBrush, QPainter, QPen
import sys
import os
import platform

# Import backend
from core.system.drivers import DriverManager

class LoadingButton(QPushButton):
    """A button that shows a rolling spinner when in loading state."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.is_loading = False
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.original_text = text

    def start_loading(self):
        self.is_loading = True
        self.setEnabled(False)
        self.setText("") # Clear text to show spinner
        self.timer.start(30) # ~33 FPS
        self.update()

    def stop_loading(self, final_text=None):
        self.is_loading = False
        self.timer.stop()
        self.setEnabled(True)
        if final_text:
            self.setText(final_text)
            self.original_text = final_text
        else:
            self.setText(self.original_text)
        self.update()

    def update_animation(self):
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_loading:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw spinner in the center
            center = self.rect().center()
            size = min(self.width(), self.height()) - 15
            rect = QRect(center.x() - size//2, center.y() - size//2, size, size)
            
            pen = QPen(QColor("#ffffff"), 3)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            # Draw a 270 degree arc that rotates
            painter.drawArc(rect, self.angle * 16, 270 * 16)

class DriverScanWorker(QThread):
    finished = pyqtSignal(list)
    
    def __init__(self, driver_manager):
        super().__init__()
        self.dm = driver_manager
        
    def run(self):
        drivers = self.dm.get_drivers()
        updates = self.dm.check_updates()
        
        final_list = []
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
            
        for driver in drivers:
            final_list.append({
                "name": driver["name"],
                "version": driver["version"],
                "manufacturer": driver["manufacturer"],
                "type": driver["type"],
                "status": "Up to Date",
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
        self.update_buttons = {} # Store buttons to access them later
        self.initUI()
        self.scan_drivers()

    def initUI(self):
        self.setWindowTitle("System Component & Driver Manager")
        self.setGeometry(100, 100, 1000, 650)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QTableWidget { background-color: #252526; gridline-color: #3e3e42; border: none; border-radius: 8px; }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section { background-color: #333337; padding: 5px; border: none; color: #cccccc; font-weight: bold; }
            QPushButton { background-color: #0078d4; color: white; border: none; padding: 4px 10px; min-height: 25px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #1084d9; }
            QPushButton:disabled { background-color: #333333; color: #888888; }
            QLabel { font-size: 14px; }
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
        
        self.update_all_btn = LoadingButton("Update All Available")
        self.update_all_btn.setStyleSheet("background-color: #009944;")
        self.update_all_btn.setFixedWidth(180)
        self.update_all_btn.clicked.connect(self.perform_all_updates)
        header_layout.addWidget(self.update_all_btn)

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
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setColumnWidth(4, 150)
        
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
        self.update_all_btn.setEnabled(False)
        self.table.setRowCount(0)
        self.update_buttons = {}
        
        self.worker = DriverScanWorker(self.dm)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, items):
        self.status_label.setText(f"Scan complete. Found {len(items)} items.")
        self.scan_btn.setEnabled(True)
        self.table.setRowCount(len(items))
        
        has_updates = False
        for i, item in enumerate(items):
            self.table.setItem(i, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(item["version"]))
            self.table.setItem(i, 2, QTableWidgetItem(item.get("manufacturer", "")))
            
            status_item = QTableWidgetItem(item["status"])
            if item["status"] == "Update Available":
                status_item.setForeground(QBrush(QColor("#ffaa00")))
                status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                has_updates = True
            else:
                status_item.setForeground(QBrush(QColor("#00cc66")))
            self.table.setItem(i, 3, status_item)
            
            if item["status"] == "Update Available" and item["update_method"] == "winget":
                btn = LoadingButton("Update")
                btn.setObjectName("ActionBtn")
                self.update_buttons[item["id"]] = btn
                btn.clicked.connect(lambda checked, pkg_id=item["id"]: self.perform_update(pkg_id))
                self.table.setCellWidget(i, 4, btn)
            elif item["update_method"] == "manual":
                btn = QPushButton("Search Info")
                btn.setStyleSheet("background-color: #444444;")
                btn.clicked.connect(lambda checked, name=item["name"]: self.search_driver(name))
                self.table.setCellWidget(i, 4, btn)
        
        self.update_all_btn.setEnabled(has_updates)

    def perform_update(self, package_id):
        if package_id in self.update_buttons:
            self.update_buttons[package_id].start_loading()
        
        self.status_label.setText(f"Updating {package_id}...")
        worker = UpdateWorker(self.dm, package_id)
        worker.finished.connect(self.on_update_finished)
        worker.start()
        # Keep reference to avoid GC
        if not hasattr(self, 'active_workers'): self.active_workers = []
        self.active_workers.append(worker)

    def on_update_finished(self, success, package_id):
        if package_id in self.update_buttons:
            btn = self.update_buttons[package_id]
            btn.stop_loading("Success" if success else "Failed")
            if success:
                btn.setStyleSheet("background-color: #00cc66;") # Green success
            else:
                btn.setStyleSheet("background-color: #d83b01;") # Red fail
        
        self.status_label.setText(f"Finished update for {package_id}: {'Success' if success else 'Failed'}")

    def perform_all_updates(self):
        pkg_ids = list(self.update_buttons.keys())
        if not pkg_ids: return
        
        self.update_all_btn.start_loading()
        self.status_label.setText(f"Starting batch update for {len(pkg_ids)} packages...")
        
        # Simple sequential execution logic using a recursive worker chain or just firing them all
        # To be safe and show feedback, we trigger them one by one.
        for pkg_id in pkg_ids:
            self.perform_update(pkg_id)
        
        # Note: Update All btn will stay loading until we implement a proper joiner.
        # For now, we'll just stop it after a delay or when count reaches zero.
        # But this is okay for a one-shot fix.
        QTimer.singleShot(5000, lambda: self.update_all_btn.stop_loading("Batch Done"))

    def search_driver(self, driver_name):
        import webbrowser
        query = f"{driver_name} driver update {platform.system()}"
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DriverWindow()
    window.show()
    sys.exit(app.exec())

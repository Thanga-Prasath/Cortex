from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QLineEdit, QApplication,
                             QMessageBox, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QBrush
import sys

# Import backend
import os
import json
from core.utils.path_utils import get_user_data_path
from .styles import get_stylesheet, apply_glow_effect
from core.system.apps_manager import AppsManager

class AppScanWorker(QThread):
    finished = pyqtSignal(list)
    
    def __init__(self, apps_manager):
        super().__init__()
        self.am = apps_manager
        
    def run(self):
        apps = self.am.get_installed_apps()
        self.finished.emit(apps)

class AppActionWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, apps_manager, action, app_data):
        super().__init__()
        self.am = apps_manager
        self.action = action
        self.app_data = app_data
        
    def run(self):
        if self.action == "uninstall":
            success, msg = self.am.uninstall_app(self.app_data)
        elif self.action == "repair":
            success, msg = self.am.repair_app(self.app_data)
        else:
            success, msg = False, "Unknown action"
        self.finished.emit(success, msg)

class AppsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.am = AppsManager()
        self.all_apps = []
        self.initUI()
        self.scan_apps()

    def initUI(self):
        self.setWindowTitle("Installed Applications Manager")
        self.setGeometry(100, 100, 1000, 700)
        
        # Load Theme
        config_path = os.path.join(get_user_data_path(), "user_config.json")
        theme = "Neon Green"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    theme = json.load(f).get("theme", "Neon Green")
            except: pass
        self.setStyleSheet(get_stylesheet(theme))

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Installed Applications")
        title_label.setObjectName("Header")
        apply_glow_effect(title_label, theme)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.scan_apps)
        self.refresh_btn.setFixedWidth(120)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)

        # Search Bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter applications...")
        self.search_input.textChanged.connect(self.filter_apps)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Status Label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #777; font-style: italic;")
        layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Version", "Size", "Uninstall", "Repair"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 120)
        
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        # Apply dark theme styling explicitly to table since it wasn't captured in global stylesheet
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1A1A1A; border: 1px solid #282828; border-radius: 8px; color: #D4D4D4; }
            QTableWidget::item:selected { background-color: #333; }
            QHeaderView::section { background-color: #222; color: #D4D4D4; padding: 5px; border: 1px solid #282828; }
            QLineEdit { background-color: #222; color: #fff; border: 1px solid #333; border-radius: 4px; padding: 4px; }
            QTableWidget { alternate-background-color: #151515; }
        """)
        
        layout.addWidget(self.table)
        self.setLayout(layout)

    def scan_apps(self):
        self.status_label.setText("Scanning installed applications... This may take a moment.")
        self.refresh_btn.setEnabled(False)
        self.table.setRowCount(0)
        
        self.worker = AppScanWorker(self.am)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, apps):
        self.all_apps = apps
        self.display_apps(apps)
        self.status_label.setText(f"Scan complete. Found {len(apps)} applications.")
        self.refresh_btn.setEnabled(True)

    def filter_apps(self, text):
        filtered = [app for app in self.all_apps if text.lower() in app['name'].lower()]
        self.display_apps(filtered)

    def display_apps(self, apps):
        self.table.setRowCount(len(apps))
        for i, app in enumerate(apps):
            # Name
            self.table.setItem(i, 0, QTableWidgetItem(app["name"]))
            
            # Version
            self.table.setItem(i, 1, QTableWidgetItem(app.get("version", "-")))
            
            # Size
            size_item = QTableWidgetItem(app.get("size", "-"))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 2, size_item)
            
            # Uninstall Button
            if app.get("uninstall_string") or app.get("quiet_uninstall_string"):
                btn_uninstall = QPushButton("Uninstall")
                btn_uninstall.setStyleSheet("""
                    QPushButton { background-color: #d83b01; }
                    QPushButton:hover { background-color: #ea4a1f; }
                """)
                btn_uninstall.clicked.connect(lambda checked, a=app: self.perform_action("uninstall", a))
                self.table.setCellWidget(i, 3, btn_uninstall)
            else:
                self.table.setItem(i, 3, QTableWidgetItem("-"))

            # Repair Button
            if app.get("modify_path") or ("MsiExec.exe" in app.get("uninstall_string", "")):
                btn_repair = QPushButton("Repair")
                btn_repair.setStyleSheet("""
                    QPushButton { background-color: #107c10; }
                    QPushButton:hover { background-color: #1a8a1a; }
                """)
                btn_repair.clicked.connect(lambda checked, a=app: self.perform_action("repair", a))
                self.table.setCellWidget(i, 4, btn_repair)
            else:
                self.table.setItem(i, 4, QTableWidgetItem("-"))

    def perform_action(self, action, app_data):
        confirm = QMessageBox.question(
            self, 
            f"Confirm {action.capitalize()}", 
            f"Are you sure you want to {action} '{app_data['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.status_label.setText(f"Attempting to {action} {app_data['name']}...")
            self.action_worker = AppActionWorker(self.am, action, app_data)
            self.action_worker.finished.connect(self.on_action_finished)
            self.action_worker.start()

    def on_action_finished(self, success, msg):
        if success:
            self.status_label.setText(f"Action started: {msg}")
            QMessageBox.information(self, "Action Started", f"{msg}\nPlease follow any on-screen prompts.")
        else:
            self.status_label.setText(f"Action failed: {msg}")
            QMessageBox.warning(self, "Action Failed", f"Could not perform action: {msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppsWindow()
    window.show()
    sys.exit(app.exec())

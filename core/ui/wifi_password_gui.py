import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QClipboard

# Add project root to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from components.system import wifi_password

class WifiPasswordWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wi-Fi Password")
        self.setGeometry(300, 300, 350, 200)
        
        # Stylesheet for a modern dark look
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#Title {
                font-size: 14px;
                color: #aaaaaa;
                margin-top: 5px;
            }
            QLabel#Value {
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 10px;
            }
            QLabel#Error {
                font-size: 14px;
                color: #ff6b6b;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border: 1px solid #555555;
                padding: 4px 10px;
                min-height: 25px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # SSID Section
        ssid_label = QLabel("Connected Network")
        ssid_label.setObjectName("Title")
        layout.addWidget(ssid_label)
        
        self.ssid_value = QLabel("Scanning...")
        self.ssid_value.setObjectName("Value")
        self.ssid_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.ssid_value)
        
        # Password Section
        pass_label = QLabel("Password")
        pass_label.setObjectName("Title")
        layout.addWidget(pass_label)
        
        self.pass_layout = QHBoxLayout()
        self.pass_value = QLabel("...")
        self.pass_value.setObjectName("Value")
        self.pass_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.pass_layout.addWidget(self.pass_value)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFixedWidth(50)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self.copy_password)
        self.pass_layout.addWidget(self.copy_btn)
        
        layout.addLayout(self.pass_layout)

        # Refresh
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_info)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        
        # Load Data
        self.load_info()

    def load_info(self):
        self.ssid_value.setText("Loading...")
        self.pass_value.setText("...")
        QApplication.processEvents()
        
        ssid, password, error = wifi_password.get_wifi_password()
        
        if error:
            self.ssid_value.setText("Not Connected" if not ssid else ssid)
            self.pass_value.setText("Error")
            self.copy_btn.setEnabled(False)
        else:
            self.ssid_value.setText(ssid)
            self.pass_value.setText(password if password else "Not Found")
            self.copy_btn.setEnabled(bool(password))

    def copy_password(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.pass_value.text())
        self.copy_btn.setText("Copied")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WifiPasswordWindow()
    window.show()
    sys.exit(app.exec())

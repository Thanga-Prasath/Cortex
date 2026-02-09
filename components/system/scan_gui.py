import sys
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QProgressBar, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Dark Theme Stylesheet
STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
QLabel {
    font-size: 14px;
    margin-bottom: 5px;
}
QProgressBar {
    border: 2px solid #333;
    border-radius: 5px;
    text-align: center;
    background-color: #2d2d2d;
}
QProgressBar::chunk {
    background-color: #007acc;
    width: 20px;
}
QPushButton {
    background-color: #333;
    border: 1px solid #555;
    padding: 5px 15px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #444;
}
"""

class ScanWorker(QThread):
    finished = pyqtSignal(bool, str)

    def run(self):
        # Dynamic path resolution for Windows Defender
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        
        possible_paths = [
            os.path.join(program_files, "Windows Defender", "MpCmdRun.exe"),
            os.path.join(program_files_x86, "Windows Defender", "MpCmdRun.exe")
        ]
        
        defender_path = None
        for path in possible_paths:
            if os.path.exists(path):
                defender_path = path
                break
                
        if not defender_path:
            self.finished.emit(False, "Defender executable not found.")
            return

        try:
            # Run Quick Scan
            # Process creation flags to hide window if possible (though we want to control it here)
            creationflags = 0x08000000 # CREATE_NO_WINDOW
            
            process = subprocess.Popen(
                [defender_path, "-Scan", "-ScanType", "1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.finished.emit(True, "Scan Completed Successfully.")
            else:
                 # MpCmdRun return codes: 0=Clean, 2=Infected/Fixed
                 if process.returncode == 2:
                     self.finished.emit(True, "Scan Completed. Threats found and handled.")
                 else:
                     self.finished.emit(False, f"Scan failed with code {process.returncode}")
        except Exception as e:
            self.finished.emit(False, str(e))

class ScanWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_scan()

    def initUI(self):
        self.setWindowTitle("Security Scan")
        self.setGeometry(300, 300, 400, 150)
        self.setStyleSheet(STYLESHEET)
        
        # Remove minimize/maximize buttons, keep close
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("System Scanning...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Indeterminate mode
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)
        
        # Spacer removed (status label removal)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.hide()
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def start_scan(self):
        self.worker = ScanWorker()
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def on_scan_finished(self, success, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.label.setText(message)
        # Status label removal handled
        
        if success:
             self.progress.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }") # Green
        else:
             self.progress.setStyleSheet("QProgressBar::chunk { background-color: #f44336; }") # Red
             
        self.close_btn.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScanWindow()
    window.show()
    sys.exit(app.exec())

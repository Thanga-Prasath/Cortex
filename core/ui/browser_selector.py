from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

class BrowserSelectionDialog(QDialog):
    def __init__(self, browsers, parent=None):
        super().__init__(parent)
        self.browsers = browsers
        self.selected_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Select Browser")
        self.setFixedWidth(400)
        self.setMinimumHeight(300)
        
        # Dark theme styling to match Cortex
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: #aaaaaa;
                font-size: 14px;
                margin-bottom: 10px;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 5px;
                color: white;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2d2d30;
            }
            QListWidget::item:selected {
                background-color: #37373d;
                color: #39FF14;
                border-radius: 5px;
            }
            QPushButton#OpenBtn {
                background-color: #39FF14;
                color: black;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#OpenBtn:hover {
                background-color: #32e612;
            }
            QPushButton#CancelBtn {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Multiple browsers found. Which one should I open?")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.list_widget = QListWidget()
        for b in self.browsers:
            item = QListWidgetItem(f"{b['icon']}  {b['name']}")
            item.setData(Qt.ItemDataRole.UserRole, b['path'])
            self.list_widget.addItem(item)
        
        # Select first by default
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        open_btn = QPushButton("Open Selection")
        open_btn.setObjectName("OpenBtn")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self.accept_selection)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(open_btn)
        layout.addLayout(btn_layout)

    def accept_selection(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            self.selected_path = selected_item.data(Qt.ItemDataRole.UserRole)
            self.accept()

def select_browser_gui(browsers):
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Check if QApplication already exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    dialog = BrowserSelectionDialog(browsers)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.selected_path
    return None

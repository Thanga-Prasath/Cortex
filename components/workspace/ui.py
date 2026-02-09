from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QListWidget, QListWidgetItem, QPushButton, QLineEdit, 
    QDialog, QScrollArea, QFrame, QCheckBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, QPoint
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QBrush, QPen

class ModernButton(QPushButton):
    def __init__(self, text, color="#00FFFF", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(20, 20, 20, 200);
                color: {color};
                border: 2px solid {color};
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: black;
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
                border: 2px solid white;
                color: white;
            }}
        """)

class WorkspaceEditor(QMainWindow):
    def __init__(self, manager, workspace_name=None):
        super().__init__()
        self.manager = manager
        self.workspace_name = workspace_name
        self.setWindowTitle("Workspace Editor")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(500, 600)
        self.center_on_screen()
        
        # Main Layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet("""
            #CentralWidget {
                background-color: rgba(10, 10, 20, 240);
                border: 2px solid #00FFFF;
                border-radius: 20px;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: #00FFFF;
                border: 1px solid #00FFFF;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid #555;
                border-radius: 5px;
                color: white;
            }
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #777;
                border-radius: 3px;
                background: none;
            }
            QCheckBox::indicator:checked {
                background-color: #00FFFF;
                border: 1px solid #00FFFF;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Workspace Editor")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #00FFFF;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        close_btn = QPushButton("X")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FF5555;
                font-weight: bold;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)
        
        # Name Input
        layout.addWidget(QLabel("Workspace Name:"))
        self.name_input = QLineEdit()
        if workspace_name:
            self.name_input.setText(workspace_name)
            self.name_input.setReadOnly(True) # Prevent renaming for now to avoid complexity
        layout.addWidget(self.name_input)
        
        # App List
        layout.addWidget(QLabel("Select Applications:"))
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search apps...")
        self.search_input.setStyleSheet("color: white; border: 1px solid #00FFFF; padding: 5px; border-radius: 5px;")
        self.search_input.textChanged.connect(self.filter_apps)
        layout.addWidget(self.search_input)
        
        # Scroll Area for Apps
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        
        self.app_checkboxes = {}
        system_apps = self.manager.get_system_apps()
        current_apps = []
        if workspace_name:
            current_apps = self.manager.get_workspace_apps(workspace_name)
            
        for app_name in system_apps:
            cb = QCheckBox(app_name)
            if app_name in current_apps:
                cb.setChecked(True)
            self.scroll_layout.addWidget(cb)
            self.app_checkboxes[app_name] = cb
            
        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = ModernButton("Save Workspace", "#00FFFF")
        save_btn.clicked.connect(self.save_workspace)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = ModernButton("Cancel", "#FF5555")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)

    def center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def save_workspace(self):
        name = self.name_input.text().strip()
        if not name:
            return 
        
        selected_apps = []
        for app_name, cb in self.app_checkboxes.items():
            if cb.isChecked():
                selected_apps.append(app_name)
        
        self.manager.create_workspace(name, selected_apps)
        self.close()

    def filter_apps(self, text):
        text = text.lower()
        for app_name, cb in self.app_checkboxes.items():
            if text in app_name.lower():
                cb.show()
            else:
                cb.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()

class WorkspaceSelector(QMainWindow):
    def __init__(self, manager, mode="LAUNCH"): # mode: LAUNCH, EDIT, REMOVE
        super().__init__()
        self.manager = manager
        self.mode = mode
        self.setWindowTitle("Select Workspace")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(400, 500)
        self.center_on_screen()
        
        # Main Layout
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.central_widget.setStyleSheet("""
            #CentralWidget {
                background-color: rgba(10, 10, 20, 240);
                border: 2px solid #574B90;
                border-radius: 20px;
            }
            QLabel { color: white; }
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid #555;
                font-size: 16px;
                color: white;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 10px;
            }
            QListWidget::item:selected {
                background-color: #574B90;
                color: white;
            }
        """)
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        
        # Header
        header = QLabel(f"{mode.title()} Workspace")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #574B90;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # List
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search workspaces...")
        self.search_input.setStyleSheet("color: white; border: 1px solid #574B90; padding: 5px; border-radius: 5px;")
        self.search_input.textChanged.connect(self.filter_workspaces)
        layout.addWidget(self.search_input)
        
        self.list_widget = QListWidget()
        workspaces = self.manager.get_workspace_names()
        for ws in workspaces:
            self.list_widget.addItem(ws)
        layout.addWidget(self.list_widget)
        
        # Hint label
        hint = QLabel("Select a workspace")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(hint)
        
        # Actions
        btn_layout = QHBoxLayout()
        
        action_color = "#574B90"
        if mode == "REMOVE":
            action_color = "#FF5555"
        
        action_btn = ModernButton(mode.title(), action_color)
        action_btn.clicked.connect(self.perform_action)
        btn_layout.addWidget(action_btn)
        
        cancel_btn = ModernButton("Cancel", "#888")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)

    def center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def perform_action(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        name = selected_items[0].text()
        
        if self.mode == "LAUNCH":
            self.manager.launch_workspace(name)
            self.close()
        elif self.mode == "REMOVE":
            self.manager.delete_workspace(name)
            self.close()
        elif self.mode == "EDIT":
            self.close()
            # Open Editor
            self.editor = WorkspaceEditor(self.manager, name)
            self.editor.show()
    
    def filter_workspaces(self, text):
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()

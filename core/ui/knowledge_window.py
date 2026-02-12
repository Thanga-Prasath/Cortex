from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QScrollArea, QFrame, 
                             QGridLayout, QPushButton, QStackedWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette
from .styles import get_stylesheet, THEME_COLORS
import json
import os

# --- 1. Custom UI Components ---

class ClickableCard(QFrame):
    """A premium interactive card with hover effects."""
    def __init__(self, title, subtitle, icon="📁", accent="#39FF14", callback=None):
        super().__init__()
        self.callback = callback
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("BentoCard")
        self.setMinimumSize(180, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.setStyleSheet(f"""
            QFrame#BentoCard {{
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 15px;
            }}
            QFrame#BentoCard:hover {{
                background-color: #252526;
                border: 1.5px solid {accent};
            }}
            QLabel {{ color: white; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 40px; margin-bottom: 5px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {accent};")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Subtitle
        self.sub_label = QLabel(subtitle)
        self.sub_label.setStyleSheet("font-size: 11px; color: #888;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_label)

    def mousePressEvent(self, event):
        if self.callback: self.callback()
        super().mousePressEvent(event)

class FunctionCard(QFrame):
    """Smaller card for individual intents/functions with expand logic."""
    def __init__(self, tag, data, accent="#39FF14"):
        super().__init__()
        self.tag = tag
        self.data = data
        self.accent = accent
        self.expanded = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 5px;
            }}
            QFrame:hover {{
                border: 1px solid {accent};
                background-color: #333;
            }}
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)

        # Header Row
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        icon = QLabel("⚙️")
        icon.setFixedWidth(25)
        h_layout.addWidget(icon)
        
        label = QLabel(tag)
        label.setStyleSheet("color: #eee; font-size: 14px; font-weight: bold; border:none;")
        h_layout.addWidget(label)
        
        self.arrow = QLabel("▼" if self.expanded else "▶")
        self.arrow.setStyleSheet(f"color: {accent}; font-weight: bold; border:none;")
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignRight)
        h_layout.addWidget(self.arrow)
        
        self.main_layout.addWidget(header)

        # Hidden Detail Area
        self.details = QWidget()
        self.details.setVisible(False)
        d_layout = QVBoxLayout(self.details)
        d_layout.setContentsMargins(30, 5, 10, 5)
        
        patterns = data.get('patterns', [])
        if patterns:
            p_label = QLabel("<b>Triggers:</b>")
            p_label.setStyleSheet("color: #888; border:none;")
            d_layout.addWidget(p_label)
            
            # Sub-container for extra patterns
            self.p_container = QWidget()
            pc_layout = QVBoxLayout(self.p_container)
            pc_layout.setContentsMargins(0, 0, 0, 0)
            pc_layout.setSpacing(2)
            
            for i, p in enumerate(patterns):
                pl = QLabel(f"• {p}")
                pl.setStyleSheet("color: #ccc; font-size: 11px; border:none;")
                pl.setWordWrap(True)
                pc_layout.addWidget(pl)
                if i >= 5: pl.setVisible(False) # Hide extras
            
            d_layout.addWidget(self.p_container)
            
            if len(patterns) > 5:
                self.btn_more = QPushButton(f"+ {len(patterns)-5} more...")
                self.btn_more.setCursor(Qt.CursorShape.PointingHandCursor)
                self.btn_more.setStyleSheet(f"""
                    QPushButton {{
                        color: {accent};
                        border: 1px solid #444;
                        border-radius: 5px;
                        padding: 2px 10px;
                        font-size: 10px;
                        text-align: left;
                    }}
                    QPushButton:hover {{ background: #444; }}
                """)
                self.btn_more.clicked.connect(self.reveal_all_patterns)
                d_layout.addWidget(self.btn_more)

        responses = data.get('responses', [])
        if responses:
            r_label = QLabel("<br><b>Sample Response:</b>")
            r_label.setStyleSheet("color: #888; border:none;")
            d_layout.addWidget(r_label)
            rl = QLabel(responses[0])
            rl.setStyleSheet("color: #aaa; font-size: 11px; font-style: italic; border:none;")
            rl.setWordWrap(True)
            d_layout.addWidget(rl)

        self.main_layout.addWidget(self.details)

    def reveal_all_patterns(self):
        """Show all hidden pattern labels."""
        layout = self.p_container.layout()
        for i in range(layout.count()):
            layout.itemAt(i).widget().setVisible(True)
        self.btn_more.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_expand()
        super().mousePressEvent(event)

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.details.setVisible(self.expanded)
        self.arrow.setText("▼" if self.expanded else "▶")
        # Update styling to highlight expanded state
        if self.expanded:
            self.setStyleSheet(f"QFrame {{ background-color: #333; border: 1.5px solid {self.accent}; border-radius: 10px; padding: 5px; }}")
        else:
            self.setStyleSheet(f"QFrame {{ background-color: #2a2a2a; border: 1px solid #444; border-radius: 10px; padding: 5px; }}")


# --- 2. Main Window ---

class KnowledgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cortex Intelligence - Knowledge Hub")
        self.setGeometry(150, 150, 1000, 750)
        
        # Theme
        try:
            config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
            with open(config_path, 'r') as f:
                theme = json.load(f).get("theme", "Neon Green")
        except: theme = "Neon Green"
        self.setStyleSheet(get_stylesheet(theme))
        self.accent_color = THEME_COLORS.get(theme, "#39FF14")

        # Layout Logic
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_layout = QVBoxLayout(self.central)
        
        # 1. Header with Breadcrumbs & Search
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background: #111; border-bottom: 1px solid #222;")
        h_layout = QHBoxLayout(header)
        
        self.breadcrumb = QLabel("<b>KNOWLEDGE HUB</b>")
        self.breadcrumb.setStyleSheet(f"font-size: 18px; color: {self.accent_color}; margin-left: 10px;")
        h_layout.addWidget(self.breadcrumb)
        
        h_layout.addStretch()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search all functions...")
        self.search_bar.setFixedWidth(350)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background: #1e1e1e;
                border: 1px solid #444;
                border-radius: 18px;
                padding: 8px 15px;
                color: white;
            }
            QLineEdit:focus { border: 1.5px solid #555; }
        """)
        self.search_bar.textChanged.connect(self.handle_search)
        h_layout.addWidget(self.search_bar)
        
        self.btn_back = QPushButton("← Back")
        self.btn_back.setFixedWidth(80)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setVisible(False)
        self.btn_back.clicked.connect(self.go_home)
        h_layout.addWidget(self.btn_back)
        
        self.main_layout.addWidget(header)

        # 2. Content Stack
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # Page: Hub Grid
        self.hub_scroll = QScrollArea()
        self.hub_scroll.setWidgetResizable(True)
        self.hub_scroll.setStyleSheet("background: transparent; border: none;")
        self.hub_content = QWidget()
        self.hub_grid = QGridLayout(self.hub_content)
        self.hub_grid.setContentsMargins(30, 30, 30, 30)
        self.hub_grid.setSpacing(25)
        self.hub_scroll.setWidget(self.hub_content)
        self.stack.addWidget(self.hub_scroll)
        
        # Page: Category Detail
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setStyleSheet("background: transparent; border: none;")
        self.detail_content = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_content)
        self.detail_layout.setContentsMargins(40, 20, 40, 40)
        self.detail_scroll.setWidget(self.detail_content)
        self.stack.addWidget(self.detail_scroll)

        # Metadata Cache
        self.all_intents = {} # {category: [intents]}
        self.load_data()

    def load_data(self):
        intents_dir = os.path.join(os.getcwd(), 'data', 'intents')
        if not os.path.exists(intents_dir): return
        
        files = sorted([f for f in os.listdir(intents_dir) if f.endswith('.json')])
        
        icon_map = {
            "automation": "⚡", "system": "🖥️", "media": "🎵", "general": "💬",
            "files": "📁", "apps": "🚀", "browser": "🌐", "window": "🪟", "workspace": "🏢"
        }
        
        row, col = 0, 0
        for filename in files:
            cat_key = filename.replace('.json', '')
            cat_name = cat_key.capitalize()
            
            try:
                with open(os.path.join(intents_dir, filename), 'r') as f:
                    data = json.load(f)
                intents = data.get('intents', [])
                self.all_intents[cat_key] = intents
                
                # Create Tile
                icon = icon_map.get(cat_key, "📦")
                tile = ClickableCard(cat_name, f"{len(intents)} Functions", icon, self.accent_color, 
                                     lambda c=cat_key: self.show_category(c))
                self.hub_grid.addWidget(tile, row, col)
                
                col += 1
                if col > 3: # 4 Columns
                    col = 0
                    row += 1
                    
            except Exception as e: print(f"[Error] Hub load {filename}: {e}")

    def show_category(self, cat_key):
        """Transition to detailed list for a category."""
        # Clear previous safely
        while self.detail_layout.count():
            child = self.detail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            
        intents = self.all_intents.get(cat_key, [])
        cat_name = cat_key.capitalize()
        
        # Add Title & Summary
        title = QLabel(f"<span style='color: {self.accent_color};'>{cat_name}</span> Environment")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 5px;")
        self.detail_layout.addWidget(title)
        
        desc = QLabel(f"Managed tools and automation for {cat_key} operations.")
        desc.setStyleSheet("color: #888; margin-bottom: 20px;")
        self.detail_layout.addWidget(desc)
        
        # Add Function List (Full width to avoid stretching neighbors)
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setSpacing(12)
        self.detail_layout.addWidget(list_container)
        
        for i in intents:
            card = FunctionCard(i['tag'], i, self.accent_color)
            list_layout.addWidget(card)
        
        self.detail_layout.addStretch()
        
        # UI State
        self.breadcrumb.setText(f"KNOWLEDGE HUB > <b>{cat_name.upper()}</b>")
        self.btn_back.setVisible(True)
        self.stack.setCurrentIndex(1)

    def go_home(self):
        self.stack.setCurrentIndex(0)
        self.btn_back.setVisible(False)
        self.breadcrumb.setText("<b>KNOWLEDGE HUB</b>")
        self.search_bar.clear()

    def handle_search(self, text):
        """Powerful search that filters either Hub tiles or Detail cards."""
        text = text.lower()
        if self.stack.currentIndex() == 0:
            # Filter Hub Tiles
            for i in range(self.hub_grid.count()):
                widget = self.hub_grid.itemAt(i).widget()
                if isinstance(widget, ClickableCard):
                    widget.setVisible(text in widget.title_label.text().lower())
        else:
            # Filter Detail Cards
            # Get the grid inside detail_layout (it's at index 2)
            grid_widget = self.detail_layout.itemAt(2).widget()
            grid = grid_widget.layout()
            for i in range(grid.count()):
                widget = grid.itemAt(i).widget()
                if isinstance(widget, FunctionCard):
                    # Match tag or patterns
                    match = text in widget.tag.lower() or any(text in p.lower() for p in widget.data.get('patterns', []))
                    widget.setVisible(match)

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QScrollArea, QFrame, 
                             QGridLayout, QPushButton, QStackedWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette
from .styles import get_stylesheet, THEME_COLORS, apply_glow_effect, get_theme_color
import json
import os
from core.utils.path_utils import get_base_path, get_data_path, get_user_data_path

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
                background-color: #1A1A1A;
                border: 1px solid #282828;
                border-radius: 12px;
            }}
            QFrame#BentoCard:hover {{
                background-color: #222222;
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
                background-color: #1A1A1A;
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 5px;
            }}
            QFrame:hover {{
                border: 1px solid {accent};
                background-color: #222222;
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
            self.setStyleSheet(f"QFrame {{ background-color: #222222; border: 1.5px solid {self.accent}; border-radius: 8px; padding: 5px; }}")
        else:
            self.setStyleSheet(f"QFrame {{ background-color: #1A1A1A; border: 1px solid #282828; border-radius: 8px; padding: 5px; }}")


# --- 2. Main Window ---

class KnowledgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cortex Intelligence - Knowledge Hub")
        self.setGeometry(150, 150, 850, 600)
        
        # Theme
        try:
            config_path = os.path.join(get_user_data_path(), "user_config.json")
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
        self.breadcrumb.setObjectName("Header")
        self.breadcrumb.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {self.accent_color}; margin-left: 10px; border: none;")
        apply_glow_effect(self.breadcrumb, theme, blur_radius=15)
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

        # Page: Search Results (global, cross-category)
        self.search_scroll = QScrollArea()
        self.search_scroll.setWidgetResizable(True)
        self.search_scroll.setStyleSheet("background: transparent; border: none;")
        self.search_content = QWidget()
        self.search_layout = QVBoxLayout(self.search_content)
        self.search_layout.setContentsMargins(40, 20, 40, 40)
        self.search_layout.setSpacing(8)
        self.search_scroll.setWidget(self.search_content)
        self.stack.addWidget(self.search_scroll)  # index 2

        # Metadata Cache
        self.all_intents = {} # {category: [intents]}
        self.load_data()

    def load_data(self):
        intents_dir = os.path.join(get_data_path(), 'intents')
        terminal_file = os.path.join(get_data_path(), 'terminal_commands.json')
        
        # 1. Load Intent Files
        if os.path.exists(intents_dir):
            files = sorted([f for f in os.listdir(intents_dir) if f.endswith('.json')])
            for filename in files:
                cat_key = filename.replace('.json', '')
                try:
                    with open(os.path.join(intents_dir, filename), 'r') as f:
                        data = json.load(f)
                    self.all_intents[cat_key] = data.get('intents', [])
                except Exception as e: print(f"[Error] Intent load {filename}: {e}")

        # 2. Load Terminal Commands & Merge
        if os.path.exists(terminal_file):
            try:
                with open(terminal_file, 'r') as f:
                    term_data = json.load(f)
                
                for cat_key, commands in term_data.items():
                    # Transform to intent format
                    intent_style_list = []
                    for cmd_key, cmd_data in commands.items():
                        intent_style_list.append({
                            "tag": cmd_key.replace('_', ' ').title(),
                            "patterns": cmd_data.get('patterns', []),
                            "responses": ["[Terminal Command] Executes system shell operation."]
                        })
                    
                    if cat_key in self.all_intents:
                        self.all_intents[cat_key].extend(intent_style_list)
                    else:
                        self.all_intents[cat_key] = intent_style_list
            except Exception as e: print(f"[Error] Terminal load: {e}")

        # 3. Create Hub Tiles
        icon_map = {
            "automation":       "⚡",
            "system":           "🖥️",
            "media":            "🎵",
            "general":          "💬",
            "files":            "📁",
            "apps":             "🚀",
            "browser":          "🌐",
            "window":           "🪟",
            "workspaces":       "🏢",   # matches workspaces.json → key 'workspaces'
            "workspace":        "🏢",   # fallback alias
            "productivity":     "✏️",
            "conversational":   "🗣️",
            "developer":        "👨\u200d💻",
            "network_advanced": "📡",
            "power_user":       "🛠️",
            "file_ops":         "🗄️",
            "voice_control":    "🎙️",
        }

        # Human-readable display names per category key
        name_map = {
            "apps":             "Applications",
            "automation":       "Automation",
            "conversational":   "Conversational AI",
            "files":            "File Manager",
            "general":          "General",
            "media":            "Media",
            "productivity":     "Productivity",
            "system":           "System",
            "window":           "Window Control",
            "workspaces":       "Workspaces",
            "workspace":        "Workspaces",
        }
        
        row, col = 0, 0
        # Sort with a priority order so important categories appear first
        priority = ["apps", "window", "workspaces", "files", "automation",
                    "productivity", "system", "conversational", "general", "media"]
        all_keys = list(self.all_intents.keys())
        ordered = [k for k in priority if k in all_keys] + sorted([k for k in all_keys if k not in priority])
        for cat_key in ordered:
            intents = self.all_intents[cat_key]
            if not intents: continue
            
            cat_name = name_map.get(cat_key, cat_key.replace('_', ' ').title())
            icon = icon_map.get(cat_key, "📦")
            
            tile = ClickableCard(cat_name, f"{len(intents)} Capabilities", icon, self.accent_color,
                                 lambda c=cat_key: self.show_category(c))
            self.hub_grid.addWidget(tile, row, col)
            
            col += 1
            if col > 3: # 4 Columns
                col = 0
                row += 1

    def show_category(self, cat_key):
        """Transition to detailed list for a category."""
        # Clear previous safely
        while self.detail_layout.count():
            child = self.detail_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            
        intents = self.all_intents.get(cat_key, [])
        
        # Build name_map locally if not in scope (show_category is called independently)
        _name_map = {
            "apps": "Applications", "automation": "Automation",
            "conversational": "Conversational AI", "files": "File Manager",
            "general": "General", "media": "Media", "productivity": "Productivity",
            "system": "System", "window": "Window Control",
            "workspaces": "Workspaces", "workspace": "Workspaces",
        }
        cat_name = _name_map.get(cat_key, cat_key.replace('_', ' ').title())
        
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
        # Clear search page so stale results don't linger
        self._clear_layout(self.search_layout)

    def _clear_layout(self, layout):
        """Remove all widgets from a layout recursively."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def handle_search(self, text):
        """Global search across all categories when on hub page.
        Category-detail search when browsing a specific category."""
        text = text.lower().strip()

        if self.stack.currentIndex() == 1:
            # ── In-category filter: search within the open category's FunctionCards ──
            try:
                list_widget = self.detail_layout.itemAt(2).widget()
                if list_widget:
                    layout = list_widget.layout()
                    for i in range(layout.count()):
                        widget = layout.itemAt(i).widget()
                        if isinstance(widget, FunctionCard):
                            match = (
                                not text
                                or text in widget.tag.lower()
                                or any(text in p.lower() for p in widget.data.get('patterns', []))
                                or any(text in k.lower() for k in widget.data.get('keywords', []))
                                or any(text in a.lower() for a in widget.data.get('anchors', []))
                            )
                            widget.setVisible(match)
            except Exception:
                pass
            return

        # ── Hub page: global cross-category search ────────────────────────────
        if not text:
            # Empty search → go back to hub grid
            self.stack.setCurrentIndex(0)
            self.btn_back.setVisible(False)
            self.breadcrumb.setText("<b>KNOWLEDGE HUB</b>")
            return

        # Build results
        self._build_search_results(text)

    def _build_search_results(self, query):
        """Search all intents across all categories and display results on page 2."""
        self._clear_layout(self.search_layout)

        _name_map = {
            "apps": "Applications", "automation": "Automation",
            "conversational": "Conversational AI", "files": "File Manager",
            "general": "General", "media": "Media", "productivity": "Productivity",
            "system": "System", "window": "Window Control",
            "workspaces": "Workspaces", "workspace": "Workspaces",
        }

        total_hits = 0

        for cat_key, intents in self.all_intents.items():
            matches = []
            for intent in intents:
                tag = intent.get('tag', '')
                patterns  = intent.get('patterns', [])
                keywords  = intent.get('keywords', [])
                anchors   = intent.get('anchors', [])
                responses = intent.get('responses', [])

                # Search across every text field
                hit = (
                    query in tag.lower()
                    or any(query in p.lower() for p in patterns)
                    or any(query in k.lower() for k in keywords)
                    or any(query in a.lower() for a in anchors)
                    or any(query in r.lower() for r in responses)
                )
                if hit:
                    matches.append(intent)

            if not matches:
                continue

            total_hits += len(matches)
            cat_name = _name_map.get(cat_key, cat_key.replace('_', ' ').title())

            # ── Category group header ──
            grp_header = QFrame()
            grp_header.setStyleSheet(
                f"QFrame {{ background: #1a1a1a; border-left: 3px solid {self.accent_color};"
                f" border-radius: 0; padding: 6px 14px; margin-top: 14px; }}"
            )
            grp_h_layout = QHBoxLayout(grp_header)
            grp_h_layout.setContentsMargins(10, 4, 10, 4)

            cat_lbl = QLabel(cat_name.upper())
            cat_lbl.setStyleSheet(
                f"color: {self.accent_color}; font-size: 13px; font-weight: bold; border: none;"
            )
            grp_h_layout.addWidget(cat_lbl)

            count_lbl = QLabel(f"{len(matches)} match{'es' if len(matches) != 1 else ''}")
            count_lbl.setStyleSheet("color: #666; font-size: 11px; border: none;")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grp_h_layout.addWidget(count_lbl)

            # Clickable header → opens that category detail view
            grp_header.setCursor(Qt.CursorShape.PointingHandCursor)
            grp_header.mousePressEvent = lambda e, c=cat_key: self.show_category(c)

            self.search_layout.addWidget(grp_header)

            # ── Matched FunctionCards ──
            for intent in matches:
                card = FunctionCard(intent['tag'], intent, self.accent_color)
                self.search_layout.addWidget(card)

        # ── Summary header / no-results state ──
        if total_hits == 0:
            no_result = QLabel(f'No results found for  "<b>{query}</b>"')
            no_result.setStyleSheet("color: #666; font-size: 14px; margin: 40px auto;")
            no_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.search_layout.insertWidget(0, no_result)
        else:
            summary = QLabel(
                f'<b style="color:{self.accent_color}">{total_hits}</b>'
                f' result{"s" if total_hits != 1 else ""} for '
                f'"<b>{query}</b>" across all categories'
            )
            summary.setStyleSheet("color: #aaa; font-size: 13px; margin-bottom: 4px;")
            self.search_layout.insertWidget(0, summary)

        self.search_layout.addStretch()

        # ── Show search page ──
        self.breadcrumb.setText(
            f"KNOWLEDGE HUB &gt; <b>SEARCH: {query.upper()}</b>"
        )
        self.btn_back.setVisible(True)
        self.stack.setCurrentIndex(2)

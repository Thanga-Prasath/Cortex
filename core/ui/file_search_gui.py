"""
Unified File Search & Results Viewer
- Fallback Mode: Appears when voice search returns no results (typed input).
- Results Mode: Displays all found files/folders with actions (Open / Open Location).
"""

import os
import sys
import platform
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QScrollArea,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor


# ── Result Card Widget ───────────────────────────────────────────────────────

class ResultCard(QFrame):
    """A single card representing a search result with actions."""
    
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("ResultCard")
        accent = "#39FF14"
        self.setStyleSheet(f"""
            QFrame#ResultCard {{
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 8px;
                margin-bottom: 2px;
            }}
            QFrame#ResultCard:hover {{
                border: 1px solid {accent};
                background-color: #333;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(15)

        # Icon/Type indicator
        icon_lbl = QLabel("📁" if self.result['type'] == 'dir' else "📄")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
        layout.addWidget(icon_lbl)

        # Info column
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        
        name = os.path.basename(self.result['path'])
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {accent if self.result.get('exact') else '#eee'};")
        
        path_lbl = QLabel(self.result['path'])
        path_lbl.setFont(QFont("Segoe UI", 8))
        path_lbl.setStyleSheet("color: #888;")
        path_lbl.setWordWrap(True)

        info_col.addWidget(name_lbl)
        info_col.addWidget(path_lbl)
        layout.addLayout(info_col, 1)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.open_btn = QPushButton("Open")
        self.open_btn.setToolTip("Open File/Folder")
        self._style_action_btn(self.open_btn, accent)
        self.open_btn.clicked.connect(self._on_open)

        self.loc_btn = QPushButton("Location")
        self.loc_btn.setToolTip("Open Folder Location")
        self._style_action_btn(self.loc_btn, "#00FFFF") # Cyber Blue
        self.loc_btn.clicked.connect(self._on_open_location)

        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.loc_btn)
        layout.addLayout(btn_layout)

    def _style_action_btn(self, btn, color):
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(90, 30) # Slightly larger
        btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: 2px solid {color};
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #000;
            }}
        """)

    def _on_open(self):
        path = self.result['path']
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            print(f"Error opening item: {e}")

    def _on_open_location(self):
        path = self.result['path']
        try:
            if os.name == 'nt':
                # Opens explorer and selects the file
                subprocess.Popen(f'explorer /select,"{os.path.abspath(path)}"')
            elif platform.system() == 'Darwin':
                # Similar for Mac
                subprocess.Popen(['open', '-R', path])
            else:
                # Linux (standard way to open parent)
                parent = os.path.dirname(path)
                subprocess.Popen(['xdg-open', parent])
        except Exception as e:
            print(f"Error opening location: {e}")


# ── Main Dialog ──────────────────────────────────────────────────────────────

class FileSearchDialog(QWidget):
    """
    A unified search interface.
    - Fallback: Input box for typed search.
    - Results: Scrollable list of matches.
    """

    ACCENT = "#39FF14"

    def __init__(self, initial_query="", status_window=None):
        super().__init__()
        self.status_window = status_window
        self._setup_ui(initial_query)

    def _setup_ui(self, initial_query):
        self.setWindowTitle("Cortex Search")
        
        # User requested:
        # 1. Bigger GUI (width 800)
        # 2. Maximize/Minimize possible
        # 3. Independent from Status Window (Not always on top)
        # 4. Standard window controls (remove FramelessWindowHint)
        
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
        
        # Background color for the whole widget
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # ── Header ──
        self.title_lbl = QLabel("File Search Results")
        self.title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {self.ACCENT};")
        self.layout.addWidget(self.title_lbl)

        # ── Search Input (Always visible) ──
        input_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search again...")
        self.search_input.setText(initial_query)
        self.search_input.setFont(QFont("Segoe UI", 12))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #2d2d30;
                color: #fff;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 10px 15px;
            }}
            QLineEdit:focus {{ border: 1px solid {self.ACCENT}; }}
        """)
        self.search_input.returnPressed.connect(self._on_manual_search)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedHeight(44)
        self.search_btn.setMinimumWidth(100)
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.ACCENT};
                color: #000;
                font-weight: bold;
                font-size: 11pt;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #55FF40; }}
        """)
        self.search_btn.clicked.connect(self._on_manual_search)

        input_row.addWidget(self.search_input)
        input_row.addWidget(self.search_btn)
        self.layout.addLayout(input_row)

        # ── Results Area (Hidden by default) ──
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #333; background: transparent; border-radius: 8px; }
            QScrollBar:vertical {
                border: none; background: #1e1e1e; width: 10px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #444; min-height: 20px; border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; }
        """)
        self.scroll_content = QWidget()
        self.results_layout = QVBoxLayout(self.scroll_content)
        self.results_layout.setContentsMargins(10, 10, 10, 10)
        self.results_layout.setSpacing(10)
        self.results_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        self.scroll.hide()
        self.layout.addWidget(self.scroll)

        # ── Status Label ──
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #aaa; font-size: 10pt;")
        self.status_lbl.setWordWrap(True)
        self.layout.addWidget(self.status_lbl)

        self._center()

    def closeEvent(self, event):
        """Ensure search animation stops when GUI is closed."""
        if self.status_window:
            self.status_window.set_searching_state(False)
        event.accept()

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry().center()
        geo = self.frameGeometry()
        geo.moveCenter(screen)
        self.move(geo.topLeft())

    # ── Input Handling ───────────────────────────────────────────────────────

    def _on_manual_search(self):
        query = self.search_input.text().strip()
        if not query: return
        if self.status_window:
            self.status_window.set_searching_state(True)
            
        self.status_lbl.setText("Searching across all partitions...")
        self.search_btn.setEnabled(False)
        
        # We invoke the search worker
        from core.ui.file_search_gui import SearchWorker
        self.worker = SearchWorker(query)
        self.worker.finished.connect(self.show_results)
        if self.status_window:
            self.worker.count_update.connect(self.status_window.update_search_count)
        self.worker.start()

    # ── Results Mode ──────────────────────────────────────────────────────────

    def show_results(self, results):
        if self.status_window:
            self.status_window.set_searching_state(False)
            
        self.search_btn.setEnabled(True)
        
        # Clear previous
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self.status_lbl.setText(f"No results found for '{self.search_input.text()}'. Try a broader term.")
            self.scroll.hide()
            return

        self.scroll.show()
        for r in results:
            card = ResultCard(r)
            self.results_layout.insertWidget(self.results_layout.count()-1, card)

        self.status_lbl.setText(f"Successfully identified {len(results)} items matching your query.")
        
        # Adjust height based on results, up to a max
        if self.isMaximized():
            return
            
        self.adjustSize()
        max_h = 800
        if self.height() > max_h:
            self.setFixedHeight(max_h)
        self._center()

# ── Threaded Search Worker (Reused) ──────────────────────────────────────────

class SearchWorker(QThread):
    finished = pyqtSignal(list)
    count_update = pyqtSignal(int)
    
    def __init__(self, query):
        super().__init__()
        self.query = query
    def run(self):
        from components.file_manager.search import _get_partitions, _search_partition_windows, _search_partition_linux
        import threading as _threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import os

        partitions, results_lock, all_results = _get_partitions(), _threading.Lock(), []
        is_windows = os.name == 'nt'
        linux_prio = [mp for mp, _ in partitions if mp != '/'] if not is_windows else []

        # Multi-platform adapter to send signal updates
        class SignalQueue:
            def __init__(self, signal): self.signal = signal
            def put(self, msg):
                if isinstance(msg, tuple) and msg[0] == "SEARCH_COUNT":
                    self.signal.emit(msg[1])
        
        sig_queue = SignalQueue(self.count_update)

        with ThreadPoolExecutor(max_workers=min(len(partitions), 8)) as executor:
            futures = []
            for mp, label in partitions:
                if is_windows:
                    futures.append(executor.submit(_search_partition_windows, mp, label, self.query, results_lock, all_results, sig_queue))
                else:
                    futures.append(executor.submit(_search_partition_linux, mp, label, self.query, results_lock, all_results, sig_queue, linux_prio if mp == '/' else None))
            for f in as_completed(futures): pass

        all_results.sort(key=lambda r: (not r['exact'], r['path'].lower()))
        seen, unique = set(), []
        for r in all_results:
            if r['path'] not in seen:
                seen.add(r['path']); unique.append(r)
                self.count_update.emit(len(unique))
        self.finished.emit(unique)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Mock results
    results = [
        {'path': 'C:\\Users\\User\\Documents\\Project\\cortex.py', 'type': 'file', 'exact': True},
        {'path': 'D:\\Backup\\cortex_stuff', 'type': 'dir', 'exact': False},
        {'path': 'C:\\Program Files\\Example\\readme.txt', 'type': 'file', 'exact': False},
    ] * 10
    w = FileSearchDialog(initial_query="cortex")
    w.show()
    w.show_results(results)
    sys.exit(app.exec())

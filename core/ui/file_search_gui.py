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
    QSizePolicy, QListWidget, QListWidgetItem
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
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(15)

        # Location Button (on the left)
        self.loc_btn = QPushButton("📂")
        self.loc_btn.setToolTip("Open Folder Location")
        self.loc_btn.setFixedSize(40, 40)
        self.loc_btn.setFont(QFont("Segoe UI Emoji", 16))
        self.loc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.loc_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #00FFFF;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00FFFF;
                color: #000;
            }
        """)
        self.loc_btn.clicked.connect(self._on_open_location)
        layout.addWidget(self.loc_btn)

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

    def mousePressEvent(self, event):
        """Make the entire card clickable to open the file/folder."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_open()
        super().mousePressEvent(event)

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
                subprocess.Popen(f'explorer /select,"{os.path.abspath(path)}"')
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', '-R', path])
            else:
                # Try DBus for advanced Linux file managers (Nautilus, Dolphin, Nemo)
                try:
                    import urllib.parse
                    file_uri = "file://" + urllib.parse.quote(os.path.abspath(path))
                    subprocess.run(
                        ['dbus-send', '--session', '--print-reply', '--dest=org.freedesktop.FileManager1', 
                         '/org/freedesktop/FileManager1', 'org.freedesktop.FileManager1.ShowItems',
                         f'array:string:"{file_uri}"', 'string:""'],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except Exception:
                    # Fallback if DBus approach fails
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
        self.initial_query = initial_query
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
        """Ensure specific search animation stops when GUI is closed."""
        if self.status_window:
            query = self.search_input.text().strip() or self.initial_query
            if query:
                self.status_window.set_searching_state((query, False))
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
        self.initial_query = query # Update tracking
        
        if self.status_window:
            self.status_window.set_searching_state((query, True))
            
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
            query = self.search_input.text().strip() or self.initial_query
            if query:
                self.status_window.set_searching_state((query, False))
            
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

# ── Cancel Search Dialog ─────────────────────────────────────────────────────

class CancelSearchDialog(QFrame):
    """A floating dialog showing all active searches with cancel buttons."""
    
    def __init__(self, active_searches, action_queue, status_window=None, parent=None):
        super().__init__(parent)
        self.active_searches = active_searches
        self.action_queue = action_queue
        self.status_window = status_window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(400, 300)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Background Container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 240);
                border: 2px solid #39FF14;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Active Searches")
        header.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; border: none;")
        header_layout = QHBoxLayout()
        header_layout.addWidget(header)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                color: #FF4444;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        container_layout.addLayout(header_layout)

        # List Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        list_container = QWidget()
        list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        for search_query in self.active_searches:
            self._add_search_item(search_query)

        scroll.setWidget(list_container)
        container_layout.addWidget(scroll)
        main_layout.addWidget(container)

        self._center_on_screen()

    def _add_search_item(self, query):
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(50, 50, 50, 100);
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px;
            }
            QFrame:hover {
                border: 1px solid #39FF14;
            }
        """)
        h_layout = QHBoxLayout(item_frame)
        h_layout.setContentsMargins(5, 5, 5, 5)

        lbl = QLabel(query)
        lbl.setStyleSheet("color: white; font-size: 14px; border: none;")
        h_layout.addWidget(lbl)

        btn = QPushButton("Cancel")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FF4444;
                color: white;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #FF0000;
            }
        """)
        btn.clicked.connect(lambda _, q=query, f=item_frame: self._cancel_search(q, f))
        h_layout.addWidget(btn)
        
        self.list_layout.addWidget(item_frame)

    def _cancel_search(self, query, frame):
        if self.action_queue:
            self.action_queue.put(("CANCEL_SEARCH", query))
        self.remove_search(query)

    def remove_search(self, query):
        """Called externally (or internally) when a search finishes to update the dialog."""
        if query in self.active_searches:
            self.active_searches.remove(query)
            
        # Find and hide the specific frame
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            if item and item.widget():
                frame = item.widget()
                # Find the label in this frame
                lbl = frame.findChild(QLabel)
                if lbl and lbl.text() == query:
                    frame.hide()
                    break
                    
        # Check if list is practically empty
        visible_count = sum(1 for i in range(self.list_layout.count()) if not self.list_layout.itemAt(i).widget().isHidden())
        if visible_count == 0:
            self.close()

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


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

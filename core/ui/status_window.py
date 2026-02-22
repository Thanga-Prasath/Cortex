from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QMenu, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QRadialGradient, QAction
import ctypes
import platform
import os
import json
import math
import random
import re

class StatusWindow(QMainWindow):

    def __init__(self, reset_event=None, shutdown_event=None, action_queue=None):
        super().__init__()
        
        # Window Flags: Frameless, Always on Top, Tool (no taskbar icon)
        base_flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        if platform.system() == "Linux":
            # BypassWindowManagerHint fully hides from dock/taskbar on GNOME/KDE (X11 & Wayland)
            base_flags |= Qt.WindowType.BypassWindowManagerHint
        self.setWindowFlags(base_flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Config Paths
        self.config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        self.widget_config_path = os.path.join(os.getcwd(), 'data', 'widget_config.json')
        
        # Load Configs
        self.theme_accent = "#39FF14"
        self.widget_config = self.load_widget_config()
        self.load_theme_config()
        
        # Dimensions
        self.base_width = 140
        self.height_val = 50
        self.setFixedSize(self.base_width, self.height_val)
        self.setMinimumSize(self.base_width, self.height_val)
        self.setMaximumSize(900, self.height_val) # Allow expansion
        self.setGeometry(100, 100, self.base_width, self.height_val) 
        
        # Initial Position using Config
        if self.widget_config.get("x", -1) != -1 and self.widget_config.get("y", -1) != -1:
            self.move(self.widget_config["x"], self.widget_config["y"])
        else:
            self.position_default() # Smart default
        
        # State
        self.reset_event = reset_event
        self.shutdown_event = shutdown_event
        self.current_state = "IDLE"
        self.wave_phase = 0
        self.wave_amplitude = 10
        self.pulse_direction = 1
        self.bar_heights = [5, 10, 15, 10, 5] 
        self.drag_pos = None # For custom dragging
        
        # Concurrent Search Progress State
        self.action_queue = action_queue
        self.active_searches = {} # { query: { 'count': 0, 'progress': 0.0 } }
        self.hovered_search = None # Currently hovered query name
        self.setMouseTracking(True)
        
        # Cursor Update based on lock
        self.update_cursor()
        
        # GUI Module Manager (Lazy Loading)
        self.windows = {
            "hub": None,
            "automation": None,
            "settings": None,
            "knowledge": None
        }
        
        # Timer for animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(25) # 40 FPS for smoother motion
        
        # Enforce Always on Top (All Platforms)
        self.top_timer = QTimer()
        self.top_timer.timeout.connect(self.enforce_topmost)
        self.top_timer.start(200) # Increased frequency (200ms) for Windows Taskbar dominance

        # Colors - Neon Palette
        self.colors = {
            "IDLE": QColor(220, 220, 220, 255),       
            "LISTENING": QColor(57, 255, 20, 255),    
            "THINKING": QColor(255, 255, 0, 255),     
            "SPEAKING": QColor(138, 43, 226, 255),    
            "PROCESSING": QColor(0, 255, 255, 255)    
        }
    
    def load_theme_config(self):
        from .styles import THEME_COLORS
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    theme_name = data.get("theme", "Neon Green")
                    self.theme_accent = THEME_COLORS.get(theme_name, "#39FF14")
        except:
            self.theme_accent = "#39FF14"
                
    def enforce_topmost(self):
        # Windows-specific low-level enforcement
        if platform.system() == "Windows":
            try:
                import win32gui
                import win32con
                
                hwnd = int(self.winId())
                
                # Check if we are really the top window
                # GetForegroundWindow() checks if we have focus, but GetWindow(GW_HWNDPREV) checks Z-order
                # If we are not topmost, re-assert it forcefully
                
                hwnd = int(self.winId())
                # DIRECT TOPMOST ENFORCEMENT
                # We use HWND_TOPMOST (-1) directly. 
                # We add SWP_NOSENDCHANGING to prevent focus race conditions
                # And we ensure the window is shown/raised.
                flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW | win32con.SWP_NOACTIVATE
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
                
                # If we are not the foreground window and we should be "always on top"
                # we don't necessarily want to STEAL focus, but we must be ABOVE the others.
                # In some cases, Windows needs a second nudge.
                                      
            except ImportError:
                # Fallback to ctypes if pywin32 is missing (though we installed it)
                hwnd = int(self.winId())
                try:
                    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0053)
                except:
                    pass
            except Exception as e:
                # Silently ignore to avoid spamming console
                pass
        else:
            # Linux/macOS: Standard Qt raise to keep it visible
            self.raise_()

    def update_lock_state(self, is_locked):
        """Update lock state live without restarting."""
        self.widget_config["locked"] = is_locked
        self.update_cursor()
        print(f"[UI] Widget lock state updated: {is_locked}")

    def load_widget_config(self):
        if os.path.exists(self.widget_config_path):
            try:
                with open(self.widget_config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"x": -1, "y": -1, "locked": False}

    def save_widget_config(self):
        try:
            with open(self.widget_config_path, 'w') as f:
                json.dump(self.widget_config, f, indent=4)
        except Exception as e:
            print(f"Error saving widget config: {e}")

    def position_default(self):
        # Position bottom-right by default (Taskbar Overlay style)
        # We use geometry() instead of availableGeometry() to reach the taskbar area
        screen = self.screen().geometry()
        # We want it at the bottom right corner over the taskbar
        # Taskbar is usually ~40-50px. Widget is 50px.
        x = screen.width() - self.width_val - 10
        y = screen.height() - self.height_val - 5
        self.move(x, y)

    def update_cursor(self):
        if self.widget_config.get("locked", False):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mousePressEvent(self, event):
        # 1. Check for cancel clicks on search loaders
        if event.button() == Qt.MouseButton.LeftButton and self.hovered_search:
            if self.action_queue:
                q = self.hovered_search
                self.action_queue.put(("CANCEL_SEARCH", q))
                # Instantly remove from UI to prevent spam and ensure snappy response
                if q in self.active_searches:
                    del self.active_searches[q]
                self.hovered_search = None
                self._update_window_width()
                self.update()
            event.accept()
            return
            
        # 2. Check lock state dynamically for dragging
        if not self.widget_config.get("locked", False):
            if event.button() == Qt.MouseButton.LeftButton:
                from PyQt6.QtGui import QMouseEvent
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
        
        if event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        # 1. Handle hover logic for search cancel buttons
        if self.active_searches:
            circle_margin = 8.0
            circle_size = self.height_val - (circle_margin * 2)
            spacing = 5.0
            total_search_width = len(self.active_searches) * (circle_size + spacing)
            
            # Loaders are anchored to the left
            mx, my = event.pos().x(), event.pos().y()
            found_hover = None
            
            if mx < total_search_width and circle_margin <= my <= self.height_val - circle_margin:
                # Find which circle we are hovering
                for i, query in enumerate(list(self.active_searches.keys())):
                    start_x = circle_margin + (i * (circle_size + spacing))
                    if start_x <= mx <= start_x + circle_size:
                        found_hover = query
                        break
            
            if found_hover != self.hovered_search:
                self.hovered_search = found_hover
                if self.hovered_search:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    self.update_cursor()
                self.update()

        # 2. Handle dragging
        if not self.widget_config.get("locked", False):
            if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
                self.move(event.globalPosition().toPoint() - self.drag_pos)
                event.accept()

    def mouseReleaseEvent(self, event):
        # Prevent dragging if we just clicked a cancel button
        if self.hovered_search:
            return
            
        if not self.widget_config.get("locked", False) and self.drag_pos:
            self.drag_pos = None
            # Save Position
            self.widget_config["x"] = self.x()
            self.widget_config["y"] = self.y()
            self.save_widget_config()
            event.accept()

    def show_context_menu(self, position):
        """Show context menu with Reset option and New GUIs."""
        menu = QMenu(self)
        
        # Style the menu to match the neon theme
        # Style the menu to match the neon theme
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #1a1a1a;
                border: 2px solid {self.theme_accent};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                color: #FFFFFF;
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {self.theme_accent};
                color: #000000;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {self.theme_accent};
                margin: 5px 10px;
            }}
        """)
        
        # --- New GUI Modules ---
        hub_action = QAction("📊 Open Hub", self)
        hub_action.triggered.connect(lambda: self.open_module("hub"))
        menu.addAction(hub_action)

        auto_action = QAction("🧠 Neural Sync", self)
        auto_action.triggered.connect(lambda: self.open_module("automation"))
        menu.addAction(auto_action)
        
        settings_action = QAction("⚙️ Cortex Control", self)
        settings_action.triggered.connect(lambda: self.open_module("settings"))
        menu.addAction(settings_action)
        
        know_action = QAction("🌐 Knowledge Graph", self)
        know_action.triggered.connect(lambda: self.open_module("knowledge"))
        menu.addAction(know_action)
        
        menu.addSeparator()

        # --- System Actions ---
        reset_action = QAction("🔄 Reset Assistant", self)
        reset_action.triggered.connect(self.reset_assistant)
        menu.addAction(reset_action)
        
        exit_action = QAction("🛑 Exit Assistant", self)
        exit_action.triggered.connect(self.shutdown_assistant)
        menu.addAction(exit_action)
        
        menu.exec(position)

    def shutdown_assistant(self):
        """Signal the main process to shutdown the assistant."""
        print("[System] Shutdown requested. Signaling main process...")
        if self.shutdown_event:
            self.shutdown_event.set()
        else:
            # Fallback if event missing
            QApplication.quit()

    def log_activity(self, message):
        """Forward log message to Hub if it is open."""
        if self.windows["hub"] and self.windows["hub"].isVisible():
            self.windows["hub"].add_log_entry(message)

    def open_module(self, module_name):
        """Lazy load and show the requested UI module."""
        try:
            if self.windows[module_name] is None:
                print(f"[UI] Lazy loading module: {module_name}...")
                
                if module_name == "hub":
                    from core.ui.hub_window import HubWindow
                    self.windows["hub"] = HubWindow()
                    
                elif module_name == "automation":
                    from core.ui.automation_window import AutomationWindow
                    self.windows["automation"] = AutomationWindow()
                    
                elif module_name == "settings":
                    from core.ui.settings_window import SettingsWindow
                    self.windows["settings"] = SettingsWindow(self.reset_event, status_window=self)
                    
                elif module_name == "knowledge":
                    from core.ui.knowledge_window import KnowledgeWindow
                    self.windows["knowledge"] = KnowledgeWindow()
            
            # Show and Bring to Front
            window = self.windows[module_name]
            window.show()
            window.raise_()
            window.activateWindow()
            print(f"[UI] Opened {module_name}")
            
        except Exception as e:
            print(f"[Error] Failed to open module {module_name}: {e}")

    def reset_assistant(self):
        """Signal the main process to restart the assistant in-place."""
        print("[System] Reset requested. Signaling main process...")
        if self.reset_event:
            self.reset_event.set()  # Signal the main process
        else:
            print("[!] Reset event not available.")

    def update_status(self, status, data=None):
        # Validate status to prevent resizing from unexpected data
        valid_states = ["IDLE", "LISTENING", "THINKING", "SPEAKING", "PROCESSING"]
        if status in valid_states:
            self.current_state = status
            self.update() # Trigger repaint

    def set_searching_state(self, msg_data):
        """msg_data is either a tuple (query, True/False) or just backward-compatible boolean."""
        if isinstance(msg_data, tuple):
            query, is_searching = msg_data
            if is_searching:
                if query not in self.active_searches:
                    self.active_searches[query] = {"count": 0, "progress": 0.0}
            else:
                if query in self.active_searches:
                    del self.active_searches[query]
        else:
            # Backward compatibility clear-all
            if not msg_data:
                self.active_searches.clear()
        
        self._update_window_width()
        self.update()
    
    def update_search_count(self, msg_data):
        """Update the file counter for a specific search."""
        if isinstance(msg_data, tuple):
            query, count = msg_data
            if query in self.active_searches:
                self.active_searches[query]["count"] = count
                self.update()
                
    def _update_window_width(self):
        """Dynamically expand to the left based on active searches."""
        n = len(self.active_searches)
        # Loader width = 34 + 5 padding = ~40px per search
        extra_width = max(0, n * 40)
        new_width = self.base_width + extra_width
        
        if new_width != self.width():
            # Calculate difference to shift x position leftwards
            diff = new_width - self.width()
            self.setFixedSize(new_width, self.height_val)
            self.move(self.x() - diff, self.y())
    
    def closeEvent(self, event):
        """Stop timers before closing to prevent Qt event loop crashes."""
        self.anim_timer.stop()
        self.top_timer.stop()
        event.accept()

    def animate(self):
        try:
            if self.current_state == "SPEAKING":
                # Beatbox Animation: Randomize bar heights
                self.bar_heights = [random.randint(5, 20) for _ in range(5)]
                self.update()
                
            elif self.current_state == "THINKING":
                # Superimposed Sine Waves (Brain Waves)
                # Use two waves with different frequencies and phases for organic look
                self.wave_phase += 0.2
                
                for i in range(5):
                    # Primary slow wave
                    val1 = math.sin(self.wave_phase + (i * 0.5))
                    # Secondary fast wave
                    val2 = math.sin((self.wave_phase * 1.5) + (i * 0.8))
                    
                    # Combine and map to height (range 3 to 18)
                    combined = (val1 + val2) / 2 # -1 to 1
                    height = 10 + (combined * 7) 
                    self.bar_heights[i] = max(3, int(height))
                self.update()

            elif self.current_state == "PROCESSING":
                # Smooth Gaussian Wave (Knight Rider / Cylon effect)
                speed = 0.4
                self.wave_phase += speed
                
                # Ping-pong the peak position between 0 and 4
                # Use sine to oscillate between -1 and 1, map to 0-4
                norm_pos = (math.sin(self.wave_phase) + 1) / 2 # 0 to 1
                peak_pos = norm_pos * 4.0 # 0 to 4.0 floating point
                
                # Sigma controls the width of the wave (spread)
                sigma = 0.8 
                
                for i in range(5):
                    # Gaussian function: e^(-(x - mu)^2 / (2*sigma^2))
                    # x=i, mu=peak_pos
                    diff = i - peak_pos
                    intensity = math.exp(-(diff * diff) / (2 * sigma * sigma))
                    
                    # Map intensity (0 to 1) to height (5 to 22)
                    height = 5 + (intensity * 17)
                    self.bar_heights[i] = int(height)
                self.update()
                
            elif self.current_state == "LISTENING":
                # Pulse Animation (Gentle Breathing)
                if self.wave_amplitude >= 15:
                    self.pulse_direction = -1
                elif self.wave_amplitude <= 5:
                    self.pulse_direction = 1
                    
                self.wave_amplitude += self.pulse_direction * 0.5
                self.bar_heights = [int(self.wave_amplitude)] * 5
                self.update()
                
            elif self.current_state == "IDLE":
                # Static low bars
                self.bar_heights = [5, 5, 5, 5, 5]
                self.update()

            # Handle concurrent search rotations independent of AI state
            if self.active_searches:
                for query, data in self.active_searches.items():
                    data["progress"] = (data["progress"] + 0.02) % 1.0
                self.update()
        except Exception as e:
            # Silently ignore animation errors to prevent crashes
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background Capsule
        # User requested transparent background
        rect = QRect(0, 0, self.width(), self.height())
        bg_color = QColor(0, 0, 0, 0) # Fully transparent
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, self.height()/2, self.height()/2)
        
        # Content based on state
        state_color = self.colors.get(self.current_state, self.colors["IDLE"])
        
        # ─── DYNAMIC LAYOUT FOR SEARCH ───
        padding_for_searches = max(0, len(self.active_searches) * 40) 
        content_rect = QRect(padding_for_searches, 0, self.base_width, self.height())

        if self.current_state in ["IDLE", "LISTENING"]:
            # Draw Text
            text = "Idle" if self.current_state == "IDLE" else "Listening"
            painter.setPen(QPen(state_color))
            font = painter.font()
            font.setPointSize(10 if self.active_searches else 12) 
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, text)

        elif self.current_state in ["SPEAKING", "PROCESSING", "THINKING"]:
            # Draw Vertical Bar Visualizer
            bar_width = 8
            gap = 4
            total_width = (5 * bar_width) + (4 * gap)
            
            # Center bars in the available content area (right side)
            start_x = content_rect.x() + (content_rect.width() - total_width) / 2
            mid_y = content_rect.height() / 2
            
            painter.setBrush(QBrush(state_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            for i, height in enumerate(self.bar_heights):
                x = start_x + (i * (bar_width + gap))
                h = height * 1.5 
                y = mid_y - (h / 2)
                painter.drawRoundedRect(int(x), int(y), int(bar_width), int(h), 4, 4)

        # ── [NEW] Concurrent Search Loaders ──
        if self.active_searches:
            from PyQt6.QtGui import QPainterPath, QFontMetrics
            from PyQt6.QtCore import QRectF
            
            circle_margin = 8.0
            circle_size = self.height() - (circle_margin * 2)
            spacing = 5.0
            
            font = painter.font()
            font.setBold(True)
            
            for i, (query, data) in enumerate(self.active_searches.items()):
                # Box for this specific loader
                start_x = circle_margin + (i * (circle_size + spacing))
                circle_rect = QRectF(start_x, circle_margin, circle_size, circle_size)
                
                if query == self.hovered_search:
                    # HOVER STATE: Red solid circle with X
                    painter.setBrush(QColor(255, 50, 50, 200))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(circle_rect)
                    
                    painter.setPen(QPen(QColor("#FFFFFF"), 2))
                    painter.drawLine(int(circle_rect.x()+10), int(circle_rect.y()+10), int(circle_rect.right()-10), int(circle_rect.bottom()-10))
                    painter.drawLine(int(circle_rect.x()+10), int(circle_rect.bottom()-10), int(circle_rect.right()-10), int(circle_rect.y()+10))
                    
                    # Tooltip Background & Text (Drawn slightly above the pill)
                    fm = QFontMetrics(font)
                    tt_text = query  # Removed repetitive "Cancel:"
                    tt_width = fm.horizontalAdvance(tt_text) + 16
                    tt_height = 24
                    
                    # Center the tooltip precisely over this specific circle
                    tt_x = circle_rect.center().x() - (tt_width / 2)
                    tt_y = 5  # Above the circle within the pill
                    
                    # Prevent tooltip from bleeding off the left edge
                    tt_x = max(5.0, tt_x)
                    
                    tt_rect = QRectF(tt_x, tt_y, tt_width, tt_height)
                    painter.setBrush(QColor(30, 30, 30, 240))
                    painter.setPen(QPen(QColor(self.theme_accent), 1))
                    painter.drawRoundedRect(tt_rect, 4, 4)
                    
                    painter.setPen(QColor("#FFFFFF"))
                    font.setPointSize(9)
                    painter.setFont(font)
                    painter.drawText(tt_rect, Qt.AlignmentFlag.AlignCenter, tt_text)

                else:
                    # NORMAL STATE: Loader animation
                    painter.setBrush(QColor(40, 40, 40, 180))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(circle_rect)
                    
                    path = QPainterPath()
                    path.addEllipse(circle_rect)
                    
                    search_pen = QPen(QColor(self.theme_accent), 3)
                    search_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    
                    circum = 3.14159 * circle_size
                    search_pen.setDashPattern([circum * 0.25, circum * 0.75])
                    search_pen.setDashOffset(data["progress"] * circum)
                    
                    painter.setPen(search_pen)
                    painter.drawPath(path)
                    
                    count_text = str(data["count"])
                    if data["count"] > 999: count_text = "99+"
                    
                    painter.setPen(QColor("#FFFFFF"))
                    font.setPointSize(8 if len(count_text) > 2 else 9)
                    painter.setFont(font)
                    painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, count_text)


from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel, QMenu, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QRadialGradient, QAction
import ctypes
import platform
import os

class StatusWindow(QMainWindow):
    def __init__(self, reset_event=None, shutdown_event=None):
        super().__init__()
        
        # Window Flags: Frameless, Always on Top, Tool (no taskbar icon)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Config & Theme
        self.config_path = os.path.join(os.getcwd(), 'data', 'user_config.json')
        self.theme_accent = "#39FF14"
        
        # Dimensions
        self.width_val = 140
        self.height_val = 50
        self.setGeometry(100, 100, self.width_val, self.height_val) 
        self.center_on_screen()
        
        # State
        self.reset_event = reset_event
        self.shutdown_event = shutdown_event
        self.current_state = "IDLE"
        self.wave_phase = 0
        self.wave_amplitude = 10
        self.pulse_direction = 1
        self.bar_heights = [5, 10, 15, 10, 5] # Initial heights for beatbox bars
        
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
        self.anim_timer.start(50)
        
        # Enforce Always on Top (All Platforms)
        self.top_timer = QTimer()
        self.top_timer.timeout.connect(self.enforce_topmost)
        self.top_timer.start(500) # Check every 500ms

        # Colors - Neon Palette
        self.colors = {
            "IDLE": QColor(220, 220, 220, 255),       # Neon White/Grey
            "LISTENING": QColor(57, 255, 20, 255),    # Neon Green
            "THINKING": QColor(255, 255, 0, 255),     # Neon Yellow
            "SPEAKING": QColor(138, 43, 226, 255),    # Neon Purple (BlueViolet)
            "PROCESSING": QColor(0, 255, 255, 255)    # Neon Cyan
        }
        
        # Load Config for Theme Colors
        self.load_theme_config()

    def load_theme_config(self):
        import json
        from .styles import THEME_COLORS
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    theme_name = data.get("theme", "Neon Green")
                    self.theme_accent = THEME_COLORS.get(theme_name, "#39FF14")
        except:
            self.theme_accent = "#39FF14"
            
        # Update Colors
        # self.colors["LISTENING"] = QColor(self.theme_accent) # KEEP GREEN per user request

    def enforce_topmost(self):
        # Windows-specific low-level enforcement
        if platform.system() == "Windows":
            # HWND_TOPMOST = -1
            # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE = 0x0002 | 0x0001 | 0x0010 = 0x0013
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0013)
        else:
            # Linux/macOS: Standard Qt raise to keep it visible
            # Note: activateWindow() would steal focus, so we just use raise_()
            self.raise_()

    def center_on_screen(self):
        # Position bottom-right by default
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 20
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

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
                    self.windows["settings"] = SettingsWindow(self.reset_event)
                    
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
        self.current_state = status
        self.update() # Trigger repaint
    
    def closeEvent(self, event):
        """Stop timers before closing to prevent Qt event loop crashes."""
        self.anim_timer.stop()
        self.top_timer.stop()
        event.accept()

    def animate(self):
        try:
            import random
            import math
            
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
        except Exception as e:
            # Silently ignore animation errors to prevent crashes
            pass

    def paintEvent(self, event):
        self.setFixedSize(self.width_val, self.height_val)
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
        painter.setPen(QPen(state_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self.current_state in ["IDLE", "LISTENING"]:
            # Draw Text
            text = "Idle" if self.current_state == "IDLE" else "Listening"
            painter.setPen(QPen(state_color))
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        elif self.current_state in ["SPEAKING", "PROCESSING", "THINKING"]:
            # Draw Vertical Bar Visualizer (Unified Design)
            # 5 Bars centered
            bar_width = 8
            gap = 4
            total_width = (5 * bar_width) + (4 * gap)
            start_x = (self.width() - total_width) / 2
            mid_y = self.height() / 2
            
            painter.setBrush(QBrush(state_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            for i, height in enumerate(self.bar_heights):
                x = start_x + (i * (bar_width + gap))
                # Draw rounded rect centered vertically
                h = height * 1.5 # Scale height
                y = mid_y - (h / 2)
                painter.drawRoundedRect(int(x), int(y), int(bar_width), int(h), 4, 4)

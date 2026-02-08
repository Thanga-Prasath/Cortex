from PyQt6.QtWidgets import QMainWindow, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QRadialGradient
import ctypes
import platform

class StatusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window Flags: Frameless, Always on Top, Tool (no taskbar icon)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Dimensions
        self.width_val = 140
        self.height_val = 50
        self.setGeometry(100, 100, self.width_val, self.height_val) 
        self.center_on_screen()
        
        # State
        self.current_state = "IDLE"
        self.wave_phase = 0
        self.wave_amplitude = 10
        self.pulse_direction = 1
        self.bar_heights = [5, 10, 15, 10, 5] # Initial heights for beatbox bars
        
        # Timer for animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(50)
        
        # Enforce Always on Top (Windows specific fix)
        if platform.system() == "Windows":
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

    def enforce_topmost(self):
        # HWND_TOPMOST = -1
        # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE = 0x0002 | 0x0001 | 0x0010 = 0x0013
        if platform.system() == "Windows":
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0013)

    def center_on_screen(self):
        # Position bottom-right by default
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 20
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()

    def mouseMoveEvent(self, event):
        pass # Not needed for system move

    def update_status(self, status, data=None):
        self.current_state = status
        self.update() # Trigger repaint

    def animate(self):
        import random
        import math
        
        if self.current_state == "SPEAKING":
            # Beatbox Animation: Randomize bar heights
            self.bar_heights = [random.randint(5, 20) for _ in range(5)]
            self.update()
            
        elif self.current_state == "THINKING":
            # Sine Wave Bars (Organized Flow)
            move_speed = 0.2
            self.wave_phase += move_speed
            
            # Calculate heights based on sine wave
            new_heights = []
            for i in range(5):
                # Phase offset for each bar to create wave
                offset = i * 0.5 
                val = math.sin(self.wave_phase + offset)
                # Map [-1, 1] to [5, 20]
                height = 12 + (val * 8) 
                new_heights.append(height)
            self.bar_heights = new_heights
            self.update()

        elif self.current_state == "PROCESSING":
             # Scanner / Ripple (Knight Rider style)
            move_speed = 0.3
            self.wave_phase += move_speed
            
            # Position of the "head" (0 to 4)
            # Use saw-tooth or sine to move back and forth? Let's do simple cycle for now
            # Cycle 0 -> 5
            pos = (self.wave_phase * 2) % 6 
            
            new_heights = []
            for i in range(5):
                # Distance from current position
                dist = abs(i - pos)
                if dist < 1.5:
                    height = 20 - (dist * 10)
                else:
                    height = 5
                
                # Clamp
                height = max(5, min(20, height))
                new_heights.append(height)
                
            self.bar_heights = new_heights
            self.update()

        else:
             self.wave_phase = 0
             self.wave_amplitude = 10
             self.bar_heights = [5, 5, 5, 5, 5]
             self.update()

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

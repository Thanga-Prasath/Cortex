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
        self.size_val = 30
        self.setGeometry(100, 100, self.size_val + 20, self.size_val + 20) # +20 for glow padding
        self.center_on_screen()
        
        # State
        self.current_state = "IDLE"
        self.pulse_val = 0
        self.pulse_direction = 1
        
        # Timer for animation
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.animate)
        self.anim_timer.start(50)
        
        # Enforce Always on Top (Windows specific fix)
        if platform.system() == "Windows":
            self.top_timer = QTimer()
            self.top_timer.timeout.connect(self.enforce_topmost)
            self.top_timer.start(500) # Check every 500ms

        # Colors
        self.colors = {
            "IDLE": QColor(100, 100, 100, 150),       # Grey, semi-transparent
            "LISTENING": QColor(0, 255, 0, 200),      # Green
            "THINKING": QColor(255, 200, 0, 200),     # Yellow/Orange
            "SPEAKING": QColor(160, 32, 240, 200),    # Purple
            "PROCESSING": QColor(0, 200, 255, 200)    # Blue
        }

    def enforce_topmost(self):
        # HWND_TOPMOST = -1
        # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE = 0x0002 | 0x0001 | 0x0010 = 0x0013
        if platform.system() == "Windows":
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0013)

    def center_on_screen(self):
        # Position bottom-right by default, or center top
        # Let's put it Top Center for high visibility like dynamic island, 
        # or Bottom Right like a notification. 
        # User requested "Floating window status", let's defaults to Bottom Right (Taskbar area)
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 20
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def update_status(self, status, data=None):
        self.current_state = status
        self.update() # Trigger repaint

    def animate(self):
        # Simple pulsing logic
        if self.current_state != "IDLE":
            self.pulse_val += 2 * self.pulse_direction
            if self.pulse_val > 10: self.pulse_direction = -1
            if self.pulse_val < 0: self.pulse_direction = 1
            self.update()
        else:
             self.pulse_val = 0
             self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Base Color
        base_color = self.colors.get(self.current_state, self.colors["IDLE"])
        
        # Draw Glow/Pulse
        if self.current_state != "IDLE":
            gradient = QRadialGradient(self.width()/2, self.height()/2, (self.size_val/2) + self.pulse_val)
            gradient.setColorAt(0, base_color)
            gradient.setColorAt(1, QColor(0, 0, 0, 0)) # Alpha 0 at edge
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, self.width(), self.height())
            
        # Draw Core Circle
        painter.setBrush(QBrush(base_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # Center the circle in the widget
        offset = (self.width() - self.size_val) / 2
        painter.drawEllipse(int(offset), int(offset), self.size_val, self.size_val)

# Common Styles for Cortex GUIs

from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

THEME_COLORS = {
    "Neon Green": "#39FF14",
    "Cyber Blue": "#00FFFF", 
    "Plasma Purple": "#BC13FE",
    "Fiery Red": "#FF3131"
}

def get_theme_color(theme_name="Neon Green"):
    return THEME_COLORS.get(theme_name, "#39FF14")

def apply_glow_effect(widget, theme_name="Neon Green", blur_radius=20, offset=0):
    """
    Applies a sleek neon glow effect to the bounding box of a widget.
    Perfect for main Headers like 'Cortex Hub'.
    """
    accent_hex = get_theme_color(theme_name)
    glow = QGraphicsDropShadowEffect(widget)
    glow.setBlurRadius(blur_radius)
    glow.setXOffset(offset)
    glow.setYOffset(offset)
    glow.setColor(QColor(accent_hex))
    widget.setGraphicsEffect(glow)
    return glow

def get_stylesheet(theme_name="Neon Green"):
    accent = get_theme_color(theme_name)
    
    return f"""
    QMainWindow, QWidget {{
        background-color: #151515;
        color: #e0e0e0;
        font-family: 'Segoe UI', sans-serif;
    }}
    
    QLabel {{
        color: #cccccc;
        font-size: 14px;
        background: transparent;
    }}
    
    QLabel#Header {{
        color: {accent};
        font-size: 32px;
        font-weight: bold;
        letter-spacing: 1px;
        background: transparent;
    }}
    
    QLabel#SubHeader {{
        color: #ffffff;
        font-size: 18px;
        font-weight: 400;
        margin-top: 10px;
        background: transparent;
    }}
    
    QPushButton {{
        background-color: #222222;
        color: #ffffff;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: #2A2A2A;
        border: 1px solid {accent};
        color: {accent};
    }}
    
    QPushButton:pressed {{
        background-color: {accent};
        color: #000000;
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: #151515;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #333333;
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #444444;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}

    /* Group Boxes / Cards (like the system vitals layout) */
    QFrame#Card {{
        background-color: #1A1A1A;
        border-radius: 8px;
        border: 1px solid #282828;
    }}
    
    /* Progress Bars: Ultra-thin neon line */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: #262626;
        text-align: right;
        color: transparent; /* Hide default internal text, use separate labels! */
        max-height: 8px;
        min-height: 8px;
    }}
    
    QProgressBar::chunk {{
        background-color: {accent};
        border-radius: 4px;
    }}
    """

# Backwards compatibility (default)
CORTEX_THEME = get_stylesheet()


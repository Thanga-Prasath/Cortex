# Common Styles for Cortex GUIs

# Common Styles for Cortex GUIs

THEME_COLORS = {
    "Neon Green": "#39FF14",
    "Cyber Blue": "#00FFFF", 
    "Plasma Purple": "#BC13FE",
    "Fiery Red": "#FF3131"
}

def get_stylesheet(theme_name="Neon Green"):
    accent = THEME_COLORS.get(theme_name, "#39FF14")
    
    return f"""
    QMainWindow, QWidget {{
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }}
    
    QLabel {{
        color: #e0e0e0;
        font-size: 14px;
    }}
    
    QLabel#Header {{
        color: {accent};
        font-size: 24px;
        font-weight: bold;
        border-bottom: 2px solid {accent};
        padding-bottom: 10px;
    }}
    
    QLabel#SubHeader {{
        color: #00ffff;
        font-size: 18px;
        font-weight: bold;
        margin-top: 15px;
    }}
    
    QPushButton {{
        background-color: #2d2d30;
        color: #ffffff;
        border: 1px solid {accent};
        border-radius: 5px;
        padding: 8px 15px;
        font-size: 13px;
    }}
    
    QPushButton:hover {{
        background-color: {accent};
        color: #000000;
        font-weight: bold;
    }}
    
    QPushButton:pressed {{
        background-color: #32CD32;
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        border: none;
        background: #1e1e1e;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #424242;
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}

    /* Group Boxes / Cards */
    QFrame#Card {{
        background-color: #252526;
        border-radius: 10px;
        border: 1px solid #444;
    }}
    
    QProgressBar {{
        border: 1px solid #444;
        border-radius: 5px;
        background-color: #1e1e1e;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background-color: {accent};
        border-radius: 4px;
    }}
    """

# Backwards compatibility (default)
CORTEX_THEME = get_stylesheet()

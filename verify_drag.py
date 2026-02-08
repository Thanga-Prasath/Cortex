
import sys
import os

# quick hack to add root to path
sys.path.append(os.getcwd())

from core.ui.status_window import StatusWindow
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StatusWindow()
    window.show()
    sys.exit(app.exec())

import sys
import os
from PyQt6.QtWidgets import QApplication

# Fix for DPI Awareness "Access Denied" error
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# Add root to sys.path to allow imports from core
sys.path.append(os.getcwd())

from core.ui.status_window import StatusWindow

def main():
    print("Initializing Application...")
    app = QApplication(sys.argv)
    
    # Create window
    print("Creating StatusWindow...")
    try:
        window = StatusWindow()
        
        # Force visible position to avoid off-screen issues
        window.move(200, 200)
        
        # Set state to THINKING
        print("Setting state to THINKING...")
        window.update_status("THINKING")
        
        window.show()
        
        print("Displaying Status Window in 'THINKING' state.")
        print("Use the window controls or press Ctrl+C in the terminal to exit.")
        
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

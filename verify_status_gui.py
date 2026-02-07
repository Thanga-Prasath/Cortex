import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from core.ui.status_window import StatusWindow

def verify_gui():
    app = QApplication(sys.argv)
    window = StatusWindow()
    window.show()

    states = ["IDLE", "LISTENING", "SPEAKING", "PROCESSING", "THINKING"]
    state_index = 0

    def cycle_states():
        nonlocal state_index
        state = states[state_index]
        print(f"Switching to state: {state}")
        window.update_status(state)
        state_index = (state_index + 1) % len(states)

    timer = QTimer()
    timer.timeout.connect(cycle_states)
    timer.start(2000)  # Change state every 2 seconds

    print("Starting GUI verification...")
    print("Press Ctrl+C in the terminal to stop (or close the window if possible).")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    verify_gui()

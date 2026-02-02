from core.listening import Listener
print("Attempting to initialize Listener...")
try:
    l = Listener()
    print("Test passed: Listener initialized successfully.")
except Exception as e:
    print(f"Test failed: {e}")

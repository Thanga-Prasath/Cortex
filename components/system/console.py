import os
import platform

def clear_console(speaker=None):
    os_type = platform.system()
    if os_type == 'Windows':
        os.system('cls')
    else:
        os.system('clear')
    
    if speaker:
        speaker.speak("Console cleared.")

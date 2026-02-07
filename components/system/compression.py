import platform
import os
import shutil
from components.system.custom_utils import run_in_separate_terminal

def compress_file(target_path, output_path=None, custom_format='zip', speaker=None):
    if speaker:
        speaker.speak(f"Compressing {os.path.basename(target_path)}", blocking=False)
    
    if not output_path:
        output_path = target_path # shutil.make_archive adds extension automatically
    
    # Removing extension from output_path if it matches format because make_archive adds it
    
    try:
        shutil.make_archive(output_path, custom_format, target_path)
        if speaker:
            speaker.speak("Compression complete.")
    except Exception as e:
        if speaker:
            speaker.speak("Compression failed.")
        print(f"Error compressing: {e}")

def extract_file(archive_path, output_path=None, speaker=None):
    if speaker:
        speaker.speak(f"Extracting {os.path.basename(archive_path)}", blocking=False)
    
    if not output_path:
        output_path = os.path.dirname(archive_path)
        
    try:
        shutil.unpack_archive(archive_path, output_path)
        if speaker:
            speaker.speak("Extraction complete.")
    except Exception as e:
        if speaker:
            speaker.speak("Extraction failed.")
        print(f"Error extracting: {e}")

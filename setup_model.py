import os
import sys
import zipfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip"
MODEL_ZIP = "model.zip"
MODEL_DIR = "model"

def download_model():
    if os.path.exists(MODEL_DIR):
        print("Model directory 'model' already exists. Removing old model to update...")
        import shutil
        shutil.rmtree(MODEL_DIR)

    print(f"Downloading Vosk model from {MODEL_URL}...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_ZIP)
        print("Download complete.")
        
        print("Extracting model...")
        with zipfile.ZipFile(MODEL_ZIP, 'r') as zip_ref:
            zip_ref.extractall(".")
            
        # Rename the extracted folder (vosk-model-en-in-0.5) to 'model'
        extracted_folder = "vosk-model-en-in-0.5"
        if os.path.exists(extracted_folder):
            os.rename(extracted_folder, MODEL_DIR)
            print(f"Model extracted to '{MODEL_DIR}'.")
        else:
            print(f"Expected folder '{extracted_folder}' not found. Please check extraction.")
            
        # Cleanup
        if os.path.exists(MODEL_ZIP):
            os.remove(MODEL_ZIP)
            
    except Exception as e:
        print(f"Error setting up model: {e}")

if __name__ == "__main__":
    download_model()

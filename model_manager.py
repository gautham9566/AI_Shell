import os
import requests
import time
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from colorama import Fore, Style
import json
import datetime
import re

# Path for storing models
MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
DOWNLOADS_INFO_FILE = os.path.join(MODELS_DIR, ".downloads_info.json")

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

class ModelManager:
    def __init__(self):
        self.downloads_info = self._load_downloads_info()
        self.clean_incomplete_downloads()
    
    def _load_downloads_info(self) -> Dict:
        """Load information about downloads"""
        if os.path.exists(DOWNLOADS_INFO_FILE):
            try:
                with open(DOWNLOADS_INFO_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_downloads_info(self):
        """Save information about downloads"""
        with open(DOWNLOADS_INFO_FILE, 'w') as f:
            json.dump(self.downloads_info, f, indent=4)
    
    def get_models_list(self) -> List[Dict]:
        """Get list of available models"""
        models = []
        
        if not os.path.exists(MODELS_DIR):
            return models
            
        for filename in os.listdir(MODELS_DIR):
            file_path = os.path.join(MODELS_DIR, filename)
            if os.path.isfile(file_path) and not filename.startswith('.'):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                models.append({
                    "filename": filename,
                    "path": file_path,
                    "size_mb": round(size_mb, 2)
                })
        
        return models
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters"""
        # Remove query parameters (everything after ?)
        filename = filename.split('?')[0]
        
        # Replace other invalid characters with underscore
        invalid_chars = r'[\\/*?:"<>|]'
        return re.sub(invalid_chars, '_', filename)
    
    def download_model(self, url: str, filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Download a model from URL with resume capability
        Returns: (success, file_path)
        """
        if not filename:
            # Extract filename from URL and sanitize it
            raw_filename = url.split('/')[-1]
            filename = self._sanitize_filename(raw_filename)
            if not filename:
                filename = f"model_{int(time.time())}.gguf"
        else:
            # Sanitize user-provided filename
            filename = self._sanitize_filename(filename)
        
        file_path = os.path.join(MODELS_DIR, filename)
        temp_file_path = f"{file_path}.temp"
        
        # Check if we have an incomplete download
        resume_byte_pos = 0
        if url in self.downloads_info:
            info = self.downloads_info[url]
            if info.get("temp_file") == temp_file_path and os.path.exists(temp_file_path):
                # Check if download is less than 1 day old
                start_time = datetime.datetime.fromisoformat(info.get("start_time"))
                now = datetime.datetime.now()
                if (now - start_time).days < 1:
                    resume_byte_pos = os.path.getsize(temp_file_path)
                    print(f"Resuming download from {resume_byte_pos / (1024*1024):.2f} MB")
                else:
                    # More than 1 day old, remove incomplete file
                    os.remove(temp_file_path)
            
        # Update download info
        self.downloads_info[url] = {
            "filename": filename,
            "temp_file": temp_file_path,
            "target_file": file_path,
            "start_time": datetime.datetime.now().isoformat()
        }
        self._save_downloads_info()
        
        headers = {}
        if resume_byte_pos > 0:
            headers['Range'] = f'bytes={resume_byte_pos}-'
        
        try:
            print(f"Downloading model from {url}...")
            response = requests.get(url, headers=headers, stream=True)
            
            # If we got a 206 Partial Content, we're resuming
            # If we got a 200 OK but requested a range, server doesn't support resume
            if headers and response.status_code == 200:
                # Server doesn't support resume, start over
                resume_byte_pos = 0
                mode = 'wb'
            elif response.status_code == 206:
                # Server supports resume
                mode = 'ab'
            else:
                response.raise_for_status()
                mode = 'wb'
            
            file_size = int(response.headers.get('content-length', 0))
            if resume_byte_pos > 0 and response.status_code == 206:
                file_size += resume_byte_pos
                
            print(f"Total size: {file_size/(1024*1024):.2f} MB")
            
            with open(temp_file_path, mode) as f:
                downloaded = resume_byte_pos
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Print progress
                        percent = (downloaded / file_size) * 100 if file_size > 0 else 0
                        print(f"\rDownloaded: {downloaded/(1024*1024):.2f} MB ({percent:.1f}%)", end="")
            
            print("\nDownload completed. Moving file to final location.")
            shutil.move(temp_file_path, file_path)
            
            # Update download info - mark as complete
            self.downloads_info[url]["completed"] = True
            self.downloads_info[url]["completion_time"] = datetime.datetime.now().isoformat()
            self._save_downloads_info()
            
            return True, file_path
            
        except Exception as e:
            print(f"\nError downloading model: {e}")
            return False, ""
    
    def delete_model(self, filename: str) -> bool:
        """Delete a model file"""
        file_path = os.path.join(MODELS_DIR, filename)
        if not os.path.exists(file_path):
            return False
            
        try:
            os.remove(file_path)
            print(f"Model {filename} deleted successfully.")
            
            # Also clean up any download info related to this file
            for url, info in list(self.downloads_info.items()):
                if info.get("target_file") == file_path:
                    del self.downloads_info[url]
            
            self._save_downloads_info()
            return True
        except Exception as e:
            print(f"Error deleting model: {e}")
            return False
    
    def clean_incomplete_downloads(self):
        """Remove incomplete downloads older than 1 day"""
        now = datetime.datetime.now()
        for url, info in list(self.downloads_info.items()):
            # Skip completed downloads
            if info.get("completed", False):
                continue
                
            start_time = datetime.datetime.fromisoformat(info.get("start_time"))
            temp_file = info.get("temp_file")
            
            if (now - start_time).days >= 1 and temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"Removed incomplete download: {os.path.basename(temp_file)}")
                del self.downloads_info[url]
        
        self._save_downloads_info()

# Singleton instance
model_manager = ModelManager()

def get_default_model_path() -> str:
    """Return a default path in the models directory"""
    return os.path.join(MODELS_DIR, "model.gguf")

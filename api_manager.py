import os
import json
from pathlib import Path

class APIManager:
    def __init__(self):
        self.config_dir = Path.home() / '.spec-drive'  # Creates a hidden folder in user's home directory
        self.config_file = self.config_dir / 'config.json'  # Stores API key in config.json
        self.ensure_config_dir()
        self.on_api_key_change = None  # Initialize on_api_key_change to None
    
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save_api_key(self, api_key):
        """Save API key to config file"""
        try:
            config = {'api_key': api_key}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            if self.on_api_key_change:
                self.on_api_key_change(api_key)  # Call the callback if it's set
            return True
        except Exception as e:
            print(f"Failed to save API key: {e}")
            return False
    
    def load_api_key(self):
        """Load API key from config file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                return config.get('api_key')
            return None
        except Exception as e:
            print(f"Failed to load API key: {e}")
            return None
    
    def is_first_run(self):
        """Check if this is the first run"""
        return not self.config_file.exists()

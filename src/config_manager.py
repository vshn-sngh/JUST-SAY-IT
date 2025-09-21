
import json
import os

class ConfigManager:
    def __init__(self, default_settings_path, user_settings_path):
        self.default_settings_path = default_settings_path
        self.user_settings_path = user_settings_path
        self.config = self.load_config()

    def load_config(self):
        config = self._load_json_file(self.default_settings_path)
        user_config = self._load_json_file(self.user_settings_path)
        if user_config:
            config.update(user_config)
        return config

    def _load_json_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # Handle empty or invalid JSON
                    return {}
        return {}

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_user_config()

    def save_user_config(self):
        user_config = self._load_json_file(self.user_settings_path)
        user_config.update(self.config)
        with open(self.user_settings_path, 'w') as f:
            json.dump(user_config, f, indent=4)

    def reload_config(self):
        self.config = self.load_config()

import json
from pathlib import Path
import logging
from typing import Dict, Any
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

class UserSettings:
    def __init__(self):
        self.settings_path = Path(__file__).parent.parent / "data" / "user_settings.json"
        self.settings_path.parent.mkdir(exist_ok=True)
    
    def _load_all_settings(self) -> Dict[str, Any]:
        if not self.settings_path.exists():
            return {}
        with open(self.settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        all_settings = self._load_all_settings()
        return all_settings.get(str(user_id), {})
    
    def save_user_setting(self, user_id: int, key: str, value: Any):
        all_settings = self._load_all_settings()
        user_settings = all_settings.get(str(user_id), {})
        user_settings[key] = value
        all_settings[str(user_id)] = user_settings
        
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(all_settings, f, ensure_ascii=False, indent=2)

user_settings = UserSettings()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
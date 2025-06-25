import os
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

# Настройки пользователей
user_settings = {}

def save_user_setting(user_id, key, value):
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id][key] = value

def get_user_settings(user_id):
    return user_settings.get(user_id, {"ai_mode": False, "voice_mode": False})

import json
import os
from dotenv import load_dotenv
from src.utils.key_manager import get_riot_api_key

# Load environment variables
load_dotenv()

# Riot API Configuration
# API key is loaded via key_manager (obfuscated production key with .env override)
RIOT_API_KEY = get_riot_api_key()
STATS_API_KEY = os.getenv('STATS_API_KEY')

# Riot API Endpoints
RIOT_REGIONS = {
    'EUW': 'euw1.api.riotgames.com',
    'EUNE': 'eun1.api.riotgames.com',
    'NA': 'na1.api.riotgames.com',
    'KR': 'kr.api.riotgames.com',
    'BR': 'br1.api.riotgames.com',
    'JP': 'jp1.api.riotgames.com',
    'LAN': 'la1.api.riotgames.com',
    'LAS': 'la2.api.riotgames.com',
    'OCE': 'oc1.api.riotgames.com',
    'TR': 'tr1.api.riotgames.com',
    'RU': 'ru.api.riotgames.com',
}

RIOT_REGIONAL_ENDPOINTS = {
    'AMERICAS': 'americas.api.riotgames.com',
    'EUROPE': 'europe.api.riotgames.com',
    'ASIA': 'asia.api.riotgames.com',
    'SEA': 'sea.api.riotgames.com',
}

# Cache settings
CACHE_DIR = 'cache'
CACHE_DURATION = 3600  # 1 hour in seconds

# Data storage
DATA_DIR = 'data'
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')

# Season config
SEASON_START_TIMESTAMP = 1736380800  # Jan 9, 2025 00:00:00 UTC

# Application settings
DEFAULT_REGION = 'EUW'
APP_NAME = 'RiftRetreat'
APP_VERSION = '1.0.0'
APP_AUTHOR = 'Treatey'


def load_app_settings() -> dict:
    """Load saved app settings (account name, region, API key)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_app_settings(settings: dict):
    """Save app settings to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

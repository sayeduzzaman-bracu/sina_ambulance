# config.py
from pathlib import Path

APP_NAME = "Sina Ambulance Professional"
APP_VERSION = "1.0.0"

# Path handling for persistence
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "sina_main.db"

# Placeholder for Google Maps API (Phase 2)
GOOGLE_MAPS_KEY = "YOUR_API_KEY_HERE"
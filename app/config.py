import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
API_KEY_ZUBE = os.getenv("API_KEY_ZUBE", "dev-key-zube-12345")
API_KEY_ASSISTANT = os.getenv("API_KEY_ASSISTANT", "dev-key-assistant-67890")
VALID_API_KEYS = {API_KEY_ZUBE, API_KEY_ASSISTANT}

# Weather defaults (Wayne, PA)
WEATHER_LAT = float(os.getenv("WEATHER_LAT", "40.0426"))
WEATHER_LON = float(os.getenv("WEATHER_LON", "-75.3899"))
WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "86400"))

# Default electricity rates (PECO Smart Time)
DEFAULT_RATES = {
    "2026-01-01": {"all": 0.11},  # 11¢ all periods
    "2026-05-21": {
        "sop": 0.053,   # Super Off-Peak: 5.3¢
        "op": 0.076,    # Off-Peak: 7.6¢
        "pk": 0.32      # Peak: 32¢
    }
}

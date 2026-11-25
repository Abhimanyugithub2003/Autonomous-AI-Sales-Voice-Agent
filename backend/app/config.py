import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "fortive_sales_ai")

# LLM Providers
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Voice Defaults
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "en-US-JennyNeural")
VOICE_RATE = os.getenv("VOICE_RATE", "+0%")
VOICE_PITCH = os.getenv("VOICE_PITCH", "+0Hz")

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS = os.getenv("GOOGLE_CALENDAR_CREDENTIALS", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

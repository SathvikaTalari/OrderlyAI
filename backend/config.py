"""
Configuration module for Orderly AI.
Manages application constants, environment variables, and default settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables if .env exists
load_dotenv()

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# App Metadata
APP_NAME = "OrderlyAI"
APP_TAGLINE = "Smart Orders. Local AI. Greater Control."
APP_VERSION = "1.0.0"

# Ollama / AI Settings (Strictly local-first)
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# Database Settings (placed inside database/ directory)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATABASE_DIR / "orderly.db"))

# Business / UI Settings
CURRENCY_SYMBOL = os.getenv("APP_CURRENCY", "₹")

ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Preparing",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
]

DEFAULT_STATUS = "Pending"

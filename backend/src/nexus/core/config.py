"""Central application configuration loaded from backend/.env."""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(BACKEND_ROOT / ".env")

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(level=logging.INFO)
logging.getLogger("nexus").setLevel(getattr(logging, LOG_LEVEL, logging.DEBUG))

APP_NAME = os.getenv("APP_NAME", "NEXPLY API")
APP_MODULE = os.getenv("APP_MODULE", "nexus.api.main:app")
APP_DIR = os.getenv("APP_DIR", "src")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_RELOAD = os.getenv("APP_RELOAD", "true").strip().lower() in {
    "1", "true", "yes", "on"
}

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "nexply")
MONGODB_RESUME_COLLECTION = os.getenv(
    "MONGODB_RESUME_COLLECTION", "resume"
)
MONGODB_JD_COLLECTION = os.getenv("MONGODB_JD_COLLECTION", "jd")
MONGODB_GRIDFS_BUCKET = os.getenv(
    "MONGODB_GRIDFS_BUCKET", "document_files"
)
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")
)

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_CHAT_PATH = os.getenv("OLLAMA_CHAT_PATH", "/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
OLLAMA_THINK = os.getenv("OLLAMA_THINK", "false").strip().lower() in {
    "1", "true", "yes", "on"
}
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "4096"))

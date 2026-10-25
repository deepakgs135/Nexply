"""Start the local NEXPLY API using settings from backend/.env."""

import sys
from pathlib import Path

import uvicorn

BACKEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from nexus.core.config import APP_DIR, APP_HOST, APP_MODULE, APP_PORT, APP_RELOAD


if __name__ == "__main__":
    uvicorn.run(
        APP_MODULE,
        app_dir=str(BACKEND_ROOT / APP_DIR),
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_RELOAD,
    )

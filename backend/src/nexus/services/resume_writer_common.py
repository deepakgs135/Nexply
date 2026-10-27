import json
import requests
from pydantic import ValidationError
from nexus.core.config import (
    OLLAMA_BASE_URL, OLLAMA_CHAT_PATH, OLLAMA_RESUME_WRITER_MODEL,
    OLLAMA_RESUME_WRITER_NUM_PREDICT, OLLAMA_TEMPERATURE, OLLAMA_TIMEOUT_SECONDS,
)
from nexus.core.debug import debug_trace
from nexus.core.prompts.resume_writing import RESUME_WRITING_PROMPT
from nexus.core.schemas.resume import ResumeData

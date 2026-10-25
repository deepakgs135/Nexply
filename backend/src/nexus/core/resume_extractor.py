
from nexus.core.debug import debug_trace
import json

import requests
from pydantic import ValidationError

from nexus.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_PATH,
    OLLAMA_MODEL,
    OLLAMA_NUM_PREDICT,
    OLLAMA_TEMPERATURE,
    OLLAMA_THINK,
    OLLAMA_TIMEOUT_SECONDS,
)
from nexus.core.schemas.resume import ResumeData


OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/{OLLAMA_CHAT_PATH.lstrip('/')}"


RESUME_EXTRACTION_PROMPT = """
You are a resume information extraction system.

Extract information only when supported by the supplied resume text.
Do not invent names, dates, skills, qualifications, or experience.
Use null for unavailable single-value fields and [] for unavailable lists.

Return only a JSON object matching this structure:
{
  "full_name": null,
  "email": null,
  "phone": null,
  "location": null,
  "professional_summary": null,
  "skills": [],
  "education": [],
  "experience": [],
  "projects": [],
  "certifications": [],
  "languages": []
}

Rules:
- Preserve factual meaning from the source.
- Keep dates as strings in their original form where possible.
- graduation_year must be an integer or null.
- Each project must include a name.
- Each experience responsibility must be a string.
- Do not include Markdown fences or explanations.
"""


@debug_trace
def extract_resume_data(parsed_text: str) -> dict:
    """Extract structured resume data using local Ollama."""
    if not parsed_text or not parsed_text.strip():
        raise ValueError("Resume text cannot be empty.")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "think": OLLAMA_THINK,
            "format": ResumeData.model_json_schema(),
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_NUM_PREDICT,
            },
            "messages": [
                {
                    "role": "system",
                    "content": RESUME_EXTRACTION_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Extract resume information from this source text:\n\n"
                        f"<resume_text>\n{parsed_text}\n</resume_text>"
                    ),
                },
            ],
        },
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    result = response.json()

    message = result.get("message")
    if not isinstance(message, dict):
        raise ValueError("Ollama response is missing its message object.")

    raw_json = message.get("content")
    if not isinstance(raw_json, str) or not raw_json.strip():
        done_reason = result.get("done_reason", "unknown")
        raise ValueError(
            f"Ollama returned empty content (done_reason={done_reason})."
        )

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Ollama returned invalid JSON.") from exc

    try:
        validated = ResumeData.model_validate(data)
    except ValidationError as exc:
        issues = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['type']}"
            for issue in exc.errors(include_input=False)
        )
        raise ValueError(
            f"Ollama response does not match ResumeData: {issues}"
        ) from exc

    return validated.model_dump()

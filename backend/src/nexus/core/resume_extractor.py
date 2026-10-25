
import json

import requests
from pydantic import ValidationError

from nexus.core.schemas.resume import ResumeData


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:9b"


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


def extract_resume_data(parsed_text: str) -> dict:
    """Extract structured resume data using local Ollama."""
    if not parsed_text or not parsed_text.strip():
        raise ValueError("Resume text cannot be empty.")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "stream": False,
            "format": "json",
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
        timeout=180,
    )

    response.raise_for_status()
    result = response.json()

    try:
        raw_json = result["message"]["content"]
        data = json.loads(raw_json)
        validated = ResumeData.model_validate(data)
    except (KeyError, TypeError, json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(
            "Ollama returned a response that does not match the resume schema."
        ) from exc

    return validated.model_dump()

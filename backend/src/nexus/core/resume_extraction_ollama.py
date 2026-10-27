import json
import requests
from pydantic import ValidationError
from nexus.core.config import (
    OLLAMA_BASE_URL, OLLAMA_CHAT_PATH, OLLAMA_MODEL, OLLAMA_NUM_PREDICT,
    OLLAMA_TEMPERATURE, OLLAMA_THINK, OLLAMA_TIMEOUT_SECONDS,
)
from nexus.core.debug import debug_trace
from nexus.core.prompts.resume_extraction import RESUME_EXTRACTION_PROMPT
from nexus.core.schemas.resume import ResumeData
from nexus.core.resume_normalization import normalize_resume_payload
from nexus.core.resume_source_contact import fill_contact_from_source
from nexus.core.resume_source_links import fill_profile_links_from_source
from nexus.core.resume_source_experience import fill_experience_dates_from_source, fill_experience_locations_from_source

OLLAMA_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/{OLLAMA_CHAT_PATH.lstrip('/')}"

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
                        "Use exactly these standard property names: full_name, email, "
                        "phone, location, professional_title, professional_summary, "
                        "skills, education, experience, projects, certifications, "
                        "languages, websites, awards, publications, volunteer_experience, "
                        "interests, references, additional_sections. Put the person's "
                        "full name into full_name, contact values into their matching "
                        "top-level properties, job title into experience.job_title, "
                        "dates into start_date/end_date, and every job bullet into "
                        "responsibilities or achievements. Extract every supported "
                        "resume detail and do not omit items to shorten the response. "
                        "Source text follows:\n\n"
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

    data = normalize_resume_payload(data)
    data = fill_contact_from_source(data, parsed_text)
    data = fill_profile_links_from_source(data, parsed_text)
    data = fill_experience_dates_from_source(data, parsed_text)
    data = fill_experience_locations_from_source(data, parsed_text)

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

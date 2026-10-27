from nexus.services.resume_writer_common import (
    OLLAMA_BASE_URL, OLLAMA_CHAT_PATH, OLLAMA_RESUME_WRITER_NUM_PREDICT,
    OLLAMA_TEMPERATURE, OLLAMA_TIMEOUT_SECONDS, RESUME_WRITING_PROMPT,
    ResumeData, ValidationError, debug_trace, json, requests,
)
from nexus.services.resume_model_catalog import available_resume_models

@debug_trace
def write_resume(profile: dict, model: str, target_job_description: str | None = None) -> dict:
    """Use an installed local Ollama model to polish a structured profile."""
    if not isinstance(profile, dict) or not profile:
        raise ValueError("The candidate profile is empty.")

    installed_models = available_resume_models()
    if model not in installed_models:
        raise ValueError("Selected Ollama model is not installed or available.")

    try:
        source = ResumeData.model_validate(profile).model_dump(mode="json")
    except ValidationError as exc:
        raise ValueError("The candidate profile does not match ResumeData.") from exc

    user_content = {
        "instructions": (
            "Improve this complete candidate profile as a polished resume. Preserve all "
            "entries and facts. Return all standard fields, including fields you leave unchanged."
        ),
        "target_job_description": target_job_description or None,
        "candidate_profile": source,
    }
    response = requests.post(
        f"{OLLAMA_BASE_URL.rstrip('/')}/{OLLAMA_CHAT_PATH.lstrip('/')}",
        json={
            "model": model,
            "stream": False,
            "format": ResumeData.model_json_schema(),
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_RESUME_WRITER_NUM_PREDICT,
            },
            "messages": [
                {"role": "system", "content": RESUME_WRITING_PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
        },
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    body = response.json()
    message = body.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Ollama returned an empty resume draft.")
    try:
        result = json.loads(content)
        validated = ResumeData.model_validate(result)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Ollama returned resume data that does not match ResumeData.") from exc
    return validated.model_dump(mode="json")

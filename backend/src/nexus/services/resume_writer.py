"""AI-assisted rewriting for resume profiles; generated profiles are not persisted."""

import json

import requests
from pydantic import ValidationError

from nexus.core.config import (
    OLLAMA_BASE_URL,
    OLLAMA_CHAT_PATH,
    OLLAMA_RESUME_WRITER_MODEL,
    OLLAMA_RESUME_WRITER_NUM_PREDICT,
    OLLAMA_TEMPERATURE,
    OLLAMA_TIMEOUT_SECONDS,
)
from nexus.core.debug import debug_trace
from nexus.core.prompts.resume_writing import RESUME_WRITING_PROMPT
from nexus.core.schemas.resume import ResumeData


@debug_trace
def available_resume_models() -> list[str]:
    """Return installed local Ollama models that support text generation."""
    response = requests.get(
        f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags",
        timeout=min(10, OLLAMA_TIMEOUT_SECONDS),
    )
    response.raise_for_status()
    result = response.json()
    models = []
    for item in result.get("models", []):
        name = item.get("name")
        capabilities = item.get("capabilities") or []
        family = (item.get("details") or {}).get("family", "")
        if name and "coder" not in name.lower() and ("completion" in capabilities or (not capabilities and family != "nomic-bert")):
            models.append(name)
    return models


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


def default_resume_model() -> str:
    """Get the configured resume writer model when installed, or fall back safely."""
    models = available_resume_models()
    if OLLAMA_RESUME_WRITER_MODEL in models:
        return OLLAMA_RESUME_WRITER_MODEL
    if models:
        return models[0]
    raise ValueError("No text-generation models are installed in Ollama.")

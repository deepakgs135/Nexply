from nexus.services.resume_writer_common import OLLAMA_BASE_URL, OLLAMA_TIMEOUT_SECONDS, debug_trace, requests

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
def default_resume_model() -> str:
    """Get the configured resume writer model when installed, or fall back safely."""
    models = available_resume_models()
    if OLLAMA_RESUME_WRITER_MODEL in models:
        return OLLAMA_RESUME_WRITER_MODEL
    if models:
        return models[0]
    raise ValueError("No text-generation models are installed in Ollama.")

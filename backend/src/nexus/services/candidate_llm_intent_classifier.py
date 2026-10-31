
"""LLM-based intent classification for NEXPLY.

Primary classifier: Ollama Qwen
Fallback classifier: Existing regex-based classifier
"""

import json
import requests

from nexus.services.candidate_query_classifier import (
    classify_candidate_query,
)


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3.5:9b"

ALLOWED_INTENTS = {
    "SKILL_SEARCH": "skills",
    "PROJECT_SEARCH": "projects",
    "EXPERIENCE_SEARCH": "experience",
    "EDUCATION_SEARCH": "education",
    "CERTIFICATION_SEARCH": "certifications",
    "SUMMARY_SEARCH": "professional_summary",
    "AWARD_SEARCH": "awards",
    "PUBLICATION_SEARCH": "publications",
    "GENERAL_SEARCH": None,
}


def _validate_classification(data: dict) -> dict:
    """Validate the classification returned by Ollama."""

    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object.")

    intent = data.get("intent")
    source_section = data.get("source_section")
    confidence = data.get("confidence")
    reason = data.get("reason", "")

    if intent not in ALLOWED_INTENTS:
        raise ValueError("Invalid intent returned by LLM.")

    expected_section = ALLOWED_INTENTS[intent]

    if source_section != expected_section:
        raise ValueError("Intent and source section do not match.")

    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        raise ValueError("Invalid confidence score.")

    if not isinstance(reason, str):
        raise ValueError("Invalid reason returned by LLM.")

    return {
        "intent": intent,
        "source_section": source_section,
        "confidence": float(confidence),
        "reason": reason,
    }


def _classify_with_regex(query: str, error: str) -> dict:
    """Use the existing regex classifier as a fallback."""

    fallback = classify_candidate_query(query)

    return {
        **fallback,
        "confidence": None,
        "reason": f"Regex fallback used: {error}",
        "classifier": "regex_fallback",
    }


def classify_candidate_query_with_llm(query: str) -> dict:
    """Classify a candidate query using Ollama with regex fallback."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    query = query.strip()

    prompt = f"""
You are the intent classification engine for NEXPLY,
an AI-powered candidate profile and resume search system.

Your task is to classify the user's query into exactly one intent.

ALLOWED INTENTS:

SKILL_SEARCH:
source_section = "skills"

PROJECT_SEARCH:
source_section = "projects"

EXPERIENCE_SEARCH:
source_section = "experience"

EDUCATION_SEARCH:
source_section = "education"

CERTIFICATION_SEARCH:
source_section = "certifications"

SUMMARY_SEARCH:
source_section = "professional_summary"

AWARD_SEARCH:
source_section = "awards"

PUBLICATION_SEARCH:
source_section = "publications"

GENERAL_SEARCH:
source_section = null

CLASSIFICATION RULES:

1. Understand the meaning of the query, not just individual keywords.
2. Use the most relevant single category when one category is requested.
3. If multiple different categories are requested, use GENERAL_SEARCH.
4. If the query is broad or does not match a specific category,
   use GENERAL_SEARCH.
5. Do not answer the user's question.
6. Do not invent additional intents or sections.
7. Confidence must be a number between 0 and 1.
8. Return only valid JSON.

REQUIRED OUTPUT FORMAT:

{{
    "intent": "PROJECT_SEARCH",
    "source_section": "projects",
    "confidence": 0.95,
    "reason": "The user is asking about candidate projects."
}}

USER QUERY:
{json.dumps(query)}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a precise intent classification "
                            "engine. Return only JSON matching the "
                            "requested structure."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0,
                },
            },
            timeout=(5, 60),
        )

        response.raise_for_status()

        response_data = response.json()
        content = response_data["message"]["content"]

        classification = json.loads(content)

        validated = _validate_classification(classification)

        return {
            **validated,
            "query": query,
            "classifier": "llm",
        }

    except (
        requests.RequestException,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:

        return _classify_with_regex(
            query=query,
            error=str(error),
        )

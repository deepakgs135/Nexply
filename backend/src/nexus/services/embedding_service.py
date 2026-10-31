
"""Ollama-based embedding service for NEXPLY candidate memory."""

import requests


OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text:latest"
EMBEDDING_DIMENSIONS = 768
REQUEST_TIMEOUT = 60


def generate_embedding(text: str) -> list[float]:
    """
    Generate a validated embedding vector using Ollama.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Embedding input text cannot be empty.")

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBEDDING_MODEL,
                "input": text.strip(),
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Failed to generate Ollama embedding: {exc}"
        ) from exc

    result = response.json()
    embeddings = result.get("embeddings")

    if not embeddings or not isinstance(embeddings, list):
        raise RuntimeError(
            "Ollama returned an invalid embedding response."
        )

    embedding = embeddings[0]

    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
            f"received {len(embedding)}."
        )

    if not all(
        isinstance(value, (int, float)) and
        not isinstance(value, bool) and
        value == value and
        abs(value) != float("inf")
        for value in embedding
    ):
        raise ValueError(
            "Embedding contains invalid numeric values."
        )

    return [float(value) for value in embedding]


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple text inputs.
    """

    if not isinstance(texts, list) or not texts:
        raise ValueError("Texts must be a non-empty list.")

    if any(
        not isinstance(text, str) or not text.strip()
        for text in texts
    ):
        raise ValueError(
            "Every embedding input must be a non-empty string."
        )

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBEDDING_MODEL,
                "input": [text.strip() for text in texts],
            },
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Failed to generate Ollama embeddings: {exc}"
        ) from exc

    result = response.json()
    embeddings = result.get("embeddings")

    if not isinstance(embeddings, list):
        raise RuntimeError(
            "Ollama returned an invalid embeddings response."
        )

    if len(embeddings) != len(texts):
        raise ValueError(
            f"Expected {len(texts)} embeddings, "
            f"received {len(embeddings)}."
        )

    validated_embeddings = []

    for embedding in embeddings:
        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                f"received {len(embedding)}."
            )

        if not all(
            isinstance(value, (int, float)) and
            not isinstance(value, bool) and
            value == value and
            abs(value) != float("inf")
            for value in embedding
        ):
            raise ValueError(
                "Embedding contains invalid numeric values."
            )

        validated_embeddings.append(
            [float(value) for value in embedding]
        )

    return validated_embeddings

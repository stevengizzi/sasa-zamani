"""OpenAI embedding generation and vector similarity math."""

from openai import OpenAI, OpenAIError

from app.config import get_settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class EmbeddingError(Exception):
    """Raised when an OpenAI embedding API call fails."""


def get_embedding_client() -> OpenAI:
    """Return an OpenAI client configured with the project API key. Patchable for tests."""
    return OpenAI(api_key=get_settings().openai_api_key)


def embed_text(text: str, *, client: OpenAI | None = None) -> list[float]:
    """Embed a single text string using OpenAI text-embedding-3-small.

    Returns a list of 1536 floats.
    Raises EmbeddingError on any OpenAI API failure.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, got {type(text).__name__}")

    api_client = client or get_embedding_client()

    try:
        response = api_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
    except OpenAIError as exc:
        raise EmbeddingError(f"OpenAI embedding request failed: {exc}") from exc

    return list(response.data[0].embedding)


def embed_texts(texts: list[str], *, client: OpenAI | None = None) -> list[list[float]]:
    """Embed multiple texts in a single OpenAI API call.

    Returns a list of embedding vectors in the same order as inputs.
    Raises EmbeddingError on any failure (no partial results).
    """
    if not isinstance(texts, list):
        raise TypeError(f"texts must be a list, got {type(texts).__name__}")

    if len(texts) == 0:
        return []

    api_client = client or get_embedding_client()

    try:
        response = api_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
    except OpenAIError as exc:
        raise EmbeddingError(f"OpenAI batch embedding request failed: {exc}") from exc

    sorted_data = sorted(response.data, key=lambda item: item.index)
    return [list(item.embedding) for item in sorted_data]

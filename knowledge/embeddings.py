"""Turn text into embedding vectors with a local model (FastEmbed, CPU only)."""

import threading

from django.conf import settings

_model = None
_lock = threading.Lock()


def model_name() -> str:
    return settings.EMBEDDING_MODEL


def _get_model():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from fastembed import TextEmbedding

                _model = TextEmbedding(model_name=model_name())
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed documents to be searched, such as knowledge base articles."""
    return [vector.tolist() for vector in _get_model().passage_embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a search query, such as a customer message."""
    return next(iter(_get_model().query_embed(text))).tolist()

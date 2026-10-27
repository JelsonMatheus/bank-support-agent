"""Find the knowledge base articles closest in meaning to a message."""

from dataclasses import dataclass

from pgvector.django import CosineDistance

from knowledge.embeddings import embed_query, model_name
from knowledge.models import KBArticle


class StaleIndexError(RuntimeError):
    """Raised when articles were indexed with a different embedding model."""


@dataclass(frozen=True)
class RetrievedArticle:
    article_id: str
    title: str
    category: str
    body: str
    score: float  # cosine similarity: higher is closer


def search(query: str, k: int = 3) -> list[RetrievedArticle]:
    current_model = model_name()
    if KBArticle.objects.exclude(embedding_model=current_model).exists():
        raise StaleIndexError(
            f"Some articles were indexed with another model; run `manage.py index_knowledge_base` "
            f"to re-index them with {current_model}."
        )

    vector = embed_query(query)
    rows = (
        KBArticle.objects.annotate(distance=CosineDistance("embedding", vector))
        .order_by("distance", "article_id")[:k]
    )
    return [
        RetrievedArticle(
            article_id=row.article_id,
            title=row.title,
            category=row.category,
            body=row.body,
            score=1 - row.distance,
        )
        for row in rows
    ]

import pytest

from knowledge.models import EMBEDDING_DIMENSIONS, KBArticle
from knowledge.retrieval import StaleIndexError, search

pytestmark = pytest.mark.django_db

FAKE_MODEL = "fake-model"


def vector(**weights: float) -> list[float]:
    """Build a vector from weights at given positions, e.g. vector(p0=1.0)."""
    values = [0.0] * EMBEDDING_DIMENSIONS
    for position, weight in weights.items():
        values[int(position[1:])] = weight
    return values


def make_article(article_id: str, embedding: list[float], model: str = FAKE_MODEL) -> KBArticle:
    return KBArticle.objects.create(
        article_id=article_id, title=f"Title {article_id}", category="cards", body="Body.",
        content_hash="x", embedding_model=model, embedding=embedding,
    )


@pytest.fixture
def fake_embedder(monkeypatch):
    monkeypatch.setattr("knowledge.retrieval.model_name", lambda: FAKE_MODEL)

    def use_query_vector(query_vector):
        monkeypatch.setattr("knowledge.retrieval.embed_query", lambda text: query_vector)

    return use_query_vector


@pytest.fixture
def articles():
    make_article("kb-001", vector(p0=1.0))
    make_article("kb-002", vector(p1=1.0))
    make_article("kb-003", vector(p2=1.0))


def test_results_are_ordered_by_similarity(articles, fake_embedder):
    fake_embedder(vector(p1=0.9, p0=0.3))

    results = search("anything", k=3)

    assert [r.article_id for r in results] == ["kb-002", "kb-001", "kb-003"]
    assert results[0].score > results[1].score > results[2].score
    assert results[2].score == pytest.approx(0.0, abs=1e-6)


def test_k_limits_the_number_of_results(articles, fake_embedder):
    fake_embedder(vector(p0=1.0))

    assert len(search("anything", k=2)) == 2


def test_empty_index_returns_no_results(fake_embedder):
    fake_embedder(vector(p0=1.0))

    assert search("anything") == []


def test_index_built_with_another_model_is_rejected(articles, fake_embedder):
    make_article("kb-004", vector(p3=1.0), model="old-model")
    fake_embedder(vector(p0=1.0))

    with pytest.raises(StaleIndexError, match="index_knowledge_base"):
        search("anything")
        
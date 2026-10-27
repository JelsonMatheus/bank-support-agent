from pathlib import Path

import pytest

from knowledge.articles import Article
from knowledge.indexing import index_articles
from knowledge.models import EMBEDDING_DIMENSIONS, KBArticle

pytestmark = pytest.mark.django_db


def article(article_id: str, body: str = "Some text.") -> Article:
    return Article(id=article_id, title=f"Title {article_id}", category="cards", body=body, path=Path(f"{article_id}.md"))


@pytest.fixture
def embedder(monkeypatch):
    """Replace the real model with a fake one and record what gets embedded."""
    calls = []

    def fake_embed(texts):
        calls.append(list(texts))
        return [[0.1] * EMBEDDING_DIMENSIONS for _ in texts]

    monkeypatch.setattr("knowledge.indexing.embed_passages", fake_embed)
    monkeypatch.setattr("knowledge.indexing.model_name", lambda: "fake-model-v1")
    return calls


def test_first_run_creates_every_article(embedder):
    report = index_articles([article("kb-001"), article("kb-002")])

    assert (report.created, report.updated, report.unchanged) == (2, 0, 0)
    assert KBArticle.objects.count() == 2
    assert KBArticle.objects.get(article_id="kb-001").embedding_model == "fake-model-v1"


def test_unchanged_articles_are_not_embedded_again(embedder):
    articles = [article("kb-001"), article("kb-002")]
    index_articles(articles)

    report = index_articles(articles)

    assert report.unchanged == 2
    assert len(embedder) == 1  # only the first run called the model


def test_only_changed_articles_are_re_embedded(embedder):
    index_articles([article("kb-001"), article("kb-002")])

    report = index_articles([article("kb-001", body="New text."), article("kb-002")])

    assert (report.updated, report.unchanged) == (1, 1)
    assert embedder[-1] == ["Title kb-001\n\nNew text."]


def test_changing_the_model_re_embeds_everything(embedder, monkeypatch):
    articles = [article("kb-001"), article("kb-002")]
    index_articles(articles)

    monkeypatch.setattr("knowledge.indexing.model_name", lambda: "fake-model-v2")
    report = index_articles(articles)

    assert report.updated == 2
    assert set(KBArticle.objects.values_list("embedding_model", flat=True)) == {"fake-model-v2"}


def test_articles_removed_from_disk_are_deleted(embedder):
    index_articles([article("kb-001"), article("kb-002")])

    report = index_articles([article("kb-001")])

    assert report.deleted == 1
    assert list(KBArticle.objects.values_list("article_id", flat=True)) == ["kb-001"]


def test_wrong_vector_size_is_rejected_before_saving(monkeypatch):
    monkeypatch.setattr("knowledge.indexing.embed_passages", lambda texts: [[0.1] * 768 for _ in texts])
    monkeypatch.setattr("knowledge.indexing.model_name", lambda: "big-model")

    with pytest.raises(ValueError, match="768 dimensions"):
        index_articles([article("kb-001")])

    assert KBArticle.objects.count() == 0
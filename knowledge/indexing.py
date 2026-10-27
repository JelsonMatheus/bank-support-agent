"""Keep the KBArticle table in sync with the Markdown articles."""

import hashlib
from dataclasses import dataclass

from django.db import transaction

from knowledge.articles import Article, load_articles
from knowledge.embeddings import embed_passages, model_name
from knowledge.models import EMBEDDING_DIMENSIONS, KBArticle


@dataclass
class IndexReport:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0


def text_to_embed(article: Article) -> str:
    return f"{article.title}\n\n{article.body}"


def content_hash(article: Article, embedding_model: str) -> str:
    fingerprint = f"{embedding_model}\n{text_to_embed(article)}"
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def index_articles(articles: list[Article] | None = None) -> IndexReport:
    articles = load_articles() if articles is None else articles
    embedding_model = model_name()
    report = IndexReport()

    stored_hashes = dict(KBArticle.objects.values_list("article_id", "content_hash"))
    pending = [a for a in articles if stored_hashes.get(a.id) != content_hash(a, embedding_model)]
    report.unchanged = len(articles) - len(pending)

    vectors = embed_passages([text_to_embed(a) for a in pending]) if pending else []
    for article, vector in zip(pending, vectors, strict=True):
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"{embedding_model} produced {len(vector)} dimensions; the table expects {EMBEDDING_DIMENSIONS}"
            )

    with transaction.atomic():
        for article, vector in zip(pending, vectors, strict=True):
            _, created = KBArticle.objects.update_or_create(
                article_id=article.id,
                defaults={
                    "title": article.title,
                    "category": article.category,
                    "body": article.body,
                    "content_hash": content_hash(article, embedding_model),
                    "embedding_model": embedding_model,
                    "embedding": vector,
                },
            )
            if created:
                report.created += 1
            else:
                report.updated += 1

        report.deleted, _ = KBArticle.objects.exclude(article_id__in=[a.id for a in articles]).delete()

    return report

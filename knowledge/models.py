from django.db import models
from pgvector.django import VectorField

# Must match the model in settings.EMBEDDING_MODEL. Changing the model to one
# with a different size requires a migration.
EMBEDDING_DIMENSIONS = 384


class KBArticle(models.Model):
    """A knowledge base article as indexed for search.

    The Markdown files in knowledge/articles/ are the source of truth; this
    table is derived from them by `manage.py index_knowledge_base`.
    """

    article_id = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=16)
    body = models.TextField()
    content_hash = models.CharField(max_length=64)
    embedding_model = models.CharField(max_length=128)
    embedding = VectorField(dimensions=EMBEDDING_DIMENSIONS)
    indexed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["article_id"]

    def __str__(self) -> str:
        return f"{self.article_id}: {self.title}"
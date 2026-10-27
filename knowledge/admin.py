from django.contrib import admin

from knowledge.models import KBArticle


@admin.register(KBArticle)
class KBArticleAdmin(admin.ModelAdmin):
    list_display = ("article_id", "title", "category", "embedding_model", "indexed_at")
    list_filter = ("category",)
    search_fields = ("article_id", "title", "body")
    exclude = ("embedding",)
    readonly_fields = ("article_id", "title", "category", "body", "content_hash", "embedding_model", "indexed_at")

    def has_add_permission(self, request):
        return False
    
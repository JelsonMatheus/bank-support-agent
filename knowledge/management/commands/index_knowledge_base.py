from django.core.management.base import BaseCommand

from knowledge.indexing import index_articles


class Command(BaseCommand):
    help = "Embed knowledge base articles and sync them with the KBArticle table."

    def handle(self, *args, **options):
        report = index_articles()
        self.stdout.write(
            f"Created {report.created}, updated {report.updated}, "
            f"unchanged {report.unchanged}, deleted {report.deleted}."
        )

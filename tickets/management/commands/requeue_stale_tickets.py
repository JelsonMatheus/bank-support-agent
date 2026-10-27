from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Ticket
from tickets.services import enqueue_ticket


class Command(BaseCommand):
    help = "Re-enqueue tickets stuck in 'received' or 'processing' for longer than --minutes."

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type=int, default=10)

    def handle(self, *args, minutes: int, **options):
        cutoff = timezone.now() - timedelta(minutes=minutes)

        stuck_processing = Ticket.objects.filter(status=Ticket.Status.PROCESSING, updated_at__lt=cutoff)
        processing_ids = list(stuck_processing.values_list("id", flat=True))
        stuck_processing.update(status=Ticket.Status.RECEIVED, updated_at=timezone.now())

        waiting_ids = list(
            Ticket.objects.filter(status=Ticket.Status.RECEIVED, updated_at__lt=cutoff).values_list("id", flat=True)
        )

        for ticket_id in processing_ids + waiting_ids:
            enqueue_ticket(ticket_id)

        self.stdout.write(
            f"Re-enqueued {len(processing_ids)} stuck in processing and {len(waiting_ids)} waiting in received."
        )

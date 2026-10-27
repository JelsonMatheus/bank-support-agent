from django.urls import reverse
from rest_framework import generics, status
from rest_framework.response import Response

from tickets.models import Ticket
from tickets.serializers import TicketCreateSerializer, TicketSerializer

from django.db import transaction
from tickets.services import enqueue_ticket


class TicketCreateView(generics.CreateAPIView):
    """Accept a customer message. The agent processes it asynchronously."""

    serializer_class = TicketCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        transaction.on_commit(lambda: enqueue_ticket(ticket.id))

        location = reverse("tickets:detail", kwargs={"id": ticket.id})
        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_202_ACCEPTED,
            headers={"Location": location},
        )


class TicketDetailView(generics.RetrieveAPIView):
    """Return a ticket's status and the latest agent result."""

    serializer_class = TicketSerializer
    queryset = Ticket.objects.prefetch_related("runs")
    lookup_field = "id"
    
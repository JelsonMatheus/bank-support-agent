from django.urls import path

from tickets.views import TicketCreateView, TicketDetailView

app_name = "tickets"

urlpatterns = [
    path("tickets/", TicketCreateView.as_view(), name="create"),
    path("tickets/<uuid:id>/", TicketDetailView.as_view(), name="detail"),
]


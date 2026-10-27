from django.contrib import admin

from tickets.models import AgentRun, Ticket


class AgentRunInline(admin.TabularInline):
    model = AgentRun
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("created_at", "outcome", "category", "confidence", "handoff_reason", "cited_articles", "prompt_version")
    readonly_fields = fields


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_id", "status", "channel", "created_at")
    list_filter = ("status", "channel")
    search_fields = ("text", "customer_id")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [AgentRunInline]


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ("ticket", "outcome", "category", "handoff_reason", "confidence", "prompt_version", "created_at")
    list_filter = ("outcome", "category", "handoff_reason", "prompt_version")
    readonly_fields = [field.name for field in AgentRun._meta.fields]

    def has_add_permission(self, request):
        return False
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ContactMessage, ContactReason


@admin.register(ContactReason)
class ContactReasonAdmin(ModelAdmin):
    list_display = ['label', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'label']


@admin.register(ContactMessage)
class ContactMessageAdmin(ModelAdmin):
    list_display = ['__str__', 'email', 'reason', 'status', 'created_at']
    list_filter = ['status', 'reason', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'message']
    readonly_fields = [
        'first_name',
        'last_name',
        'email',
        'user',
        'reason',
        'message',
        'created_at',
        'updated_at',
    ]
    ordering = ['-created_at']
    actions = ['mark_as_read', 'mark_as_resolved']

    @admin.action(description='Marquer comme lu')
    def mark_as_read(self, request, queryset):
        queryset.update(status=ContactMessage.STATUS_READ)
        self.message_user(request, f"{queryset.count()} message(s) marqué(s) comme lu.")

    @admin.action(description='Marquer comme résolu')
    def mark_as_resolved(self, request, queryset):
        queryset.update(status=ContactMessage.STATUS_RESOLVED)
        self.message_user(request, f"{queryset.count()} message(s) marqué(s) comme résolu.")

    def has_add_permission(self, request):
        """On ne crée pas de messages depuis l'admin."""
        return False

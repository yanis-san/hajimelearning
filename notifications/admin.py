from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    # CORRECTION : J'ai enlevé 'title' et mis 'message' à la place
    list_display = ('recipient', 'message', 'is_read', 'created_at')

    list_filter = ('is_read', 'created_at')

    # CORRECTION : J'ai enlevé 'title' de la recherche aussi
    search_fields = ('recipient__email', 'recipient__first_name', 'message')

    actions = ['mark_as_read']

    @admin.action(description='Marquer les notifications sélectionnées comme lues')
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_support', 'email_progress', 'email_newsletter', 'updated_at')
    list_filter = ('email_support', 'email_progress', 'email_newsletter')
    search_fields = ('user__email',)
    list_select_related = ('user',)

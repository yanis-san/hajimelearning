from django.contrib import admin
from .models import Notification

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
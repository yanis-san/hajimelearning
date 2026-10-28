from django.contrib import admin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import AccessRequest, ActivationCode, Coupon, Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(ModelAdmin):
    list_display = ['student', 'course', 'enrolled_at']
    list_filter = ['course']
    search_fields = ['student__email', 'course__title']
    readonly_fields = ['enrolled_at']


@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_until', 'status_display']
    list_filter = ['is_active', 'valid_from', 'valid_until']
    search_fields = ['code']

    @admin.display(description="État")
    def status_display(self, obj):
        if not obj.is_active:
            return "🔴 Désactivé"
        if obj.is_valid:
            return "🟢 En cours"
        if obj.valid_until and timezone.now() > obj.valid_until:
            return "🔴 Expiré"
        return "🟠 Pas encore commencé"


@admin.register(AccessRequest)
class AccessRequestAdmin(ModelAdmin):
    # Ce qu'on voit dans la liste
    list_display = ['student', 'course', 'status', 'created_at']
    list_select_related = ['student', 'course']

    # Les filtres sur la droite (très utile pour voir juste les PENDING)
    list_filter = ['status', 'course']

    # Barre de recherche (par email ou titre du cours)
    search_fields = ['student__email', 'course__title']

    # Petit bonus : Permet de changer le status direct depuis la liste sans ouvrir
    list_editable = ['status']

    # Trie par le plus récent en premier
    ordering = ['-created_at']


@admin.register(ActivationCode)
class ActivationCodeAdmin(ModelAdmin):
    list_display = ['code', 'course', 'is_used', 'used_by']
    list_filter = ['is_used', 'course']

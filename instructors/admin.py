from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import InstructorPlan, InstructorProfile, InstructorRequest


@admin.register(InstructorPlan)
class InstructorPlanAdmin(ModelAdmin):
    list_display = ['name', 'price', 'max_courses', 'revenue_percent', 'is_featured', 'is_active', 'order']
    list_editable = ['order', 'is_active', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(InstructorRequest)
class InstructorRequestAdmin(ModelAdmin):
    list_display = ['user', 'plan', 'status', 'created_at']
    list_filter = ['status', 'plan']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'plan', 'payment_proof', 'created_at']
    actions = ['approve_requests', 'reject_requests']

    @admin.action(description="✅ Approuver les demandes sélectionnées")
    def approve_requests(self, request, queryset):
        for req in queryset.filter(status='PENDING'):
            req.status = 'APPROVED'
            req.save()
            # Le signal post_save crée le profil
        self.message_user(request, f"{queryset.count()} demande(s) approuvée(s).")

    @admin.action(description="❌ Refuser les demandes sélectionnées")
    def reject_requests(self, request, queryset):
        queryset.update(status='REJECTED')
        self.message_user(request, f"{queryset.count()} demande(s) refusée(s).")


@admin.register(InstructorProfile)
class InstructorProfileAdmin(ModelAdmin):
    list_display = ['user', 'plan', 'max_courses', 'revenue_percent', 'is_active', 'activated_at']
    list_filter = ['plan', 'is_active']
    search_fields = ['user__email']

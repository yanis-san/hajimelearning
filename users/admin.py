from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin, TabularInline
from .models import User
from access.models import AccessRequest, ActivationCode

# Inlines (Garde tes accès comme avant)
class AccessRequestInline(TabularInline):
    model = AccessRequest
    fk_name = 'student'
    extra = 0
    fields = ['course', 'status', 'created_at']
    readonly_fields = ['created_at']
    can_delete = True
    verbose_name = "Accès via Preuve/CCP"

class ActivationCodeInline(TabularInline):
    model = ActivationCode
    fk_name = 'used_by'
    extra = 0
    fields = ['course', 'code', 'is_used', 'used_at']
    readonly_fields = ['course', 'code', 'used_at']
    can_delete = True
    verbose_name = "Code d'Activation"

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'country', 'gender', 'is_active']
    search_fields = ['email', 'last_name', 'phone_number']

    # Organisation du formulaire Admin
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Identité', {'fields': ('first_name', 'last_name', 'gender', 'birth_date')}),
        ('Coordonnées', {'fields': ('phone_number', 'address', 'city', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name'),
        }),
    )

    inlines = [AccessRequestInline, ActivationCodeInline]
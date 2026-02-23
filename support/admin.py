from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Question, Response

class ResponseInline(TabularInline):
    model = Response
    extra = 1
    fields = ['author', 'content', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ['title', 'student', 'course', 'status', 'created_at']
    list_filter = ['status', 'course', 'created_at']
    search_fields = ['title', 'content', 'student__email']
    
    # On ajoute les réponses directement dans la page de la question
    inlines = [ResponseInline]
    
    # Actions rapides
    actions = ['mark_as_resolved']

    @admin.action(description='Marquer comme Résolu')
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='RESOLVED')
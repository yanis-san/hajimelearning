from django.contrib import admin
from django.db import models
from markdownx.widgets import AdminMarkdownxWidget
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import Category, ContentBlock, Course, CourseCompletion, Lesson, Module, QuizResult


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


# 1. Configuration des Blocs de Contenu (Page Builder)
class ContentBlockInline(StackedInline):
    model = ContentBlock
    extra = 0  # On commence vide
    fields = ['order', 'type', 'text_content', 'video_id', 'file_content']

    # On applique l'éditeur Markdown uniquement pour les champs TextField (text_content)
    formfield_overrides = {
        models.TextField: {'widget': AdminMarkdownxWidget},
    }

    # On replie les blocs pour que ce soit plus lisible
    classes = ['collapse']


# 2. Admin des Leçons (Avec le constructeur de page)
@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    list_display = ['title', 'module', 'is_free']
    search_fields = ['title']
    prepopulated_fields = {"slug": ("title",)}

    # On injecte les blocs ici
    inlines = [ContentBlockInline]


# 3. Admin des Modules (Avec les leçons en liste simple)
class LessonInline(TabularInline):
    model = Lesson
    extra = 1
    fields = ['order', 'title', 'slug', 'is_free']  # On a retiré video_id ici car c'est dans les blocs maintenant
    prepopulated_fields = {"slug": ("title",)}
    tab = True


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    inlines = [LessonInline]
    search_fields = ['title']


# 4. Admin des Cours (Avec les modules)
class ModuleInline(TabularInline):
    model = Module
    extra = 1
    fields = ['order', 'title']
    tab = True


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ['title', 'category', 'price', 'is_published', 'created_at']
    list_filter = ['is_published', 'category']
    search_fields = ['title']
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ModuleInline]


@admin.register(QuizResult)
class QuizResultAdmin(ModelAdmin):
    # Colonnes à afficher
    list_display = ['student', 'get_course', 'get_quiz_name', 'score_display', 'completed_at']

    # Filtres sur la droite (Optimisés pour filtrer par Cours)
    list_filter = ['block__lesson__module__course', 'completed_at']

    # Barre de recherche (Cherche par email ou titre du quiz)
    search_fields = ['student__email', 'block__quiz_title', 'block__lesson__title']

    # --- OPTIMISATION PERFORMANCE (Le Secret) ---
    def get_queryset(self, request):
        # On charge toutes les relations en une seule requête SQL
        return (
            super()
            .get_queryset(request)
            .select_related(
                'student',  # L'élève
                'block',  # Le bloc Quiz
                'block__lesson',  # La leçon parente
                'block__lesson__module',  # Le module parent
                'block__lesson__module__course',  # Le cours parent
            )
        )

    # --- Colonnes personnalisées ---

    def get_course(self, obj):
        # Grâce au select_related, ceci ne déclenche pas de nouvelle requête SQL
        return obj.block.lesson.module.course.title

    get_course.short_description = "Formation"
    get_course.admin_order_field = 'block__lesson__module__course__title'  # Rend la colonne triable

    def get_quiz_name(self, obj):
        return obj.block.quiz_title or f"Quiz (Bloc #{obj.block.id})"

    get_quiz_name.short_description = "Quiz"

    def score_display(self, obj):
        return f"{obj.score} / {obj.total_questions}"

    score_display.short_description = "Note"


@admin.register(CourseCompletion)
class CourseCompletionAdmin(ModelAdmin):
    list_display = ['student', 'course', 'completed_at', 'has_certificate']
    list_filter = ['course', 'completed_at']
    search_fields = ['student__email', 'course__title']
    readonly_fields = ['student', 'course', 'completed_at', 'certificate_pdf']

    def has_certificate(self, obj):
        return bool(obj.certificate_pdf)

    has_certificate.boolean = True
    has_certificate.short_description = "Certificat généré"

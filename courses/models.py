from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from markdownx.models import MarkdownxField

from .storage import protected_storage
from .validators import (
    ANKI_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DOC_EXTENSIONS,
    IMAGE_EXTENSIONS,
    FileSizeValidator,
    get_upload_path,
)


class Category(models.Model):
    """Catégorie d'une formation — gérable depuis l'admin."""

    name = models.CharField("Étiquette", max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField("Ordre", default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField(unique=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_as_instructor',
        verbose_name="Instructeur",
        help_text="L'instructeur propriétaire de cette formation (vide = plateforme)",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="Catégorie",
    )

    # 1. POUR LA CARTE (ACCUEIL)
    # On renomme l'ancien usage en "short_description" pour être clair
    short_description = models.TextField(
        "Phrase d'accroche (Carte)", help_text="Ce texte s'affiche sur la page d'accueil (court)."
    )

    # 2. POUR LA PAGE DE VENTE (LANDING PAGE)
    # On utilise Markdown pour pouvoir mettre du gras, des titres, des listes...
    description = MarkdownxField(
        "Page de Vente (Détails)", help_text="Description longue et détaillée pour convaincre."
    )

    # 3. ARGUMENTS MARKETING
    what_you_will_learn = MarkdownxField("Ce que vous allez apprendre", help_text="Liste à puces", blank=True)
    prerequisites = MarkdownxField("Pré-requis", help_text="Matériel nécessaire", blank=True, default="Aucun.")
    trailer_video_id = models.CharField("ID Vidéo Trailer (YouTube)", max_length=100, blank=True)

    meta_description = models.CharField(
        "Meta Description (Google)", max_length=160, blank=True, help_text="Résumé pour Google (160 caractères max)."
    )
    keywords = models.CharField(
        "Mots-clés", max_length=255, blank=True, help_text="Séparés par des virgules (ex: python, django, code)"
    )

    # Pour le sitemap (date de dernière modif)
    updated_at = models.DateTimeField(auto_now=True)

    # INFOS
    price = models.DecimalField("Prix (DA)", max_digits=10, decimal_places=0, default=0)

    thumbnail = models.ImageField(
        "Image carte (catalogue / accueil)",
        upload_to=get_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        help_text="Utilisée sur les cartes (catalogue, page d'accueil).",
    )
    cover_image = models.ImageField(
        "Image de couverture (vitrine)",
        upload_to=get_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        help_text="Grande image affichée sur la page de vente (vitrine).",
    )

    is_published = models.BooleanField("Publié ?", default=False)
    is_featured = models.BooleanField(
        "Afficher sur l'accueil", default=False, help_text="Si coché, ce cours apparaît sur la page d'accueil."
    )
    hide_title_on_card = models.BooleanField(
        "Masquer le titre sur la carte",
        default=False,
        help_text="Si coché, le titre n'apparaît pas sur la carte (utile si la jaquette contient déjà le titre).",
    )
    completion_sound = models.FileField(
        "Son de complétion",
        upload_to=get_upload_path,
        blank=True,
        null=True,
        help_text="MP3 joué quand l'étudiant termine une leçon (optionnel).",
        validators=[FileExtensionValidator(allowed_extensions=AUDIO_EXTENSIONS)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['is_published', 'is_featured'], name='course_published_featured_idx')]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course_detail', args=[self.slug])


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField("Titre du module", max_length=200)
    order = models.PositiveIntegerField("Ordre", default=0, help_text="1, 2, 3...")
    is_published = models.BooleanField("Publié", default=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Module"
        indexes = [models.Index(fields=['course', 'order'], name='module_course_order_idx')]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField("Titre de la leçon", max_length=200)
    slug = models.SlugField()
    order = models.PositiveIntegerField("Ordre", default=0)
    is_free = models.BooleanField("Gratuit (Aperçu)", default=False)
    is_published = models.BooleanField("Publié", default=True)
    duration_minutes = models.PositiveSmallIntegerField(
        "Durée estimée (min)",
        null=True,
        blank=True,
        help_text="Affichée à l'étudiant dans le sommaire (optionnel).",
    )

    class Meta:
        ordering = ['order']
        constraints = [models.UniqueConstraint(fields=['module', 'slug'], name='unique_lesson_slug_per_module')]
        verbose_name = "Leçon"

    def __str__(self):
        return self.title

    # Priorité d'affichage du type principal d'une leçon (icône du sommaire)
    _TYPE_PRIORITY = ('video', 'quiz', 'anki', 'audio', 'file', 'text')

    @property
    def primary_type(self):
        """Type dominant de la leçon (utilise les blocs préchargés si dispo)."""
        types = {b.type for b in self.blocks.all()}
        for t in self._TYPE_PRIORITY:
            if t in types:
                return t
        return 'text'


class ContentBlock(models.Model):
    CONTENT_TYPES = (
        ('text', '📝 Texte / Image'),
        ('video', '🎬 Vidéo (YouTube)'),
        ('audio', '🎧 Audio (MP3)'),
        ('file', '📎 Fichier à télécharger'),
        ('quiz', '🧠 Quiz / Examen'),
        ('anki', '🗂️ Deck Anki'),
    )

    lesson = models.ForeignKey(Lesson, related_name='blocks', on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    order = models.PositiveIntegerField(default=0)

    # Titre générique (Nom du fichier, Titre de l'audio...)
    title = models.CharField("Titre du bloc", max_length=200, blank=True, null=True)

    # Champs Contenu
    text_content = MarkdownxField("Contenu", blank=True, null=True)
    video_id = models.CharField("ID Vidéo", max_length=100, blank=True)

    # Fichier principal (Audio, Doc ou Deck Anki) - PROTÉGÉ (hors MEDIA_ROOT)
    file_content = models.FileField(
        "Fichier Principal",
        upload_to=get_upload_path,
        storage=protected_storage,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=AUDIO_EXTENSIONS + DOC_EXTENSIONS + ANKI_EXTENSIONS),
            FileSizeValidator(max_mb=100),
        ],
    )

    # Fichier correction (Caché) - PROTÉGÉ
    related_file = models.FileField(
        "Fichier associé (Correction)",
        upload_to=get_upload_path,
        storage=protected_storage,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=DOC_EXTENSIONS), FileSizeValidator(max_mb=10)],
    )

    # Deck Anki : nombre de cartes (calculé automatiquement à l'upload, modifiable)
    card_count = models.PositiveIntegerField("Nombre de cartes", null=True, blank=True)

    # Titre du Quiz
    quiz_title = models.CharField("Titre du Quiz", max_length=200, blank=True, null=True)
    pass_percent = models.PositiveSmallIntegerField(
        "Seuil de réussite (%)",
        default=70,
        help_text="Score minimum pour considérer le quiz comme réussi.",
    )

    class Meta:
        ordering = ['order']
        verbose_name = "Bloc de contenu"
        indexes = [models.Index(fields=['lesson', 'order'], name='block_lesson_order_idx')]

    def __str__(self):
        return f"Bloc {self.type} - {self.lesson.title}"


class QuizQuestion(models.Model):
    block = models.ForeignKey(ContentBlock, related_name='questions', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    question_text = models.CharField("Question", max_length=500)

    choice_a = models.CharField("A", max_length=200)
    choice_b = models.CharField("B", max_length=200)
    choice_c = models.CharField("C", max_length=200, blank=True, null=True)
    choice_d = models.CharField("D", max_length=200, blank=True, null=True)

    CORRECT_ANSWERS = (('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'))
    correct_answer = models.CharField("Réponse", max_length=1, choices=CORRECT_ANSWERS)

    explanation = models.TextField("Explication", blank=True)
    duration = models.PositiveIntegerField("Durée (secondes)", default=20, help_text="Temps pour répondre")

    class Meta:
        ordering = ['order']


class QuizResult(models.Model):
    """Dernier résultat d'un étudiant à un quiz (une ligne par étudiant/quiz)."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_results')
    block = models.ForeignKey(ContentBlock, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'block'], name='unique_quiz_result_student_block')]

    def __str__(self):
        return f"{self.student.email} - Quiz {self.block.id}: {self.score}/{self.total_questions}"


class QuizAttempt(models.Model):
    """Historique de chaque tentative d'un étudiant à un quiz."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    block = models.ForeignKey(ContentBlock, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"

    def __str__(self):
        return f"{self.student.email} - Quiz {self.block_id}: {self.score}/{self.total_questions}"


class LandingSection(models.Model):
    """Section libre pour la page vitrine d'un cours (page-builder léger)."""

    SECTION_TYPES = (
        ('text', '📝 Texte'),
        ('image', '🖼️ Image'),
        ('video', '🎬 Vidéo YouTube'),
        ('features', '✅ Points forts'),
        ('hero', '🦸 Hero'),
        ('text_image', '📐 Texte + Image'),
        ('faq', '❓ FAQ'),
        ('testimonials', '💬 Témoignages'),
    )

    BG_CHOICES = (
        ('none', 'Aucun'),
        ('white', 'Blanc'),
        ('gray', 'Gris clair'),
        ('green', 'Vert clair'),
        ('orange', 'Teinte principale claire'),
        ('dark', 'Sombre'),
    )

    IMAGE_POSITION_CHOICES = (
        ('right', 'Image à droite'),
        ('left', 'Image à gauche'),
    )

    course = models.ForeignKey(Course, related_name='landing_sections', on_delete=models.CASCADE)
    section_type = models.CharField("Type", max_length=20, choices=SECTION_TYPES)
    order = models.PositiveIntegerField("Ordre", default=0)

    title = models.CharField("Titre", max_length=200, blank=True)
    body = MarkdownxField("Contenu", blank=True, help_text="Markdown supporté")
    image = models.ImageField(
        "Image",
        upload_to=get_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
    )
    video_id = models.CharField("ID YouTube", max_length=100, blank=True)

    subtitle = models.CharField("Sous-titre", max_length=300, blank=True)
    cta_text = models.CharField("Texte du bouton", max_length=100, blank=True, help_text="Ex : S'inscrire maintenant")
    cta_url = models.CharField("Lien du bouton", max_length=500, blank=True, help_text="URL ou ancre (#inscription)")
    image_position = models.CharField("Position image", max_length=10, choices=IMAGE_POSITION_CHOICES, default='right')

    css_class = models.CharField(
        "Classes CSS", max_length=500, blank=True, help_text="Classes Tailwind personnalisées (ex: py-12 text-center)"
    )
    background = models.CharField("Fond", max_length=20, choices=BG_CHOICES, default='none')
    is_visible = models.BooleanField(
        "Visible", default=True, help_text="Décochez pour masquer cette section sans la supprimer"
    )

    class Meta:
        ordering = ['order']
        verbose_name = "Section vitrine"
        verbose_name_plural = "Sections vitrine"

    def __str__(self):
        return f"{self.get_section_type_display()} — {self.title or '(sans titre)'}"


class StudentProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'lesson'], name='unique_student_progress_student_lesson')
        ]
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.student.email} - {self.lesson.title}"


class CourseActivity(models.Model):
    """Dernière leçon consultée par un étudiant dans un cours (bouton « Continuer »)."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_activities')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='activities')
    last_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_course_activity_student_course')
        ]
        ordering = ['-updated_at']
        verbose_name = "Activité de cours"
        verbose_name_plural = "Activités de cours"

    def __str__(self):
        return f"{self.student.email} — {self.course.title}"


class CourseCompletion(models.Model):
    """Enregistrement unique quand un étudiant termine toutes les leçons d'un cours."""

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='completions',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='completions',
    )
    completed_at = models.DateTimeField(auto_now_add=True)
    certificate_pdf = models.FileField(
        "Certificat PDF",
        upload_to='certificates/',
        storage=protected_storage,  # données personnelles : jamais servi par /media/
        blank=True,
        null=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_course_completion_student_course')
        ]
        ordering = ['-completed_at']
        verbose_name = "Complétion de cours"
        verbose_name_plural = "Complétions de cours"

    def __str__(self):
        return f"{self.student.email} — {self.course.title}"


class StudentNote(models.Model):
    """Notes personnelles de l'étudiant pour un bloc de contenu."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notes')
    block = models.ForeignKey(ContentBlock, on_delete=models.CASCADE, related_name='student_notes')
    content = models.TextField("Mes notes", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'block'], name='unique_student_note_student_block')]
        ordering = ['-updated_at']
        verbose_name = "Note personnelle"
        verbose_name_plural = "Notes personnelles"

    def __str__(self):
        return f"Notes de {self.student.email} sur le bloc {self.block.id}"

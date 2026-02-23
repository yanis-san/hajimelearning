from django.db import models
from django.conf import settings
from markdownx.models import MarkdownxField
from django.core.validators import FileExtensionValidator
from .validators import get_upload_path, FileSizeValidator, IMAGE_EXTENSIONS, DOC_EXTENSIONS, AUDIO_EXTENSIONS
from django.urls import reverse

class Course(models.Model):
    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField(unique=True)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses_as_instructor',
        verbose_name="Instructeur",
        help_text="L'instructeur propriétaire de cette formation (vide = plateforme)",
    )
    
    # 1. POUR LA CARTE (ACCUEIL)
    # On renomme l'ancien usage en "short_description" pour être clair
    short_description = models.TextField("Phrase d'accroche (Carte)", help_text="Ce texte s'affiche sur la page d'accueil (court).")
    
    # 2. POUR LA PAGE DE VENTE (LANDING PAGE)
    # On utilise Markdown pour pouvoir mettre du gras, des titres, des listes...
    description = MarkdownxField("Page de Vente (Détails)", help_text="Description longue et détaillée pour convaincre.")
    
    # 3. ARGUMENTS MARKETING
    what_you_will_learn = MarkdownxField("Ce que vous allez apprendre", help_text="Liste à puces", blank=True)
    prerequisites = MarkdownxField("Pré-requis", help_text="Matériel nécessaire", blank=True, default="Aucun.")
    trailer_video_id = models.CharField("ID Vidéo Trailer (YouTube)", max_length=100, blank=True)

    meta_description = models.CharField("Meta Description (Google)", max_length=160, blank=True, help_text="Résumé pour Google (160 caractères max).")
    keywords = models.CharField("Mots-clés", max_length=255, blank=True, help_text="Séparés par des virgules (ex: python, django, code)")
    
    # Pour le sitemap (date de dernière modif)
    updated_at = models.DateTimeField(auto_now=True)

    # INFOS
    price = models.DecimalField("Prix (DA)", max_digits=10, decimal_places=0, default=0)
    
    thumbnail = models.ImageField(
        "Image carte (catalogue / accueil)",
        upload_to=get_upload_path,
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        help_text="Utilisée sur les cartes (catalogue, page d'accueil)."
    )
    cover_image = models.ImageField(
        "Image de couverture (vitrine)",
        upload_to=get_upload_path,
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        help_text="Grande image affichée sur la page de vente (vitrine)."
    )
    
    is_published = models.BooleanField("Publié ?", default=False)
    is_featured = models.BooleanField(
        "Afficher sur l'accueil",
        default=False,
        help_text="Si coché, ce cours apparaît sur la page d'accueil."
    )
    hide_title_on_card = models.BooleanField(
        "Masquer le titre sur la carte",
        default=False,
        help_text="Si coché, le titre n'apparaît pas sur la carte (utile si la jaquette contient déjà le titre)."
    )
    completion_sound = models.FileField(
        "Son de complétion",
        upload_to=get_upload_path,
        blank=True, null=True,
        help_text="MP3 joué quand l'étudiant termine une leçon (optionnel).",
        validators=[FileExtensionValidator(allowed_extensions=AUDIO_EXTENSIONS)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField("Titre de la leçon", max_length=200)
    slug = models.SlugField()
    order = models.PositiveIntegerField("Ordre", default=0)
    is_free = models.BooleanField("Gratuit (Aperçu)", default=False)
    is_published = models.BooleanField("Publié", default=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['module', 'slug']
        verbose_name = "Leçon"

    def __str__(self):
        return self.title

class ContentBlock(models.Model):
    CONTENT_TYPES = (
        ('text', '📝 Texte / Image'),
        ('video', '🎬 Vidéo (Bunny)'),
        ('audio', '🎧 Audio (MP3)'),
        ('file', '📎 Fichier à télécharger'),
        ('quiz', '🧠 Quiz / Examen'), 
    )

    lesson = models.ForeignKey(Lesson, related_name='blocks', on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    order = models.PositiveIntegerField(default=0)
    
    # Titre générique (Nom du fichier, Titre de l'audio...)
    title = models.CharField("Titre du bloc", max_length=200, blank=True, null=True)

    # Champs Contenu
    text_content = MarkdownxField("Contenu", blank=True, null=True)
    video_id = models.CharField("ID Vidéo", max_length=100, blank=True)
    
    # Fichier principal (Audio ou Doc) - SÉCURISÉ
    file_content = models.FileField(
        "Fichier Principal", 
        upload_to=get_upload_path, 
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=AUDIO_EXTENSIONS + DOC_EXTENSIONS),
            FileSizeValidator(max_mb=50)
        ]
    )

    # Fichier correction (Caché) - SÉCURISÉ
    related_file = models.FileField(
        "Fichier associé (Correction)", 
        upload_to=get_upload_path, 
        blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=DOC_EXTENSIONS),
            FileSizeValidator(max_mb=10)
        ]
    )
    
    # Titre du Quiz
    quiz_title = models.CharField("Titre du Quiz", max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Bloc de contenu"

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
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_results')
    block = models.ForeignKey(ContentBlock, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'block'] 

    def __str__(self):
        return f"{self.student.email} - Quiz {self.block.id}: {self.score}/{self.total_questions}"
        
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
        ('orange', 'Orange clair'),
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
        blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)]
    )
    video_id = models.CharField("ID YouTube", max_length=100, blank=True)

    subtitle = models.CharField("Sous-titre", max_length=300, blank=True)
    cta_text = models.CharField("Texte du bouton", max_length=100, blank=True,
                                help_text="Ex : S'inscrire maintenant")
    cta_url = models.CharField("Lien du bouton", max_length=500, blank=True,
                               help_text="URL ou ancre (#inscription)")
    image_position = models.CharField(
        "Position image", max_length=10,
        choices=IMAGE_POSITION_CHOICES, default='right'
    )

    css_class = models.CharField(
        "Classes CSS", max_length=500, blank=True,
        help_text="Classes Tailwind personnalisées (ex: py-12 text-center)"
    )
    background = models.CharField("Fond", max_length=20, choices=BG_CHOICES, default='none')
    is_visible = models.BooleanField("Visible", default=True,
                                     help_text="Décochez pour masquer cette section sans la supprimer")

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
        unique_together = ['student', 'lesson']
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.student.email} - {self.lesson.title}"
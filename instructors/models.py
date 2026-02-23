from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from courses.validators import get_upload_path, FileSizeValidator, IMAGE_EXTENSIONS


class InstructorPlan(models.Model):
    """
    Offre instructeur (Starter, Pro, Expert).
    Gérée par le superadmin via Django Unfold.
    """
    name = models.CharField("Nom de l'offre", max_length=100)
    slug = models.SlugField(unique=True)
    price = models.DecimalField("Prix (DA)", max_digits=10, decimal_places=0)
    
    # Limites
    max_courses = models.PositiveIntegerField(
        "Nombre max de formations",
        help_text="0 = illimité",
    )
    max_modules_per_course = models.PositiveIntegerField(
        "Modules max par formation",
        default=0,
        help_text="0 = illimité",
    )
    max_lessons_per_course = models.PositiveIntegerField(
        "Leçons max par formation",
        default=0,
        help_text="0 = illimité",
    )
    revenue_percent = models.PositiveIntegerField(
        "Part de l'instructeur (%)",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Pourcentage des revenus pour l'instructeur",
    )

    # Affichage
    description = models.TextField(
        "Description courte",
        blank=True,
        help_text="Résumé marketing de l'offre",
    )
    features = models.TextField(
        "Avantages",
        blank=True,
        help_text="Un avantage par ligne (affiché en checklist)",
    )
    is_featured = models.BooleanField(
        "Mettre en avant",
        default=False,
        help_text="L'offre mise en avant (au milieu, badge 'Populaire')",
    )
    is_active = models.BooleanField("Active", default=True)
    order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Offre instructeur"
        verbose_name_plural = "Offres instructeur"

    def __str__(self):
        return f"{self.name} — {self.price} DA"

    def get_features_list(self):
        """Retourne les avantages sous forme de liste."""
        if not self.features:
            return []
        return [f.strip() for f in self.features.strip().split('\n') if f.strip()]


class InstructorRequest(models.Model):
    """
    Demande pour devenir instructeur (avec preuve de paiement).
    Même flow que AccessRequest pour les étudiants.
    """
    STATUS_CHOICES = (
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Refusé'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_requests',
    )
    plan = models.ForeignKey(
        InstructorPlan,
        on_delete=models.PROTECT,
        related_name='requests',
    )
    payment_proof = models.ImageField(
        "Preuve de paiement",
        upload_to=get_upload_path,
        help_text="Reçu CCP/BaridiMob (JPG, PNG)",
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
            FileSizeValidator(max_mb=5),
        ],
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
    )
    admin_note = models.TextField("Note admin", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Demande instructeur"
        verbose_name_plural = "Demandes instructeur"

    def __str__(self):
        return f"{self.user.email} → {self.plan.name} ({self.get_status_display()})"


class InstructorProfile(models.Model):
    """
    Profil instructeur (créé après approbation).
    Lie un utilisateur à un plan avec des limites concrètes.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='instructor_profile',
    )
    plan = models.ForeignKey(
        InstructorPlan,
        on_delete=models.PROTECT,
        related_name='instructors',
    )
    # Snapshot des limites au moment de l'achat
    max_courses = models.PositiveIntegerField("Formations max")
    max_modules_per_course = models.PositiveIntegerField("Modules max / formation", default=0)
    max_lessons_per_course = models.PositiveIntegerField("Leçons max / formation", default=0)
    revenue_percent = models.PositiveIntegerField("Part revenus (%)")

    is_active = models.BooleanField("Actif", default=True)
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Profil instructeur"
        verbose_name_plural = "Profils instructeur"

    def __str__(self):
        return f"{self.user.email} — {self.plan.name}"

    @property
    def courses_remaining(self):
        """Nombre de formations encore créables."""
        if self.max_courses == 0:
            return None  # Illimité
        from courses.models import Course
        used = Course.objects.filter(instructor=self.user).count()
        return max(0, self.max_courses - used)

    @property
    def can_create_course(self):
        remaining = self.courses_remaining
        return remaining is None or remaining > 0

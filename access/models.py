from django.db import models
from django.conf import settings
from courses.models import Course
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from courses.validators import get_upload_path, FileSizeValidator, IMAGE_EXTENSIONS
from django.utils import timezone
import uuid

# --- MODÈLE COUPON ---
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="Code en majuscules (ex: RAMADAN2025)")
    discount_percent = models.IntegerField(
        "Réduction (%)",
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Pourcentage de réduction (ex: 20 pour 20%)"
    )
    is_active = models.BooleanField("Actif ?", default=True)
    
    valid_from = models.DateTimeField("Valable à partir du", default=timezone.now, help_text="Date de début")
    valid_until = models.DateTimeField("Valable jusqu'au", null=True, blank=True, help_text="Laisser vide pour illimité")

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"

    @property
    def is_valid(self):
        now = timezone.now()
        if not self.is_active: return False
        if self.valid_from and now < self.valid_from: return False
        if self.valid_until and now > self.valid_until: return False
        return True

# --- MODÈLE DEMANDE D'ACCÈS ---
class AccessRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente de validation'),
        ('APPROVED', 'Validé (Accès donné)'),
        ('REJECTED', 'Refusé'),
    )

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    
    # SÉCURITÉ RENFORCÉE ICI
    payment_proof = models.ImageField(
        upload_to=get_upload_path, # Renommage UUID
        help_text="Reçu CCP/BaridiMob (JPG, PNG)",
        validators=[
            FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS), # Que des images
            FileSizeValidator(max_mb=5) # Max 5 Mo
        ]
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    final_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.student.email} -> {self.course.title}"

# --- MODÈLE CODE D'ACTIVATION ---
class ActivationCode(models.Model):
    code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Code {self.course.title}"

# --- INSCRIPTION (cours gratuits) ---
class Enrollment(models.Model):
    """Inscription explicite à un cours (gratuit uniquement)."""
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"

    def __str__(self):
        return f"{self.student.email} → {self.course.title}"


# --- LOGIQUE D'ACCÈS ---
def user_has_access(user, course):
    if not user.is_authenticated: return False
    if user.is_staff: return True
    if course.instructor == user: return True

    # Cours gratuit : inscription explicite requise
    if course.price == 0:
        return Enrollment.objects.filter(student=user, course=course).exists()

    # Cours payant : demande approuvée ou code d'activation
    if AccessRequest.objects.filter(student=user, course=course, status='APPROVED').exists():
        return True

    if ActivationCode.objects.filter(used_by=user, course=course, is_used=True).exists():
        return True

    return False
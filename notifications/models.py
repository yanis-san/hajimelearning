from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    Notification unifiée avec discriminant `notification_type`.

    - 'student'    : concerne l'étudiant (progression, réponse support…)
    - 'instructor' : concerne l'instructeur (nouvelle question dans son cours,
                     nouvelle inscription, nouvelle demande d'accès…)
    """

    TYPE_STUDENT = 'student'
    TYPE_INSTRUCTOR = 'instructor'
    TYPE_CHOICES = (
        (TYPE_STUDENT, 'Étudiant'),
        (TYPE_INSTRUCTOR, 'Instructeur'),
    )

    CATEGORY_PROGRESS = 'progress'
    CATEGORY_SUPPORT = 'support'
    CATEGORY_INSTRUCTOR = 'instructor'
    CATEGORY_CHOICES = (
        (CATEGORY_PROGRESS, 'Progression'),
        (CATEGORY_SUPPORT, 'Support'),
        (CATEGORY_INSTRUCTOR, 'Instructeur'),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_STUDENT,
        db_index=True,
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_PROGRESS,
        db_index=True,
    )
    title = models.CharField(max_length=100, null=True, blank=True, verbose_name="Titre")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, help_text="Lien vers la discussion ou le cours")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Les plus récentes en premier
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'notification_type'], name='notif_recipient_unread_idx'),
        ]

    def __str__(self):
        titre_aff = self.title if self.title else "Notification"
        return f"Notif pour {self.recipient}: {titre_aff} - {self.message}"

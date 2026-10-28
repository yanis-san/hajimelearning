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


class NotificationPreference(models.Model):
    """
    Préférences d'e-mails d'un utilisateur.

    Les e-mails *essentiels* (compte, paiement, accès, demandes) sont toujours envoyés et n'apparaissent pas ici.
    Les e-mails *facultatifs* sont regroupés en catégories que l'utilisateur peut couper.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences'
    )
    email_support = models.BooleanField(
        "Questions et réponses",
        default=True,
        help_text="Réponses à vos questions, nouvelles questions de vos étudiants.",
    )
    email_progress = models.BooleanField(
        "Progression et certificats", default=True, help_text="Certificat prêt et félicitations."
    )
    email_newsletter = models.BooleanField(
        "Actualités", default=False, help_text="Nouvelles formations et nouveautés de la plateforme."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Préférences de notification"
        verbose_name_plural = "Préférences de notification"

    def __str__(self):
        return f"Préférences de {self.user}"

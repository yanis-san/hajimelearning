from django.conf import settings
from django.db import models


class ContactReason(models.Model):
    """Motif de contact — gérable depuis l'admin Unfold."""

    label = models.CharField("Motif", max_length=100)
    is_active = models.BooleanField("Actif", default=True)
    order = models.PositiveSmallIntegerField("Ordre", default=0)

    class Meta:
        ordering = ['order', 'label']
        verbose_name = "Motif de contact"
        verbose_name_plural = "Motifs de contact"

    def __str__(self):
        return self.label


class ContactMessage(models.Model):
    """Message envoyé via le formulaire de contact."""

    STATUS_NEW = 'new'
    STATUS_READ = 'read'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = (
        (STATUS_NEW, 'Nouveau'),
        (STATUS_READ, 'Lu'),
        (STATUS_RESOLVED, 'Résolu'),
    )

    # Identité (pré-remplie si connecté)
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    email = models.EmailField("Email")

    # Lien optionnel vers le compte connecté
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_messages',
        verbose_name="Compte utilisateur",
    )
    reason = models.ForeignKey(
        ContactReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Motif",
    )
    message = models.TextField("Message")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.reason or 'Sans motif'}"

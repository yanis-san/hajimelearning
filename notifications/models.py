from django.db import models
from django.conf import settings

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100, null=True, blank=True, verbose_name="Titre")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, help_text="Lien vers la discussion ou le cours")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Les plus récentes en premier

    def __str__(self):
        titre_aff = self.title if self.title else "Notification"
        return f"Notif pour {self.recipient}: {titre_aff} - {self.message}"
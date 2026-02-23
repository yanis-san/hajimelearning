from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AccessRequest
from .tasks import send_access_confirmation_email # <--- On importe la tâche

@receiver(post_save, sender=AccessRequest)
def trigger_access_email(sender, instance, created, **kwargs):
    """
    Déclencheur : Si approuvé, on lance la tâche Celery.
    """
    if instance.status == 'APPROVED':
        # .delay() est la commande magique.
        # Elle dit : "Mets cette tâche dans Redis, le worker la fera plus tard".
        # On passe l'ID, pas l'objet complet !
        send_access_confirmation_email.delay(instance.id)
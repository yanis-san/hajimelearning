from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import AccessRequest
from .tasks import send_access_confirmation_email


def _dispatch(task, *args):
    """Lance une task Celery : synchrone en DEBUG ou test (eager), async en prod."""
    if settings.DEBUG or getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        task.apply(args=args)
    else:
        task.delay(*args)


@receiver(pre_save, sender=AccessRequest)
def track_previous_status(sender, instance, **kwargs):
    """
    Stocke le statut avant sauvegarde pour éviter les doublons d'email
    (ex: admin qui modifie une note sur un APPROVED déjà existant).
    """
    if instance.pk:
        try:
            instance._previous_status = AccessRequest.objects.get(pk=instance.pk).status
        except AccessRequest.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=AccessRequest)
def trigger_access_email(sender, instance, created, **kwargs):
    """
    Envoie l'email de confirmation UNIQUEMENT quand le statut
    passe à APPROVED pour la première fois (transition).
    Ne se redéclenche pas si l'admin ré-enregistre un accès déjà approuvé.
    """
    previous = getattr(instance, '_previous_status', None)
    if instance.status == AccessRequest.Status.APPROVED and previous != AccessRequest.Status.APPROVED:
        _dispatch(send_access_confirmation_email, instance.id)

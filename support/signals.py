from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Question, Response
from .tasks import send_question_notification_email, send_response_notification_email


def _dispatch(task, *args):
    """Lance une task Celery : synchrone en dev/test (eager), async en prod."""
    if settings.DEBUG or getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        task.apply(args=args)
    else:
        task.delay(*args)


@receiver(post_save, sender=Question)
def trigger_question_email(sender, instance, created, **kwargs):
    """Envoie une notification email quand une nouvelle question est posée."""
    if created:
        _dispatch(send_question_notification_email, instance.id)


@receiver(post_save, sender=Response)
def trigger_response_email(sender, instance, created, **kwargs):
    """Envoie une notification email quand une réponse est publiée."""
    if created:
        _dispatch(send_response_notification_email, instance.id)

"""Envoi asynchrone (ou synchrone en mode eager) des e-mails du catalogue `notifications.emails`."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def deliver_email(name, pk):
    """Construit et envoie l'e-mail `name` pour l'objet `pk` (voir `notifications.emails.EMAILS`)."""
    from .emails import deliver

    return deliver(name, pk)


def dispatch_email(name, pk):
    """
    Point d'entrée à utiliser dans le code métier : lance l'envoi sans jamais lever d'exception.

    Un incident de messagerie ne doit pas empêcher l'action de l'utilisateur (poser une question, payer…).
    """
    try:
        deliver_email.delay(name, pk)
    except Exception:
        logger.exception("Impossible de lancer l'envoi de l'e-mail « %s » (objet %s)", name, pk)

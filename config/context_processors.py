"""Variables de marque disponibles dans tous les gabarits (pages et e-mails, y compris ceux d'allauth)."""

from .emailing import base_context


def branding(request):
    return base_context()

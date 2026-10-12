"""Stockage des fichiers de cours protégés (hors MEDIA_ROOT)."""
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class ProtectedStorage(FileSystemStorage):
    """
    Fichiers inaccessibles par URL publique.
    Ils sont servis uniquement via la vue `block_file` (contrôle d'accès).
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('location', settings.PROTECTED_MEDIA_ROOT)
        super().__init__(**kwargs)

    def url(self, name):
        # Aucune URL directe : les widgets (admin, builder) afficheront un lien inerte.
        return '#'


def protected_storage():
    """Callable utilisé par les FileField (évalué au chargement, stable en migration)."""
    return ProtectedStorage()

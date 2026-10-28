import os
import uuid

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


# 1. FONCTION DE RENOMMAGE (Sécurité Maximale)
# Cette fonction transforme "mon_cv.pdf" en "a1b2-c3d4-e5f6.pdf"
def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    # On trie par type de contenu pour rester organisé
    return os.path.join('uploads/secure/', filename)

# 2. VALIDATEUR DE TAILLE
@deconstructible
class FileSizeValidator:
    def __init__(self, max_mb=10):
        self.max_mb = max_mb

    def __call__(self, value):
        limit = self.max_mb * 1024 * 1024
        if value.size > limit:
            raise ValidationError(f"Fichier trop volumineux. Max : {self.max_mb} MB.")

# LISTES BLANCHES (Ce qui est autorisé)
# Images (Preuves de paiement, miniatures)
IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']

# Documents (Ressources cours)
DOC_EXTENSIONS = ['pdf', 'doc', 'docx', 'zip', 'rar', 'xls', 'xlsx', 'ppt', 'pptx', 'txt']

# Audio (Dictées, sons de complétion)
AUDIO_EXTENSIONS = ['mp3', 'wav', 'm4a', 'ogg']

# Decks Anki (bloc « Deck Anki »)
ANKI_EXTENSIONS = ['apkg']

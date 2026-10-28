"""Réglages de la suite de tests : rapides, sans service externe."""

from .base import *

DEBUG = False
SECRET_KEY = 'test-only-secret-key'
ALLOWED_HOSTS = ['testserver', 'localhost']

# Hachage rapide : les tests créent beaucoup d'utilisateurs
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Celery exécute les tâches immédiatement, sans broker
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Emails conservés en mémoire (mailoutbox)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Fichiers déposés dans un dossier jetable
MEDIA_ROOT = BASE_DIR / 'media_test'
PROTECTED_MEDIA_ROOT = BASE_DIR / 'protected_media_test'


from .base import *

DEBUG = True

SECRET_KEY = 'django-insecure-dev-key-change-me'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Emails affichés dans la console en dev (décodés pour URLs copiables)
EMAIL_BACKEND = 'config.email_backends.DecodedConsoleEmailBackend'

INSTALLED_APPS += ['django_browser_reload']

MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

INTERNAL_IPS = [
    "127.0.0.1",
]

# Celery : exécution synchrone en dev (pas besoin de Redis/RabbitMQ)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True  # les exceptions remontent normalement
CELERY_BROKER_URL = 'memory://'
CELERY_BACKEND = 'cache+memory://'

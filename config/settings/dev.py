
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

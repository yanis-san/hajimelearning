from .base import *
import os

# ==============================================================================
# 🚀 GUIDE DE DÉPLOIEMENT CPANEL
# ==============================================================================
#
# A. VARIABLES D'ENVIRONNEMENT (Dans l'interface "Setup Python App") :
#    1. DJANGO_SETTINGS_MODULE = config.settings.prod  <-- CRITIQUE
#    2. DJANGO_SECRET_KEY      = (Générez une longue chaîne aléatoire)
#    3. DJANGO_ALLOWED_HOSTS   = mondomaine.com www.mondomaine.com
#    
#    [Base de données MySQL cPanel] :
#    4. DB_NAME     = (Nom de la base cPanel)
#    5. DB_USER     = (Utilisateur cPanel)
#    6. DB_PASSWORD = (Mot de passe utilisateur)
#    7. DB_HOST     = localhost
#
# B. CONFIGURATION DU FICHIER 'passenger_wsgi.py' :
#    Ce fichier est créé par cPanel à la racine. Remplacez son contenu par :
#
#    import os
#    import sys
#    from config.wsgi import application
#
#    sys.path.insert(0, os.path.dirname(__file__))
#    # C'est la ligne la plus importante :
#    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
#
# ==============================================================================

# --- SÉCURITÉ CRITIQUE ---
DEBUG = False

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("❌ ERREUR PROD : Variable 'DJANGO_SECRET_KEY' manquante !")

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(' ')

# --- BASE DE DONNÉES (MySQL via PyMySQL) ---
# En production, on impose MySQL.
import pymysql
pymysql.install_as_MySQLdb()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'connect_timeout': 10,
        },
    }
}

# --- EMAILS (Configuration cPanel SMTP) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'mail.hajimelearning.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465))
EMAIL_USE_SSL = True  # Port 465 utilise SSL
EMAIL_USE_TLS = False
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') # noreply@hajimelearning.com
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# L'expéditeur affiché
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Hajime Learning <noreply@hajimelearning.com>')
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', 'contact@hajimelearning.com')

# Préfixe pour les emails django-allauth
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Hajime Learning] "

# --- CELERY (Désactivé / Mode Synchrone sur cPanel) ---
# On exécute les tâches immédiatement dans le même thread 
# pour éviter d'avoir besoin d'un worker Celery et de Redis sur cPanel.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# --- OPTIMISATION STATIQUES (WhiteNoise Prod) ---
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# --- SECURITE HTTPS ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# HSTS — force HTTPS pendant 1 an
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
# Cookies
CSRF_COOKIE_HTTPONLY = False   # HTMX/Alpine ont besoin de lire le cookie CSRF
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
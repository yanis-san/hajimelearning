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
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# --- EMAILS (SMTP en production) ---
# Configurez ces variables d'env dans cPanel : EMAIL_HOST, EMAIL_HOST_USER, etc.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# --- CELERY (Redis via env var en prod) ---
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# --- OPTIMISATION STATIQUES (WhiteNoise Prod) ---
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# --- SÉCURITÉ HTTPS ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
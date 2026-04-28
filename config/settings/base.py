
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Application definition

INSTALLED_APPS = [
    # Whitenoise runserver must be first in INSTALLED_APPS for functionality in dev
    'whitenoise.runserver_nostatic',

    "unfold",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 3rd Party
    'django_cotton',
    'django_htmx',
    'tailwind',
    
    # Local
    'theme',

    #myapps

    'markdownx',
    'allauth',
    'allauth.account', 
    # 'allauth.socialaccount',
    'users',
    'courses',
    'access',
    'support',
    'django.contrib.sitemaps',
    'notifications',
    'instructors',
    'contact',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise 2nd
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # HTMX Middleware
    'django_htmx.middleware.HtmxMiddleware',

    #allauth
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',           # Pour t'aider au développement
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.user_notifications', # Pour les alertes globales du site
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- CONFIGURATION ALLAUTH
AUTH_USER_MODEL = 'users.User'
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# 1. Formulaires Custom
ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
    'login': 'users.forms.CustomLoginForm', 
    'reset_password': 'users.forms.CustomResetPasswordForm',       
    'reset_password_from_key': 'users.forms.CustomResetPasswordKeyForm'
}

# 2. Méthodes de Connexion (Nouvelle Syntaxe)
ACCOUNT_LOGIN_METHODS = {'email'} # Remplace ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_USER_MODEL_USERNAME_FIELD = None 

# 3. Champs requis à l'inscription (Nouvelle Syntaxe)
# Cette liste remplace EMAIL_REQUIRED, USERNAME_REQUIRED, PASSWORD_REQUIRED
# Le fait de ne mettre 'password' qu'une fois désactive la confirmation "Enter Twice".
ACCOUNT_SIGNUP_FIELDS = [
    'email*', 
    'password1', 
]   

# 4. Vérification Email
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3

# 5. Email
# EMAIL_BACKEND est défini dans dev.py ou prod.py
DEFAULT_FROM_EMAIL = 'Hajime Learning <noreply@hajimelearning.com>'

# 6. Redirections
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Africa/Algiers'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Fichiers Médias (Uploads utilisateurs : Avatars, Cours)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ALLOW_STUDENT_REPLIES = False

# --- CONFIGURATION CELERY (Asynchrone) ---
# Surcharge dans dev.py / prod.py via variable d'env CELERY_BROKER_URL
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Si on lance "pytest" ou "test", on configure Celery pour ne pas utiliser Redis
if 'test' in sys.argv or 'pytest' in sys.argv[0]:
    # Exécuter les tâches immédiatement (synchrone) sans broker
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    
    # Stocker les emails en mémoire au lieu de tenter de les envoyer
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    
    # Utiliser un système de cache en mémoire simple pour les tests
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Tailwind
TAILWIND_APP_NAME = 'theme'
TAILWIND_CSS_PATH = 'css/dist/styles.css'
# --watch=always uses built-in polling instead of watchman
TAILWIND_STANDALONE_START_COMMAND_ARGS = (
    '-i static_src/src/styles.css -o static/css/dist/styles.css --watch=always'
)

# Markdownx — extensions pour le rendu (tables, code fencé, etc.)
MARKDOWNX_MARKDOWN_EXTENSIONS = [
    'markdown.extensions.tables',
    'markdown.extensions.fenced_code',
    'markdown.extensions.nl2br',
]

# Email de destination pour le formulaire de contact
CONTACT_EMAIL = 'contact@hajimelearning.com'
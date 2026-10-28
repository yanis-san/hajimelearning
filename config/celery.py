import os

from celery import Celery

# 1. On dit à Celery où sont les settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# 2. On crée l'application Celery
app = Celery('config')

# 3. On charge la config depuis settings.py (tout ce qui commence par CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. On dit à Celery de chercher automatiquement les fichiers "tasks.py" dans tes apps
app.autodiscover_tasks()

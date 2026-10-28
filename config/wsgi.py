import os

from django.core.wsgi import get_wsgi_application

# Point to config.settings.prod for production safety/defaults
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

application = get_wsgi_application()

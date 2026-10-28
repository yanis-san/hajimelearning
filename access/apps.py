from django.apps import AppConfig


class AccessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'access'

    def ready(self):
        # on charge les signaux
        import access.signals  # noqa: F401

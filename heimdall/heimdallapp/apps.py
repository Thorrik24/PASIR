from django.apps import AppConfig


class HeimdallappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'heimdallapp'

    def ready(self):
            import heimdallapp.signals
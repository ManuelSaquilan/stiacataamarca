from django.apps import AppConfig


class OrdenesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ordenes'

    def ready(self):
        import ordenes.signals  # Importa las señales al iniciar la aplicación
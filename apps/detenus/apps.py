from django.apps import AppConfig


class DetenusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.detenus'
    verbose_name = 'Détenus'
    
    def ready(self):
        import apps.detenus.models
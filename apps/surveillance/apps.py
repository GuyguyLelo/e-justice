from django.apps import AppConfig


class SurveillanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.surveillance'
    verbose_name = 'Surveillance et Reconnaissance Faciale'
    
    def ready(self):
        try:
            import apps.surveillance.signals
        except ImportError:
            # Les dépendances de reconnaissance faciale ne sont pas encore installées
            pass

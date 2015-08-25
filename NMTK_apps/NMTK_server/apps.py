from django.apps import AppConfig


class NMTK_serverConfig(AppConfig):
    name = 'NMTK_server'
    verbose_name = 'Non-Motorized Toolkit Server'

    def ready(self):
        from NMTK_server import signals

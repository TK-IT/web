from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class EvalConfig(AppConfig):
    name = 'eval'
    verbose_name = "Evaluerings wiki"

    def ready(self):
        autodiscover_modules('evalmacros')

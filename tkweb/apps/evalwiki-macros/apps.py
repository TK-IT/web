from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class EvalwikiConfig(AppConfig):
    name = 'tkweb.apps.evalwiki-macros'
    verbose_name = "Evaluerings wiki"

    def ready(self):
        autodiscover_modules('evalwiki-macros')

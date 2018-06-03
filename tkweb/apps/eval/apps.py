from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class EvalConfig(AppConfig):
    name = "tkweb.apps.eval"
    verbose_name = "Evaluerings wiki"

    def ready(self):
        autodiscover_modules("evalmacros")
        autodiscover_modules("mdcheatsheet")

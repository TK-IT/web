from django import template
from wiki.plugins.macros import settings
from tkweb.apps.evalmacros.evalmacros import EvalMacroPreprocessor

register = template.Library()

@register.simple_tag
def allowed_evalmacros():
    for method in settings.METHODS:
        try:
            yield getattr(EvalMacroPreprocessor, method).meta
        except AttributeError:
            continue

from django import template
from tkweb.apps.evalmacros.evalmacros import EvalMacroPreprocessor, METHODS

register = template.Library()

@register.simple_tag
def allowed_evalmacros():
    for method in METHODS:
        try:
            yield getattr(EvalMacroPreprocessor, method).meta
        except AttributeError:
            continue

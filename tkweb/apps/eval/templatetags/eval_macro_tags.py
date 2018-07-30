from django import template
from tkweb.apps.eval.evalmacros import EvalMacroPattern, METHODS

register = template.Library()

@register.simple_tag
def allowed_evalmacros():
    for method in METHODS:
        try:
            yield getattr(EvalMacroPattern, method).meta
        except AttributeError:
            continue

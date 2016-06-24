# encoding: utf8
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
from tkweb.apps.tkbrand import util

register = template.Library()

html_tk = (
    '<span style="vertical-align: -0.038em;">T</span>'
    '<span style="font-weight: bold; margin-left: -0.05em;">Å</span>'
    '<span style="margin-left: -0.05em;">G</span>'
    '<span style="display: inline-block; transform: rotate(8deg);">E</span>'
    '<span style="vertical-align: -0.057em; margin-left: 0.05em;">K</span>'
    '<span style="vertical-align: 0.020em; font-weight: bold;">A</span>'
    '<span style="vertical-align: -0.057em;">M</span>'
    '<span style="display: inline-block; transform: rotate(-8deg); font-weight: bold; margin-left: 0.060em;">M</span>'
    '<span style="margin-left: 0.05em;">E</span>'
    '<span style="margin-left: 0.02em;">R</span>')

html_tket = html_tk + '<span style="vertical-align: 0.057em">ET</span>'

html_tkets = html_tket + 's'

@register.simple_tag
def tk(monospace=None):
    return mark_safe('<span class="tk-brand">' + html_tk + '</span>')


@register.simple_tag
def tket():
    return mark_safe('<span class="tk-brand">' + html_tket + '</span>')

@register.simple_tag
def tkets():
    return mark_safe('<span class="tk-brand">' + html_tkets + '</span>')

@register.filter
def gfyearPP(gfyear):
    return util.gfyearPP(gfyear)

@register.filter
def gfyearPPslash(gfyear):
    return util.gfyearPPslash(gfyear)

# For evaluation of tags in flatpages
@register.tag(name="evaluate")
def do_evaluate(parser, token):
    """
    tag usage {% evaluate flatpage.content %}
    """
    try:
        tag_name, variable = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    return EvaluateNode(variable)

class EvaluateNode(template.Node):
    def __init__(self, variable):
        self.variable = template.Variable(variable)

    def render(self, context):
        try:
            content = self.variable.resolve(context)
            content = '{% load tkbrand %}\n' + content # Always load tkbrand
            t = template.Template(content)
            return t.render(context)
        except (template.VariableDoesNotExist, template.TemplateSyntaxError):
            return 'Error rendering', self.variable

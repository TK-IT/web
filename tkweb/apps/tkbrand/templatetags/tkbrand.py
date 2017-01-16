# encoding: utf8
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
from constance import config
from tkweb.apps.tkbrand import util
import tktitler as tk

register = template.Library()

HTML_T = (
    '<span style="vertical-align: -0.038em;">T</span>'
)

HTML_ARING = (
    '<span style="font-weight: bold; margin-left: -0.05em;">Å</span>'
)

HTML_AA = (
    '<span style="font-weight: bold; margin-left: -0.05em;">A</span>'
    '<span style="vertical-align: -0.01em; margin-left: -0.05em; ">A</span>'
)

HTML_GEKAMMER = (
    '<span style="margin-left: -0.05em;">G</span>'
    '<span style="display: inline-block; transform: rotate(8deg);">E</span>'
    '<span style="vertical-align: -0.057em; margin-left: 0.05em;">K</span>'
    '<span style="vertical-align: 0.020em; font-weight: bold;">A</span>'
    '<span style="vertical-align: -0.057em;">M</span>'
    '<span style="display: inline-block; transform: rotate(-8deg); font-weight: bold; margin-left: 0.060em;">M</span>'
    '<span style="margin-left: 0.05em;">E</span>'
    '<span style="margin-left: 0.02em;">R</span>'
)

HTML_TK = HTML_T + HTML_ARING + HTML_GEKAMMER
HTML_TKAA = HTML_T + HTML_AA + HTML_GEKAMMER

HTML_ET = '<span style="vertical-align: 0.057em">ET</span>'

HTML_TKET = HTML_TK + HTML_ET
HTML_TKETAA = HTML_TKAA + HTML_ET

HTML_TKETs = HTML_TKET + 's'
HTML_TKETsAA = HTML_TKETAA + 's'

HTML_TKETS = HTML_TKET + 'S'
HTML_TKETSAA = HTML_TKETAA + 'S'


@register.simple_tag
def TK():
    return mark_safe('<span class="tk-brand">' + HTML_TK + '</span>')


@register.simple_tag
def TKAA():
    return mark_safe('<span class="tk-brand">' + HTML_TKAA + '</span>')


@register.simple_tag
def TKET():
    return mark_safe('<span class="tk-brand">' + HTML_TKET + '</span>')


@register.simple_tag
def TKETAA():
    return mark_safe('<span class="tk-brand">' + HTML_TKETAA + '</span>')


@register.simple_tag
def TKETs():
    return mark_safe('<span class="tk-brand">' + HTML_TKETs + '</span>')


@register.simple_tag
def TKETsAA():
    return mark_safe('<span class="tk-brand">' + HTML_TKETsAA + '</span>')


@register.simple_tag
def TKETS():
    return mark_safe('<span class="tk-brand">' + HTML_TKETS + '</span>')


@register.simple_tag
def TKETSAA():
    return mark_safe('<span class="tk-brand">' + HTML_TKETSAA + '</span>')


@register.filter
def gfyearPP(gfyear):
    return util.gfyearPP(gfyear)


@register.filter
def gfyearPPslash(gfyear):
    return util.gfyearPPslash(gfyear)


@register.filter
def gfyearPPslash_gallery(gfyear):
    """
    For the gallery app where there is a special multi-year album
    """
    if gfyear == 1960:
        return "60/64"
    return util.gfyearPPslash(gfyear)


@register.filter
def tk_prefix(title, arg=tk.PREFIXTYPE_UNICODE):
    return tk.prefix(title, gfyear=config.GFYEAR,  type=arg)


@register.filter
def tk_kprefix(title, arg=tk.PREFIXTYPE_UNICODE):
    return tk.kprefix(title, gfyear=config.GFYEAR, type=arg)


@register.filter
def tk_postfix(title, arg=tk.POSTFIXTYPE_SINGLE):
    return tk.postfix(title, gfyear=config.GFYEAR, type=arg)


@register.filter
def tk_prepostfix(title, arg=tk.POSTFIXTYPE_SINGLE):
    """
    :param str arg: postfixtype til :func:`tktitler.prepostfix`.
    Det er ikke muligt at ændre prefixtype.
    """
    return tk.prepostfix(title, gfyear=config.GFYEAR,
                         prefixtype=tk.PREFIXTYPE_UNICODE, postfixtype=arg)


@register.filter
def tk_email(title, arg=tk.EMAILTYPE_POSTFIX):
    return tk.email(title, gfyear=config.GFYEAR, type=arg)


# For evaluation of tags in flatpages
@register.tag(name="evaluate")
def do_evaluate(parser, token):
    """
    tag usage {% evaluate flatpage.content %}
    """
    try:
        tag_name, variable = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument"
                                           % token.contents.split()[0])
    return EvaluateNode(variable)


class EvaluateNode(template.Node):
    def __init__(self, variable):
        self.variable = template.Variable(variable)

    def render(self, context):
        try:
            content = self.variable.resolve(context)
            content = '{% load tkbrand %}\n' + content  # Always load tkbrand
            t = template.Template(content)
            return t.render(context)
        except (template.VariableDoesNotExist, template.TemplateSyntaxError):
            return 'Error rendering', self.variable

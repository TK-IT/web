# encoding: utf8
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
from tkweb.apps.tkbrand import util

register = template.Library()

html_tk = ('<span style="vertical-align: -0.038em">T</span>'
           '<span style="font-weight: bold">&Aring;</span>'
           'G'
           '<span style="display: inline-block; transform: rotate(8deg);">E</span>'
           '<span style="vertical-align: -0.057em;">K</span>'
           '<span style="vertical-align: 0.020em; font-weight: bold;">A</span>'
           '<span style="vertical-align: -0.057em; margin-left: 0.075em;">M</span>'
           '<span style="display: inline-block; transform: rotate(-8deg); font-weight: bold; margin-left: 0.110em;">M</span>'
           '<span style="margin-left: 0.075em;">ER</span>')

html_tket = html_tk + '<span style="vertical-align: 0.057em">ET</span>'


@register.simple_tag
def tk(monospace=None):
    return mark_safe('<span class="tk-brand">' + html_tk + '</span>')


@register.simple_tag
def tket():
    return mark_safe('<span class="tk-brand">' + html_tket + '</span>')

@register.filter
def gfyearPP(gfyear):
    return util.gfyearPP(gfyear)

@register.filter
def gfyearPPslash(gfyear):
    return util.gfyearPPslash(gfyear)

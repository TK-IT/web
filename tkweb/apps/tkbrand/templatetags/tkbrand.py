import functools
import re
import django.db.utils
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

HTML_ET = (
    '<span style="vertical-align: 0.057em">E</span>'
    + '<span style="vertical-align: 0.057em">T</span>'
)

HTML_TKET = HTML_TK + HTML_ET
HTML_TKETAA = HTML_TKAA + HTML_ET

HTML_TKETs = HTML_TKET + 's'
HTML_TKETsAA = HTML_TKETAA + 's'

HTML_TKETS = HTML_TKET + 'S'
HTML_TKETSAA = HTML_TKETAA + 'S'


@register.simple_tag
def TK():
    return wrap_tk_html(HTML_TK)


@register.simple_tag
def TKAA():
    return wrap_tk_html(HTML_TKAA)


@register.simple_tag
def TKET():
    return wrap_tk_html(HTML_TKET)


@register.simple_tag
def TKETAA():
    return wrap_tk_html(HTML_TKETAA)


@register.simple_tag
def TKETs():
    return wrap_tk_html(HTML_TKETs)


@register.simple_tag
def TKETsAA():
    return wrap_tk_html(HTML_TKETsAA)


@register.simple_tag
def TKETS():
    return wrap_tk_html(HTML_TKETS)


@register.simple_tag
def TKETSAA():
    return wrap_tk_html(HTML_TKETSAA)


PRIDE_COLORS = (
    '''#e40303 #ff8c00 #ffed00 #008026 #004dff #b100cc #e40303 #ff8c00
    #ffed00 #008026 #004dff #b100cc'''.split()
)
UKRAINE_COLORS = '#449FFF #FFD500'.split() * 6


def add_colors(colors, html):
    insert_after = 'style="'
    count = html.count(insert_after)
    if count < len(colors):
        colors = [
            colors[int(i / count * len(colors))] for i in range(count)
        ]
    else:
        s = 1
        extra = count - len(colors) + 1
        # Repeat element at index s enough times.
        colors = colors[:s] + extra * colors[s:s+1] + colors[s+1:]
    assert len(colors) == count

    def repl(mo):
        # Insert next color from 'colors' after 'style="'
        return "%scolor: %s; " % (mo.group(0), colors.pop(0))

    return re.sub(re.escape(insert_after), repl, html)


def catch_db_errors(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except django.db.utils.OperationalError:
            return "?"

    return wrapper


@catch_db_errors
def wrap_tk_html(html):
    if config.PRIDE:
        html = add_colors(PRIDE_COLORS, html)
    elif config.UKRAINE:
        html = add_colors(UKRAINE_COLORS, html)
    return mark_safe('<span class="tk-brand">' + html + '</span>')


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
@catch_db_errors
def tk_prefix(title, arg='unicode'):
    return tk.prefix(title, gfyear=config.GFYEAR,  type=arg)


@register.filter
@catch_db_errors
def tk_kprefix(title, arg='unicode'):
    return tk.kprefix(title, gfyear=config.GFYEAR, type=arg)


@register.filter
def tk_postfix(title, arg='single'):
    return tk.postfix(title, type=arg)


@register.filter
@catch_db_errors
def tk_prepostfix(title, arg='longslash'):
    """
    :param str arg: postfixtype til :func:`tktitler.prepostfix`.
    Det er ikke muligt at ændre prefixtype.
    """
    return tk.prepostfix(title, gfyear=config.GFYEAR,
                         prefixtype='unicode', postfixtype=arg)


@register.filter
@catch_db_errors
def tk_email(title, arg='postfix'):
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

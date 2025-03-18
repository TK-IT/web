from django import template
from django.utils.html import format_html
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse


register = template.Library()


@register.simple_tag
def regnskab_site_name():
    return 'INKAs regnskabsmaskine'


@register.simple_tag
def regnskab_icon():
    return format_html(
        '<img src="{}" class="regnskab-icon" />',
        staticfiles_storage.url('regnskab/ikonINKA.svg'))


@register.simple_tag
def nav_session(regnskab_session):
    return format_html(
        '<a href="{}"><li>Opgørelse {}</li></a>',
        reverse('regnskab:session_update',
                kwargs=dict(pk=regnskab_session.pk)),
        regnskab_session.pk)

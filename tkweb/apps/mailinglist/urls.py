# encoding: utf8
from __future__ import unicode_literals
from django.conf.urls import url
from tkweb.apps.mailinglist.views import EmailFormView


urlpatterns = [
    url('^$', EmailFormView.as_view(), name='email_form'),
]

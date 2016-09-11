# encoding: utf8
from __future__ import unicode_literals
from django.conf.urls import url
from tkweb.apps.mailinglist.views import EmailSend


urlpatterns = [
    url('^$', EmailSend.as_view(), name='emailsend'),
]

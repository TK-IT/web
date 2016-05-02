# encoding: utf8
from __future__ import unicode_literals
from django.conf.urls import url
from django.contrib.flatpages import views


urlpatterns = [
    url(r'^40/$',
        views.flatpage, {'url': '/J40/'},
        name='J40'),
    url(r'^40hist/$',
        views.flatpage, {'url': '/J40hist/'},
        name='J40'),
    url(r'^50/$',
        views.flatpage, {'url': '/J50/'},
        name='J50'),
    url(r'^60/$',
        views.flatpage, {'url': '/J60/'},
        name='J60'),
]

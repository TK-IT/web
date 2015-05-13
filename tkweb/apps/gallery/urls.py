from django.conf.urls import patterns, url

from tkweb.apps.gallery import views

urlpatterns = patterns('',
                       url(r'^$',
                           'tkweb.apps.gallery.views.gallery',
                           name='gallery'))

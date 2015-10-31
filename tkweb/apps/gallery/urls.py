from django.conf.urls import patterns, url

from tkweb.apps.gallery import views

urlpatterns = patterns('',
                       url(r'^$',
                           'tkweb.apps.gallery.views.gallery',
                           name='gallery'),
                       url(r'^upload/',
                           'tkweb.apps.gallery.views.upload',
                           name='jfu_upload'),
                       url(r'^delete/(?P<pk>\d+)$',
                           'tkweb.apps.gallery.views.upload_delete',
                           name='jfu_delete'))


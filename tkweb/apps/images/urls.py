from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^upload/',
                           'tkweb.apps.images.views.upload',
                           name='jfu_upload'),
                       url(r'^delete/(?P<pk>\d+)$',
                           'tkweb.apps.images.views.upload_delete',
                           name='jfu_delete'))

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'tkweb.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),
                       url(r'^gallery/',
                           include('tkweb.apps.gallery.urls'),
                           name = 'gallery'),
                       url(r'^images/',
                           include('tkweb.apps.images.urls'),
                           name='images'),

                       url(r'^admin/',
                           include(admin.site.urls)),

                           # Temporary media (user uploaded static files) serving from dev server
                       url(r'^media/(?P<path>.*)$',
                           'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT}),
)

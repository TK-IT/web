from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.flatpages import views
from django.views.generic.base import RedirectView


urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'tkweb.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),
                       url('^$',
                           RedirectView.as_view(url='/kalender/'),
                           name='index'),

                       url(r'^om/$',
                           views.flatpage, {'url': '/om/'},
                           name='om'),
                       url(r'^bestfu/$',
                           views.flatpage, {'url': '/bestfu/'},
                           name='bestfu'),
                       url(r'^arrangementer/$',
                           views.flatpage, {'url': '/arrangementer/'},
                           name='arrangementer'),
                       url(r'^kontakt/$',
                           views.flatpage, {'url': '/kontakt/'},
                           name='kontakt'),
                       url(r'^ket/$',
                           views.flatpage, {'url': '/ket/'},
                           name='ket'),

                       url(r'^kalender/',
                           'tkweb.apps.calendar.views.kalender',
                           name='kalender'),

                       url(r'^galleri/',
                           include('tkweb.apps.gallery.urls'),
                           name='gallery'),

                       url(r'^admin/',
                           include(admin.site.urls)),

                       # Temporary media (user uploaded static files)
                       # serving from dev server
                       url(r'^media/(?P<path>.*)$',
                           'django.views.static.serve',
                           {'document_root': settings.MEDIA_ROOT}),
                       )

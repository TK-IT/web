from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.flatpages import views
from django.views.generic.base import RedirectView

import tkweb.apps.barplan.urls
import tkweb.apps.calendar.views
import tkweb.apps.drinks.urls
import tkweb.apps.eval.urls
import tkweb.apps.gallery.urls
import tkweb.apps.idm.urls
import tkweb.apps.jubi.urls
import tkweb.apps.mailinglist.urls
import tkweb.apps.redirect.urls
import tkweb.apps.regnskab
import tkweb.apps.uniprint.urls
import django.views.static
import django.views.defaults
import tkweb.views


urlpatterns = [
    # Examples:
    # url(r'^$', 'tkweb.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url('^$',
        RedirectView.as_view(url='/kalender/', permanent=False),
        name='index'),

    url(r'^om/$',
        views.flatpage, {'url': '/om/'},
        name='om'),
    url(r'^bestfu/$',
        tkweb.views.bestfu,
        name='bestfu'),
    url(r'^arrangementer/$',
        views.flatpage, {'url': '/arrangementer/'},
        name='arrangementer'),
    url(r'^jubi/$',
        views.flatpage, {'url': '/jubi/'},
        name='jubi'),
    url(r'^kontakt/$',
        views.flatpage, {'url': '/kontakt/'},
        name='kontakt'),
    url(r'^ket/$',
        views.flatpage, {'url': '/ket/'},
        name='ket'),

    url(r'^kalender/$',
        tkweb.apps.calendar.views.kalender,
        name='kalender'),

    url(r'^galleri/',
        include(tkweb.apps.gallery.urls),
        name='gallery'),

    url(r'^email/',
        include(tkweb.apps.mailinglist.urls),
        name='mailinglist'),

    # Note the missing trailing slash. This catches everything that start with
    # 'J' or 'j'. Since 'J' is first in [Jj], reverse() will return URLs
    # starting with 'J'.
    url(r'^[Jj]',
        include(tkweb.apps.jubi.urls)),

    url(r'^eval/',
        include(tkweb.apps.eval.urls),
        name='eval'),

    url(r'^idm/',
        include(tkweb.apps.idm.urls),
        name='idm'),

    url(r'^regnskab/',
        tkweb.apps.regnskab.site.urls),

    url(r'^print/',
        include((tkweb.apps.uniprint.urls, 'uniprint', 'uniprint'))),

    url(r'^drinks/',
        include((tkweb.apps.drinks.urls, 'drinks', 'drinks'))),

    url(r'^barplan/',
        include((tkweb.apps.barplan.urls, 'barplan', 'barplan'))),

    url(r'^admin/', admin.site.urls),

    # Temporary media (user uploaded static files)
    # serving from dev server
    url(r'^media/(?P<path>.*)$',
        django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}),

    # 404 page for debugging
    url(r'^404/$',
        django.views.defaults.page_not_found,
        kwargs = {'exception': Exception("Intentional 404")}),

    # Send the rest to the redirect app
    url('',
        include(tkweb.apps.redirect.urls), ),

]

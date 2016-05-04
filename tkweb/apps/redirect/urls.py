# encoding: utf8
from __future__ import unicode_literals
from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from tkweb.apps.redirect.views import GalleryIndexRedirectView, GalleryShowFolderRedirectView, GalleryShowPictureRedirectView
from tkweb.settings.base import STATIC_URL

urlpatterns = [
    url(r'^OmTK.php$',
        RedirectView.as_view(url='/om/', permanent=True), ),

    url(r'^BESTFU.php',
        RedirectView.as_view(url='/bestfu/', permanent=True), ),

    url(r'^Kalender.php',
        RedirectView.as_view(url='/kalender/', permanent=True), ),

    url(r'^Arrangementer.php',
        RedirectView.as_view(url='/arrangementer/', permanent=True), ),

    url(r'^Kontakt.php',
        RedirectView.as_view(url='/kontakt/', permanent=True), ),

    url(r'^Login.php',
        RedirectView.as_view(url='/admin/', permanent=True), ),

    url(r'^Billeder/index.php',
        GalleryIndexRedirectView.as_view(), ),

    url(r'^Billeder/ShowFolder.php',
        GalleryShowFolderRedirectView.as_view(), ),

    url(r'^Billeder/ShowPicture.php',
        GalleryShowPictureRedirectView.as_view(), ),

    url(r'^tk40/tk40new.php',
        RedirectView.as_view(url='/J40/', permanent=True), ),

    url(r'^tk40/jubi40_histnew.php',
        RedirectView.as_view(url='/J40hist/', permanent=True), ),

    url(r'^J50Resume.php',
        RedirectView.as_view(url='/J50/', permanent=True), ),

    url(r'^J50Resume/J50-Jubiskrift.pdf',
        RedirectView.as_view(url=STATIC_URL+'jubi/J50/J50-Jubiskrift.pdf',
                             permanent=True), ),

    url(r'(?i)^J60/index.html',
        RedirectView.as_view(url='/J60/', permanent=True), ),


]

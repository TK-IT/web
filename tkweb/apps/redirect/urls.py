from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from tkweb.apps.redirect.views import GalleryIndexRedirectView, GalleryShowFolderRedirectView, GalleryShowPictureRedirectView

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

]

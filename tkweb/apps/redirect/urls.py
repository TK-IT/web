# encoding: utf8
from __future__ import unicode_literals
from django.conf.urls import url
from django.views.generic.base import RedirectView

from tkweb.apps.redirect.views import (
    GalleryIndexRedirectView,
    GalleryShowFolderRedirectView,
    GalleryShowPictureRedirectView,
    http410,
)
from tkweb.settings.base import STATIC_URL

urlpatterns = [
    url(r"^OmTK.php$", RedirectView.as_view(url="/om/", permanent=True)),
    url(r"^BESTFU.php", RedirectView.as_view(url="/bestfu/", permanent=True)),
    url(r"^Kalender.php", RedirectView.as_view(url="/kalender/", permanent=True)),
    url(
        r"^Arrangementer.php",
        RedirectView.as_view(url="/arrangementer/", permanent=True),
    ),
    url(r"^Kontakt.php", RedirectView.as_view(url="/kontakt/", permanent=True)),
    url(r"^Login.php", RedirectView.as_view(url="/admin/", permanent=True)),
    url(r"^Billeder/index.php", GalleryIndexRedirectView.as_view()),
    url(r"^Billeder/ShowFolder.php", GalleryShowFolderRedirectView.as_view()),
    url(r"^Billeder/ShowPicture.php", GalleryShowPictureRedirectView.as_view()),
    url(
        r"^vedtaegter.pdf",
        RedirectView.as_view(url=STATIC_URL + "vedtaegter.pdf", permanent=True),
    ),
    # J40
    url(r"^tk40/tk40new.php", RedirectView.as_view(url="/J40/resume/", permanent=True)),
    url(
        r"^tk40/jubi40_histnew.php",
        RedirectView.as_view(url="/J40/historie/", permanent=True),
    ),
    # J50
    url(r"^J50Resume.php", RedirectView.as_view(url="/J50/resume/", permanent=True)),
    url(r"^j50/Adresser.php", http410),
    url(
        r"^j50/Arrangementer.php",
        RedirectView.as_view(url="/J50/arrangementer/", permanent=True),
    ),
    url(
        r"^J50Resume/J50-Jubiskrift.pdf",
        RedirectView.as_view(
            url=STATIC_URL + "jubi/J50/J50-Jubiskrift.pdf", permanent=True
        ),
    ),
    url(
        r"^J50Resume/J50-Sangbog.pdf",
        RedirectView.as_view(
            url=STATIC_URL + "jubi/J50/J50-Sangbog.pdf", permanent=True
        ),
    ),
    url(
        r"^J50Resume/J50-Revy.pdf",
        RedirectView.as_view(url=STATIC_URL + "jubi/J50/J50-Revy.pdf", permanent=True),
    ),
    # J60
    url(r"(?i)^J60/index.html", RedirectView.as_view(url="/J60/", permanent=True)),
    url(
        r"(?i)^J60/j60brev.pdf",
        RedirectView.as_view(url=STATIC_URL + "jubi/J60/j60brev.pdf", permanent=True),
    ),
    url(
        r"(?i)^J60/katalog-j60.pdf",
        RedirectView.as_view(
            url=STATIC_URL + "jubi/J60/katalog-j60.pdf", permanent=False
        ),
    ),
    url(
        r"(?i)^J60revy$",
        RedirectView.as_view(url="https://auws.au.dk/TKrevy", permanent=False),
    ),
    url(
        r"(?i)^J60foredrag$",
        RedirectView.as_view(url="https://auws.au.dk/TKforedrag", permanent=False),
    ),
    url(
        r"(?i)^J60foredrag-prerelease$",
        RedirectView.as_view(url="https://auws.au.dk/TKforedrag", permanent=False),
    ),
]

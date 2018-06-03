# encoding: utf8
from __future__ import unicode_literals
from django.conf.urls import url
import tkweb.apps.gallery.views

urlpatterns = [
    # Gallery overview
    url(r"^$", tkweb.apps.gallery.views.gallery, name="gallery_index"),
    url(r"^(?P<gfyear>\d+)$", tkweb.apps.gallery.views.gallery, name="gfyear"),
    # Album overview
    url(
        r"^(?P<gfyear>\d+)/(?P<album_slug>[^/]+)$",
        tkweb.apps.gallery.views.album,
        name="album",
    ),
    # Single images
    url(
        r"^(?P<gfyear>\d+)/(?P<album_slug>[^/]+)/(?P<image_slug>[^/]+)$",
        tkweb.apps.gallery.views.image,
        name="image",
    ),
    # Bulk-update BaseMedia.visibility
    url(
        r"^set_visibility/$",
        tkweb.apps.gallery.views.set_visibility,
        name="set_image_visibility",
    ),
    # JFU upload
    url(r"^upload/", tkweb.apps.gallery.views.upload, name="jfu_upload"),
    # RSS feed
    url(r"^album\.rss$", tkweb.apps.gallery.views.AlbumFeed(), name="album_rss"),
]

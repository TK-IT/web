# encoding: utf8
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.views.generic.base import RedirectView

from tkweb.apps.gallery.models import Album

class GalleryIndexRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):

        mainfoldernr = self.request.GET.get('mainfoldernr','')
        if not mainfoldernr:
            return reverse('gallery_index')

        albums = Album.objects.filter(oldFolder__startswith = mainfoldernr)
        if not albums:
            return reverse('gallery_index')

        gfyear = albums[0].gfyear
        return reverse('gfyear', kwargs={'gfyear': gfyear})

# encoding: utf8
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic.base import RedirectView
from django.shortcuts import render

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

class GalleryShowFolderRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):

        folder = self.request.GET.get('folder','')
        if not folder:
            return None # The old page prints a load of garbage. This will
                        # return a 410 GONE instead.

        albums = Album.objects.filter(oldFolder__startswith = folder)
        if not albums:
            raise Http404("Albummet kan ikke findes")

        gfyear = albums[0].gfyear
        album_slug = albums[0].slug
        return reverse('album', kwargs={'gfyear': gfyear,
                                        'album_slug': album_slug})

class GalleryShowPictureRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):

        folder = self.request.GET.get('folder','')
        pic_count = int(self.request.GET.get('pic_count',''))
        if not folder:
            return None # The old page prints a load of garbage. This will
                        # return a 410 GONE instead.

        albums = Album.objects.filter(oldFolder__startswith = folder)
        if not albums:
            raise Http404("Albummet kan ikke findes")

        gfyear = albums[0].gfyear
        album_slug = albums[0].slug
        images = list(albums[0].basemedia.all())

        if pic_count >= len(images):
            raise Http404("Billedet kan ikke findes")

        image_slug = images[pic_count].slug

        return reverse('image', kwargs={'gfyear': gfyear,
                                        'album_slug': album_slug,
                                        'image_slug': image_slug})


def http410(request):
    context = {"status": "410 Gone"}
    return render(request, "404.html", context, status=410)

# encoding: utf8
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic.base import RedirectView
from django.shortcuts import render
from django.utils.encoding import uri_to_iri
import logging

from tkweb.apps.gallery.models import Album

logger = logging.getLogger(__name__)


class GalleryIndexRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):

        mainfoldernr = self.request.GET.get('mainfoldernr', '')
        albums = Album.objects.filter(oldFolder__startswith=mainfoldernr)
        if not mainfoldernr or not albums:
            logger.info('GalleryIndexRedirectView: The \'mainfoldernr\' '
                        'request parameter cold not be parsed or did not fit '
                        'an Album. Returning current year instead. '
                        '\'mainfoldernr\' was %s' % (mainfoldernr))
            return reverse('gallery_index')

        gfyear = albums[0].gfyear
        return reverse('gfyear', kwargs={'gfyear': gfyear})


class GalleryShowFolderRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):

        folder = self.request.GET.get('folder', '')
        # Some of the old string are double encoded.
        folder = uri_to_iri(folder)

        if not folder:
            logger.warning('GalleryShowFolderRedirectView: The \'folder\' '
                           'request parameter cold not be parsed. Returning '
                           '410. \'folder\' doubledecoded was %s' % (folder))
            # The old page prints a load of garbage. This will
            # return a 410 GONE instead.
            return None

        albums = Album.objects.filter(oldFolder__startswith = folder)
        if not albums:
            logger.warning('GalleryShowFolderRedirectView: The album could '
                           'not be found when comparing the \'folder\' '
                           'request parameter with \'oldFolder\' on albums. '
                           'Returning 404. \'folder\' doubledecoded was %s'
                           % (folder))
            raise Http404("Albummet kan ikke findes")

        gfyear = albums[0].gfyear
        album_slug = albums[0].slug
        return reverse('album', kwargs={'gfyear': gfyear,
                                        'album_slug': album_slug})


class GalleryShowPictureRedirectView(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):

        folder = self.request.GET.get('folder', '')
        # Some of the old string are double encoded.
        folder = uri_to_iri(folder)

        pic_countStr = self.request.GET.get('pic_count', '')
        try:
            pic_count = int(pic_countStr)
        except ValueError:
            logger.warning('GalleryShowPictureRedirectView: The \'pic_count\' '
                           'request parameter cold not be parsed. Returning '
                           '404. \'pic_count\' was %s' % (pic_countStr))
            raise Http404("Billedet kan ikke findes")

        if not folder:
            logger.warning('GalleryShowPictureRedirectView: The \'folder\' '
                           'request parameter cold not be parsed. Returning '
                           '410. \'folder\' doubledecoded was %s' % (folder))
            # The old page prints a load of garbage. This will
            # return a 410 GONE instead.
            return None

        albums = Album.objects.filter(oldFolder__startswith = folder)
        if not albums:
            logger.warning('GalleryShowPictureRedirectView: The album could '
                           'not be found when comparing the \'folder\' '
                           'request parameter with \'oldFolder\' on albums. '
                           'Returning 404. \'folder\' doubledecoded was %s'
                           % (folder))
            raise Http404("Albummet kan ikke findes")

        gfyear = albums[0].gfyear
        album_slug = albums[0].slug
        images = list(albums[0].basemedia.all())

        if pic_count >= len(images):
            logger.warning('GalleryShowPictureRedirectView: The picture could '
                           'not be found. \'pic_count\' was larger than the '
                           'number of images in the album. Returning 404. '
                           '\'pic_count\' was %s. Album was %s' % (pic_count,
                                                                   albums[0]))
            raise Http404("Billedet kan ikke findes")

        image_slug = images[pic_count].slug

        return reverse('image', kwargs={'gfyear': gfyear,
                                        'album_slug': album_slug,
                                        'image_slug': image_slug})


def http410(request):
    context = {"status": "410 Gone"}
    return render(request, "404.html", context, status=410)

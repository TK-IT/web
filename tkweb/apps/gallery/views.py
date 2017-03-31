# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from tkweb.apps.gallery.models import Album, BaseMedia, Image, GenericFile
import os


def gallery(request, **kwargs):
    allalbums = Album.objects.exclude(basemedia__isnull=True)
    # Without order_by(), distinct() still returns duplicate gfyears.
    years = allalbums.order_by().values_list('gfyear', flat=True).distinct()
    years = sorted(years, reverse=True)
    if not years:
        raise Http404("No albums exist")
    latest_year = years[0]

    show_year = kwargs.get('gfyear', latest_year)
    show_year = int(show_year) if show_year else None

    albums = allalbums.filter(gfyear__exact=show_year).prefetch_related('basemedia').annotate(count=Count('basemedia'))

    firstImages = BaseMedia.objects.filter(album__in=albums, isCoverFile=True).prefetch_related('album').select_subclasses()
    firstImages = {fi.album: fi for fi in firstImages}
    albumSets = [(a, firstImages.get(a)) for a in albums]

    context = {'years': years,
               'show_year': show_year,
               'albumSets': albumSets,
    }

    return render(request, 'gallery.html', context)


def album(request, gfyear, album_slug):
    album = get_object_or_404(Album, gfyear=gfyear, slug=album_slug)
    files = album.basemedia.filter(visibility=BaseMedia.PUBLIC).select_subclasses()
    context = {'album': album,
               'files': files}
    return render(request, 'album.html', context)


def image(request, gfyear, album_slug, image_slug, **kwargs):
    album = get_object_or_404(Album, gfyear=gfyear, slug=album_slug)

    # list() will force evaluation of the QuerySet. It is now iterable.
    files = list(album.basemedia.exclude(notPublic=True).select_subclasses())
    start_file = album.basemedia.filter(album=album, slug=image_slug).select_subclasses().first()

    if not start_file:
        raise Http404("Billedet kan ikke findes")

    if start_file.notPublic:
        raise Http404("Billedet kan ikke findes")

    prev_files = files[1:]+files[:1]
    next_files = files[-1:]+files[:-1]
    file_orders = zip(files, prev_files, next_files)
    file_count = len(files)

    context = {
        'album': album,
        'file_orders': file_orders,
        'start_file': start_file,
        'file_count': file_count,
    }
    return render(request, 'image.html', context)


@require_POST
@permission_required('gallery.add_image', raise_exception=True)
def upload(request):
    file = upload_receive(request)
    album = Album.objects.get(id=int(request.POST['object_id']))
    ext = os.path.splitext(file.name)[1].lower()

    if ext in (".png", ".gif", ".jpg", ".jpeg" ):
        instance = Image(file=file, album=album)
    elif ext in (".mp3"):
        instance = GenericFile(file=file, album=album)
        instance.type = BaseMedia.AUDIO
    elif ext in (".mp4"):
        instance = GenericFile(file=file, album=album)
        instance.type = BaseMedia.VIDEO
    else:
        instance = GenericFile(file=file, album=album)
        instance.type = BaseMedia.OTHER

    try:
        instance.full_clean()
    except ValidationError as exn:
        try:
            error = ' '.join(
                '%s: %s' % (k, v)
                for k, vs in exn.message_dict.items()
                for v in vs)
        except AttributeError:
            error = ' '.join(exn.messages)

        jfu_msg = {
            'name': file.name,
            'size': file.size,
            'error': error,
        }
        return UploadResponse(request, jfu_msg)

    instance.save()
    jfu_msg = {
        'name': os.path.basename(instance.file.path),
        'size': file.size,
        'url': instance.file.url,
    }
    return UploadResponse(request, jfu_msg)


@require_POST
@permission_required('gallery.delete_image', raise_exception=True)
def upload_delete(request, pk):
    success = True
    try:
        instance = Image.objects.get(pk=pk)
        instance.image.delete(save=False)
        instance.delete()
    except Image.DoesNotExist:
        success = False

    return JFUResponse(request, success)

# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from tkweb.apps.gallery.models import Album, BaseMedia, Image, File
import os


def gallery(request, **kwargs):
    albums = Album.objects.exclude(basemedia__isnull=True)
    gfyears = sorted(set([a.gfyear for a in albums]), reverse=True)
    group_by_year = [[y, [[a, a.basemedia.exclude(notPublic=True).select_subclasses().first(),
                           len(a.basemedia.exclude(notPublic=True).select_subclasses())] for a in
                          albums if a.gfyear == y]] for y in gfyears]

    qs = Album.objects.all().aggregate(Max('gfyear'))
    latest_gfyear = qs['gfyear__max']
    gfyear = int(kwargs.get('gfyear', latest_gfyear))

    context = {'group_by_year': group_by_year,
               'show_year': gfyear}

    return render(request, 'gallery.html', context)


def album(request, gfyear, album_slug):
    album = get_object_or_404(Album, gfyear=gfyear, slug=album_slug)
    images = album.basemedia.exclude(notPublic=True).select_subclasses()
    context = {'album': album,
               'images': images}
    return render(request, 'album.html', context)


def image(request, gfyear, album_slug, image_slug, **kwargs):
    album = get_object_or_404(Album, gfyear=gfyear, slug=album_slug)

    # list() will force evaluation of the QuerySet. We can now use .index()
    files = list(album.basemedia.exclude(notPublic=True).select_subclasses())
    paginator = Paginator(files, 1)
    start_file = album.basemedia.filter(album=album, slug=image_slug).select_subclasses().first()
    if not start_file:
        raise Http404("Billedet kan ikke findes")

    if start_file.notPublic:
        raise Http404("Billedet kan ikke findes")
    try:
        prev_file = paginator.page((files.index(start_file))+1-1)[0]
        # +1 because paginator is 1-indexed, -1 to get the previous image
    except EmptyPage:
        # We are at the first image
        prev_file = paginator.page(paginator.num_pages)[0]

    try:
        next_file = paginator.page((files.index(start_file))+1+1)[0]
        # +1 because paginator is 1-indexed, +1 to get the next image
    except EmptyPage:
        # We are at the last image
        next_file = paginator.page(1)[0]


    context = {
        'album': album,
        'files': files,
        'start_file': start_file,
        'prev_file': prev_file,
        'next_file': next_file,
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
    elif ext in (".mp3", ".mp4", ".pdf", ".txt"):
        instance = File(file=file, album=album)
    else:
        jfu_msg = {
            'name': file.name,
            'size': file.size,
            'error': "Unsurported file type",
        }
        return UploadResponse(request, jfu_msg)

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

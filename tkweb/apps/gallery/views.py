# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.shortcuts import get_object_or_404, get_list_or_404
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from tkweb.apps.gallery.models import Album, Image
import os


def gallery(request, **kwargs):
    albums = Album.objects.exclude(images__isnull=True)
    gfyears = sorted(set([a.gfyear for a in albums]), reverse=True)
    group_by_year = [[y, [a for a in albums if a.gfyear == y]] for y
                     in gfyears]
    context = {'group_by_year': group_by_year}
    qs = Album.objects.all().aggregate(Max('gfyear'))
    latest_gfyear = qs['gfyear__max']
    gfyear = kwargs.get('gfyear', latest_gfyear)
    context['show_year'] = None if gfyear is None else int(gfyear)
    get_list_or_404(Album, gfyear=context['show_year'])
    return render(request, 'gallery.html', context)


def album(request, gfyear, album_slug):
    album = get_object_or_404(Album, slug=album_slug)
    if int(gfyear) != album.gfyear:
        return redirect(
            'album',
            gfyear=album.gfyear,
            album_slug=album_slug)
    else:
        context = {'album': album}
        return render(request, 'album.html', context)


def image(request, album_slug, image_slug, **kwargs):
    album = get_object_or_404(Album, slug=album_slug)
    if not album.images.filter(slug=image_slug):
        return redirect(
            'album',
            gfyear=album.gfyear,
            album_slug=album_slug)
    else:
        image = album.images.get(slug=image_slug)
        context = {
            'album': album,
            'start_image': image,
        }
        next_image = album.images.filter(date__gt=image.date)
        try:
            context['next_image'] = next_image[0]
        except:
            context['next_image'] = image
            prev_image = album.images.filter(date__lt=image.date).reverse()
        try:
            context['prev_image'] = prev_image[0]
        except:
            context['prev_image'] = image
    return render(request, 'image.html', context)


@require_POST
@permission_required('gallery.add_image', raise_exception=True)
def upload(request):
    # The assumption here is that jQuery File Upload
    # has been configured to send files one at a time.
    # If multiple files can be uploaded simulatenously,
    # 'file' may be a list of files.
    image = upload_receive(request)
    content_type = ContentType.objects.get(model=request.POST['content_type'])
    object_id = request.POST['object_id']
    instance = Image(image=image, content_type=content_type,
                     object_id=object_id)
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
        file_dict = {
            'name': image.name,
            'size': image.size,
            'error': error,
        }
        return UploadResponse(request, file_dict)
    instance.save()

    basename = os.path.basename(instance.image.path)

    file_dict = {
        'name': basename,
        'size': image.size,

        'url': instance.image.url,
    }

    return UploadResponse(request, file_dict)


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

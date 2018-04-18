# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

from django.contrib.syndication.views import Feed
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import Count
from django.http import (
    Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect)
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from tkweb.apps.gallery.models import Album, BaseMedia, Image, GenericFile
from tkweb.apps.gallery.forms import EditVisibilityForm
import os
import logging
import datetime

logger = logging.getLogger(__name__)

GALLERY_PERMISSION = 'gallery.change_image'


def gallery(request, **kwargs):
    allalbums = Album.objects.all()
    edit_visibility = request.user.has_perm(GALLERY_PERMISSION)
    if not edit_visibility:
        # Hide albums with no public images
        allalbums = allalbums.filter(basemedia__visibility=BaseMedia.PUBLIC)
    # Hide albums with no images
    allalbums = allalbums.exclude(basemedia__isnull=True)
    # Without order_by(), distinct() still returns duplicate gfyears.
    years = allalbums.order_by().values_list('gfyear', flat=True).distinct()
    years = sorted(years, reverse=True)
    if not years:
        raise Http404("No albums exist")
    latest_year = years[0]

    show_year = kwargs.get('gfyear', latest_year)
    show_year = int(show_year) if show_year else None

    albums = allalbums.filter(gfyear__exact=show_year)
    albums = albums.annotate(count=Count('basemedia'))

    firstImages = BaseMedia.objects.filter(album__in=albums, isCoverFile=True)
    firstImages = firstImages.select_subclasses()
    firstImages = {fi.album_id: fi for fi in firstImages}
    albumSets = [(a, firstImages.get(a.id)) for a in albums]

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

    edit_visibility = request.user.has_perm(GALLERY_PERMISSION)
    new_file = album.basemedia.filter(visibility=BaseMedia.NEW).first()
    if edit_visibility and new_file:
        if request.POST.get('set_all_new_visible'):
            qs = album.basemedia.filter(visibility=BaseMedia.NEW)
            qs.update(visibility=BaseMedia.PUBLIC)

            # Update isCoverFile
            album.clean()

            return redirect('album', gfyear=gfyear, album_slug=album_slug)

        kwargs = dict(gfyear=album.gfyear, album_slug=album.slug,
                      image_slug=new_file.slug)
        context['edit_visibility_link'] = (
            reverse('image', kwargs=kwargs) + '?v=1')

        qs = album.basemedia.all().order_by()
        qs_visibility = qs.values_list('visibility')
        visibility_counts = dict(qs_visibility.annotate(count=Count('pk')))
        c_public = visibility_counts.pop(BaseMedia.PUBLIC, 0)
        c_discarded = visibility_counts.pop(BaseMedia.DISCARDED, 0)
        c_sensitive = visibility_counts.pop(BaseMedia.SENSITIVE, 0)
        c_delete = visibility_counts.pop(BaseMedia.DELETE, 0)
        c_new = visibility_counts.pop(BaseMedia.NEW, 0)
        if visibility_counts:
            raise ValueError(visibility_counts)
        context['visible_count'] = c_public
        context['hidden_count'] = c_discarded + c_sensitive + c_delete + c_new
        context['new_count'] = c_new
    try:
        r = render(request, 'album.html', context)
    except OSError as exn:
        logger.error('OSError: %s at %s' % (exn, request.path))
        context = {'status': '500 Internal Server Error',
                   'explanation': 'Dette album kan ikke vises, da en eller flere af de tilføjede filer er beskadiget.'}
        r = render(request, '404.html', context)
        r.status_code = 500
    return r


def image(request, gfyear, album_slug, image_slug, **kwargs):
    album = get_object_or_404(Album, gfyear=gfyear, slug=album_slug)

    edit_visibility = (bool(request.GET.get('v')) and
                       request.user.has_perm(GALLERY_PERMISSION))

    qs = album.basemedia.all()
    if not edit_visibility:
        qs = qs.filter(visibility=BaseMedia.PUBLIC)
    qs = qs.select_subclasses()
    # list() will force evaluation of the QuerySet. It is now iterable.
    files = list(qs)
    start_file = album.basemedia.filter(album=album, slug=image_slug).select_subclasses().first()
    if edit_visibility:
        form = EditVisibilityForm(files)
        for file, (pk, key) in zip(files, form.basemedias):
            file.visibility_field = form[key]

    if not start_file:
        raise Http404("Billedet kan ikke findes")

    if start_file.notPublic and not edit_visibility:
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
        'edit_visibility': edit_visibility,
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


@require_POST
@permission_required(GALLERY_PERMISSION, raise_exception=True)
def set_visibility(request):
    try:
        form = EditVisibilityForm.from_POST(request.POST)
    except EditVisibilityForm.Missing as exn:
        return HttpResponseBadRequest(str(exn))
    if not form.is_valid():
        return HttpResponseBadRequest(str(form.errors))
    for pk, key in form.basemedias:
        initial = form.fields[key].initial
        value = form.cleaned_data[key]
        if initial != value:
            BaseMedia.objects.filter(pk=pk).update(visibility=value)

    albums = list(Album.objects.filter(pk__in=form.album_pks))
    for a in albums:
        # Update isCoverFile
        a.clean()

    # Redirect to album
    if albums:
        album = albums[0]
        kwargs = dict(gfyear=album.gfyear, album_slug=album.slug)
        return HttpResponseRedirect(reverse('album', kwargs=kwargs))
    else:
        return HttpResponse('Synlighed på givne billeder er blevet opdateret')


class AlbumFeed(Feed):
    title = 'TÅGEKAMMERETs billedalbummer'

    def link(self):
        return reverse('gallery_index')

    description = 'Feed med nye billedalbummer fra TÅGEKAMMERETs begivenheder.'

    def items(self):
        return Album.objects.order_by('-publish_date')

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_pubdate(self, item):
        return datetime.datetime.combine(item.publish_date, datetime.time.min)

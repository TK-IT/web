# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

import os
import re

from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import (
    Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect)
from django import forms
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from tkweb.apps.gallery.models import Album, BaseMedia, Image, GenericFile


class EditVisibilityForm(forms.Form):
    class Missing(Exception):
        pass

    def __init__(self, file_visibility, **kwargs):
        super(EditVisibilityForm, self).__init__(**kwargs)
        self.basemedias = []
        self.album_pks = set()
        for file in file_visibility:
            if isinstance(file, BaseMedia):
                pk = file.pk
                visibility = file.visibility
                album = file.album_id
            elif isinstance(file, tuple):
                pk, visibility, album = file
            else:
                raise TypeError(type(file))
            k = 'i%s' % pk
            self.album_pks.add(album)
            self.fields[k] = forms.ChoiceField(
                choices=BaseMedia.VISIBILITY,
                initial=visibility,
                widget=forms.RadioSelect)
            self.basemedias.append((pk, k))

    @classmethod
    def from_POST(cls, post_data):
        pattern = r'^i(\d+)$'
        pks = []
        for k, v in post_data.items():
            mo = re.match(pattern, k)
            if mo:
                pks.append(int(mo.group(1)))
        files = BaseMedia.objects.filter(pk__in=pks)
        files = list(files.values_list('pk', 'visibility', 'album_id'))
        found_pks = [f[0] for f in files]
        missing = set(pks) - set(found_pks)
        if missing:
            raise cls.Missing('Not found: %r' % (sorted(missing),))
        return cls(files, data=post_data)


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

    edit_visibility = request.user.has_perms('gallery.change_image')
    file = album.basemedia.first()
    if edit_visibility and file:
        kwargs = dict(gfyear=album.gfyear, album_slug=album.slug,
                      image_slug=file.slug)
        context['edit_visibility_link'] = (
            reverse('image', kwargs=kwargs) + '?v=1')
    return render(request, 'album.html', context)


def image(request, gfyear, album_slug, image_slug, **kwargs):
    album = get_object_or_404(Album, gfyear=gfyear, slug=album_slug)

    edit_visibility = (bool(request.GET.get('v')) and
                       request.user.has_perms('gallery.change_image'))

    qs = album.basemedia.all()
    if not edit_visibility:
        qs = qs.filter(visibility=BaseMedia.PUBLIC)
    qs = qs.select_subclasses()
    # list() will force evaluation of the QuerySet. It is now iterable.
    files = list(qs)
    form = EditVisibilityForm(files)
    start_file = album.basemedia.filter(album=album, slug=image_slug).select_subclasses().first()
    if edit_visibility:
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
@permission_required('gallery.change_image', raise_exception=True)
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

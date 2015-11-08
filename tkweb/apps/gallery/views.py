import os
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from tkweb.apps.gallery.models import Album, Image


def gallery(request, **kwargs):
    albums = Album.objects.exclude(images__isnull=True)
    gfyears = sorted(set([a.gfyear for a in albums]), reverse=True)
    group_by_year = [[y, [a for a in albums if a.gfyear==y]] for y in gfyears]
    context = {'group_by_year': group_by_year}
    if kwargs['gfyear']:
        show_year = int(kwargs['gfyear'])
        get_list_or_404(Album, gfyear=show_year)
        context['show_year'] = show_year
    else:
        qs = Album.objects.all().aggregate(Max('gfyear'))
        latest_gfyear = qs['gfyear__max']
        context['show_year'] = show_year
    return render(request, 'gallery.html', context)
    
def album(request, gfyear, album_slug):
    album = get_object_or_404(Album, slug=album_slug)
    if int(gfyear) != album.gfyear:
        return redirect(
            'gallery:album', 
            gfyear=album.gfyear, 
            album_slug=album_slug,
        )
    else:
        context = {'album': album}
        return render(request, 'album.html', context)

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
    instance = Image(image=image, content_type=content_type, object_id=object_id)
    instance.save()

    basename = os.path.basename(instance.image.path)

    file_dict = {
        'name' : basename,
        'size' : image.size,

        'url': instance.image.url,

        'deleteUrl': reverse('jfu_delete', kwargs={'pk': instance.pk}),
        'deleteType': 'POST',
    }

    return UploadResponse(request, file_dict)

@require_POST
@permission_required('gallery.delete_image', raise_exception=True)
def upload_delete(request, pk):
    success = True
    try:
        instance = Image.objects.get(pk=pk)
        os.unlink(instance.image.path)
        instance.delete()
    except Image.DoesNotExist:
        success = False

    return JFUResponse(request, success)

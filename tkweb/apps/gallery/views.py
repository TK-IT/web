import os
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template import RequestContext
from django.views import generic
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse

from tkweb.apps.gallery.models import Album, Image

def gallery(request):
    albums = Album.objects.all()
    context = {'albums': albums}
    return render(request, 'gallery.html', context)

@permission_required('gallery.add_image')
def galleryImgUpload(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    context = RequestContext(request, {
        'album_id' : album_id,
        'album_name' : str(album),
    })
    return render_to_response('album-img-upload.html', context)

@require_POST
@permission_required('gallery.add_image', raise_exception=True)
def upload(request):

    # jQuery File Upload needs to send files one at a time.
    # If multiple files can be uploaded simulatenously,
    # 'image' may be a list of files.
    image = upload_receive(request)
    album_id = request.POST['album_id']
    album = get_object_or_404(Album, id=album_id)
    instance = Image(image = image, album = album)
    instance.save()

    basename = os.path.basename(instance.image.path)

    file_dict = {
        'name' : basename,
        'size' : image.size,

        'url': instance.image.url,
        'thumbnailUrl': instance.thumbnail.url,

        'deleteUrl': reverse('jfu_delete', kwargs = { 'pk': instance.pk }),
        'deleteType': 'POST',
    }

    return UploadResponse(request, file_dict)

@require_POST
@permission_required('gallery.add_image', raise_exception=True)
def upload_delete( request, pk ):
    success = True
    try:
        instance = Image.objects.get( pk = pk )
        os.unlink( instance.image.path )
        os.unlink( instance.thumbnail.path )
        instance.delete()
    except Image.DoesNotExist:
        success = False

    return JFUResponse( request, success )

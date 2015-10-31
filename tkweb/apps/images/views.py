import os
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse

from tkweb.apps.images.models import Image

@require_POST
@permission_required('image.add_image', raise_exception=True)
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
@permission_required('image.delete_image', raise_exception=True)
def upload_delete(request, pk):
    success = True
    try:
        instance = Image.objects.get(pk=pk)
        os.unlink(instance.image.path)
        instance.delete()
    except Image.DoesNotExist:
        success = False

    return JFUResponse(request, success)

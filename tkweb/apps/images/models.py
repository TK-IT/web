import os
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify

def file_name(instance, filename):
    sepFilename = os.path.splitext(filename)
    newFilename = slugify(sepFilename[0]) + sepFilename[1]
    content_type_folder = slugify(instance.content_type.model)
    object_id_folder = slugify(instance.object_id)
    return '/'.join([content_type_folder, object_id_folder, newFilename])

class Image(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    associatedObject = generic.GenericForeignKey('content_type', 'object_id')

    image = models.ImageField(upload_to=file_name)
    caption = models.CharField(max_length=200, blank=True)

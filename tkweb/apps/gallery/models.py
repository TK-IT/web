import os
from django.db import models
from django.utils.text import slugify
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

def file_name(instance, filename):
    sepFilename = os.path.splitext(filename)
    newFilename = slugify(sepFilename[0]) + sepFilename[1]
    folder = slugify(str(instance.album.gfyear) + '-' + instance.album.title)
    return '/'.join(['gallery', folder, newFilename])

class Album(models.Model):
    title = models.CharField(max_length = 200)
    gfyear = models.PositiveSmallIntegerField()
    description = models.TextField(blank = True)

    def __unicode__(self):
        return self.title

class Image(models.Model):
    album = models.ForeignKey(Album, related_name = 'images')
    image = models.ImageField(upload_to = file_name)
    thumbnail = ImageSpecField(source = 'image',
                               processors = [ResizeToFill(160, 120)],
                               format = 'JPEG',
                               options = {'quality': 60},)
    caption = models.CharField(max_length = 200, blank=True)

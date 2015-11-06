from PIL.ExifTags import TAGS
from datetime import date, datetime
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from sorl.thumbnail import ImageField
import PIL
import os


def file_name(instance, filename):
    sepFilename = os.path.splitext(filename)
    newFilename = slugify(sepFilename[0]) + sepFilename[1]
    content_type_folder = slugify(instance.content_type.model)
    object_id_folder = slugify(instance.object_id)
    return '/'.join([content_type_folder, object_id_folder, newFilename])

def get_exif_date_or_now(filename):
    image = PIL.Image.open(filename)
    info = image._getexif()
    if info is not None:
        exif = {}
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            exif[decoded] = value

        for t in ["Original", "Digitized", ""]:
            """
            Check the exif fields DateTimeOriginal, DateTimeDigitized and
            DateTime in that order. Return when the first is found.
            """
            if 'DateTime' + t in exif:
                s = exif['DateTime' + t]
                if type(s) is tuple:
                    s = str(s[0])
                if 'SubsecTime' + t in exif:
                    ms = exif['SubsecTime' + t]
                    if type(ms) is tuple:
                        ms = str(ms[0])
                else:
                    ms = '0'
                s += "." + ms
                return datetime.strptime(s, '%Y:%m:%d %H:%M:%S.%f')
    return datetime.now()

class Image(models.Model):

    class Meta:
        ordering = ['date']

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    associatedObject = generic.GenericForeignKey('content_type', 'object_id')

    image = ImageField(upload_to=file_name)
    date = models.DateTimeField(null=True,blank=True)
    caption = models.CharField(max_length=200, blank=True)

    def save(self):
        self.date = get_exif_date_or_now(self.image)
        super(Image, self).save()

class Album(models.Model):
    class Meta:
        ordering = ['gfyear', 'order']

    def nextGfyear():
        # TODO: Dette skal erstattes af et globalt gfyear på et
        # tidspunkt

        if Album.objects.exists():
            gfyear = Album.objects.last().gfyear
        else:
            gfyear = date.today().year
        return gfyear

    def nextOrder():
        if Album.objects.exists():
            order = Album.objects.last().order
        else:
            order = 1
        return order

    title = models.CharField(max_length = 200)
    publish_date = models.DateField(default=date.today())
    eventalbum = models.BooleanField(default=True)
    gfyear = models.PositiveSmallIntegerField(default=nextGfyear)
    slug = models.SlugField(unique=True, editable=False)
    order = models.PositiveSmallIntegerField(default=nextOrder) # skal udfases
    description = models.TextField(blank = True)
    images = generic.GenericRelation(Image)
    
    def save(self, *args, **kwargs):
        self.slug =  slugify('%s-%s' %(self.title, self.publish_date.year))
        super(Album, self).save(self, *args, **kwargs)


    def __str__(self):
        return '%s: %s' % (self.gfyear, self.title)

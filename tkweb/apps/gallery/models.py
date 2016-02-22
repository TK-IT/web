from PIL.ExifTags import TAGS
from datetime import date, datetime
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.http import int_to_base36
from sorl.thumbnail import ImageField
import PIL
import hashlib
import os
import shutil
import string
import tempfile


def file_name(instance, filename):
    sepFilename = os.path.splitext(filename)
    newFilename = slugify(sepFilename[0]) + sepFilename[1]
    content_type_folder = slugify(instance.content_type.model)
    object_id_folder = slugify(instance.object_id)
    return '/'.join([content_type_folder, object_id_folder, newFilename])


def get_exif_date_or_now(filename):
    try:
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
    except Exception:
        return datetime.now()

class Image(models.Model):
    SLUG_SIZE = 9

    class Meta:
        ordering = ['date']

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    associatedObject = GenericForeignKey('content_type', 'object_id')

    image = ImageField(upload_to=file_name)
    date = models.DateTimeField(null=True, blank=True)
    caption = models.CharField(max_length=200, blank=True)

    slug = models.SlugField(unique=True)

    def clean(self):
        try:
            self.image.open('rb')
            self.date = get_exif_date_or_now(self.image)

            self.image.open('rb')  # open() does a seek(0)
            m = hashlib.sha1()

            while True:
                b = self.image.read(2 ** 20)
                if not b:
                    break
                m.update(b)

        finally:
            self.image.close()

        v = int(m.hexdigest(), 16)
        slug = (int_to_base36(v) + '0' * self.SLUG_SIZE)[:self.SLUG_SIZE]

        self.slug = slug

    def __str__(self):
        return '%s, %s' % (self.slug, self.date)


class Album(models.Model):
    class Meta:
        ordering = ['gfyear', '-eventalbum', 'publish_date']

    title = models.CharField(max_length=200)
    publish_date = models.DateField()
    eventalbum = models.BooleanField()
    gfyear = models.PositiveSmallIntegerField()
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    images = GenericRelation(Image)

    def number_of_images(self):
        return self.images.count()

    def prev(self, image_slug):
        image = self.images.get(slug=image_slug)
        prev = self.images.filter(date__lt=image.date).reverse[0]
        print(prev)
        return prev

    def __str__(self):
        return '%s: %s' % (self.gfyear, self.title)

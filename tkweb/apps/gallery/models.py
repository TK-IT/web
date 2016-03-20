# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

from PIL.ExifTags import TAGS
from datetime import datetime
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from django.utils.http import int_to_base36
from django.utils.timezone import get_current_timezone
from sorl.thumbnail import ImageField
from PIL import Image as PilImage
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

def file_name(instance, path):
    filename = os.path.split(path)[1]
    sepFilename = os.path.splitext(filename)
    newFilename = slugify(sepFilename[0]) + sepFilename[1]
    gfyear = str(instance.album.gfyear)
    album_slug = instance.album.slug

    return '/'.join([gfyear, album_slug, newFilename])


def get_exif_date(filename):
    logger.debug('get_exif_date: called with filename: %s' % filename.name)
    try:
        image = PilImage.open(filename)
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
                    logger.debug('get_exif_date: found EXIF field DateTime%s. Parsed it as %s', t, s)

                    if 'SubsecTime' + t in exif:
                        ms = exif['SubsecTime' + t]
                        if type(ms) is tuple:
                            ms = str(ms[0])
                        logger.debug('get_exif_date: found EXIF field SubsecTime. Parsed it as %s', ms)
                    else:
                        ms = '0'

                    s += "." + ms
                    dt = datetime.strptime(s, '%Y:%m:%d %H:%M:%S.%f')
                    dt = dt.replace(tzinfo=get_current_timezone())

                    logger.info('get_exif_date: returning exif date: %s', dt)
                    return dt
    except Exception as e:
        logger.warning('get_exif_date: An exception occurred in this slightly volatile function.', exc_info=True)

    logger.info('get_exif_date: could not get exif date. Returning none')
    return None

class Album(models.Model):
    class Meta:
        ordering = ['-gfyear', '-eventalbum', '-publish_date']
        unique_together = (('gfyear', 'slug'),)

    title = models.CharField(max_length=200)
    publish_date = models.DateField()
    eventalbum = models.BooleanField()
    gfyear = models.PositiveSmallIntegerField()
    slug = models.SlugField()
    description = models.TextField(blank=True)

    def number_of_images(self):
        return self.images.count()

    def prev(self, image_slug):
        image = self.images.get(slug=image_slug)
        prev = self.images.filter(date__lt=image.date).reverse[0]
        print(prev)
        return prev

    def __str__(self):
        return '%s: %s' % (self.gfyear, self.title)

class Image(models.Model):
    class Meta:
        ordering = ['date']

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="images")

    image = ImageField(upload_to=file_name)
    date = models.DateTimeField(null=True, blank=True)
    caption = models.CharField(max_length=200, blank=True)

    slug = models.SlugField(blank=True)

    def clean(self):
        self.date = get_exif_date(self.image)
        if self.date == None:
            self.slug = os.path.basename(self.image.name)
            logger.debug('slug')
        else:
            self.slug = self.date.strftime('%Y%m%d%H%M%S_%f')[:len("YYYYmmddHHMMSS_ff")]
            logger.debug('slug')

    def __str__(self):
        return '%s' % (self.slug)

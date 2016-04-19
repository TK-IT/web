# encoding: utf8
from __future__ import absolute_import, unicode_literals, division

from PIL.ExifTags import TAGS
from constance import config
from datetime import date, datetime
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.http import int_to_base36
from django.utils.timezone import get_current_timezone
from model_utils.managers import InheritanceManager
from sorl.thumbnail import get_thumbnail
from versatileimagefield.fields import VersatileImageField
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from PIL import Image as PilImage
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

def file_name(instance, path):
    filename = os.path.basename(path)
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

                    if any(str(n) in s for n in range(1,10)):
                        dt = datetime.strptime(s, '%Y:%m:%d %H:%M:%S.%f')
                        dt = dt.replace(tzinfo=get_current_timezone())

                        logger.info('get_exif_date: returning exif date: %s', dt)
                        return dt

                    logger.debug('get_exif_date: the DateTime%s field only contained zeros. Trying next field', t)

    except AttributeError as e:
        logger.info('get_exif_date: could not get exif data. This file is properly not a jpg or tif. Returning None')
        return None

    except Exception as e:
        logger.warning('get_exif_date: An exception occurred in this slightly volatile function.', exc_info=True)

    logger.info('get_exif_date: could not get exif date. Returning None')
    return None

def get_gfyear():
    return config.GFYEAR

class Album(models.Model):
    class Meta:
        ordering = ['gfyear', '-eventalbum', 'oldFolder', 'publish_date']
        unique_together = (('gfyear', 'slug'),)

    title = models.CharField(max_length=200)
    publish_date = models.DateField(blank=True, null=True, default=date.today)
    eventalbum = models.BooleanField(default=True)
    gfyear = models.PositiveSmallIntegerField(default=get_gfyear)
    slug = models.SlugField()
    description = models.TextField(blank=True)

    oldFolder = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return '%s: %s' % (self.gfyear, self.title)

class BaseMedia(models.Model):
    class Meta:
        ordering = ['date', 'slug']
        unique_together = (('album', 'slug'),)

    objects = InheritanceManager()
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='basemedia')

    date = models.DateTimeField(null=True, blank=True)
    notPublic = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True)

    slug = models.SlugField(blank=True)

    def admin_thumbnail(self):
        return None

    def __str__(self):
        return '%s' % (self.slug)

class Image(BaseMedia):
    file = VersatileImageField(upload_to=file_name)

    def admin_thumbnail(self):
        return u'<img src="%s" />' % (get_thumbnail(self.file, '150x150').url)
    admin_thumbnail.short_description = 'Thumbnail'
    admin_thumbnail.allow_tags = True

    def clean(self):
        self.date = get_exif_date(self.file)
        if self.date == None:
            self.slug = os.path.basename(self.file.name)
        else:
            self.slug = self.date.strftime('%Y%m%d%H%M%S_%f')[:len("YYYYmmddHHMMSS_ff")]

class File(BaseMedia):
    file = models.FileField(upload_to=file_name)

    def clean(self):
        self.slug = os.path.basename(self.file.name)

@receiver(models.signals.post_save, sender=Image)
def generateImageThumbnails(sender, instance, **kwargs):
    image_warmer = VersatileImageFieldWarmer(
        instance_or_queryset=instance,
        rendition_key_set='gallery',
        image_attr='file',
    )

    num_created, failed_to_create = image_warmer.warm()
    logger.debug('generateImageThumbnails: %d thumbnails created. Missing %s' % (
                 num_created, failed_to_create))

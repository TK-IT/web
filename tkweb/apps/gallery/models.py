from django.contrib.contenttypes import generic
from django.db import models

from tkweb.apps.images.models import Image

class Album(models.Model):
    title = models.CharField(max_length = 200)
    gfyear = models.PositiveSmallIntegerField()
    description = models.TextField(blank = True)

    images = generic.GenericRelation(Image)

    def __unicode__(self):
        return self.title

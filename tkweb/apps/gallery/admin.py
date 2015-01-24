from django import forms
from django.contrib import admin
from django.db import models
from tkweb.apps.gallery.models import Album, Image

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'gfyear', 'image_admin_url')

    def image_admin_url(self, obj):
        return '<a href="/gallery/uploadf/%s">Upload images</a>' % obj.id
    image_admin_url.allow_tags = True

admin.site.register(Album, AlbumAdmin)

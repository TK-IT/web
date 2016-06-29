# encoding: utf8
from __future__ import unicode_literals
from django import forms
from django.contrib import admin
from django.db import models
from tkweb.apps.gallery.models import Album, BaseMedia


class InlineBaseMediaAdmin(admin.TabularInline):
    model = BaseMedia
    extra = 0
    fields = ( 'admin_thumbnail', 'date', 'caption', 'notPublic', 'slug', 'forcedOrder', 'isCoverFile',)
    readonly_fields = ( 'admin_thumbnail', 'slug', 'isCoverFile',)

    def has_add_permission(self, request):
        return False


class AlbumAdminForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = [
            'title',
            'publish_date',
            'gfyear',
            'eventalbum',
            'description',
            'slug',
        ]

class AlbumAdmin(admin.ModelAdmin):
    # List display of multiple albums
    list_display = ('title', 'gfyear', 'publish_date',)
    ordering = ['-gfyear', 'eventalbum', '-oldFolder', '-publish_date'] # Reverse of models.Album.ordering
    list_filter = ('gfyear', 'eventalbum')

    # Form display of single album
    inlines = [InlineBaseMediaAdmin]
    form = AlbumAdminForm
    prepopulated_fields = { 'slug': ('title',), }
    formfield_overrides = { models.SlugField:
                            { 'widget':
                              forms.TextInput(attrs = { 'readOnly': 'True' })}}

admin.site.register(Album, AlbumAdmin)

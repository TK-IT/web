# encoding: utf8
from __future__ import unicode_literals
from django import forms
from django.contrib import admin
from django.db import models
from tkweb.apps.gallery.models import Album, BaseMedia


class InlineBaseMediaAdmin(admin.TabularInline):
    model = BaseMedia
    extra = 0
    fields = ( 'admin_thumbnail', 'date', 'caption', 'visibility', 'slug', 'forcedOrder', 'isCoverFile',)
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

    add_form_template = 'admin/gallery/add_form.html'

    def get_inline_instances(self, request, obj=None):
        if obj is None:
            # When creating Album, don't display the BaseMedia inlines
            return []
        return super(AlbumAdmin, self).get_inline_instances(request, obj)


admin.site.register(Album, AlbumAdmin)

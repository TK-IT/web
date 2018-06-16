from django import forms
from django.contrib import admin
from django.db import models
from tkweb.apps.gallery.models import Album, BaseMedia
from django.urls import reverse
from django.utils.html import format_html


class InlineBaseMediaAdmin(admin.TabularInline):
    model = BaseMedia
    extra = 0
    fields = ('admin_thumbnail', 'date', 'caption', 'visibility', 'slug', 'forcedOrder', 'isCoverFile')
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
    list_display = ('title', 'gfyear', 'publish_date', 'get_visibility_link')
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

    def get_visibility_link(self, album):
        file = album.basemedia.first()
        if file:
            kwargs = dict(gfyear=album.gfyear, album_slug=album.slug,
                          image_slug=file.slug)
            return format_html(
                '<a href="{}?v=1">Udvælg billeder</a>',
                reverse('image', kwargs=kwargs))

    get_visibility_link.short_description = 'Udvælg billeder'


admin.site.register(Album, AlbumAdmin)

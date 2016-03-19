from constance import config
from datetime import date
from django import forms
from django.contrib import admin
from django.contrib.admin import TabularInline
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.text import slugify
from sorl.thumbnail.admin import AdminImageMixin
from tkweb.apps.gallery.models import Album, Image


class InlineImageAdmin(AdminImageMixin, TabularInline):
    model = Image
    extra = 0

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

    def __init__(self, *args, **kwargs):
        if not kwargs.get('initial'):
            kwargs['initial'] = {}
            kwargs['initial'].update({
                'publish_date': date.today(),
                'gfyear': config.GFYEAR,
                'eventalbum': True,
            })
            super(AlbumAdminForm, self).__init__(*args, **kwargs)

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'gfyear', 'publish_date', 'slug')
    inlines = [InlineImageAdmin]
    form = AlbumAdminForm
    prepopulated_fields = { 'slug': ('title',), }

admin.site.register(Album, AlbumAdmin)

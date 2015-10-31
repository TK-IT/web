from django.contrib import admin
from django.contrib.contenttypes import generic
from sorl.thumbnail.admin import AdminImageMixin
from tkweb.apps.gallery.models import Album, Image


class InlineImageAdmin(AdminImageMixin, generic.GenericTabularInline):
    model = Image
    extra = 0
    def has_add_permission(self, request):
        return False

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'gfyear')
    inlines = [InlineImageAdmin]

admin.site.register(Album, AlbumAdmin)

from django.contrib import admin
from django.contrib.contenttypes import generic
from sorl.thumbnail.admin import AdminImageMixin
from tkweb.apps.gallery.models import Album, Image
from django.core.exceptions import ValidationError
from django import forms
from django.utils.text import slugify


class InlineImageAdmin(AdminImageMixin, generic.GenericTabularInline):
    model = Image
    extra = 0
    def has_add_permission(self, request):
        return False

        
class AlbumAdminForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = '__all__'

    def clean(self, *args, **kwargs):
        cleaned_data = self.cleaned_data
        title = cleaned_data.get('title')
        year = cleaned_data.get('publish_date').year
        potentialslug = slugify('%s-%s' %(title, year))
        qs = Album.objects.filter(slug=potentialslug).exclude(id=cleaned_data.get('id'))
        if qs.count() > 0:
            msg = "Albummet '%s' i %s eksisterer allerede" % (title,year)
            raise ValidationError(msg)
        cleaned_data['slug'] = potentialslug
        return cleaned_data

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'gfyear', 'publish_date', 'slug')
    inlines = [InlineImageAdmin]
    form = AlbumAdminForm
    
admin.site.register(Album, AlbumAdmin)

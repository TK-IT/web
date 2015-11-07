from django.contrib import admin
from django.contrib.contenttypes import generic
from sorl.thumbnail.admin import AdminImageMixin
from tkweb.apps.gallery.models import Album, Image
from django.core.exceptions import ValidationError
from django import forms
from django.utils.text import slugify
from datetime import date
from django.db.models import Max


class InlineImageAdmin(AdminImageMixin, generic.GenericTabularInline):
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
            'description'
        ]
        
    def get_gfyear(self):
        qs = Album.objects.all().aggregate(Max('gfyear'))
        return qs['gfyear__max']
        
    def __init__(self, *args, **kwargs):
        if not kwargs['initial']:
            kwargs['initial'] = {}
        kwargs['initial'].update({
            'publish_date': date.today(),
            'gfyear': self.get_gfyear(),
            'eventalbum': True,
        })
        super(AlbumAdminForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        cleaned_data = self.cleaned_data
        title = cleaned_data['title']
        year = cleaned_data['publish_date'].year
        potentialslug = slugify('%s-%s' %(title, year))
        qs = Album.objects.filter(slug=potentialslug)
        if qs.count() == 1 and qs[0] != cleaned_data:
            msg = "Albummet '%s' i %s eksisterer allerede" % (title,year)
            raise ValidationError(msg)

    def save(self, commit=True):
        instance = super(AlbumAdminForm, self).save(commit=False)
        instance.slug = slugify(
        '%s-%s' % (instance.title, instance.publish_date.year))
        if commit:
            instance.save()
        return instance

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'gfyear', 'publish_date', 'slug')
    inlines = [InlineImageAdmin]
    form = AlbumAdminForm

admin.site.register(Album, AlbumAdmin)

from django.conf.urls import patterns, url

from tkweb.apps.gallery import views

urlpatterns = patterns('',
    url(r'^$',
        'tkweb.apps.gallery.views.gallery',
        name='gallery_index'),
    url(r'^upload/',
        'tkweb.apps.gallery.views.upload',
        name='jfu_upload'),
    url(r'^delete/(?P<pk>\d+)$',
        'tkweb.apps.gallery.views.upload_delete',
        name='jfu_delete'),
    url(r'^(?P<gfyear>\d+)$',
        'tkweb.apps.gallery.views.gallery',
        name='gfyear'),
    url(r'^(?P<gfyear>\d+)/(?P<album_slug>[^/]+)$',
        'tkweb.apps.gallery.views.album',
        name='album'),
    url(r'^(?P<album_slug>[^/]+)$',
        'tkweb.apps.gallery.views.album',
        {'gfyear': '0000'}),
    url(r'^(?P<gfyear>\d+)/(?P<album_slug>[^/]+)/(?P<image_slug>[^/]+)$',
        'tkweb.apps.gallery.views.image',
        name='image'),
    url(r'^(?P<album_slug>[^/]+)/(?P<image_slug>[^/]+)$',
        'tkweb.apps.gallery.views.image',
        name='image'),
    )
 
from django.shortcuts import render

from tkweb.apps.gallery.models import Album

def gallery(request):
    albums = Album.objects.all()
    context = {'albums': albums}
    return render(request, 'gallery.html', context)

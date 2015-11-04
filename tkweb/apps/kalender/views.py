from django.shortcuts import render
from tkweb.apps.kalender.models import Event
from datetime import date, timedelta
def kalender(request):
    futureEvents = Event.objects.filter(date__gt=(date.today() - timedelta(days=1)))
    pastEvents = Event.objects.filter(date__range=((date.today() - timedelta(days=365)), date.today()))

    context = {'futureEvents' : futureEvents,
               'pastEvents' : pastEvents}
    return render(request, 'kalender.html', context)

from datetime import date, timedelta
from django.shortcuts import render
from tkweb.apps.calendar.models import Event

def kalender(request):
    todayish = date.today() - timedelta(days=1)
    yearAgo = date.today() - timedelta(days=365)

    futureEvents = Event.objects.filter(date__gt=(todayish))
    pastEvents = Event.objects.filter(date__range=(yearAgo, todayish))

    context = {'futureEvents' : futureEvents,
               'pastEvents' : pastEvents}
    return render(request, 'kalender.html', context)

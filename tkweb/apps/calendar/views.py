# encoding: utf8
from __future__ import unicode_literals
from datetime import date, timedelta
from django.shortcuts import render
from tkweb.apps.calendar.models import Event


def kalender(request):
    todayish = date.today() - timedelta(days=1)
    yearAgo = date.today() - timedelta(days=365)

    futureEvents = Event.objects.filter(date__gt=(todayish))
    pastEvents = Event.objects.filter(date__range=(yearAgo, todayish)).reverse()

    context = {"futureEvents": futureEvents, "pastEvents": pastEvents}
    return render(request, "kalender.html", context)

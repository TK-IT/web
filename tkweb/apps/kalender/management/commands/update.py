from django.core.management.base import BaseCommand
from icalendar import Calendar, Event, vDatetime
from tkweb.apps.kalender.models import Event
import datetime
import urllib.request

class Command(BaseCommand):
    help = 'Updater kalenderen fra ical'

    def handle(self, *args, **options):
        Event.objects.all().delete()

        url = "https://www.google.com/calendar/ical/best@taagekammeret.dk/public/basic.ics" # TODO: gem den her url et andet sted
        response = urllib.request.urlopen(url)
        data = response.read().decode('utf-8')

        cal = Calendar.from_ical(data)
        for component in cal.walk():
            if component.name == "VEVENT":
                title = component.decoded('summary').decode('utf-8')
                startdatetime = component.decoded('dtstart')
                if type(startdatetime) is datetime.datetime:
                    startdate = startdatetime.date()
                elif type(startdatetime) is datetime.date:
                    startdate = startdatetime
                description = component.decoded('description').decode('utf-8')
                e = Event(title=title, date=startdate, description=description)
                e.save()
        self.stdout.write('Kalenderen blev opdateret')

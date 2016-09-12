# encoding: utf8
from __future__ import unicode_literals
from constance import config
from django.core.management.base import BaseCommand
from icalendar import Calendar
from tkweb.apps.calendar.models import Event
import datetime
from six.moves import urllib
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Opdater kalenderen fra iCal'

    def handle(self, *args, **options):
        Event.objects.all().delete()

        url = config.ICAL_URL

        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode('utf-8')
        except ValueError as e:
            logger.error("%s Did you remember to preprend http(s?):// URL: '%s'" % (e, url))
            return
        except urllib.error.HTTPError as e:
            logger.error("Received HTTP error code %s. URL: '%s'" % (e.code, url))
            return

        try:
            cal = Calendar.from_ical(data)
        except ValueError as e:
            logger.error("Could not parse response as ical.")
            logger.debug("Response was %s" % (data))
            return

        eventsAdded = False

        for component in cal.walk():
            if component.name == "VEVENT":
                eventsAdded = True
                title = component.decoded('summary').decode('utf-8')
                startdatetime = component.decoded('dtstart')
                if type(startdatetime) is datetime.datetime:
                    startdate = startdatetime.date()
                elif type(startdatetime) is datetime.date:
                    startdate = startdatetime
                description = component.decoded('description').decode('utf-8')
                e = Event(title=title, date=startdate, description=description)
                e.clean()
                e.save()

        if not eventsAdded:
            noEventsText = "The calendar was updated, but it contained no events."
            logger.warning(noEventsText)
            self.stdout.write(noEventsText)
        else:
            finishText = 'The calendar was updated. %s events was imported.' % (Event.objects.count())
            logger.info(finishText)
            self.stdout.write(finishText)

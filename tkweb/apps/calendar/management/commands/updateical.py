# encoding: utf8
from __future__ import unicode_literals
from constance import config
from django.core.management.base import BaseCommand
from django.utils.html import strip_tags
from icalendar import Calendar
from tkweb.apps.calendar.models import Event
import datetime
from six.moves import urllib
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Opdater kalenderen fra iCal"

    def get_calendar(self):
        url = config.ICAL_URL

        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode("utf-8")
        except ValueError as e:
            logger.error(
                "%s Did you remember to preprend http(s?):// URL: '%s'" % (e, url)
            )
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
        return cal

    def handle(self, *args, **options):
        cal = self.get_calendar()
        if cal is None:
            return

        def event_key(event):
            return (event.title, event.date, event.description, event.facebook)

        previous_events = {}
        for e in Event.objects.all():
            k = event_key(e)
            if k in previous_events:
                logger.warning("Duplicate event %s, deleting", k)
                e.delete()
            else:
                previous_events[k] = e
        # At this point, "previous_events"
        # contains all the events in the database.
        assert set(Event.objects.all()) == set(previous_events.values())

        same_events = []
        new_events = []

        for component in cal.walk():
            if component.name == "VEVENT":
                title = component.decoded("summary").decode("utf-8")
                startdatetime = component.decoded("dtstart")
                if type(startdatetime) is datetime.datetime:
                    startdate = startdatetime.date()
                elif type(startdatetime) is datetime.date:
                    startdate = startdatetime
                description = component.decoded("description").decode("utf-8")

                title = strip_tags(title)
                description = strip_tags(description)

                e = Event(title=title, date=startdate, description=description)
                e.clean()
                k = event_key(e)
                if k in previous_events:
                    same_events.append(previous_events.pop(k))
                else:
                    new_events.append(e)

        # At this point, "previous_events" and "same_events"
        # contain all the events in the database.
        assert set(Event.objects.all()) == set(previous_events.values()) | set(
            same_events
        )
        # "previous_events" and "same_events" have no events in common.
        assert len(set(previous_events.values()) & set(same_events)) == 0

        # The "new_events" are events we have not seen before.
        for e in new_events:
            e.save()

        if not new_events and not same_events:
            # Calendar feed empty?
            noEventsText = "The calendar was updated, but it contained no events."
            logger.warning(noEventsText)
            print(noEventsText, file=self.stdout)
            return

        # Delete the old events that were not in "cal".
        previous_event_ids = [e.id for e in previous_events.values()]
        if previous_event_ids:
            Event.objects.filter(id__in=previous_event_ids).delete()

        # At this point, "new_events" and "same_events"
        # contain all the events in the database.
        assert set(Event.objects.all()) == set(new_events) | set(same_events)

        finishText = (
            "The calendar was updated. "
            + "%s events deleted, " % len(previous_event_ids)
            + "%s events created, " % len(new_events)
            + "%s left unchanged." % len(same_events)
        )
        # Don't log unless something changed
        if len(previous_event_ids) or len(new_events):
            logger.info(finishText)
        print(finishText, file=self.stdout)

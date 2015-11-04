from django.core.management.base import BaseCommand, CommandError
import icalendar

class Command(BaseCommand):
    help = 'Updater kalenderen fra ical'

    def handle(self, *args, **options):
        # TODO: implementer
        self.stdout.write('Kalenderen blev opdateret')

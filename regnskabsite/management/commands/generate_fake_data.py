from django.core.management.base import BaseCommand, CommandError
from regnskabsite.fixtures import generate_auto_data


class Command(BaseCommand):
    def handle(self, *args, **options):
        generate_auto_data()

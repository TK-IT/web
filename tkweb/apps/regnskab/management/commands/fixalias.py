from django.core.management.base import BaseCommand

from tkweb.apps.regnskab.models import Title, config


class Command(BaseCommand):
    def handle(self, *args, **options):
        GFYEAR = config.GFYEAR
        for t in Title.objects.all():
            if t.root.startswith("FU"):
                kind = Title.FU
            elif t.root.startswith("EFU"):
                kind = Title.EFU
            else:
                kind = Title.BEST
            if t.kind != kind:
                t.kind = kind
                self.stdout.write("%s %s" % (kind, t.display_title(GFYEAR)))
                t.save()

from django.core.management.base import BaseCommand

from tkweb.apps.regnskab.models import Alias, Title, config
from tkweb.apps.regnskab.legacy.export import is_title


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = Alias.objects.all()

        GFYEAR = config.GFYEAR
        delete_ids = []
        new = []
        for a in qs:
            if is_title(a.root) and a.period is not None:
                self.stdout.write(a.display_title(GFYEAR))
                if a.root.startswith("FU"):
                    kind = Title.FU
                elif a.root.startswith("EFU"):
                    kind = Title.EFU
                else:
                    kind = Title.BEST
                new.append(
                    Title(
                        profile_id=a.profile_id, root=a.root, kind=kind, period=a.period
                    )
                )
                delete_ids.append(a.id)
        Title.objects.bulk_create(new)
        Alias.objects.filter(id__in=delete_ids).delete()
